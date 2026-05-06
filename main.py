from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from game import Game
import stripe
import os
import urllib.parse
import json

from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from meta_progression import (
    build_meta_snapshot,
    calculate_experience_gain,
    can_unlock_talent,
    compute_level_reward_bonuses,
    compute_talent_bonuses,
    default_stats,
    decode_talent_state,
    encode_talent_state,
    evaluate_achievements,
    get_talent_definition,
    level_from_experience,
    unlocked_level_reward_ids,
)


def get_database_url() -> str:
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # SQLAlchemy expects the canonical scheme even if a provider gives postgres://
        return database_url.replace("postgres://", "postgresql://", 1)

    legacy_password = os.environ.get("db_pw")
    if legacy_password:
        return (
            "postgresql://"
            f"slaskecards:{legacy_password}"
            "@dpg-cuu6h3qj1k6c738je0j0-a.frankfurt-postgres.render.com/slaskecards"
            "?sslmode=require"
        )

    raise RuntimeError("DATABASE_URL environment variable is required.")


DATABASE_URL = get_database_url()


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class PlayerCurrency(Base):
    __tablename__ = "player_currencies"
    email = Column(String, primary_key=True, index=True)
    slaskecoins = Column(Integer, default=0)


class PlayerProgression(Base):
    __tablename__ = "player_progressions"
    email = Column(String, primary_key=True, index=True)
    stats_json = Column(Text, default="{}")
    achievements_json = Column(Text, default="[]")
    talents_json = Column(Text, default="[]")


def decode_email(email: str) -> str:
    return urllib.parse.unquote(email).strip()


def load_json_blob(raw_value: str | None, fallback):
    if not raw_value:
        return fallback
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return fallback


def get_or_create_progress(session, email: str) -> PlayerProgression:
    progression = (
        session.query(PlayerProgression)
        .filter(PlayerProgression.email == email)
        .first()
    )
    if progression:
        return progression

    progression = PlayerProgression(
        email=email,
        stats_json=json.dumps(default_stats()),
        achievements_json="[]",
        talents_json="[]",
    )
    session.add(progression)
    session.flush()
    return progression


def read_progress_state(progression: PlayerProgression):
    stats = load_json_blob(progression.stats_json, default_stats())
    achievements = load_json_blob(progression.achievements_json, [])
    talents_state = load_json_blob(progression.talents_json, [])
    talent_ranks, specialization = decode_talent_state(talents_state)
    return stats, achievements, talent_ranks, specialization


def save_progress_state(
    progression: PlayerProgression,
    stats: dict,
    achievements: list[str],
    talent_ranks: dict[str, int],
    specialization: str | None,
):
    progression.stats_json = json.dumps(stats)
    progression.achievements_json = json.dumps(sorted(set(achievements)))
    progression.talents_json = json.dumps(encode_talent_state(talent_ranks, specialization))


def build_progress_snapshot(progression: PlayerProgression) -> dict:
    stats, achievements, talent_ranks, specialization = read_progress_state(progression)
    return build_meta_snapshot(stats, achievements, talent_ranks, specialization)


def update_player_progress(email: str, stat_changes: dict[str, int]) -> dict:
    normalized_email = decode_email(email)
    session = SessionLocal()
    try:
        progression = get_or_create_progress(session, normalized_email)
        stats, achievements, talent_ranks, specialization = read_progress_state(progression)
        previous_achievements = list(achievements)
        for key, amount in stat_changes.items():
            stats[key] = int(stats.get(key, 0)) + int(amount)
        achievements = evaluate_achievements(stats, achievements)
        experience_gain = calculate_experience_gain(stat_changes, previous_achievements, achievements)
        if experience_gain > 0:
            stats["experience_total"] = int(stats.get("experience_total", 0)) + experience_gain
        save_progress_state(progression, stats, achievements, talent_ranks, specialization)
        session.commit()
        session.refresh(progression)
        return build_progress_snapshot(progression)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def calculate_elo_delta(
    player_rating: int,
    opponent_rating: int,
    score: float,
    k_factor: int = 24,
) -> int:
    expected_score = 1 / (1 + (10 ** ((opponent_rating - player_rating) / 400)))
    return int(round(k_factor * (score - expected_score)))


def update_match_progress(
    winner_email: str | None,
    loser_email: str | None,
    winner_stat_changes: dict[str, int],
    loser_stat_changes: dict[str, int],
) -> dict[str, dict] | None:
    if not winner_email and not loser_email:
        return None

    normalized_winner_email = decode_email(winner_email) if winner_email else None
    normalized_loser_email = decode_email(loser_email) if loser_email else None

    session = SessionLocal()
    try:
        winner_progress = (
            get_or_create_progress(session, normalized_winner_email)
            if normalized_winner_email
            else None
        )
        loser_progress = (
            get_or_create_progress(session, normalized_loser_email)
            if normalized_loser_email
            else None
        )

        winner_snapshot = None
        loser_snapshot = None

        winner_rating = 1500
        loser_rating = 1500

        if winner_progress:
            winner_stats, winner_achievements, winner_talent_ranks, winner_specialization = read_progress_state(winner_progress)
            winner_previous_achievements = list(winner_achievements)
            winner_rating = int(winner_stats.get("elo_rating", 1500))
        else:
            winner_stats = winner_achievements = winner_talent_ranks = winner_specialization = winner_previous_achievements = None

        if loser_progress:
            loser_stats, loser_achievements, loser_talent_ranks, loser_specialization = read_progress_state(loser_progress)
            loser_previous_achievements = list(loser_achievements)
            loser_rating = int(loser_stats.get("elo_rating", 1500))
        else:
            loser_stats = loser_achievements = loser_talent_ranks = loser_specialization = loser_previous_achievements = None

        winner_delta = calculate_elo_delta(winner_rating, loser_rating, 1.0)
        loser_delta = calculate_elo_delta(loser_rating, winner_rating, 0.0)
        winner_after_rating = max(100, winner_rating + winner_delta)
        loser_after_rating = max(100, loser_rating + loser_delta)

        if winner_progress:
            for key, amount in winner_stat_changes.items():
                winner_stats[key] = int(winner_stats.get(key, 0)) + int(amount)
            winner_stats["elo_rating"] = winner_after_rating
            winner_achievements = evaluate_achievements(winner_stats, winner_achievements)
            winner_xp_gain = calculate_experience_gain(
                winner_stat_changes,
                winner_previous_achievements,
                winner_achievements,
            )
            if winner_xp_gain > 0:
                winner_stats["experience_total"] = int(winner_stats.get("experience_total", 0)) + winner_xp_gain
            save_progress_state(
                winner_progress,
                winner_stats,
                winner_achievements,
                winner_talent_ranks,
                winner_specialization,
            )

        if loser_progress:
            for key, amount in loser_stat_changes.items():
                loser_stats[key] = int(loser_stats.get(key, 0)) + int(amount)
            loser_stats["elo_rating"] = loser_after_rating
            loser_achievements = evaluate_achievements(loser_stats, loser_achievements)
            loser_xp_gain = calculate_experience_gain(
                loser_stat_changes,
                loser_previous_achievements,
                loser_achievements,
            )
            if loser_xp_gain > 0:
                loser_stats["experience_total"] = int(loser_stats.get("experience_total", 0)) + loser_xp_gain
            save_progress_state(
                loser_progress,
                loser_stats,
                loser_achievements,
                loser_talent_ranks,
                loser_specialization,
            )

        session.commit()

        if winner_progress:
            session.refresh(winner_progress)
            winner_snapshot = build_progress_snapshot(winner_progress)
        if loser_progress:
            session.refresh(loser_progress)
            loser_snapshot = build_progress_snapshot(loser_progress)

        return {
            "winner": {
                "snapshot": winner_snapshot,
                "elo_before": winner_rating if winner_progress else None,
                "elo_after": winner_after_rating if winner_progress else None,
                "elo_delta": winner_delta if winner_progress else None,
            },
            "loser": {
                "snapshot": loser_snapshot,
                "elo_before": loser_rating if loser_progress else None,
                "elo_after": loser_after_rating if loser_progress else None,
                "elo_delta": loser_delta if loser_progress else None,
            },
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_player_talent_bonuses(email: str | None) -> dict:
    if not email:
        return {}

    normalized_email = decode_email(email)
    session = SessionLocal()
    try:
        progression = get_or_create_progress(session, normalized_email)
        _, _, talent_ranks, _ = read_progress_state(progression)
        session.commit()
        return compute_talent_bonuses(talent_ranks)
    except Exception:
        session.rollback()
        return {}
    finally:
        session.close()


def get_player_account_state(email: str | None) -> dict:
    if not email:
        return {
            "talent_bonuses": {},
            "level": 1,
            "level_rewards": [],
            "level_reward_bonuses": {},
        }

    normalized_email = decode_email(email)
    session = SessionLocal()
    try:
        progression = get_or_create_progress(session, normalized_email)
        stats, _, talent_ranks, _ = read_progress_state(progression)
        level = level_from_experience(int(stats.get("experience_total", 0)))
        session.commit()
        return {
            "talent_bonuses": compute_talent_bonuses(talent_ranks),
            "level": level,
            "level_rewards": unlocked_level_reward_ids(level),
            "level_reward_bonuses": compute_level_reward_bonuses(unlocked_level_reward_ids(level)),
        }
    except Exception:
        session.rollback()
        return {
            "talent_bonuses": {},
            "level": 1,
            "level_rewards": [],
            "level_reward_bonuses": {},
        }
    finally:
        session.close()


async def finalize_match(
    game_id: str,
    winner_id: str,
    loser_id: str | None,
    reason: str,
    winner_stat_changes: dict[str, int] | None = None,
    loser_stat_changes: dict[str, int] | None = None,
) -> dict:
    game = games[game_id]
    game.set_match_over(winner_id, reason)

    winner_player = game.players.get(winner_id)
    loser_player = game.players.get(loser_id) if loser_id else None
    progress_result = update_match_progress(
        winner_player.account_email if winner_player else None,
        loser_player.account_email if loser_player else None,
        winner_stat_changes or {"games_won": 1},
        loser_stat_changes or {"games_lost": 1},
    )

    elo_changes = {}
    for player_id, role in ((winner_id, "winner"), (loser_id, "loser")):
        if not player_id:
            continue
        role_payload = progress_result.get(role) if progress_result else None
        elo_changes[player_id] = {
            "before": role_payload.get("elo_before") if role_payload else None,
            "after": role_payload.get("elo_after") if role_payload else None,
            "delta": role_payload.get("elo_delta") if role_payload else None,
        }

    await game.broadcast({
        "type": "match_over",
        "winner": winner_id,
        "loser": loser_id,
        "reason": reason,
        "scores": {player.name: player.wins for player in game.players.values()},
        "avatars": {player.name: player.avatar for player in game.players.values()},
        "elo_changes": elo_changes,
    })
    await game.broadcast_match_state()

    return {
        "winner": winner_id,
        "loser": loser_id,
        "reason": reason,
        "elo_changes": elo_changes,
    }


async def resolve_game_state(game_id: str) -> dict | None:
    if game_id not in games:
        return None

    game = games[game_id]
    resolution = game.resolve_timeout_or_inactivity()
    if not resolution:
        return None

    return await finalize_match(
        game_id,
        resolution["winner"],
        resolution.get("loser"),
        resolution["reason"],
    )

def addOrRemoveSlaskecoins(email: str, amount: int) -> int:
    """
    Adds (or subtracts, if amount is negative) slaskecoins for the given email.
    If the user doesn't exist, they are created with an initial balance of 0.
    Returns the new balance.
    """
    session = SessionLocal()
    try:
        # Find the user by email
        player = session.query(PlayerCurrency).filter(PlayerCurrency.email == email).first()
        if not player:
            # Create new user entry if not found
            player = PlayerCurrency(email=email, slaskecoins=0)
            session.add(player)
        # Update coin balance
        player.slaskecoins += amount
        # Optional: prevent negative balances
        if player.slaskecoins < 0:
            player.slaskecoins = 0
        session.commit()
        return player.slaskecoins
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()




stripe.api_key = os.environ.get("stripe_api_key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

@app.get("/slaskecoins/{email}")
def get_slaskecoins(email: str) -> int:
    # Decode the email in case it's percent-encoded
    decoded_email = decode_email(email)
    print("Decoded email:", decoded_email)
    
    session = SessionLocal()
    try:
        # Print the entire database records with email details
        all_players = session.query(PlayerCurrency).all()
        print("Entire database:")
        for record in all_players:
            # Assuming the PlayerCurrency model has an 'email' attribute
            print("Record:", record, "Email:", getattr(record, "email", "No email attribute"))
        
        # Query for the specific player using the decoded email
        player = session.query(PlayerCurrency).filter(PlayerCurrency.email == decoded_email).first()
        
        # Print the session object and the queried player
        print("Session object:", session)
        print("Queried player:", player)
        
        return player.slaskecoins if player else 0
    finally:
        session.close()


@app.get("/meta/{email}")
def get_meta_progress(email: str):
    decoded_email = decode_email(email)
    session = SessionLocal()
    try:
        progression = get_or_create_progress(session, decoded_email)
        session.commit()
        session.refresh(progression)
        return build_progress_snapshot(progression)
    finally:
        session.close()


@app.post("/meta/{email}/talents/{talent_id}")
def unlock_talent(email: str, talent_id: str):
    decoded_email = decode_email(email)
    session = SessionLocal()
    try:
        progression = get_or_create_progress(session, decoded_email)
        stats, achievements, talent_ranks, specialization = read_progress_state(progression)
        can_unlock, error = can_unlock_talent(talent_id, achievements, talent_ranks, specialization)
        if not can_unlock:
            return {"error": error or "Unable to unlock talent"}

        if not specialization:
            talent_definition = get_talent_definition(talent_id)
            specialization = talent_definition["specialization"] if talent_definition else None
        talent_ranks[talent_id] = int(talent_ranks.get(talent_id, 0)) + 1
        achievements = evaluate_achievements(stats, achievements)
        save_progress_state(progression, stats, achievements, talent_ranks, specialization)
        session.commit()
        session.refresh(progression)
        return build_progress_snapshot(progression)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()




# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/pay")
def create_payment(
    amount: int = Body(...),
    currency: str = Body("usd"),
    description: str = Body("Payment from FastAPI"),
    email: str = Body(...),
):
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            description=description,
        )
        addOrRemoveSlaskecoins(email, 1000)
        return {"client_secret": payment_intent.client_secret}
    except Exception as e:
        return {"error": str(e)}

games: Dict[str, dict] = {}


def summarize_played_hand(cards: list[dict], hand_type: str) -> dict[str, int]:
    stat_changes: dict[str, int] = {
        "hands_played": 1,
    }

    if hand_type == "straight flush":
        stat_changes["straight_flushes_played"] = 1
    if hand_type == "royal flush":
        stat_changes["royal_flushes_played"] = 1
        stat_changes["straight_flushes_played"] = 1

    if "flush" in hand_type and cards:
        suits = {card["suit"] for card in cards}
        if len(suits) == 1:
            flush_suit = next(iter(suits)).lower()
            stat_changes[f"{flush_suit}_flushes"] = 1

    return stat_changes


def summarize_drawn_hand(cards: list[dict]) -> dict[str, int]:
    if len(cards) < 8:
        return {}

    ranks = {card["rank"] for card in cards}
    if len(ranks) == 1:
        return {"full_hand_of_a_kind_draws": 1}

    return {}

@app.get("/games")
def list_games():
    return {
        "games": [
            {
                "game_id": game_id,
                "player_count": len(game.players),
                "players": list(game.players.keys()),
            }
            for game_id, game in games.items()
        ]
    }

@app.get("/game/{game_id}/players")
def get_players(game_id: str):
    if game_id not in games:
        return {"error": "Game not found"}
    
    game = games[game_id]
    players = list(game.players.keys())
    next_player = game.get_current_player_id()
    avatars = {player.name: player.avatar for player in game.players.values()}
    return {
        "players": players,
        "next_player": next_player,
        "avatars": avatars,
        "phase": game.phase,
        "battle_deadline_at": game.battle_deadline_at,
        "shop_deadlines": dict(game.shop_deadlines),
    }

@app.post("/game/create/{game_id}")
def create_game(game_id: str):
    if game_id in games:
        return {"error": "Game ID already exists. Choose a different ID."}
    
    games[game_id] = Game()
    return {"message": f"Game {game_id} created successfully"}

@app.post("/game/join/{game_id}")
async def join_game(
    game_id: str,
    player_id: str,
    email: str | None = None,
    avatar: str | None = None,
):
    if game_id not in games:
        return {"error": "Game not found"}

    game = games[game_id]
    decoded_email = decode_email(email) if email else None
    account_state = get_player_account_state(decoded_email)
    game.add_player(
        player_id,
        account_email=decoded_email,
        talent_bonuses=account_state["talent_bonuses"],
        avatar=avatar,
        level_unlocks=account_state["level_rewards"],
        level_reward_bonuses=account_state["level_reward_bonuses"],
    )

    print(f"Player {player_id} joined {game_id}. Waiting for WebSocket connection...")

    if len(game.players) >= 2 and game.phase == "waiting":
        game.start_battle_phase()

    await game.broadcast({
        "type": "players_updated",
        "players": list(game.players.keys()),
        "next_player": list(game.players.keys())[game.turn_index] if game.players else None,
        "avatars": {player.name: player.avatar for player in game.players.values()},
    })
    await game.broadcast_match_state()

    return {"message": f"{player_id} joined game {game_id}"}

@app.post("/game/{game_id}/leave")
async def leave_game(game_id: str, player_id: str):
    if game_id not in games:
        return {"error": "Game not found"}

    game = games[game_id]
    if player_id not in game.players:
        return {"error": "Player not found"}

    if len(game.players) > 1 and game.phase != "match_over":
        opponent_id = game.get_opponent_id(player_id)
        if opponent_id:
            await finalize_match(
                game_id,
                opponent_id,
                player_id,
                f"{player_id} left the lobby.",
            )

    game.remove_player(player_id)

    if not game.players:
        del games[game_id]
        return {"message": f"{player_id} left and game {game_id} was deleted"}

    await game.broadcast({
        "type": "players_updated",
        "players": list(game.players.keys()),
        "next_player": game.get_current_player_id(),
        "avatars": {player.name: player.avatar for player in game.players.values()},
    })
    await game.broadcast_shop_status()
    await game.broadcast_match_state()

    remaining_players = list(game.players.keys())
    next_player = game.get_current_player_id()

    return {
        "message": f"{player_id} left game {game_id}",
        "players": remaining_players,
        "next_player": next_player
    }

@app.websocket("/game/{game_id}/ws/{player_id}")
async def game_websocket(websocket: WebSocket, game_id: str, player_id: str):
    if game_id not in games:
        print(f"Game ID {game_id} not found in games.")
        await websocket.close()
        return

    game = games[game_id]

    if player_id not in game.players:
        print(f"Player ID {game_id} not found in games.")
        await websocket.close()
        return

    await websocket.accept()
    game.websocket_connections[player_id] = websocket
    print(f"WebSocket connected: {player_id}")

    player = game.players[player_id]

    # ✅ Deal hand *only if* player has no cards yet    
    if not player.hand:
        for _ in range(player.hand_size):
            if game.deck:
                game.deal_card(player_id)

        print(f"Dealt hand to {player_id}: {[str(card) for card in player.hand]}")

    # ✅ Now, send hand after WebSocket connection
    hand_message = {
        "type": "new_hand",
        "player": player_id,
        "cards": [{"rank": c.rank, "suit": c.suit} for c in player.hand],
        "next_player": game.get_current_player_id(),
        "remaining_discards": player.remaining_discards,
    }
    await websocket.send_json(hand_message)
    await websocket.send_json(game.serialize_match_state())
    for game_player in game.players.values():
        await websocket.send_json(game_player.apply_upgrades())
    print(f"Sent hand to {player_id} via WebSocket: {player.hand}")

    if player.account_email:
        update_player_progress(
            player.account_email,
            summarize_drawn_hand(hand_message["cards"]),
        )

    try:
        while True:
            data = await websocket.receive_json()
            await game.broadcast(data)
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {player_id}")
    finally:
        game.websocket_connections.pop(player_id, None)


@app.post("/game/{game_id}/heartbeat/{player_id}")
async def heartbeat(game_id: str, player_id: str):
    if game_id not in games:
        return {"error": "Game not found"}

    game = games[game_id]
    if player_id not in game.players:
        return {"error": "Player not found"}

    game.record_activity(player_id)
    resolution = await resolve_game_state(game_id)
    return {
        "message": "Heartbeat received",
        "phase": game.phase,
        "resolved": resolution is not None,
    }

@app.post("/game/{game_id}/discard")
async def discard(game_id: str, request: dict):
    if game_id not in games:
        return {"error": "Game not found"}

    game = games[game_id]
    if len(game.players) < 2:
        return {"error": "Waiting for another player"}

    player_id = request.get("player_id")
    selected_cards = request.get("cards", [])

    game.record_activity(player_id)
    resolution = await resolve_game_state(game_id)
    if resolution:
        return {"error": resolution["reason"]}
    if game.phase != "battle":
        return {"error": "Round is not active"}

    if player_id not in game.players:
        return {"error": "Player not found"}

    player_keys = list(game.players.keys())

    if player_id != player_keys[game.turn_index]:
        return {"error": "Not your turn"}
    if not selected_cards:
        return {"error": "No cards selected"}

    player = game.players[player_id]

    if player.remaining_discards < 1:
        return {"error": "No discards remaining"}

    player.remaining_discards -= 1

    # Use the extracted card removal function
    result = game.remove_selected_cards(player_id, selected_cards)
    if "error" in result:
        return result

    # Broadcast updated hand to player
    hand_message = {
        "type": "hand_updated",
        "player": player_id,
        "cards": result["new_hand"],
        "remaining_discards": player.remaining_discards
    }
    await game.broadcast(hand_message)

    if player.account_email:
        draw_stats = summarize_drawn_hand(result["new_hand"])
        update_player_progress(
            player.account_email,
            {"cards_discarded": len(result["discarded"]), **draw_stats},
        )

    return {
        "message": "Cards discarded and new ones drawn",
        "discarded": result["discarded"],
        "new_hand": result["new_hand"],
        "remaining_discards": player.remaining_discards
    }

@app.post("/game/{game_id}/play_hand")
async def play_hand(game_id: str, request: dict):
    if game_id not in games:
        return {"error": "Game not found"}

    game = games[game_id]
    if len(game.players) < 2:
        return {"error": "Waiting for another player"}

    player_id = request.get("player_id")
    selected_cards = request.get("cards", [])

    game.record_activity(player_id)
    resolution = await resolve_game_state(game_id)
    if resolution:
        return {"error": resolution["reason"]}
    if game.phase != "battle":
        return {"error": "Round is not active"}

    if player_id not in game.players:
        return {"error": "Player not found"}

    player = game.players[player_id]
    opponent_id = [pid for pid in game.players if pid != player_id][0]
    opponent = game.players[opponent_id]

    async with game.lock:
        if player_id != list(game.players.keys())[game.turn_index]:
            return {"error": "Not your turn"}
            
    if not selected_cards:
        return {"error": "No cards selected"}

    # Calculate damage
    damage, hand_type, multiplier = game.calculate_damage(selected_cards, player_id)
    armor_reduction = opponent.get_armor_damage_reduction()
    actual_damage = max(
        0,
        int(round(damage * opponent.damage_taken_multiplier * (1.0 - armor_reduction))),
    )
    stat_changes = summarize_played_hand(selected_cards, hand_type)
    stat_changes["damage_dealt"] = actual_damage

    # Remove played cards
    result = game.remove_selected_cards(player_id, selected_cards)
    if "error" in result:
        return result
    stat_changes.update(summarize_drawn_hand(result["new_hand"]))

    # Apply damage to opponent
    opponent.health = max(0, opponent.health - actual_damage)

    # Check for win condition
    winner = None
    match_finished = False
    round_finished = False
    if opponent.health == 0:
        winner = player_id
        round_finished = True
        player.wins += 1
        if player.wins >= 5:
            match_finished = True

    #Increase discards
    player.remaining_discards = player.max_discards

    # Move turn
    if not winner:
        game.turn_index = (game.turn_index + 1) % len(game.players)
        game.start_battle_phase()
    player.gold += multiplier + player.gold_gain_flat

    # Broadcast update
    await game.broadcast({
        "type": "hand_played",
        "player": player_id,
        "cards": selected_cards,
        "damage": actual_damage,
        "health_update": {p.name: p.health for p in game.players.values()},
        "max_health_update": {p.name: p.max_health for p in game.players.values()},
        "score_update": {p.name: p.wins for p in game.players.values()},
        "next_player": list(game.players.keys())[game.turn_index],
        "hand_type": hand_type,
        "new_hand": result["new_hand"],  # ✅ Send updated hand
        "multiplier": multiplier,
        "winner": winner,
        "round_finished": round_finished,
        "match_finished": match_finished,
        "remaining_discards": player.remaining_discards,
        "gold": multiplier + player.gold_gain_flat
    })
    if not winner:
        await game.broadcast_match_state()
    elif match_finished:
        await finalize_match(
            game_id,
            player_id,
            opponent_id,
            f"{player_id} reached 5 wins.",
            {**stat_changes, "games_won": 1},
            {"games_lost": 1},
        )
    else:
        await game.reset_game()

    if not winner and player.account_email:
        update_player_progress(player.account_email, stat_changes)

    return {
        "message": f"{player_id} played a hand",
        "damage": actual_damage,
        "multiplier": multiplier,
        "new_hand": result["new_hand"],  # ✅ Send updated hand
        "winner": winner,
        "round_finished": round_finished,
        "match_finished": match_finished,
    }

@app.post("/game/{game_id}/end_turn")
async def end_turn(game_id: str, player_id: str):
    if game_id not in games:
        return {"error": "Game not found"}
    
    game = games[game_id]
    if len(game.players) < 2:
        return {"error": "Waiting for another player"}

    game.record_activity(player_id)
    resolution = await resolve_game_state(game_id)
    if resolution:
        return {"error": resolution["reason"]}
    if game.phase != "battle":
        return {"error": "Round is not active"}

    async with game.lock:
        player_keys = list(game.players.keys())

        if player_id != player_keys[game.turn_index]:
            return {"error": "Not your turn"}

        # Move to the next player
        game.turn_index = (game.turn_index + 1) % len(player_keys)
        next_player = player_keys[game.turn_index]
        game.start_battle_phase()

        # Broadcast turn update
        await game.broadcast({"message": "Turn ended", "next_player": next_player})
        await game.broadcast_match_state()

        return {"message": "Turn ended", "next_player": next_player}

@app.post("/game/{gameId}/{playerId}/buyupgrade/{upgrade_id}")
async def add_upgrade(gameId: str, playerId: str, upgrade_id: str):

    if gameId not in games:
        return {"error": "Game not found"}
    game = games[gameId]
    game.record_activity(playerId)
    resolution = await resolve_game_state(gameId)
    if resolution:
        return {"error": resolution["reason"]}
    if game.phase != "shop":
        return {"error": "Shop is not open"}
    price = game.get_price(upgrade_id)
    player = game.players[playerId]
    print(f"Type of price: {type(price)} and player.gold {type(player.gold)}")
    print(f"Is {price} > {player.gold}?")
    if price > player.gold:
        return {"message": "Not enough gold"}
    player.gold -= price

    async with game.lock:
        await game.add_upgrade(playerId, upgrade_id)
        await game.apply_upgrades(playerId)
        if player.account_email:
            update_player_progress(player.account_email, {"upgrades_bought": 1})
        return {
            "message": f"{playerId} bought upgrade {upgrade_id}",
            "price": price,
        }


@app.post("/game/{game_id}/shop/reroll")
async def reroll_shop(game_id: str, player_id: str):
    if game_id not in games:
        return {"error": "Game not found"}

    game = games[game_id]
    if player_id not in game.players:
        return {"error": "Player not found"}

    game.record_activity(player_id)
    resolution = await resolve_game_state(game_id)
    if resolution:
        return {"error": resolution["reason"]}
    if game.phase != "shop":
        return {"error": "Shop is not open"}

    rerolled_selection = game.reroll_shop_selection(player_id)
    if isinstance(rerolled_selection, dict) and rerolled_selection.get("error"):
        return rerolled_selection

    return {
        "message": "Shop rerolled",
        "upgrades": rerolled_selection,
        "rerolls_remaining": game.shop_rerolls_remaining.get(player_id, 0),
    }


@app.post("/game/{game_id}/shop/continue")
async def continue_from_shop(game_id: str, player_id: str):
    if game_id not in games:
        return {"error": "Game not found"}

    game = games[game_id]
    if player_id not in game.players:
        return {"error": "Player not found"}

    game.record_activity(player_id)
    resolution = await resolve_game_state(game_id)
    if resolution:
        return {"error": resolution["reason"]}
    if game.phase != "shop":
        return {"error": "Shop is not open"}

    await game.mark_shop_ready(player_id)
    return {
        "message": f"{player_id} is ready",
        "waiting_players": game.get_shop_waiting_players(),
    }
