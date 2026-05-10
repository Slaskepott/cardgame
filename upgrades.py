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

        # Increase Armor
        self.add_upgrade(90, "Increase Armor", 1, "common", "+10 Armor", 4)
        self.add_upgrade(91, "Increase Armor", 2, "uncommon", "+18 Armor", 7)
        self.add_upgrade(92, "Increase Armor", 3, "rare", "+28 Armor", 11)
        self.add_upgrade(93, "Increase Armor", 4, "epic", "+42 Armor", 16)
        self.add_upgrade(94, "Increase Armor", 5, "legendary", "+60 Armor", 23)

        # Damage resistances
        self.add_upgrade(95, "Low Card Shield", 1, "common", "+12% Low Card Resistance", 4)
        self.add_upgrade(96, "Low Card Shield", 2, "uncommon", "+20% Low Card Resistance", 7)
        self.add_upgrade(97, "Low Card Shield", 3, "rare", "+32% Low Card Resistance", 11)
        self.add_upgrade(98, "High Card Shield", 1, "common", "+10% High Card Resistance", 4)
        self.add_upgrade(99, "High Card Shield", 2, "uncommon", "+18% High Card Resistance", 7)
        self.add_upgrade(100, "High Card Shield", 3, "rare", "+28% High Card Resistance", 11)
        self.add_upgrade(101, "Straight Shelter", 1, "uncommon", "+12% Straight Resistance", 5)
        self.add_upgrade(102, "Straight Shelter", 2, "rare", "+20% Straight Resistance", 9)
        self.add_upgrade(103, "Straight Shelter", 3, "epic", "+30% Straight Resistance", 14)
        self.add_upgrade(104, "Flush Shelter", 1, "uncommon", "+12% Flush Resistance", 5)
        self.add_upgrade(105, "Flush Shelter", 2, "rare", "+20% Flush Resistance", 9)
        self.add_upgrade(106, "Flush Shelter", 3, "epic", "+30% Flush Resistance", 14)

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

        for element in elements:
            self.add_upgrade(id_counter, f"Increase {element} Draw", 1, "common", f"+8% {element} Draw Chance", 4)
            id_counter += 1
            self.add_upgrade(id_counter, f"Increase {element} Draw", 2, "uncommon", f"+15% {element} Draw Chance", 7)
            id_counter += 1
            self.add_upgrade(id_counter, f"Increase {element} Draw", 3, "rare", f"+25% {element} Draw Chance", 11)
            id_counter += 1
            self.add_upgrade(id_counter, f"Increase {element} Draw", 4, "epic", f"+40% {element} Draw Chance", 16)
            id_counter += 1
            self.add_upgrade(id_counter, f"Increase {element} Draw", 5, "legendary", f"+60% {element} Draw Chance", 23)
            id_counter += 1

        # Card rank specialists
        self.add_upgrade(id_counter, "High Cards Specialist", 1, "common", "+5% High Card Damage", 5)
        id_counter += 1
        self.add_upgrade(id_counter, "High Cards Specialist", 2, "uncommon", "+10% High Card Damage", 8)
        id_counter += 1
        self.add_upgrade(id_counter, "High Cards Specialist", 3, "rare", "+20% High Card Damage", 13)
        id_counter += 1
        self.add_upgrade(id_counter, "High Cards Specialist", 4, "epic", "+40% High Card Damage", 19)
        id_counter += 1
        self.add_upgrade(id_counter, "High Cards Specialist", 5, "legendary", "+60% High Card Damage", 26)
        id_counter += 1

        self.add_upgrade(id_counter, "Low Cards Specialist", 1, "common", "+10% Low Card Damage", 6)
        id_counter += 1
        self.add_upgrade(id_counter, "Low Cards Specialist", 2, "uncommon", "+20% Low Card Damage", 10)
        id_counter += 1
        self.add_upgrade(id_counter, "Low Cards Specialist", 3, "rare", "+40% Low Card Damage", 16)
        id_counter += 1
        self.add_upgrade(id_counter, "Low Cards Specialist", 4, "epic", "+80% Low Card Damage", 24)
        id_counter += 1
        self.add_upgrade(id_counter, "Low Cards Specialist", 5, "legendary", "+120% Low Card Damage", 34)
        id_counter += 1

        self.add_upgrade(id_counter, "High Draw Specialist", 1, "common", "+8% High Card Draw Chance", 5)
        id_counter += 1
        self.add_upgrade(id_counter, "High Draw Specialist", 2, "uncommon", "+15% High Card Draw Chance", 8)
        id_counter += 1
        self.add_upgrade(id_counter, "High Draw Specialist", 3, "rare", "+25% High Card Draw Chance", 12)
        id_counter += 1
        self.add_upgrade(id_counter, "High Draw Specialist", 4, "epic", "+40% High Card Draw Chance", 18)
        id_counter += 1
        self.add_upgrade(id_counter, "High Draw Specialist", 5, "legendary", "+60% High Card Draw Chance", 26)
        id_counter += 1

        self.add_upgrade(id_counter, "Low Draw Specialist", 1, "common", "+10% Low Card Draw Chance", 6)
        id_counter += 1
        self.add_upgrade(id_counter, "Low Draw Specialist", 2, "uncommon", "+18% Low Card Draw Chance", 9)
        id_counter += 1
        self.add_upgrade(id_counter, "Low Draw Specialist", 3, "rare", "+30% Low Card Draw Chance", 14)
        id_counter += 1
        self.add_upgrade(id_counter, "Low Draw Specialist", 4, "epic", "+50% Low Card Draw Chance", 21)
        id_counter += 1
        self.add_upgrade(id_counter, "Low Draw Specialist", 5, "legendary", "+80% Low Card Draw Chance", 30)
        id_counter += 1

        self.add_upgrade(id_counter, "Royal Invitation", 1, "epic", "+25% Q/K/A Draw Chance", 18)
        id_counter += 1
        self.add_upgrade(id_counter, "Royal Invitation", 2, "legendary", "+50% Q/K/A Draw Chance", 29)
        id_counter += 1

        self.add_upgrade(id_counter, "Tiny Troublemakers", 1, "epic", "+45% Chance To Draw 2 Or 3", 17)
        id_counter += 1
        self.add_upgrade(id_counter, "Tiny Troublemakers", 2, "legendary", "+90% Chance To Draw 2 Or 3", 28)
        id_counter += 1

        self.add_upgrade(id_counter, "Echo Hand", 1, "common", "+2% Chance To Play A Hand Twice", 4)
        id_counter += 1
        self.add_upgrade(id_counter, "Echo Hand", 2, "uncommon", "+8% Chance To Play A Hand Twice", 8)
        id_counter += 1
        self.add_upgrade(id_counter, "Echo Hand", 3, "rare", "+15% Chance To Play A Hand Twice", 13)
        id_counter += 1
        self.add_upgrade(id_counter, "Echo Hand", 4, "epic", "+30% Chance To Play A Hand Twice", 20)
        id_counter += 1
        self.add_upgrade(id_counter, "Echo Hand", 5, "legendary", "+50% Chance To Play A Hand Twice", 31)
        id_counter += 1

        self.add_upgrade(id_counter, "Gap Straight", 1, "legendary", "Straights Can Skip One Rank", 24)
        id_counter += 1
        self.add_upgrade(id_counter, "Soft Flush", 1, "legendary", "Flushes Only Need 4 Suited Cards", 24)
        id_counter += 1

        self.add_upgrade(id_counter, "Grand Bazaar", 1, "epic", "+1 Shop Selection", 18)
        id_counter += 1
        self.add_upgrade(id_counter, "Grand Bazaar", 2, "legendary", "+3 Shop Selections", 30)


    def add_upgrade(self, id, name, tier, rarity, effect, cost):
        upgrade = Upgrade(id, name, tier, rarity, effect, cost)
        self.upgrades[rarity].append(upgrade)

    def get_upgrades_by_rarity(self, rarity):
        return self.upgrades.get(rarity, [])

    def get_all_upgrades(self):
        return self.upgrades
    
    def get_selection_of_upgrades(self, selection_size=5):
        selection = []
        seen_ids = set()
        rarity_weights = {"common": 20, "uncommon": 10, "rare": 5, "epic": 3, "legendary": 1}
        rarities = list(self.upgrades.keys())

        while len(selection) < selection_size:
            chosen_rarity = random.choices(rarities, weights=[rarity_weights[r] for r in rarities], k=1)[0]
            if self.upgrades[chosen_rarity]:
                upgrade = random.choice(self.upgrades[chosen_rarity])
                if upgrade.id in seen_ids:
                    continue
                selection.append(upgrade)
                seen_ids.add(upgrade.id)

        return selection
