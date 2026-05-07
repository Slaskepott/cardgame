from typing import List

from card import Card
from relics import Relic
from upgrades import Upgrade


class Player:
    def __init__(
        self,
        name: str,
        account_email: str | None = None,
        talent_bonuses: dict | None = None,
        avatar: str | None = None,
        level_unlocks: list[str] | None = None,
        level_reward_bonuses: dict | None = None,
    ):
        self.name = name
        self.account_email = account_email
        self.avatar = avatar or "👤"
        self.talent_bonuses = talent_bonuses or {}
        self.level_unlocks = list(level_unlocks or [])
        self.level_reward_bonuses = level_reward_bonuses or {}
        self.max_health = 100
        self.health = self.max_health
        self.armor = 0
        self.wins = 0
        self.hand: List[Card] = []
        self.special_deck: List[Card] = []
        self.remaining_discards = 1
        self.max_discards = 1
        self.hand_size = 8
        self.upgrades: List[Upgrade] = []
        self.relics: List[Relic] = []
        self.gold = 0
        self.damage_modifier = 1.0
        self.water_damage_modifier = 1.0
        self.fire_damage_modifier = 1.0
        self.air_damage_modifier = 1.0
        self.earth_damage_modifier = 1.0
        self.plasma_damage_modifier = 1.0
        self.low_card_damage_modifier = 1.0
        self.high_card_damage_modifier = 1.0
        self.water_draw_modifier = 1.0
        self.fire_draw_modifier = 1.0
        self.air_draw_modifier = 1.0
        self.earth_draw_modifier = 1.0
        self.plasma_draw_modifier = 1.0
        self.low_card_draw_modifier = 1.0
        self.high_card_draw_modifier = 1.0
        self.royal_draw_modifier = 1.0
        self.tiny_draw_modifier = 1.0
        self.joker_draw_modifier = 1.0
        self.pair_damage_modifier = 1.0
        self.straight_damage_modifier = 1.0
        self.flush_damage_modifier = 1.0
        self.full_house_damage_modifier = 1.0
        self.gold_gain_flat = 0
        self.shop_rerolls_flat = 0
        self.damage_taken_multiplier = 1.0
        self.plasma_bonus_value = 0
        self.tiny_rank_damage_multiplier = 1.0
        self.discard_gold_bonus = 0
        self.reroll_health_cost = 0
        self.full_house_armor_gain = 0
        self.repeated_suit_damage_bonus_pct = 0
        self.apply_upgrades()
        self.special_deck = self.build_special_deck()

    def reset(self):
        """Resets player for a new round but keeps wins."""
        self.health = self.max_health
        self.special_deck = self.build_special_deck()
        self.remaining_discards = self.max_discards
        while len(self.hand) > self.hand_size:
            self.hand.pop()

    def get_available_suits(self) -> list[str]:
        suits = ["Fire", "Air", "Earth", "Water"]
        if "plasma" in self.level_unlocks:
            suits.append("Plasma")
        return suits

    def get_available_ranks(self) -> list[str]:
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        if "fifteen" in self.level_unlocks:
            ranks.append("15")
        return ranks

    def build_special_deck(self) -> List[Card]:
        special_cards: List[Card] = []

        if "joker" in self.level_unlocks:
            special_cards.extend([
                Card("Joker", "Wild"),
                Card("Joker", "Wild"),
                Card("Joker", "Wild"),
            ])

        if "flame" in self.level_unlocks:
            special_cards.append(Card("Flame", "Fire"))

        if "fifteen" in self.level_unlocks:
            for suit in ["Fire", "Air", "Earth", "Water"]:
                special_cards.append(Card("15", suit))

        if "plasma" in self.level_unlocks:
            for rank in ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]:
                special_cards.append(Card(rank, "Plasma"))

        if "afterimage_coil" in self.level_unlocks:
            special_cards.extend([
                Card("Q", "Plasma"),
                Card("K", "Plasma"),
                Card("A", "Plasma"),
            ])

        return special_cards

    def apply_upgrades(self):
        self.max_health = 100
        self.armor = 0
        self.max_discards = 1
        self.hand_size = 8
        self.damage_modifier = 1.0 + (
            (self.talent_bonuses.get("damage_pct", 0) + self.level_reward_bonuses.get("damage_pct", 0))
            / 100.0
        )
        self.max_health += int(self.talent_bonuses.get("health_flat", 0))
        self.max_health += int(self.level_reward_bonuses.get("health_flat", 0))
        self.armor += int(self.talent_bonuses.get("armor_flat", 0))
        self.armor += int(self.level_reward_bonuses.get("armor_flat", 0))
        self.water_damage_modifier = 1.0 + (self.talent_bonuses.get("water_damage_pct", 0) / 100.0)
        self.fire_damage_modifier = 1.0 + (self.talent_bonuses.get("fire_damage_pct", 0) / 100.0)
        self.air_damage_modifier = 1.0 + (self.talent_bonuses.get("air_damage_pct", 0) / 100.0)
        self.earth_damage_modifier = 1.0 + (self.talent_bonuses.get("earth_damage_pct", 0) / 100.0)
        self.plasma_damage_modifier = 1.0 + (self.talent_bonuses.get("plasma_damage_pct", 0) / 100.0)
        self.low_card_damage_modifier = 1.0 + (self.talent_bonuses.get("low_card_damage_pct", 0) / 100.0)
        self.high_card_damage_modifier = 1.0 + (self.talent_bonuses.get("high_card_damage_pct", 0) / 100.0)
        self.water_draw_modifier = 1.0 + (
            (self.talent_bonuses.get("water_draw_pct", 0) + self.level_reward_bonuses.get("water_draw_pct", 0))
            / 100.0
        )
        self.fire_draw_modifier = 1.0 + (
            (self.talent_bonuses.get("fire_draw_pct", 0) + self.level_reward_bonuses.get("fire_draw_pct", 0))
            / 100.0
        )
        self.air_draw_modifier = 1.0 + (
            (self.talent_bonuses.get("air_draw_pct", 0) + self.level_reward_bonuses.get("air_draw_pct", 0))
            / 100.0
        )
        self.earth_draw_modifier = 1.0 + (
            (self.talent_bonuses.get("earth_draw_pct", 0) + self.level_reward_bonuses.get("earth_draw_pct", 0))
            / 100.0
        )
        self.plasma_draw_modifier = 1.0 + (self.talent_bonuses.get("plasma_draw_pct", 0) / 100.0)
        self.low_card_draw_modifier = 1.0 + (self.talent_bonuses.get("low_card_draw_pct", 0) / 100.0)
        self.high_card_draw_modifier = 1.0 + (self.talent_bonuses.get("high_card_draw_pct", 0) / 100.0)
        self.royal_draw_modifier = 1.0 + (self.talent_bonuses.get("royal_draw_pct", 0) / 100.0)
        self.tiny_draw_modifier = 1.0 + (self.talent_bonuses.get("tiny_draw_pct", 0) / 100.0)
        self.joker_draw_modifier = 1.0 + (self.talent_bonuses.get("joker_draw_pct", 0) / 100.0)
        self.pair_damage_modifier = 1.0 + (self.talent_bonuses.get("pair_damage_pct", 0) / 100.0)
        self.straight_damage_modifier = 1.0 + (self.talent_bonuses.get("straight_damage_pct", 0) / 100.0)
        self.flush_damage_modifier = 1.0 + (self.talent_bonuses.get("flush_damage_pct", 0) / 100.0)
        self.full_house_damage_modifier = 1.0 + (self.talent_bonuses.get("full_house_damage_pct", 0) / 100.0)
        self.gold_gain_flat = int(self.talent_bonuses.get("gold_gain_flat", 0))
        self.shop_rerolls_flat = int(self.talent_bonuses.get("shop_rerolls_flat", 0))
        self.damage_taken_multiplier = max(
            0.1,
            1.0 + (self.talent_bonuses.get("damage_taken_pct", 0) / 100.0),
        )
        self.plasma_draw_modifier += self.level_reward_bonuses.get("plasma_draw_pct", 0) / 100.0
        self.plasma_damage_modifier += self.level_reward_bonuses.get("plasma_damage_pct", 0) / 100.0
        self.plasma_bonus_value = int(self.level_reward_bonuses.get("plasma_bonus_value", 0))
        self.tiny_rank_damage_multiplier = 1.0
        self.discard_gold_bonus = 0
        self.reroll_health_cost = 0
        self.full_house_armor_gain = 0
        self.repeated_suit_damage_bonus_pct = 0

        health_percentage_bonus = 1.0 + (
            (self.talent_bonuses.get("health_pct", 0) + self.level_reward_bonuses.get("health_pct", 0))
            / 100.0
        )
        self.max_discards += int(self.talent_bonuses.get("max_discards_flat", 0))
        self.hand_size += int(self.talent_bonuses.get("hand_size_flat", 0))
        for upgrade in self.upgrades:
            if upgrade.name == "Increase Health":
                self.max_health += int(upgrade.effect.split()[0])
            elif upgrade.name == "Increase Armor":
                self.armor += int(upgrade.effect.split()[0])
            elif upgrade.name == "Increase Health %":
                health_percentage_bonus += int(upgrade.effect.split("%")[0]) / 100.0
            elif upgrade.name == "Increase Discards":
                self.max_discards += int(upgrade.effect.split()[0])
            elif upgrade.name == "Increase Damage":
                self.damage_modifier += int(upgrade.effect.split("%")[0]) / 100.0
            elif upgrade.name == "Low Cards Specialist":
                self.low_card_damage_modifier += int(upgrade.effect.split("%")[0]) / 100.0
            elif upgrade.name == "High Cards Specialist":
                self.high_card_damage_modifier += int(upgrade.effect.split("%")[0]) / 100.0
            elif upgrade.name == "Low Draw Specialist":
                self.low_card_draw_modifier += int(upgrade.effect.split("%")[0]) / 100.0
            elif upgrade.name == "High Draw Specialist":
                self.high_card_draw_modifier += int(upgrade.effect.split("%")[0]) / 100.0
            elif upgrade.name == "Royal Invitation":
                self.royal_draw_modifier += int(upgrade.effect.split("%")[0]) / 100.0
            elif upgrade.name == "Tiny Troublemakers":
                self.tiny_draw_modifier += int(upgrade.effect.split("%")[0]) / 100.0
            elif "Increase" in upgrade.name and "Damage" in upgrade.name:
                element = upgrade.name.split()[1]
                modifier_name = f"{element.lower()}_damage_modifier"
                setattr(
                    self,
                    modifier_name,
                    getattr(self, modifier_name) + int(upgrade.effect.split("%")[0]) / 100.0,
                )
            elif "Increase" in upgrade.name and "Draw" in upgrade.name:
                element = upgrade.name.split()[1]
                modifier_name = f"{element.lower()}_draw_modifier"
                setattr(
                    self,
                    modifier_name,
                    getattr(self, modifier_name) + int(upgrade.effect.split("%")[0]) / 100.0,
                )

        for relic in self.relics:
            if relic.id == "tiny_tyrants":
                self.tiny_rank_damage_multiplier = 3.0
            elif relic.id == "house_advantage":
                self.full_house_armor_gain += 12
            elif relic.id == "greedy_fingers":
                self.discard_gold_bonus += 1
                self.max_health -= 20
            elif relic.id == "wild_orbit":
                self.joker_draw_modifier += 1.5
                self.reroll_health_cost += 6
            elif relic.id == "tidal_memory":
                self.repeated_suit_damage_bonus_pct += 18
            elif relic.id == "overflow_chamber":
                self.hand_size += 1
                self.damage_modifier = max(0.4, self.damage_modifier - 0.2)
            elif relic.id == "plasma_lattice":
                self.plasma_damage_modifier += 0.4
                self.plasma_draw_modifier += 0.3
            elif relic.id == "fortress_heart":
                self.armor += 25
                self.max_health += 20

        self.max_health = int(self.max_health * health_percentage_bonus)
        self.health = self.max_health
        self.remaining_discards = self.max_discards

        return {
            "type": "apply_upgrades",
            "player": self.name,
            "health": self.health,
            "max_health": self.max_health,
            "max_discards": self.max_discards,
            "armor": self.armor,
            "armor_reduction_pct": self.get_armor_damage_reduction_pct(),
            "upgrades": [upgrade.to_dict() for upgrade in self.upgrades],
            "relics": [relic.to_dict() for relic in self.relics],
        }

    def get_draw_weight(self, card: Card) -> float:
        suit_modifier = getattr(self, f"{card.suit.lower()}_draw_modifier", 1.0)
        rank_modifier = 1.0

        if card.rank == "Joker":
            return max(0.01, self.joker_draw_modifier)
        if card.rank == "Flame":
            return 1.0
        if card.rank in {"2", "3"}:
            rank_modifier *= self.tiny_draw_modifier
        if card.rank in {"Q", "K", "A"}:
            rank_modifier *= self.royal_draw_modifier
        if card.rank in {"2", "3", "4", "5", "6", "7"}:
            rank_modifier *= self.low_card_draw_modifier
        if card.rank in {"10", "J", "Q", "K", "A", "15"}:
            rank_modifier *= self.high_card_draw_modifier

        return max(0.01, suit_modifier * rank_modifier)

    def get_armor_damage_reduction(self) -> float:
        if self.armor <= 0:
            return 0.0

        scaled_armor = float(self.armor) ** 0.9
        return scaled_armor / (scaled_armor + 120.0)

    def get_armor_damage_reduction_pct(self) -> int:
        return int(round(self.get_armor_damage_reduction() * 100))
