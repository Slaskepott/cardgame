import random

class Upgrade:
    def __init__(self, name, tier, rarity, effect, cost):
        self.name = name
        self.tier = tier
        self.rarity = rarity
        self.effect = effect
        self.cost = cost

    def __repr__(self):
        return f"{self.rarity} {self.name} (Tier {self.tier}) - {self.effect} (Cost: {self.cost})"

class UpgradeStore:
    def __init__(self):
        self.upgrades = {
            "common": [],
            "uncommon": [],
            "rare": [],
            "epic": [],
            "legendary": []
        }
        self._initialize_upgrades()

    def _initialize_upgrades(self):
        # Increase Health
        self.add_upgrade("Increase Health", 1, "common", "+20 HP", 2)
        self.add_upgrade("Increase Health", 2, "uncommon", "+40 HP", 5)
        self.add_upgrade("Increase Health", 3, "rare", "+60 HP", 8)
        
        # Increase Health Percentage
        self.add_upgrade("Increase Health %", 1, "common", "+25% HP", 2)
        self.add_upgrade("Increase Health %", 2, "uncommon", "+50% HP", 4)
        
        # Increase Discards
        self.add_upgrade("Increase Discards", 1, "common", "+1 Discard", 3)
        self.add_upgrade("Increase Discards", 2, "uncommon", "+2 Discards", 4)
        self.add_upgrade("Increase Discards", 3, "rare", "+3 Discards", 5)
        
        # Increase Damage
        self.add_upgrade("Increase Damage", 1, "uncommon", "+10% Damage", 4)
        self.add_upgrade("Increase Damage", 2, "rare", "+20% Damage", 6)
        self.add_upgrade("Increase Damage", 3, "epic", "+30% Damage", 9)
        self.add_upgrade("Increase Damage", 4, "legendary", "+50% Damage", 12)
        
        # Elemental Damage (Earth, Fire, Water, Air)
        elements = ["Earth", "Fire", "Water", "Air"]
        for element in elements:
            self.add_upgrade(f"Increase {element} Damage", 1, "uncommon", f"+20% {element} Damage", 4)
            self.add_upgrade(f"Increase {element} Damage", 2, "rare", f"+40% {element} Damage", 7)
            self.add_upgrade(f"Increase {element} Damage", 3, "epic", f"+60% {element} Damage", 10)

    def add_upgrade(self, name, tier, rarity, effect, cost):
        upgrade = Upgrade(name, tier, rarity, effect, cost)
        self.upgrades[rarity].append(upgrade)

    def get_upgrades_by_rarity(self, rarity):
        return self.upgrades.get(rarity, [])

    def get_all_upgrades(self):
        return self.upgrades
    
    def get_selection_of_upgrades(self):
        selection = []
        rarity_weights = {"common": 20, "uncommon": 10, "rare": 5, "epic": 3, "legendary": 1}
        rarities = list(self.upgrades.keys())
        
        while len(selection) < 5:
            chosen_rarity = random.choices(rarities, weights=[rarity_weights[r] for r in rarities], k=1)[0]
            if self.upgrades[chosen_rarity]:
                selection.append(random.choice(self.upgrades[chosen_rarity]))
        
        return selection