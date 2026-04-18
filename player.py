from typing import List
from card import Card
from upgrades import Upgrade

class Player:
    def __init__(
        self,
        name: str,
        account_email: str | None = None,
        talent_bonuses: dict | None = None,
        avatar: str | None = None,
    ):
        self.name = name
        self.account_email = account_email
        self.avatar = avatar or "👤"
        self.talent_bonuses = talent_bonuses or {}
        self.max_health = 100
        self.health = self.max_health
        self.wins = 0
        self.hand: List[Card] = []
        self.remaining_discards = 1
        self.max_discards = 1
        self.hand_size = 8
        self.upgrades: List[Upgrade] = []
        self.gold = 0
        self.damage_modifier = 1.0
        self.water_damage_modifier = 1.0
        self.fire_damage_modifier = 1.0
        self.air_damage_modifier = 1.0
        self.earth_damage_modifier = 1.0
        self.low_card_damage_modifier = 1.0
        self.high_card_damage_modifier = 1.0
        self.water_draw_modifier = 1.0
        self.fire_draw_modifier = 1.0
        self.air_draw_modifier = 1.0
        self.earth_draw_modifier = 1.0
        self.low_card_draw_modifier = 1.0
        self.high_card_draw_modifier = 1.0
        self.royal_draw_modifier = 1.0
        self.tiny_draw_modifier = 1.0
        self.pair_damage_modifier = 1.0
        self.straight_damage_modifier = 1.0
        self.flush_damage_modifier = 1.0
        self.full_house_damage_modifier = 1.0
        self.gold_gain_flat = 0
        self.damage_taken_multiplier = 1.0
        self.apply_upgrades()

    def reset(self):
        """Resets player for a new round but keeps wins."""
        self.health = self.max_health
        #self.hand = []
        self.remaining_discards = self.max_discards
        while len(self.hand) > self.hand_size:
            self.hand.pop()

    def apply_upgrades(self):
        # Reset base values
        self.max_health = 100
        self.max_discards = 1
        self.hand_size = 8
        self.damage_modifier = 1.0 + (self.talent_bonuses.get("damage_pct", 0) / 100.0)
        self.max_health += int(self.talent_bonuses.get("health_flat", 0))
        self.water_damage_modifier = 1.0 + (self.talent_bonuses.get("water_damage_pct", 0) / 100.0)
        self.fire_damage_modifier = 1.0 + (self.talent_bonuses.get("fire_damage_pct", 0) / 100.0)
        self.air_damage_modifier = 1.0 + (self.talent_bonuses.get("air_damage_pct", 0) / 100.0)
        self.earth_damage_modifier = 1.0 + (self.talent_bonuses.get("earth_damage_pct", 0) / 100.0)
        self.low_card_damage_modifier = 1.0 + (self.talent_bonuses.get("low_card_damage_pct", 0) / 100.0)
        self.high_card_damage_modifier = 1.0 + (self.talent_bonuses.get("high_card_damage_pct", 0) / 100.0)
        self.water_draw_modifier = 1.0 + (self.talent_bonuses.get("water_draw_pct", 0) / 100.0)
        self.fire_draw_modifier = 1.0 + (self.talent_bonuses.get("fire_draw_pct", 0) / 100.0)
        self.air_draw_modifier = 1.0 + (self.talent_bonuses.get("air_draw_pct", 0) / 100.0)
        self.earth_draw_modifier = 1.0 + (self.talent_bonuses.get("earth_draw_pct", 0) / 100.0)
        self.low_card_draw_modifier = 1.0 + (self.talent_bonuses.get("low_card_draw_pct", 0) / 100.0)
        self.high_card_draw_modifier = 1.0 + (self.talent_bonuses.get("high_card_draw_pct", 0) / 100.0)
        self.royal_draw_modifier = 1.0 + (self.talent_bonuses.get("royal_draw_pct", 0) / 100.0)
        self.tiny_draw_modifier = 1.0 + (self.talent_bonuses.get("tiny_draw_pct", 0) / 100.0)
        self.pair_damage_modifier = 1.0 + (self.talent_bonuses.get("pair_damage_pct", 0) / 100.0)
        self.straight_damage_modifier = 1.0 + (self.talent_bonuses.get("straight_damage_pct", 0) / 100.0)
        self.flush_damage_modifier = 1.0 + (self.talent_bonuses.get("flush_damage_pct", 0) / 100.0)
        self.full_house_damage_modifier = 1.0 + (self.talent_bonuses.get("full_house_damage_pct", 0) / 100.0)
        self.gold_gain_flat = int(self.talent_bonuses.get("gold_gain_flat", 0))
        self.damage_taken_multiplier = max(
            0.1,
            1.0 + (self.talent_bonuses.get("damage_taken_pct", 0) / 100.0),
        )

        # Apply upgrades
        health_percentage_bonus = 1.0 + (self.talent_bonuses.get("health_pct", 0) / 100.0)
        self.max_discards += int(self.talent_bonuses.get("max_discards_flat", 0))
        self.hand_size += int(self.talent_bonuses.get("hand_size_flat", 0))
        for upgrade in self.upgrades:
            print(f"Upgrade name: {upgrade.name}")
            if upgrade.name == "Increase Health":
                self.max_health += int(upgrade.effect.split()[0])
            elif upgrade.name == "Increase Health %":
                health_percentage_bonus += int(upgrade.effect.split('%')[0]) / 100.0
            elif upgrade.name == "Increase Discards":
                print(f"Adding {int(upgrade.effect.split()[0])} discards")
                self.max_discards += int(upgrade.effect.split()[0])
            elif upgrade.name == "Increase Damage":
                self.damage_modifier += int(upgrade.effect.split('%')[0]) / 100.0
            elif upgrade.name == "Low Cards Specialist":
                self.low_card_damage_modifier += int(upgrade.effect.split('%')[0]) / 100.0
            elif upgrade.name == "High Cards Specialist":
                self.high_card_damage_modifier += int(upgrade.effect.split('%')[0]) / 100.0
            elif upgrade.name == "Low Draw Specialist":
                self.low_card_draw_modifier += int(upgrade.effect.split('%')[0]) / 100.0
            elif upgrade.name == "High Draw Specialist":
                self.high_card_draw_modifier += int(upgrade.effect.split('%')[0]) / 100.0
            elif upgrade.name == "Royal Invitation":
                self.royal_draw_modifier += int(upgrade.effect.split('%')[0]) / 100.0
            elif upgrade.name == "Tiny Troublemakers":
                self.tiny_draw_modifier += int(upgrade.effect.split('%')[0]) / 100.0
            elif "Increase" in upgrade.name and "Damage" in upgrade.name:
                element = upgrade.name.split()[1]  # Extracts Earth, Fire, Water, or Air
                modifier_name = f"{element.lower()}_damage_modifier"
                setattr(self, modifier_name, getattr(self, modifier_name) + int(upgrade.effect.split('%')[0]) / 100.0)
            elif "Increase" in upgrade.name and "Draw" in upgrade.name:
                element = upgrade.name.split()[1]
                modifier_name = f"{element.lower()}_draw_modifier"
                setattr(self, modifier_name, getattr(self, modifier_name) + int(upgrade.effect.split('%')[0]) / 100.0)
        
        # Apply health percentage upgrade
        self.max_health = int(self.max_health * health_percentage_bonus)
        
        self.health = self.max_health
        self.remaining_discards = self.max_discards

        return {"type":"apply_upgrades",
                "player":self.name,
                "health":self.health,
                "max_health":self.max_health,
                "max_discards":self.max_discards}

    def get_draw_weight(self, card: Card) -> float:
        suit_modifier = getattr(self, f"{card.suit.lower()}_draw_modifier", 1.0)
        rank_modifier = 1.0

        if card.rank in {"2", "3"}:
            rank_modifier *= self.tiny_draw_modifier
        if card.rank in {"Q", "K", "A"}:
            rank_modifier *= self.royal_draw_modifier
        if card.rank in {"2", "3", "4", "5", "6", "7"}:
            rank_modifier *= self.low_card_draw_modifier
        if card.rank in {"10", "J", "Q", "K", "A"}:
            rank_modifier *= self.high_card_draw_modifier

        return max(0.01, suit_modifier * rank_modifier)
