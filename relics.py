from dataclasses import dataclass
import random


@dataclass(frozen=True)
class Relic:
    id: str
    name: str
    theme: str
    description: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "theme": self.theme,
            "description": self.description,
        }


RELIC_POOL: list[Relic] = [
    Relic(
        id="tiny_tyrants",
        name="Tiny Tyrants",
        theme="chaos",
        description="2s, 3s, and 4s deal triple damage.",
    ),
    Relic(
        id="house_advantage",
        name="House Advantage",
        theme="bulwark",
        description="Playing a full house grants 12 armor.",
    ),
    Relic(
        id="greedy_fingers",
        name="Greedy Fingers",
        theme="greed",
        description="Every discard gives +1 gold, but you lose 20 max health.",
    ),
    Relic(
        id="wild_orbit",
        name="Wild Orbit",
        theme="wild",
        description="Jokers are much more likely, but shop rerolls cost 6 health.",
    ),
    Relic(
        id="tidal_memory",
        name="Tidal Memory",
        theme="flow",
        description="Repeated suits in a hand gain escalating damage.",
    ),
    Relic(
        id="overflow_chamber",
        name="Overflow Chamber",
        theme="excess",
        description="Draw 1 extra card every round, but deal 20% less overall damage.",
    ),
    Relic(
        id="plasma_lattice",
        name="Plasma Lattice",
        theme="plasma",
        description="Plasma cards gain +40% damage and +30% draw chance.",
    ),
    Relic(
        id="fortress_heart",
        name="Fortress Heart",
        theme="bulwark",
        description="Gain 25 armor and 20 max health.",
    ),
]


RELICS_BY_ID = {relic.id: relic for relic in RELIC_POOL}


def get_relic_by_id(relic_id: str) -> Relic | None:
    return RELICS_BY_ID.get(relic_id)


def get_relic_offer_set(excluded_ids: set[str] | None = None, count: int = 3) -> list[Relic]:
    blocked = excluded_ids or set()
    available = [relic for relic in RELIC_POOL if relic.id not in blocked]
    if len(available) <= count:
        return list(available)
    return random.sample(available, count)
