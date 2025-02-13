from card import Card
from typing import Dict, List
from player import Player
from fastapi import WebSocket
import asyncio
import random
from upgrades import UpgradeStore
import traceback

class Game:
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.turn_index: int = 0
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.lock = asyncio.Lock()
        self.deck = self.generate_deck()
        self.upgrade_store = UpgradeStore()

    def add_player(self, player_name: str):
        if player_name not in self.players:
            self.players[player_name] = Player(player_name)

    async def reset_game(self):
        """Resets all players but keeps scores."""
        self.deck = self.generate_deck()
        for player in self.players.values():
            player.reset()
        self.turn_index = 0
        await self.open_upgrade_store()


    async def open_upgrade_store(self):
        """Send each player a unique selection of upgrades."""
        for player_id, ws in self.websocket_connections.items():
            try:
                store_selection = self.upgrade_store.get_selection_of_upgrades()
                await ws.send_json({
                    "type": "open_store",
                    "player": player_id,
                    "upgrades": store_selection
                })
            except Exception as e:
                print(f"Failed to send store selection to {player_id}: {e}")
                traceback.print_exc()




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
            self.deck = self.generate_deck()

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
    
    def generate_deck(self):
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        suits = ["Fire", "Air", "Earth", "Water"]
        return [Card(rank, suit) for rank in ranks for suit in suits] * 10

    def calculate_damage(self, cards):
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