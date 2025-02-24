from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from typing import Dict
from game import Game
import random
import math
import stripe
import os

from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Replace with your actual credentials and DB name
DATABASE_URL = f"postgresql://slaskecards:{os.environ.get('db_pw')}@dpg-cuu6h3qj1k6c738je0j0-a.frankfurt-postgres.render.com/slaskecards"


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class PlayerCurrency(Base):
    __tablename__ = "player_currencies"
    email = Column(String, primary_key=True, index=True)
    slaskecoins = Column(Integer, default=0)

# Create the table if it doesn't exist yet
Base.metadata.create_all(bind=engine)

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


app = FastAPI()

@app.get("/slaskecoins/{email}")
def getSlaskecoins(email: str) -> int:
    """
    Retrieves the current number of slaskecoins for the given email.
    If the user does not exist, returns 0.
    """
    session = SessionLocal()
    try:
        player = session.query(PlayerCurrency).filter(PlayerCurrency.email == email).first()
        return player.slaskecoins if player else 0
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
    email: str = ""
):
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            description=description,
        )
        addOrRemoveSlaskecoins(email, amount)
        return {"client_secret": payment_intent.client_secret}
    except Exception as e:
        return {"error": str(e)}

games: Dict[str, dict] = {}

@app.get("/game/{game_id}/players")
def get_players(game_id: str):
    if game_id not in games:
        return {"error": "Game not found"}
    
    return {"players": list(games[game_id].players.keys())}

@app.post("/game/create/{game_id}")
def create_game(game_id: str):
    if game_id in games:
        return {"error": "Game ID already exists. Choose a different ID."}
    
    games[game_id] = Game()
    return {"message": f"Game {game_id} created successfully"}

@app.post("/game/join/{game_id}")
async def join_game(game_id: str, player_id: str):
    if game_id not in games:
        return {"error": "Game not found"}

    game = games[game_id]
    game.add_player(player_id)

    print(f"Player {player_id} joined {game_id}. Waiting for WebSocket connection...")

    await game.broadcast({
        "type": "players_updated",
        "players": list(game.players.keys())
    })

    return {"message": f"{player_id} joined game {game_id}"}

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
        for _ in range(8):
            if game.deck:
                player.hand.append(game.deck.pop(random.randint(0, len(game.deck) - 1)))

        print(f"Dealt hand to {player_id}: {[str(card) for card in player.hand]}")

    # ✅ Now, send hand after WebSocket connection
    hand_message = {
        "type": "new_hand",
        "player": player_id,
        "cards": [{"rank": c.rank, "suit": c.suit} for c in player.hand]
    }
    await websocket.send_json(hand_message)
    print(f"Sent hand to {player_id} via WebSocket: {player.hand}")

    try:
        while True:
            data = await websocket.receive_json()
            await game.broadcast(data)
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {player_id}")
    finally:
        del game.websocket_connections[player_id]

@app.post("/game/{game_id}/discard")
async def discard(game_id: str, request: dict):
    if game_id not in games:
        return {"error": "Game not found"}

    game = games[game_id]
    player_id = request.get("player_id")
    selected_cards = request.get("cards", [])

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
    player_id = request.get("player_id")
    selected_cards = request.get("cards", [])

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

    # Remove played cards
    result = game.remove_selected_cards(player_id, selected_cards)
    if "error" in result:
        return result

    # Apply damage to opponent
    opponent.health = max(0, opponent.health - damage)

    # Check for win condition
    winner = None
    if opponent.health == 0:
        winner = player_id
        player.wins += 1
        await game.reset_game()

    #Increase discards
    player.remaining_discards = player.max_discards

    # Move turn
    game.turn_index = (game.turn_index + 1) % len(game.players)
    player.gold += multiplier #placeholder

    # Broadcast update
    await game.broadcast({
        "type": "hand_played",
        "player": player_id,
        "cards": selected_cards,
        "damage": damage,
        "health_update": {p.name: p.health for p in game.players.values()},
        "max_health_update": {p.name: p.max_health for p in game.players.values()},
        "score_update": {p.name: p.wins for p in game.players.values()},
        "next_player": list(game.players.keys())[game.turn_index],
        "hand_type": hand_type,
        "new_hand": result["new_hand"],  # ✅ Send updated hand
        "multiplier": multiplier,
        "winner": winner,
        "remaining_discards": player.remaining_discards,
        "gold": multiplier #placeholder
    })

    return {
        "message": f"{player_id} played a hand",
        "damage": damage,
        "multiplier": multiplier,
        "new_hand": result["new_hand"],  # ✅ Send updated hand
        "winner": winner
    }

@app.post("/game/{game_id}/end_turn")
async def end_turn(game_id: str, player_id: str):
    if game_id not in games:
        return {"error": "Game not found"}
    
    game = games[game_id]

    async with game.lock:
        player_keys = list(game.players.keys())

        if player_id != player_keys[game.turn_index]:
            return {"error": "Not your turn"}

        # Move to the next player
        game.turn_index = (game.turn_index + 1) % len(player_keys)
        next_player = player_keys[game.turn_index]

        # Broadcast turn update
        await game.broadcast({"message": "Turn ended", "next_player": next_player})

        return {"message": "Turn ended", "next_player": next_player}

@app.post("/game/{gameId}/{playerId}/buyupgrade/{upgrade_id}")
async def add_upgrade(gameId: str, playerId: str, upgrade_id: str):

    if gameId not in games:
        return {"error": "Game not found"}
    game = games[gameId]
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
        return {
            "message":f"{playerId} bought upgrade {upgrade_id}",
            "price":price
        }
