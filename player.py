from typing import List
from card import Card
from upgrades import Upgrade

class Player:
    def __init__(self, name: str):
        self.name = name
        self.max_health = 100
        self.health = self.max_health
        self.wins = 0
        self.hand: List[Card] = []
        self.remaining_discards = 1
        self.max_discards = 1
        self.upgrades: List[Upgrade] = []
        self.gold = 0
        self.damage_modifier = 1.0
        self.water_damage_modifier = 1.0
        self.fire_damage_modifier = 1.0
        self.air_damage_modifier = 1.0
        self.earth_damage_modifier = 1.0

    def reset(self):
        """Resets player for a new round but keeps wins."""
        self.health = self.max_health
        #self.hand = []
        self.remaining_discards = self.max_discards

    def apply_upgrades(self):
        # Reset base values
        self.max_health = 100
        self.max_discards = 1
        self.damage_modifier = 1.0
        self.water_damage_modifier = 1.0
        self.fire_damage_modifier = 1.0
        self.air_damage_modifier = 1.0
        self.earth_damage_modifier = 1.0

        # Apply upgrades
        health_percentage_bonus = 1.0
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
            elif "Increase" in upgrade.name and "Damage" in upgrade.name:
                element = upgrade.name.split()[1]  # Extracts Earth, Fire, Water, or Air
                modifier_name = f"{element.lower()}_damage_modifier"
                setattr(self, modifier_name, getattr(self, modifier_name) + int(upgrade.effect.split('%')[0]) / 100.0)
        
        # Apply health percentage upgrade
        self.max_health = int(self.max_health * health_percentage_bonus)
        
        self.health = self.max_health
        self.remaining_discards = self.max_discards

        return {"type":"change_max_health","player":self.name,"health":self.health,"max_health":self.max_health}
