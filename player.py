from typing import List
from card import Card

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