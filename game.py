import asyncio
import random
import time
import traceback
from itertools import product
from typing import Dict, List

from fastapi import WebSocket

from card import Card
from player import Player
from upgrades import UpgradeStore


BASE_RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
CLASSIC_SUITS = ["Fire", "Air", "Earth", "Water"]
RANK_VALUES = {
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
    "A": 14,
    "15": 15,
}
HAND_MULTIPLIERS = {
    "high card": 1,
    "pair": 2,
    "two pair": 3,
    "three of a kind": 3,
    "straight": 4,
    "flush": 4,
    "full house": 4,
    "four of a kind": 7,
    "straight flush": 8,
    "royal flush": 10,
}


class Game:
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.turn_index: int = 0
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.shop_waiting_players: set[str] = set()
        self.shop_deadlines: dict[str, float] = {}
        self.last_activity: dict[str, float] = {}
        self.phase: str = "waiting"
        self.battle_deadline_at: float | None = None
        self.match_winner: str | None = None
        self.match_end_reason: str | None = None
        self.lock = asyncio.Lock()
        self.deck = self.generate_deck()
        self.upgrade_store = UpgradeStore()

    def add_player(
        self,
        player_name: str,
        account_email: str | None = None,
        talent_bonuses: dict | None = None,
        avatar: str | None = None,
        level_unlocks: list[str] | None = None,
        level_reward_bonuses: dict | None = None,
    ):
        if player_name not in self.players:
            self.players[player_name] = Player(
                player_name,
                account_email=account_email,
                talent_bonuses=talent_bonuses,
                avatar=avatar,
                level_unlocks=level_unlocks,
                level_reward_bonuses=level_reward_bonuses,
            )
            self.last_activity[player_name] = time.time()
            return

        player = self.players[player_name]
        if account_email:
            player.account_email = account_email
            player.talent_bonuses = talent_bonuses or {}
        if avatar:
            player.avatar = avatar
        if level_unlocks is not None:
            player.level_unlocks = list(level_unlocks)
        if level_reward_bonuses is not None:
            player.level_reward_bonuses = dict(level_reward_bonuses)
        player.apply_upgrades()
        player.special_deck = player.build_special_deck()
        self.last_activity[player_name] = time.time()

    def remove_player(self, player_name: str):
        if player_name not in self.players:
            return

        del self.players[player_name]
        self.websocket_connections.pop(player_name, None)
        self.shop_waiting_players.discard(player_name)
        self.shop_deadlines.pop(player_name, None)
        self.last_activity.pop(player_name, None)

        if self.players:
            self.turn_index %= len(self.players)
        else:
            self.turn_index = 0
            self.phase = "waiting"
            self.battle_deadline_at = None

    def get_current_player_id(self) -> str | None:
        if not self.players:
            return None
        player_ids = list(self.players.keys())
        return player_ids[self.turn_index % len(player_ids)]

    def get_opponent_id(self, player_id: str) -> str | None:
        for candidate in self.players.keys():
            if candidate != player_id:
                return candidate
        return None

    def record_activity(self, player_id: str):
        if player_id in self.players:
            self.last_activity[player_id] = time.time()

    def start_waiting_phase(self):
        self.phase = "waiting"
        self.battle_deadline_at = None
        self.shop_waiting_players = set()
        self.shop_deadlines = {}

    def start_battle_phase(self):
        if len(self.players) < 2:
            self.start_waiting_phase()
            return

        self.phase = "battle"
        self.battle_deadline_at = time.time() + 60
        self.shop_waiting_players = set()
        self.shop_deadlines = {}

    def start_shop_phase(self):
        if len(self.players) < 2:
            self.start_waiting_phase()
            return

        self.phase = "shop"
        self.battle_deadline_at = None
        deadline = time.time() + 120
        self.shop_waiting_players = set(self.players.keys())
        self.shop_deadlines = {player_name: deadline for player_name in self.players.keys()}

    def set_match_over(self, winner_id: str, reason: str):
        self.phase = "match_over"
        self.match_winner = winner_id
        self.match_end_reason = reason
        self.battle_deadline_at = None
        self.shop_waiting_players = set()
        self.shop_deadlines = {}

    def serialize_match_state(self) -> dict:
        return {
            "type": "match_state",
            "phase": self.phase,
            "current_turn": self.get_current_player_id(),
            "battle_deadline_at": self.battle_deadline_at,
            "shop_deadlines": dict(self.shop_deadlines),
            "waiting_players": self.get_shop_waiting_players(),
            "wins_to_clinch": 5,
            "best_of": 9,
            "match_winner": self.match_winner,
            "match_end_reason": self.match_end_reason,
        }

    async def broadcast_match_state(self):
        await self.broadcast(self.serialize_match_state())

    def resolve_timeout_or_inactivity(self) -> dict | None:
        if self.phase == "match_over" or len(self.players) < 2:
            return None

        now = time.time()

        for player_name, last_seen in list(self.last_activity.items()):
            if player_name not in self.players:
                continue
            if now - last_seen >= 120:
                opponent_id = self.get_opponent_id(player_name)
                if opponent_id:
                    return {
                        "winner": opponent_id,
                        "loser": player_name,
                        "reason": f"{player_name} went inactive.",
                    }

        if self.phase == "battle" and self.battle_deadline_at and now >= self.battle_deadline_at:
            timed_out_player = self.get_current_player_id()
            opponent_id = self.get_opponent_id(timed_out_player) if timed_out_player else None
            if timed_out_player and opponent_id:
                return {
                    "winner": opponent_id,
                    "loser": timed_out_player,
                    "reason": f"{timed_out_player} ran out of time on their turn.",
                }

        if self.phase == "shop":
            for player_name in self.get_shop_waiting_players():
                deadline = self.shop_deadlines.get(player_name)
                if deadline and now >= deadline:
                    opponent_id = self.get_opponent_id(player_name)
                    if opponent_id:
                        return {
                            "winner": opponent_id,
                            "loser": player_name,
                            "reason": f"{player_name} ran out of time in the shop.",
                        }

        return None

    def get_price(self, upgrade_id):
        return self.upgrade_store.get_price_by_id(upgrade_id)

    async def reset_game(self):
        self.deck = self.generate_deck()
        for player in self.players.values():
            player.reset()

        self.turn_index = 0
        await self.open_upgrade_store()

    def get_shop_waiting_players(self) -> list[str]:
        return [player_name for player_name in self.players.keys() if player_name in self.shop_waiting_players]

    async def broadcast_shop_status(self):
        await self.broadcast({
            "type": "shop_status",
            "waiting_players": self.get_shop_waiting_players(),
        })

    async def mark_shop_ready(self, player_id: str):
        self.shop_waiting_players.discard(player_id)
        self.shop_deadlines.pop(player_id, None)
        await self.broadcast_shop_status()
        if not self.shop_waiting_players:
            self.start_battle_phase()
            await self.broadcast_match_state()

    async def open_upgrade_store(self):
        self.start_shop_phase()
        for player_id, ws in self.websocket_connections.items():
            try:
                store_selection = self.upgrade_store.get_selection_of_upgrades()
                serialized_upgrades = [upgrade.to_dict() for upgrade in store_selection]

                await ws.send_json({
                    "type": "open_store",
                    "player": player_id,
                    "upgrades": serialized_upgrades,
                    "waiting_players": self.get_shop_waiting_players(),
                })
            except Exception as error:
                print(f"Failed to send store selection to {player_id}: {error}")
                traceback.print_exc()

        await self.broadcast_shop_status()
        await self.broadcast_match_state()

    async def apply_upgrades(self, player_id):
        await self.broadcast(self.players[player_id].apply_upgrades())

    async def broadcast(self, message: dict):
        disconnected_players = []
        for player, ws in self.websocket_connections.items():
            try:
                await ws.send_json(message)
            except Exception:
                disconnected_players.append(player)

        for player in disconnected_players:
            del self.websocket_connections[player]

    async def add_upgrade(self, player_id, upgrade_id):
        player = self.players[player_id]
        player.upgrades.append(self.upgrade_store.get_upgrade_by_id(upgrade_id))
        print(f"Added upgrade {upgrade_id} to player {player_id}")

    def deal_card(self, player_id: str):
        if player_id not in self.players:
            return {"error": "Player not found"}

        player = self.players[player_id]
        if not self.deck and not player.special_deck:
            self.deck = self.generate_deck()
            player.special_deck = player.build_special_deck()

        combined_pool = self.deck + player.special_deck
        if not combined_pool:
            return {"error": "No cards available"}

        weights = [player.get_draw_weight(card) for card in combined_pool]
        selected_index = random.choices(range(len(combined_pool)), weights=weights, k=1)[0]

        if selected_index < len(self.deck):
            card = self.deck.pop(selected_index)
        else:
            card = player.special_deck.pop(selected_index - len(self.deck))

        player.hand.append(card)
        return card

    def remove_selected_cards(self, player_id: str, selected_cards: List[dict]) -> dict:
        if player_id not in self.players:
            return {"error": "Player not found"}

        player = self.players[player_id]
        if not player.hand:
            return {"error": "Player has no hand"}

        selected_card_tuples = {(card["rank"], card["suit"]) for card in selected_cards}
        new_hand = [card for card in player.hand if (card.rank, card.suit) not in selected_card_tuples]
        discarded_cards = [card for card in player.hand if (card.rank, card.suit) in selected_card_tuples]

        if len(new_hand) == len(player.hand):
            return {"error": "Selected cards not found in hand"}

        player.hand = new_hand
        while len(player.hand) < player.hand_size:
            dealt = self.deal_card(player_id)
            if isinstance(dealt, dict) and dealt.get("error"):
                break

        return {
            "discarded": self.serialize_cards(discarded_cards),
            "new_hand": self.serialize_cards(player.hand),
        }

    def generate_deck(self):
        return [Card(rank, suit) for rank in BASE_RANKS for suit in CLASSIC_SUITS] * 10

    def serialize_cards(self, cards: list[Card]) -> list[dict]:
        return [{"rank": card.rank, "suit": card.suit} for card in cards]

    def resolve_card_variants(self, player: Player, card: dict) -> list[dict]:
        rank = card["rank"]
        suit = card["suit"]

        if rank == "Joker" or suit == "Wild":
            return [
                {"rank": candidate_rank, "suit": candidate_suit}
                for candidate_suit in player.get_available_suits()
                for candidate_rank in player.get_available_ranks()
            ]

        if rank == "Flame":
            return [
                {"rank": candidate_rank, "suit": "Fire"}
                for candidate_rank in player.get_available_ranks()
            ]

        return [card]

    def evaluate_concrete_hand(self, cards: list[dict], player: Player) -> tuple[int, str, int]:
        rank_counts = {}
        suit_counts = {}
        ranks = []
        base_values = []
        modifier_dict = {
            "Water": player.water_damage_modifier,
            "Fire": player.fire_damage_modifier,
            "Air": player.air_damage_modifier,
            "Earth": player.earth_damage_modifier,
            "Plasma": player.plasma_damage_modifier,
        }

        for card in cards:
            rank = RANK_VALUES[card["rank"]]
            suit = card["suit"]
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
            suit_counts[suit] = suit_counts.get(suit, 0) + 1
            ranks.append(rank)
            rank_modifier = 1.0
            if rank <= 7:
                rank_modifier *= player.low_card_damage_modifier
            elif rank >= 10:
                rank_modifier *= player.high_card_damage_modifier

            total_modifier = modifier_dict.get(suit, 1.0) * player.damage_modifier * rank_modifier
            damage_rank = rank + (player.plasma_bonus_value if suit == "Plasma" else 0)
            base_values.append(damage_rank * total_modifier)

        rank_frequencies = sorted(rank_counts.values(), reverse=True)
        is_flush = len(cards) >= 5 and max(suit_counts.values()) == len(cards)
        sorted_ranks = sorted(set(ranks))
        is_straight = False

        if len(sorted_ranks) >= 5:
            for index in range(len(sorted_ranks) - 4):
                window = sorted_ranks[index:index + 5]
                if window[-1] - window[0] == 4 and len(window) == 5:
                    is_straight = True
                    break

            if sorted_ranks[-5:] == [2, 3, 4, 5, 14]:
                is_straight = True

        is_royal = is_flush and {10, 11, 12, 13, 14}.issubset(set(ranks))
        if is_royal:
            hand_type = "royal flush"
        elif is_straight and is_flush:
            hand_type = "straight flush"
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

        multiplier = HAND_MULTIPLIERS[hand_type]
        hand_type_modifier = 1.0
        if hand_type in {"pair", "two pair"}:
            hand_type_modifier *= player.pair_damage_modifier
        if hand_type in {"straight", "straight flush", "royal flush"}:
            hand_type_modifier *= player.straight_damage_modifier
        if hand_type in {"flush", "straight flush", "royal flush"}:
            hand_type_modifier *= player.flush_damage_modifier
        if hand_type in {"three of a kind", "full house"}:
            hand_type_modifier *= player.full_house_damage_modifier

        base_damage = sum(base_values) // max(1, len(base_values))
        total_damage = int(round(base_damage * multiplier * hand_type_modifier))
        return total_damage, hand_type, multiplier

    def calculate_damage(self, cards, player_id):
        player = self.players[player_id]
        variants_per_card = [self.resolve_card_variants(player, card) for card in cards]
        best_result = None
        best_score = None

        for resolved_cards in product(*variants_per_card):
            resolved_list = list(resolved_cards)
            total_damage, hand_type, multiplier = self.evaluate_concrete_hand(resolved_list, player)
            rank_total = sum(RANK_VALUES[card["rank"]] for card in resolved_list)
            score = (total_damage, multiplier, rank_total)
            if best_score is None or score > best_score:
                best_score = score
                best_result = (total_damage, hand_type, multiplier)

        if best_result is None:
            return 0, "high card", 1

        return best_result
