from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from typing import Dict, List, Optional
import asyncio
import random

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

games: Dict[str, dict] = {}

class Card:
    def __init__(self, rank: str, suit: str, base_damage: int = 5):
        self.rank = rank  # e.g., "Ace", "2", "King"
        self.suit = suit  # e.g., "Hearts", "Spades"
        self.base_damage = base_damage

    def __repr__(self):
        return f"{self.rank} of {self.suit}"

def generate_deck():
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
    return [Card(rank, suit) for rank in ranks for suit in suits]

class Game:
    def __init__(self):
        self.players: List[str] = []
        self.turn_index: int = 0
        self.health: Dict[str, int] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.lock = asyncio.Lock()
        self.deck = generate_deck()  # ✅ Full deck of 52 cards
        self.player_hands: Dict[str, List[Card]] = {}

    async def broadcast(self, message: dict):
        disconnected_players = []
        for player, ws in self.websocket_connections.items():
            try:
                await ws.send_json(message)
            except Exception:
                disconnected_players.append(player)

        # Remove disconnected players
        for player in disconnected_players:
            del self.websocket_connections[player]
    
    def deal_card(self, player_id):
        """Draws a random card for a player."""
        if player_id not in self.player_hands:
            self.player_hands[player_id] = []
        if self.deck:
            card = self.deck.pop(random.randint(0, len(self.deck) - 1))
            self.player_hands[player_id].append(card)
            return card
        return None

def calculate_damage(hand: List[Card]):
    """Evaluates a hand and returns damage based on poker multipliers."""
    rank_counts = {}
    for card in hand:
        rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1

    # Find the highest match (pair, three of a kind, etc.)
    max_match = max(rank_counts.values(), default=1)
    multiplier = max_match  # Pair = 2x, Three of a kind = 3x, etc.

    base_damage = sum(card.base_damage for card in hand)
    return base_damage * multiplier  # Apply multiplier


@app.get("/game/{game_id}/players")
def get_players(game_id: str):
    if game_id not in games:
        return {"error": "Game not found"}
    return {"players": games[game_id].players}

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
    if player_id in game.players:
        return {"error": "Player already in game"}

    game.players.append(player_id)
    game.health[player_id] = 100  # ✅ Set initial health to 100

    # ✅ Broadcast full health state to all players
    health_status = {"type": "health_update", "players_health": game.health}
    await game.broadcast(health_status)

    return {"message": "Joined game", "players": game.players, "health": game.health}

@app.websocket("/game/{game_id}/ws/{player_id}")
async def game_websocket(websocket: WebSocket, game_id: str, player_id: str):
    if game_id not in games:
        await websocket.close()
        return

    game = games[game_id]
    await websocket.accept()
    game.websocket_connections[player_id] = websocket
    print(f"WebSocket connected: {player_id}")

    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received WebSocket message from {player_id}: {data}")

            # ✅ Broadcast message to ALL players
            await game.broadcast({"player": player_id, "data": data})

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {player_id}")
        del game.websocket_connections[player_id]


@app.post("/game/{game_id}/play_card")
async def play_card(game_id: str, player_id: str):
    if game_id not in games:
        return {"error": "Game not found"}

    game = games[game_id]
    
    if player_id != game.players[game.turn_index]:
        return {"error": "Not your turn"}

    card = game.deal_card(player_id)
    if not card:
        return {"error": "No more cards in deck"}

    damage = calculate_damage(game.player_hands[player_id])

    # Apply damage to opponent
    opponent_id = game.players[(game.turn_index + 1) % len(game.players)]
    game.health[opponent_id] = max(0, game.health[opponent_id] - damage)

    # ✅ Broadcast update
    await game.broadcast({
        "type": "card_played",
        "player": player_id,
        "card": str(card),
        "damage": damage,
        "health_update": game.health
    })

    return {"message": f"{player_id} played {card}. Dealt {damage} damage."}


@app.post("/game/{game_id}/end_turn")
async def end_turn(game_id: str, player_id: str):
    if game_id not in games:
        return {"error": "Game not found"}
    
    game = games[game_id]
    async with game.lock:
        if game.players[game.turn_index] != player_id:
            return {"error": "Not your turn"}

        game.turn_index = (game.turn_index + 1) % len(game.players)
        await game.broadcast({"message": "Turn ended", "next_player": game.players[game.turn_index]})
        return {"message": "Turn ended"}
