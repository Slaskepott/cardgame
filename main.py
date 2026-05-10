import asyncio
import itertools
import random
import re
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from game import Game, HAND_MULTIPLIERS, RANK_VALUES
import os
import urllib.parse
import json
from relics import RELIC_POOL

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
    normalize_talent_element,
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

PEAK_STAT_KEYS = {
    "elo_rating",
    "max_armor_in_game",
    "max_health_in_game",
    "max_single_hand_damage",
    "max_win_health_remaining_pct",
}

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
    talent_ranks, specialization, talent_elements = decode_talent_state(talents_state)
    return stats, achievements, talent_ranks, specialization, talent_elements


def save_progress_state(
    progression: PlayerProgression,
    stats: dict,
    achievements: list[str],
    talent_ranks: dict[str, int],
    specialization: str | None,
    talent_elements: dict[str, str] | None = None,
):
    progression.stats_json = json.dumps(stats)
    progression.achievements_json = json.dumps(sorted(set(achievements)))
    progression.talents_json = json.dumps(
        encode_talent_state(talent_ranks, specialization, talent_elements)
    )


def build_progress_snapshot(progression: PlayerProgression) -> dict:
    stats, achievements, talent_ranks, specialization, talent_elements = read_progress_state(
        progression
    )
    return build_meta_snapshot(stats, achievements, talent_ranks, specialization, talent_elements)


def update_player_progress(email: str, stat_changes: dict[str, int]) -> dict:
    normalized_email = decode_email(email)
    session = SessionLocal()
    try:
        progression = get_or_create_progress(session, normalized_email)
        stats, achievements, talent_ranks, specialization, talent_elements = read_progress_state(
            progression
        )
        previous_achievements = list(achievements)
        for key, amount in stat_changes.items():
            if key in PEAK_STAT_KEYS:
                stats[key] = max(int(stats.get(key, 0)), int(amount))
            else:
                stats[key] = int(stats.get(key, 0)) + int(amount)
        achievements = evaluate_achievements(stats, achievements)
        experience_gain = calculate_experience_gain(stat_changes, previous_achievements, achievements)
        if experience_gain > 0:
            stats["experience_total"] = int(stats.get("experience_total", 0)) + experience_gain
        save_progress_state(
            progression, stats, achievements, talent_ranks, specialization, talent_elements
        )
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
            winner_stats, winner_achievements, winner_talent_ranks, winner_specialization, winner_talent_elements = read_progress_state(winner_progress)
            winner_previous_achievements = list(winner_achievements)
            winner_rating = int(winner_stats.get("elo_rating", 1500))
        else:
            winner_stats = winner_achievements = winner_talent_ranks = winner_specialization = winner_previous_achievements = winner_talent_elements = None

        if loser_progress:
            loser_stats, loser_achievements, loser_talent_ranks, loser_specialization, loser_talent_elements = read_progress_state(loser_progress)
            loser_previous_achievements = list(loser_achievements)
            loser_rating = int(loser_stats.get("elo_rating", 1500))
        else:
            loser_stats = loser_achievements = loser_talent_ranks = loser_specialization = loser_previous_achievements = loser_talent_elements = None

        winner_delta = calculate_elo_delta(winner_rating, loser_rating, 1.0)
        loser_delta = calculate_elo_delta(loser_rating, winner_rating, 0.0)
        winner_after_rating = max(100, winner_rating + winner_delta)
        loser_after_rating = max(100, loser_rating + loser_delta)

        if winner_progress:
            for key, amount in winner_stat_changes.items():
                if key in PEAK_STAT_KEYS:
                    winner_stats[key] = max(int(winner_stats.get(key, 0)), int(amount))
                else:
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
                winner_talent_elements,
            )

        if loser_progress:
            for key, amount in loser_stat_changes.items():
                if key in PEAK_STAT_KEYS:
                    loser_stats[key] = max(int(loser_stats.get(key, 0)), int(amount))
                else:
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
                loser_talent_elements,
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
        _, _, talent_ranks, _, talent_elements = read_progress_state(progression)
        session.commit()
        return compute_talent_bonuses(talent_ranks, talent_elements)
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
        stats, _, talent_ranks, _, talent_elements = read_progress_state(progression)
        level = level_from_experience(int(stats.get("experience_total", 0)))
        session.commit()
        return {
            "talent_bonuses": compute_talent_bonuses(talent_ranks, talent_elements),
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
    if winner_player:
        winner_health_pct = int(
            round((winner_player.health / max(1, winner_player.max_health)) * 100)
        )
        winner_stat_changes = {
            **(winner_stat_changes or {"games_won": 1}),
            "max_win_health_remaining_pct": winner_health_pct,
        }
    else:
        winner_stat_changes = winner_stat_changes or {"games_won": 1}

    loser_stat_changes = loser_stat_changes or {"games_lost": 1}
    progress_result = None
    if should_track_progress(game):
        progress_result = update_match_progress(
            winner_player.account_email if winner_player else None,
            loser_player.account_email if loser_player else None,
            winner_stat_changes,
            loser_stat_changes,
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
        "is_bot_match": game.is_bot_match,
        "progression_disabled": not should_track_progress(game),
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)


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
def unlock_talent(email: str, talent_id: str, element: str | None = None):
    decoded_email = decode_email(email)
    session = SessionLocal()
    try:
        progression = get_or_create_progress(session, decoded_email)
        stats, achievements, talent_ranks, specialization, talent_elements = read_progress_state(
            progression
        )
        can_unlock, error = can_unlock_talent(talent_id, achievements, talent_ranks, specialization)
        if not can_unlock:
            return {"error": error or "Unable to unlock talent"}

        talent_definition = get_talent_definition(talent_id)
        selected_element = normalize_talent_element(element)
        if talent_definition and talent_definition.get("elemental_choice"):
            talent_elements[talent_id] = selected_element or talent_elements.get(talent_id) or "Fire"

        if not specialization:
            specialization = talent_definition["specialization"] if talent_definition else None
        talent_ranks[talent_id] = int(talent_ranks.get(talent_id, 0)) + 1
        achievements = evaluate_achievements(stats, achievements)
        save_progress_state(
            progression, stats, achievements, talent_ranks, specialization, talent_elements
        )
        session.commit()
        session.refresh(progression)
        return build_progress_snapshot(progression)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.post("/meta/{email}/talents/{talent_id}/element")
def set_talent_element(email: str, talent_id: str, element: str):
    decoded_email = decode_email(email)
    normalized_element = normalize_talent_element(element)
    if not normalized_element:
        return {"error": "Invalid element"}

    session = SessionLocal()
    try:
        progression = get_or_create_progress(session, decoded_email)
        stats, achievements, talent_ranks, specialization, talent_elements = read_progress_state(
            progression
        )
        talent_definition = get_talent_definition(talent_id)
        if not talent_definition or not talent_definition.get("elemental_choice"):
            return {"error": "Talent does not support elemental selection"}

        talent_elements[talent_id] = normalized_element
        save_progress_state(
            progression, stats, achievements, talent_ranks, specialization, talent_elements
        )
        session.commit()
        session.refresh(progression)
        return build_progress_snapshot(progression)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.post("/meta/{email}/talents/actions/reset-all")
def reset_talents(email: str):
    decoded_email = decode_email(email)
    session = SessionLocal()
    try:
        progression = get_or_create_progress(session, decoded_email)
        stats, achievements, _, _, _ = read_progress_state(progression)
        save_progress_state(progression, stats, achievements, {}, None, {})
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
games: Dict[str, Game] = {}
global_chat_messages: list[dict] = []


def build_chat_message(scope: str, author: str, avatar: str, text: str, game_id: str | None = None) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "scope": scope,
        "game_id": game_id,
        "author": author,
        "avatar": avatar,
        "text": text.strip(),
        "created_at": int(time.time()),
    }


def append_global_chat_message(author: str, avatar: str, text: str) -> dict:
    entry = build_chat_message("global", author, avatar, text)
    global_chat_messages.append(entry)
    del global_chat_messages[:-80]
    return entry


@app.get("/chat/global")
def get_global_chat():
    return {"messages": global_chat_messages}


@app.post("/chat/global")
def post_global_chat_message(
    author: str = Body(...),
    text: str = Body(...),
    avatar: str = Body("👤"),
):
    normalized_author = author.strip()
    normalized_text = text.strip()
    if not normalized_author:
        return {"error": "Author is required"}
    if not normalized_text:
        return {"error": "Message is required"}
    return {"message": append_global_chat_message(normalized_author, avatar, normalized_text)}

BOT_IDENTITIES = {
    "easy": [
        ("Sootsprite", "🦊"),
        ("Pebble Pup", "🐶"),
        ("Mossling", "🌿"),
    ],
    "medium": [
        ("Mist Dealer", "🌫️"),
        ("Circuit Crow", "🐦"),
        ("Rune Fox", "🦊"),
    ],
    "hard": [
        ("Void Crown", "👑"),
        ("Oracle Coil", "🐉"),
        ("Night Algorithm", "🤖"),
    ],
}


def should_track_progress(game: Game) -> bool:
    return not game.is_bot_match


def first_number(value: str) -> int:
    match = re.search(r"-?\d+", value)
    return int(match.group(0)) if match else 0


def generate_private_game_id(prefix: str = "bot") -> str:
    while True:
        game_id = f"{prefix}-{uuid.uuid4().hex[:8]}"
        if game_id not in games:
            return game_id


def choose_bot_identity(difficulty: str) -> tuple[str, str]:
    choices = BOT_IDENTITIES.get(difficulty, BOT_IDENTITIES["medium"])
    return random.choice(choices)


def get_bot_delay_seconds(game: Game) -> float:
    if game.phase == "shop":
        return {"easy": 2.8, "medium": 1.9, "hard": 1.2}.get(game.bot_difficulty or "medium", 1.9)
    return {"easy": 2.4, "medium": 1.5, "hard": 0.95}.get(game.bot_difficulty or "medium", 1.5)


def serialize_selected_cards(cards) -> list[dict]:
    return [{"rank": card.rank, "suit": card.suit} for card in cards]


def get_bot_combo_candidates(hand, difficulty: str):
    max_cards = min(5, len(hand))
    min_cards = 1
    if difficulty == "easy":
        sizes = [5] if len(hand) >= 5 else [max_cards]
    elif difficulty == "medium":
        sizes = list(range(min(3, max_cards), max_cards + 1))
    else:
        sizes = list(range(min_cards, max_cards + 1))

    candidates = []
    for size in sizes:
        candidates.extend(itertools.combinations(hand, size))
    return candidates


def choose_best_bot_hand(game: Game, bot_id: str, difficulty: str):
    player = game.players[bot_id]
    best_result = None

    for combo in get_bot_combo_candidates(player.hand, difficulty):
        serialized_cards = serialize_selected_cards(combo)
        damage, hand_type, multiplier = game.calculate_damage(serialized_cards, bot_id)
        score = (
            damage,
            HAND_MULTIPLIERS.get(hand_type, multiplier),
            len(combo),
        )
        if best_result is None or score > best_result["score"]:
            best_result = {
                "cards": serialized_cards,
                "damage": damage,
                "hand_type": hand_type,
                "multiplier": multiplier,
                "score": score,
            }

    return best_result


def choose_bot_discards(game: Game, bot_id: str, difficulty: str):
    player = game.players[bot_id]
    if player.remaining_discards < 1 or not player.hand:
        return []

    best_hand = choose_best_bot_hand(game, bot_id, difficulty)
    if not best_hand:
        return []

    best_multiplier = best_hand["multiplier"]
    best_damage = best_hand["damage"]
    if difficulty == "easy" and (best_multiplier >= 3 or best_damage >= 48):
        return []
    if difficulty == "medium" and (best_multiplier >= 3 or best_damage >= 38):
        return []
    if difficulty == "hard" and (best_multiplier >= 2 or best_damage >= 28):
        return []

    keep_tuples = {(card["rank"], card["suit"]) for card in best_hand["cards"]}
    discard_pool = [
        card
        for card in player.hand
        if (card.rank, card.suit) not in keep_tuples
    ]
    discard_pool.sort(key=lambda card: game.get_compressed_rank_value(RANK_VALUES[card.rank]))
    discard_limit = 2 if difficulty == "easy" else 3 if difficulty == "medium" else 4
    return serialize_selected_cards(discard_pool[:discard_limit])


def bot_upgrade_score(game: Game, bot_id: str, upgrade_dict: dict, difficulty: str) -> float:
    player = game.players[bot_id]
    name = upgrade_dict["name"]
    effect = upgrade_dict["effect"]
    cost = max(1, int(upgrade_dict["cost"]))
    amount = first_number(effect)
    rarity_bonus = {
        "common": 0.4,
        "uncommon": 0.8,
        "rare": 1.2,
        "epic": 1.8,
        "legendary": 2.4,
    }.get(upgrade_dict["rarity"], 0.4)

    score = rarity_bonus
    low_health = player.health < max(65, int(player.max_health * 0.55))

    if name == "Increase Health":
        score += amount * (0.18 if low_health else 0.1)
    elif name == "Increase Health %":
        score += amount * (0.22 if low_health else 0.11)
    elif name == "Increase Armor":
        score += amount * (0.19 if low_health else 0.1)
    elif name == "Low Card Shield":
        score += amount * (0.16 if difficulty != "easy" else 0.11)
    elif name == "High Card Shield":
        score += amount * (0.16 if difficulty != "easy" else 0.11)
    elif name == "Straight Shelter":
        score += amount * (0.17 if difficulty == "hard" else 0.12)
    elif name == "Flush Shelter":
        score += amount * (0.17 if difficulty == "hard" else 0.12)
    elif name == "Increase Discards":
        score += amount * (1.5 if difficulty != "easy" else 1.0)
    elif name == "Increase Damage":
        score += amount * 0.16
    elif "Increase" in name and "Damage" in name:
        score += amount * (0.17 if difficulty == "hard" else 0.13)
    elif "Increase" in name and "Draw" in name:
        score += amount * (0.13 if difficulty != "easy" else 0.09)
    elif "Draw Specialist" in name:
        score += amount * 0.15
    elif "Cards Specialist" in name:
        score += amount * 0.12
    elif name == "Royal Invitation":
        score += amount * 0.12
    elif name == "Tiny Troublemakers":
        score += amount * 0.11
    elif name == "Echo Hand":
        score += amount * (0.22 if difficulty == "hard" else 0.18)
    elif name == "Grand Bazaar":
        score += amount * (2.6 if difficulty == "hard" else 2.2 if difficulty == "medium" else 1.8)
    elif name == "Gap Straight":
        score += 4.8 if difficulty == "hard" else 3.4
    elif name == "Soft Flush":
        score += 4.8 if difficulty == "hard" else 3.4

    return score / cost


def bot_relic_score(game: Game, bot_id: str, relic: dict, difficulty: str) -> float:
    player = game.players[bot_id]
    relic_id = relic["id"]
    score = 1.0

    if relic_id == "tiny_tyrants":
        score += (player.low_card_damage_modifier - 1.0) * 10
        score += (player.low_card_draw_modifier - 1.0) * 8
        score += (player.tiny_draw_modifier - 1.0) * 10
    elif relic_id == "house_advantage":
        score += (player.full_house_damage_modifier - 1.0) * 12
        score += (player.pair_damage_modifier - 1.0) * 6
    elif relic_id == "greedy_fingers":
        score += player.max_discards * 1.8
        score += 1.5 if player.health > 60 else -2.0
    elif relic_id == "wild_orbit":
        score += 4.5 if "joker" in player.level_unlocks else 0.5
        score += (player.joker_draw_modifier - 1.0) * 10
    elif relic_id == "tidal_memory":
        score += (player.flush_damage_modifier - 1.0) * 12
        score += sum(
            modifier - 1.0
            for modifier in (
                player.fire_draw_modifier,
                player.water_draw_modifier,
                player.air_draw_modifier,
                player.earth_draw_modifier,
            )
        ) * 2.2
    elif relic_id == "overflow_chamber":
        score += 4.0 if difficulty == "hard" else 2.8
    elif relic_id == "plasma_lattice":
        score += 5.0 if "plasma" in player.level_unlocks else -0.5
    elif relic_id == "fortress_heart":
        score += 5.0 if player.health < 55 else 2.6
    elif relic_id == "pattern_ward":
        score += 4.8 if player.health < 65 else 2.7

    return score


async def execute_discard_action(game_id: str, player_id: str, selected_cards: list[dict]):
    game = games[game_id]
    player = game.players[player_id]
    player.remaining_discards -= 1
    result = game.remove_selected_cards(player_id, selected_cards)
    if "error" in result:
        player.remaining_discards += 1
        return result

    hand_message = {
        "type": "hand_updated",
        "player": player_id,
        "cards": result["new_hand"],
        "remaining_discards": player.remaining_discards
    }
    await game.broadcast(hand_message)

    if player.discard_gold_bonus > 0:
        player.gold += player.discard_gold_bonus

    if should_track_progress(game) and player.account_email:
        draw_stats = summarize_drawn_hand(result["new_hand"])
        update_player_progress(
            player.account_email,
            {
                "cards_discarded": len(result["discarded"]),
                **draw_stats,
                **summarize_player_peaks(player),
            },
        )

    return {
        "message": "Cards discarded and new ones drawn",
        "discarded": result["discarded"],
        "new_hand": result["new_hand"],
        "remaining_discards": player.remaining_discards,
        "gold": player.gold,
    }


async def execute_play_hand_action(game_id: str, player_id: str, selected_cards: list[dict]):
    game = games[game_id]
    player = game.players[player_id]
    opponent_id = [pid for pid in game.players if pid != player_id][0]
    opponent = game.players[opponent_id]

    damage_details = game.calculate_damage_details(selected_cards, player_id)
    damage = damage_details["damage"]
    hand_type = damage_details["hand_type"]
    multiplier = damage_details["multiplier"]
    actual_damage = opponent.mitigate_incoming_damage(
        damage,
        damage_details["resolved_cards"],
        hand_type,
    )
    hits = 1
    damage_instances = [actual_damage]
    if player.play_twice_chance_pct > 0 and random.random() < (player.play_twice_chance_pct / 100.0):
        hits = 2
        damage_instances.append(actual_damage)
    total_damage = sum(damage_instances)
    stat_changes = summarize_played_hand(selected_cards, hand_type)
    stat_changes["damage_dealt"] = total_damage
    stat_changes["max_single_hand_damage"] = total_damage

    result = game.remove_selected_cards(player_id, selected_cards)
    if "error" in result:
        return result
    stat_changes.update(summarize_drawn_hand(result["new_hand"]))

    opponent.health = max(0, opponent.health - total_damage)
    if hand_type == "full house" and player.full_house_armor_gain > 0:
        player.armor += player.full_house_armor_gain

    winner = None
    match_finished = False
    round_finished = False
    if opponent.health == 0:
        winner = player_id
        round_finished = True
        player.wins += 1
        if player.wins >= 5:
            match_finished = True

    player.remaining_discards = player.max_discards

    if not winner:
        game.turn_index = (game.turn_index + 1) % len(game.players)
        game.start_battle_phase()
    player.gold += multiplier + player.gold_gain_flat

    await game.broadcast({
        "type": "hand_played",
        "player": player_id,
        "cards": selected_cards,
        "damage": total_damage,
        "damage_instances": damage_instances,
        "hits": hits,
        "double_play_triggered": hits > 1,
        "health_update": {p.name: p.health for p in game.players.values()},
        "max_health_update": {p.name: p.max_health for p in game.players.values()},
        "armor_update": {p.name: p.armor for p in game.players.values()},
        "armor_reduction_update": {
            p.name: p.get_armor_damage_reduction_pct() for p in game.players.values()
        },
        "score_update": {p.name: p.wins for p in game.players.values()},
        "next_player": list(game.players.keys())[game.turn_index],
        "hand_type": hand_type,
        "new_hand": result["new_hand"],
        "multiplier": multiplier,
        "winner": winner,
        "round_finished": round_finished,
        "match_finished": match_finished,
        "remaining_discards": player.remaining_discards,
        "gold": multiplier + player.gold_gain_flat
    })
    if not winner:
        await game.broadcast_match_state()
        if game.is_bot_match and game.get_current_player_id() == game.bot_player_id:
            schedule_bot_action(game_id)
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
        if game.is_bot_match and game.bot_player_id in game.shop_waiting_players:
            schedule_bot_action(game_id)

    if should_track_progress(game) and not winner and player.account_email:
        update_player_progress(
            player.account_email,
            {**stat_changes, **summarize_player_peaks(player)},
        )

    return {
        "message": f"{player_id} played a hand",
        "damage": total_damage,
        "multiplier": multiplier,
        "new_hand": result["new_hand"],
        "winner": winner,
        "round_finished": round_finished,
        "match_finished": match_finished,
    }


async def execute_buy_upgrade_action(game_id: str, player_id: str, upgrade_id: int):
    game = games[game_id]
    async with game.lock:
        price = game.get_price(upgrade_id)
        player = game.players[player_id]
        if price > player.gold:
            return {"message": "Not enough gold"}

        player.gold -= price
        await game.add_upgrade(player_id, upgrade_id)
        await game.apply_upgrades(player_id)
    if should_track_progress(game) and player.account_email:
        update_player_progress(
            player.account_email,
            {"upgrades_bought": 1, **summarize_player_peaks(player)},
        )
    return {
        "message": f"{player_id} bought upgrade {upgrade_id}",
        "price": price,
    }


async def run_bot_shop_phase(game_id: str):
    if game_id not in games:
        return
    game = games[game_id]
    bot_id = game.bot_player_id
    if not game.is_bot_match or not bot_id or bot_id not in game.players:
        return
    if game.phase != "shop" or bot_id not in game.shop_waiting_players:
        return

    difficulty = game.bot_difficulty or "medium"
    player = game.players[bot_id]
    offers = game.upgrade_store.get_selection_of_upgrades(game.get_shop_selection_size(bot_id))

    while True:
        affordable = [upgrade for upgrade in offers if upgrade.cost <= player.gold]
        if not affordable:
            if game.shop_rerolls_remaining.get(bot_id, 0) > 0:
                rerolled = game.reroll_shop_selection(bot_id)
                if isinstance(rerolled, list):
                    offers = [game.upgrade_store.get_upgrade_by_id(entry["id"]) for entry in rerolled]
                    offers = [upgrade for upgrade in offers if upgrade is not None]
                    continue
            break

        best_upgrade = max(
            affordable,
            key=lambda upgrade: bot_upgrade_score(game, bot_id, upgrade.to_dict(), difficulty),
        )
        best_score = bot_upgrade_score(game, bot_id, best_upgrade.to_dict(), difficulty)
        threshold = 0.7 if difficulty == "easy" else 0.6 if difficulty == "medium" else 0.5
        if best_score < threshold:
            if game.shop_rerolls_remaining.get(bot_id, 0) > 0:
                rerolled = game.reroll_shop_selection(bot_id)
                if isinstance(rerolled, list):
                    offers = [game.upgrade_store.get_upgrade_by_id(entry["id"]) for entry in rerolled]
                    offers = [upgrade for upgrade in offers if upgrade is not None]
                    continue
            break

        await execute_buy_upgrade_action(game_id, bot_id, best_upgrade.id)
        offers = [upgrade for upgrade in offers if upgrade.id != best_upgrade.id]
        await asyncio.sleep(0.18 if difficulty == "hard" else 0.28)

    await game.mark_shop_ready(bot_id)
    if game.phase == "battle" and game.get_current_player_id() == bot_id:
        schedule_bot_action(game_id)
    elif game.phase == "relic" and bot_id in game.relic_waiting_players:
        schedule_bot_action(game_id)


async def run_bot_relic_phase(game_id: str):
    if game_id not in games:
        return
    game = games[game_id]
    bot_id = game.bot_player_id
    if not game.is_bot_match or not bot_id or bot_id not in game.players:
        return
    if game.phase != "relic" or bot_id not in game.relic_waiting_players:
        return

    offered_relics = [relic.to_dict() for relic in game.relic_choices_by_player.get(bot_id, [])]
    if not offered_relics:
        await game.mark_relic_ready(bot_id)
        return

    chosen = max(
        offered_relics,
        key=lambda relic: bot_relic_score(game, bot_id, relic, game.bot_difficulty or "medium"),
    )
    game.choose_relic(bot_id, chosen["id"])
    await game.mark_relic_ready(bot_id)
    await game.broadcast(game.players[bot_id].apply_upgrades())
    if game.phase == "battle" and game.get_current_player_id() == bot_id:
        schedule_bot_action(game_id)


async def run_bot_battle_turn(game_id: str):
    if game_id not in games:
        return
    game = games[game_id]
    bot_id = game.bot_player_id
    if not game.is_bot_match or not bot_id or bot_id not in game.players:
        return
    if game.phase != "battle" or game.get_current_player_id() != bot_id:
        return

    difficulty = game.bot_difficulty or "medium"
    discard_cards = choose_bot_discards(game, bot_id, difficulty)
    if discard_cards:
        await execute_discard_action(game_id, bot_id, discard_cards)
        if game.phase == "battle" and game.get_current_player_id() == bot_id:
            schedule_bot_action(game_id, 0.7 if difficulty == "easy" else 0.5 if difficulty == "medium" else 0.35)
        return

    best_hand = choose_best_bot_hand(game, bot_id, difficulty)
    if not best_hand or not best_hand["cards"]:
        game.turn_index = (game.turn_index + 1) % len(game.players)
        game.start_battle_phase()
        await game.broadcast({"message": "Turn ended", "next_player": game.get_current_player_id()})
        await game.broadcast_match_state()
        return

    await execute_play_hand_action(game_id, bot_id, best_hand["cards"])
    if game_id in games:
        updated_game = games[game_id]
        if updated_game.phase == "battle" and updated_game.get_current_player_id() == updated_game.bot_player_id:
            schedule_bot_action(game_id)


async def run_bot_action(game_id: str):
    if game_id not in games:
        return

    game = games[game_id]
    bot_id = game.bot_player_id
    if not game.is_bot_match or not bot_id:
        return

    if game.phase == "shop" and bot_id in game.shop_waiting_players:
        await run_bot_shop_phase(game_id)
    elif game.phase == "relic" and bot_id in game.relic_waiting_players:
        await run_bot_relic_phase(game_id)
    elif game.phase == "battle" and game.get_current_player_id() == bot_id:
        await run_bot_battle_turn(game_id)


def schedule_bot_action(game_id: str, delay_seconds: float | None = None):
    game = games.get(game_id)
    if not game or not game.is_bot_match or not game.bot_player_id:
        return
    if game.phase == "match_over":
        game.cancel_bot_task()
        return
    if game.phase == "battle" and game.get_current_player_id() != game.bot_player_id:
        return
    if game.phase == "shop" and game.bot_player_id not in game.shop_waiting_players:
        return
    if game.phase == "relic" and game.bot_player_id not in game.relic_waiting_players:
        return

    game.cancel_bot_task()

    async def runner():
        try:
            await asyncio.sleep(delay_seconds if delay_seconds is not None else get_bot_delay_seconds(game))
            await run_bot_action(game_id)
        except asyncio.CancelledError:
            return
        finally:
            if game_id in games and games[game_id].bot_task is asyncio.current_task():
                games[game_id].bot_task = None

    game.bot_task = asyncio.create_task(runner())


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

    rank_counts: dict[str, int] = {}
    for card in cards:
        rank_counts[card["rank"]] = rank_counts.get(card["rank"], 0) + 1

    if rank_counts and max(rank_counts.values()) >= 5:
        return {"full_hand_of_a_kind_draws": 1}

    return {}


def summarize_player_peaks(player) -> dict[str, int]:
    return {
        "max_armor_in_game": int(getattr(player, "armor", 0)),
        "max_health_in_game": int(getattr(player, "max_health", 0)),
    }

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
            if game.public_visibility and len(game.players) < 2
        ]
    }


@app.post("/game/bot/start")
async def start_bot_game(
    difficulty: str,
    player_id: str,
    email: str | None = None,
    avatar: str | None = None,
):
    normalized_difficulty = difficulty.strip().lower()
    if normalized_difficulty not in {"easy", "medium", "hard"}:
        return {"error": "Invalid bot difficulty"}

    normalized_player_id = player_id.strip()
    if not normalized_player_id:
        return {"error": "Player name is required"}

    game_id = generate_private_game_id("bot")
    bot_name, bot_avatar = choose_bot_identity(normalized_difficulty)
    if bot_name == normalized_player_id:
        bot_name = f"{bot_name} Bot"

    game = Game(
        is_bot_match=True,
        bot_player_id=bot_name,
        bot_difficulty=normalized_difficulty,
        public_visibility=False,
    )
    games[game_id] = game

    decoded_email = decode_email(email) if email else None
    account_state = get_player_account_state(decoded_email)
    game.add_player(
        normalized_player_id,
        account_email=decoded_email,
        talent_bonuses=account_state["talent_bonuses"],
        avatar=avatar,
        level_unlocks=account_state["level_rewards"],
        level_reward_bonuses=account_state["level_reward_bonuses"],
    )
    game.add_player(bot_name, avatar=bot_avatar)
    game.start_battle_phase()

    if game.get_current_player_id() == bot_name:
        schedule_bot_action(game_id)

    return {
        "message": f"Started {normalized_difficulty} bot match",
        "game_id": game_id,
        "player_id": normalized_player_id,
        "bot_player_id": bot_name,
        "difficulty": normalized_difficulty,
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
        "is_bot_match": game.is_bot_match,
        "relics_by_player": {
            player_id: [relic.to_dict() for relic in player.relics]
            for player_id, player in game.players.items()
        },
    }


@app.get("/game/{game_id}/chat")
def get_game_chat(game_id: str):
    if game_id not in games:
        return {"error": "Game not found"}
    return {"messages": games[game_id].chat_messages}


@app.post("/game/{game_id}/chat")
async def post_game_chat_message(
    game_id: str,
    player_id: str = Body(...),
    text: str = Body(...),
):
    if game_id not in games:
        return {"error": "Game not found"}

    game = games[game_id]
    if player_id not in game.players:
        return {"error": "Player not found"}

    normalized_text = text.strip()
    if not normalized_text:
        return {"error": "Message is required"}

    player = game.players[player_id]
    entry = game.add_chat_message(player.name, player.avatar, normalized_text)
    entry["game_id"] = game_id
    await game.broadcast({"type": "chat_message", "message": entry})
    return {"message": entry}

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
    if not game.public_visibility:
        return {"error": "Game not found"}
    if player_id not in game.players and len(game.players) >= 2:
        return {"error": "Game is full"}
    decoded_email = decode_email(email) if email else None
    account_state = get_player_account_state(decoded_email)
    try:
        game.add_player(
            player_id,
            account_email=decoded_email,
            talent_bonuses=account_state["talent_bonuses"],
            avatar=avatar,
            level_unlocks=account_state["level_rewards"],
            level_reward_bonuses=account_state["level_reward_bonuses"],
        )
    except ValueError as error:
        return {"error": str(error)}

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

    if game.is_bot_match:
        game.cancel_bot_task()
        if game_id in games:
            del games[game_id]
        return {"message": f"{player_id} left bot match {game_id}"}

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
        upgrade_payload = game_player.apply_upgrades()
        await websocket.send_json(upgrade_payload)
    print(f"Sent hand to {player_id} via WebSocket: {player.hand}")

    if should_track_progress(game) and player.account_email:
        update_player_progress(
            player.account_email,
            {
                **summarize_drawn_hand(hand_message["cards"]),
                **summarize_player_peaks(player),
            },
        )

    if game.is_bot_match and game.bot_player_id:
        if game.phase == "battle" and game.get_current_player_id() == game.bot_player_id:
            schedule_bot_action(game_id)
        elif game.phase == "shop" and game.bot_player_id in game.shop_waiting_players:
            schedule_bot_action(game_id)
        elif game.phase == "relic" and game.bot_player_id in game.relic_waiting_players:
            schedule_bot_action(game_id)

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
    return await execute_discard_action(game_id, player_id, selected_cards)

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

    return await execute_play_hand_action(game_id, player_id, selected_cards)

    # Calculate damage
    damage_details = game.calculate_damage_details(selected_cards, player_id)
    damage = damage_details["damage"]
    hand_type = damage_details["hand_type"]
    multiplier = damage_details["multiplier"]
    actual_damage = opponent.mitigate_incoming_damage(
        damage,
        damage_details["resolved_cards"],
        hand_type,
    )
    stat_changes = summarize_played_hand(selected_cards, hand_type)
    stat_changes["damage_dealt"] = actual_damage
    stat_changes["max_single_hand_damage"] = actual_damage

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
        update_player_progress(
            player.account_email,
            {**stat_changes, **summarize_player_peaks(player)},
        )

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
        if game.is_bot_match and next_player == game.bot_player_id:
            schedule_bot_action(game_id)

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
    return await execute_buy_upgrade_action(gameId, playerId, int(upgrade_id))

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
            update_player_progress(
                player.account_email,
                {"upgrades_bought": 1, **summarize_player_peaks(player)},
            )
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

    player = game.players.get(player_id)
    if player and should_track_progress(game) and player.account_email:
        update_player_progress(player.account_email, {"shop_rerolls_used": 1})

    return {
        "message": "Shop rerolled",
        "upgrades": rerolled_selection,
        "rerolls_remaining": game.shop_rerolls_remaining.get(player_id, 0),
        "health": game.players[player_id].health,
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
    if game.phase == "battle" and game.get_current_player_id() == game.bot_player_id:
        schedule_bot_action(game_id)
    elif game.phase == "relic" and game.bot_player_id in game.relic_waiting_players:
        schedule_bot_action(game_id)
    return {
        "message": f"{player_id} is ready",
        "waiting_players": game.get_shop_waiting_players(),
    }


@app.post("/game/{game_id}/relic/choose")
async def choose_relic(game_id: str, player_id: str, relic_id: str):
    if game_id not in games:
        return {"error": "Game not found"}

    game = games[game_id]
    if player_id not in game.players:
        return {"error": "Player not found"}

    game.record_activity(player_id)
    resolution = await resolve_game_state(game_id)
    if resolution:
        return {"error": resolution["reason"]}
    if game.phase != "relic":
        return {"error": "Relic choice is not open"}

    chosen = game.choose_relic(player_id, relic_id)
    if isinstance(chosen, dict) and chosen.get("error"):
        return chosen

    await game.broadcast(game.players[player_id].apply_upgrades())
    await game.mark_relic_ready(player_id)
    if game.phase == "battle" and game.get_current_player_id() == game.bot_player_id:
        schedule_bot_action(game_id)
    return {
        "message": f"{player_id} chose {chosen.name}",
        "waiting_players": game.get_relic_waiting_players(),
    }
