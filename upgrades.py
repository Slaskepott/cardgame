import random

class Upgrade:
    def __init__(self, id, name, tier, rarity, effect, cost):
        self.id = id
        self.name = name
        self.tier = tier
        self.rarity = rarity
        self.effect = effect
        self.cost = cost

    def __repr__(self):
        return f"Id{self.id}:{self.rarity} {self.name} (Tier {self.tier}) - {self.effect} (Cost: {self.cost})"

    def to_dict(self):
        return {
            "id":self.id,
            "name": self.name,
            "tier": self.tier,
            "rarity": self.rarity,
            "effect": self.effect,
            "cost": self.cost
        }

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
    
    def get_price_by_id(self, upgrade_id):
        for key in self.upgrades:
            for upgrade in self.upgrades[key]:
                if int(upgrade.id) == int(upgrade_id):
                    return upgrade.cost
        return None

    def get_upgrade_by_id(self, upgrade_id):
        for key in self.upgrades:
            for upgrade in self.upgrades[key]:
                if int(upgrade.id) == int(upgrade_id):
                    return upgrade
        return None


    def _initialize_upgrades(self):
        # Increase Health
        self.add_upgrade(1, "Increase Health", 1, "common", "+20 HP", 4)
        self.add_upgrade(2, "Increase Health", 2, "uncommon", "+40 HP", 10)
        self.add_upgrade(3, "Increase Health", 3, "rare", "+60 HP", 16)

        # Increase Health Percentage
        self.add_upgrade(4, "Increase Health %", 1, "common", "+25% HP", 4)
        self.add_upgrade(5, "Increase Health %", 2, "uncommon", "+50% HP", 8)

        # Increase Discards
        self.add_upgrade(6, "Increase Discards", 1, "common", "+1 Discard", 6)
        self.add_upgrade(7, "Increase Discards", 2, "rare", "+2 Discards", 12)
        self.add_upgrade(8, "Increase Discards", 3, "legendary", "+3 Discards", 22)

        # Increase Damage
        self.add_upgrade(9, "Increase Damage", 1, "uncommon", "+10% Damage", 8)
        self.add_upgrade(10, "Increase Damage", 2, "rare", "+20% Damage", 12)
        self.add_upgrade(11, "Increase Damage", 3, "epic", "+30% Damage", 18)
        self.add_upgrade(12, "Increase Damage", 4, "legendary", "+50% Damage", 24)


        # Elemental Damage (Earth, Fire, Water, Air)
        elements = ["Earth", "Fire", "Water", "Air"]
        id_counter = 13  # Start IDs after the previous upgrades
        for element in elements:
            self.add_upgrade(id_counter, f"Increase {element} Damage", 1, "uncommon", f"+20% {element} Damage", 4)
            id_counter += 1
            self.add_upgrade(id_counter, f"Increase {element} Damage", 2, "rare", f"+40% {element} Damage", 7)
            id_counter += 1
            self.add_upgrade(id_counter, f"Increase {element} Damage", 3, "epic", f"+60% {element} Damage", 10)
            id_counter += 1


    def add_upgrade(self, id, name, tier, rarity, effect, cost):
        upgrade = Upgrade(id, name, tier, rarity, effect, cost)
        self.upgrades[rarity].append(upgrade)

    def get_upgrades_by_rarity(self, rarity):
        return self.upgrades.get(rarity, [])

    def get_all_upgrades(self):
        return self.upgrades
    
    def get_selection_of_upgrades(self):
        selection = set()
        rarity_weights = {"common": 20, "uncommon": 10, "rare": 5, "epic": 3, "legendary": 1}
        rarities = list(self.upgrades.keys())

        while len(selection) < 5:
            chosen_rarity = random.choices(rarities, weights=[rarity_weights[r] for r in rarities], k=1)[0]
            if self.upgrades[chosen_rarity]:
                upgrade = random.choice(self.upgrades[chosen_rarity])
                selection.add(upgrade)

        return list(selection)
