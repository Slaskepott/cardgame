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

def calculate_damage(cards):
    """Evaluates a hand and returns damage and hand type based on poker multipliers."""
    multipliers = {
        "high card": 1,
        "pair": 2,
        "two pair": 3,
        "three of a kind": 4,
        "straight": 5,
        "flush": 6,
        "full house": 7,
        "four of a kind": 10,
        "straight flush": 15,
        "royal flush": 20
    }
    rank_dict = {
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "10": 10,
        "J": 11,
        "Q": 12,
        "K": 13,
        "A": 14
    }


    rank_counts = {}
    suit_counts = {}
    ranks = []
    
    for card in cards:
        rank = rank_dict[card["rank"]]
        suit = card["suit"]
        rank_counts[rank] = rank_counts.get(rank, 0) + 1
        suit_counts[suit] = suit_counts.get(suit, 0) + 1
        ranks.append(rank)

    rank_frequencies = sorted(rank_counts.values(), reverse=True)
    is_flush = (max(suit_counts.values()) == len(cards)) and len(cards) >= 5
    sorted_ranks = sorted(ranks)
    is_straight = (sorted_ranks == list(range(min(sorted_ranks), min(sorted_ranks) + len(cards)))) and len(cards) >= 5

    if is_straight and is_flush:
        hand_type = "royal flush" if max(ranks) == 14 else "straight flush"
    elif 4 in rank_frequencies:
        hand_type = "four of a kind"
    elif 3 in rank_frequencies and 2 in rank_frequencies:
        hand_type = "full house"
    elif is_flush:
        hand_type = "flush"
    elif is_straight:
        hand_type = "straight"
    elif 3 in rank_frequencies:
        hand_type = "three of a kind"
    elif rank_frequencies.count(2) == 2:
        hand_type = "two pair"
    elif 2 in rank_frequencies:
        hand_type = "pair"
    else:
        hand_type = "high card"

    multiplier = multipliers[hand_type]
    base_damage = 2 * len(cards)  # Base damage per card
    total_damage = base_damage * multiplier

    return total_damage, hand_type

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

    # ✅ Register player in the game
    game.players.append(player_id)
    game.health[player_id] = 100  # Initialize health
    game.player_hands[player_id] = []  # Empty hand (will be dealt after WebSocket connects)

    print(f"Player {player_id} joined {game_id}. Waiting for WebSocket connection...")

    return {"message": f"{player_id} joined game {game_id}"}




@app.websocket("/game/{game_id}/ws/{player_id}")
async def game_websocket(websocket: WebSocket, game_id: str, player_id: str):
    if game_id not in games:
        await websocket.close()
        return

    game = games[game_id]
    await websocket.accept()
    game.websocket_connections[player_id] = websocket
    print(f"WebSocket connected: {player_id}")

    # ✅ Deal hand *only if* player has no cards yet    
    if not game.player_hands[player_id]:
        dealt_cards = []
        for _ in range(8):
            if game.deck:
                card = game.deck.pop(random.randint(0, len(game.deck) - 1))
                dealt_cards.append(card)

        game.player_hands[player_id] = dealt_cards
        print(f"Dealt hand to {player_id}: {[str(card) for card in game.player_hands[player_id]]}")


    # ✅ Now, send hand after WebSocket connection
    hand_message = {
        "type": "new_hand",
        "player": player_id,
        "cards": [{"rank": c.rank, "suit": c.suit} for c in game.player_hands[player_id]]
    }
    await websocket.send_json(hand_message)
    print(f"Sent hand to {player_id} via WebSocket: {game.player_hands[player_id]}")

    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received WebSocket message from {player_id}: {data}")

            # ✅ Broadcast message to ALL players
            await game.broadcast(data)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {player_id}")
        del game.websocket_connections[player_id]

@app.post("/game/{game_id}/discard")
async def discard(game_id: str, request: dict):
    if game_id not in games:
        return {"error": "Game not found"}

    game = games[game_id]
    player_id = request.get("player_id")
    selected_cards = request.get("cards", [])

    if player_id != game.players[game.turn_index]:
        return {"error": "Not your turn"}
    if not selected_cards:
        return {"error": "No cards selected"}
    if player_id not in game.player_hands:
        return {"error": "Player has no hand"}

    # Convert selected_cards to a set of (rank, suit) tuples for comparison
    selected_card_tuples = {(card["rank"], card["suit"]) for card in selected_cards}

    # Remove selected cards from player's hand
    new_hand = [card for card in game.player_hands[player_id] if (card.rank, card.suit) not in selected_card_tuples]
    discarded_cards = [card for card in game.player_hands[player_id] if (card.rank, card.suit) in selected_card_tuples]

    if len(new_hand) == len(game.player_hands[player_id]):  # No valid cards were removed
        return {"error": "Selected cards not found in hand"}

    game.player_hands[player_id] = new_hand

    # Draw new cards to maintain hand size (if possible)
    while len(game.player_hands[player_id]) < 8 and game.deck:
        new_card = game.deal_card(player_id)
        if new_card:
            game.player_hands[player_id].append(new_card)

    # Broadcast updated hand to player
    hand_message = {
        "type": "hand_updated",
        "player": player_id,
        "cards": [{"rank": c.rank, "suit": c.suit} for c in game.player_hands[player_id]]
    }
    await game.broadcast(hand_message)

    return {
        "message": "Cards discarded and new ones drawn",
        "discarded": [{"rank": c.rank, "suit": c.suit} for c in discarded_cards],
        "new_hand": [{"rank": c.rank, "suit": c.suit} for c in game.player_hands[player_id]]
    }

@app.post("/game/{game_id}/play_hand")
async def play_hand(game_id: str, request: dict):
    if game_id not in games:
        return {"error": "Game not found"}

    game = games[game_id]
    player_id = request.get("player_id")
    selected_cards = request.get("cards", [])

    if player_id != game.players[game.turn_index]:
        return {"error": "Not your turn"}

    if not selected_cards:
        return {"error": "No cards selected"}

    # Calculate damage based on poker rules
    damage, hand_type = calculate_damage(selected_cards)

    # Apply damage to opponent
    opponent_id = game.players[(game.turn_index + 1) % len(game.players)]
    game.health[opponent_id] = max(0, game.health[opponent_id] - damage)

    # Move to the next turn
    game.turn_index = (game.turn_index + 1) % len(game.players)

    # Broadcast game state update
    await game.broadcast({
        "type": "hand_played",
        "player": player_id,
        "cards": selected_cards,
        "damage": damage,
        "health_update": game.health,
        "next_player": game.players[game.turn_index],
        "hand_type": hand_type
    })

    return {"message": f"{player_id} played a hand", "damage": damage}



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
