class Card:
    def __init__(self, rank: str, suit: str, base_damage: int = 5):
        self.rank = rank  # e.g., "Ace", "2", "King"
        self.suit = suit  # e.g., "Hearts", "Spades"
        self.base_damage = base_damage

    def __repr__(self):
        return f"{self.rank} of {self.suit}"