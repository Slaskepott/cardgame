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
    suits = ["Fire", "Air", "Earth", "Water"]
    return [Card(rank, suit) for rank in ranks for suit in suits] * 10

class Player:
    def __init__(self, name: str):
        self.name = name
        self.max_health = 100
        self.health = self.max_health
        self.wins = 0
        self.hand: List[Card] = []
        self.remaining_discards = 1

    def reset(self):
        """Resets player for a new round but keeps wins."""
        self.health = self.max_health
        self.hand = []
        self.remaining_discards = 1


class Game:
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.turn_index: int = 0
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.lock = asyncio.Lock()
        self.deck = generate_deck()

    def add_player(self, player_name: str):
        if player_name not in self.players:
            self.players[player_name] = Player(player_name)

    def reset_game(self):
        """Resets all players but keeps scores."""
        self.deck = generate_deck()
        for player in self.players.values():
            player.reset()
        self.turn_index = 0

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
    
    def deal_card(self, player_id: str):
        """Draws a random card for a player."""
        if player_id not in self.players:
            return {"error": "Player not found"}

        player = self.players[player_id]

        if not self.deck:
            self.deck = generate_deck()

        card = self.deck.pop(random.randint(0, len(self.deck) - 1))
        player.hand.append(card)
        return card


    def remove_selected_cards(self, player_id: str, selected_cards: List[dict]) -> dict:
        """Removes selected cards from player's hand and returns discarded cards."""
        if player_id not in self.players:
            return {"error": "Player not found"}

        player = self.players[player_id]

        if not player.hand:
            return {"error": "Player has no hand"}

        # Convert selected_cards to a set of (rank, suit) tuples for comparison
        selected_card_tuples = {(card["rank"], card["suit"]) for card in selected_cards}

        print(f"Selected: {selected_card_tuples}")
        print(f"Player {player_id} Hand Before: {[{'rank': c.rank, 'suit': c.suit} for c in player.hand]}")

        # Remove selected cards from player's hand
        new_hand = [card for card in player.hand if (card.rank, card.suit) not in selected_card_tuples]
        discarded_cards = [card for card in player.hand if (card.rank, card.suit) in selected_card_tuples]

        if len(new_hand) == len(player.hand):  # No valid cards were removed
            return {"error": "Selected cards not found in hand"}

        player.hand = new_hand

        # Draw new cards to maintain hand size (if possible)
        while len(player.hand) < 8 and self.deck:
            self.deal_card(player_id)

        return {
            "discarded": [{"rank": c.rank, "suit": c.suit} for c in discarded_cards],
            "new_hand": [{"rank": c.rank, "suit": c.suit} for c in player.hand]
        }

def calculate_damage(cards):
    """Evaluates a hand and returns damage and hand type based on poker multipliers."""
    multipliers = {
        "high card": 1,
        "pair": 2,
        "two pair": 2,
        "three of a kind": 3,
        "straight": 4,
        "flush": 4,
        "full house": 4,
        "four of a kind": 7,
        "straight flush": 8,
        "royal flush": 10
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
    sorted_ranks = sorted(set(ranks))  # Remove duplicates and sort
    is_straight = False

    if len(sorted_ranks) >= 5:
        for i in range(len(sorted_ranks) - 4):
            if sorted_ranks[i + 4] - sorted_ranks[i] == 4:  # Consecutive check
                is_straight = True
                break

        # Ace-low straight check (A, 2, 3, 4, 5)
        if sorted_ranks[-5:] == [2, 3, 4, 5, 14]:
            is_straight = True

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
    base_damage = sum(ranks) // 5
    total_damage = base_damage * multiplier

    return total_damage, hand_type, multiplier

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
        await websocket.close()
        return

    game = games[game_id]

    if player_id not in game.players:
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
    damage, hand_type, multiplier = calculate_damage(selected_cards)

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
        game.reset_game()

    # Move turn
    game.turn_index = (game.turn_index + 1) % len(game.players)

    # Broadcast update
    await game.broadcast({
        "type": "hand_played",
        "player": player_id,
        "cards": selected_cards,
        "damage": damage,
        "health_update": {p.name: p.health for p in game.players.values()},
        "score_update": {p.name: p.wins for p in game.players.values()},
        "next_player": list(game.players.keys())[game.turn_index],
        "hand_type": hand_type,
        "new_hand": result["new_hand"],  # ✅ Send updated hand
        "multiplier": multiplier,
        "winner": winner
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

