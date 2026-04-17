from __future__ import annotations

from copy import deepcopy


ACHIEVEMENT_DEFINITIONS = [
    {
        "id": "hands_25",
        "name": "Warm-Up Duelist",
        "description": "Play 25 hands.",
        "stat": "hands_played",
        "target": 25,
    },
    {
        "id": "hands_100",
        "name": "Table Veteran",
        "description": "Play 100 hands.",
        "stat": "hands_played",
        "target": 100,
    },
    {
        "id": "wins_5",
        "name": "First Bloodline",
        "description": "Win 5 games.",
        "stat": "games_won",
        "target": 5,
    },
    {
        "id": "wins_25",
        "name": "Crown Collector",
        "description": "Win 25 games.",
        "stat": "games_won",
        "target": 25,
    },
    {
        "id": "damage_750",
        "name": "Chip Damage Adds Up",
        "description": "Deal 750 total damage.",
        "stat": "damage_dealt",
        "target": 750,
    },
    {
        "id": "damage_3000",
        "name": "Arena Breaker",
        "description": "Deal 3000 total damage.",
        "stat": "damage_dealt",
        "target": 3000,
    },
    {
        "id": "discards_50",
        "name": "Mulligan Enjoyer",
        "description": "Discard 50 cards.",
        "stat": "cards_discarded",
        "target": 50,
    },
    {
        "id": "earth_flush_10",
        "name": "Stone Garden",
        "description": "Play 10 Earth flushes.",
        "stat": "earth_flushes",
        "target": 10,
    },
    {
        "id": "fire_flush_10",
        "name": "Volcanic Taste",
        "description": "Play 10 Fire flushes.",
        "stat": "fire_flushes",
        "target": 10,
    },
    {
        "id": "water_flush_10",
        "name": "Tidecaller",
        "description": "Play 10 Water flushes.",
        "stat": "water_flushes",
        "target": 10,
    },
    {
        "id": "air_flush_10",
        "name": "Storm Table",
        "description": "Play 10 Air flushes.",
        "stat": "air_flushes",
        "target": 10,
    },
    {
        "id": "straight_flush_3",
        "name": "Impossible Lines",
        "description": "Play 3 straight flushes.",
        "stat": "straight_flushes_played",
        "target": 3,
    },
    {
        "id": "royal_flush_1",
        "name": "Crowned By Chaos",
        "description": "Play a royal flush.",
        "stat": "royal_flushes_played",
        "target": 1,
    },
    {
        "id": "upgrades_25",
        "name": "Greedy Between Rounds",
        "description": "Buy 25 upgrades.",
        "stat": "upgrades_bought",
        "target": 25,
    },
]


TALENT_DEFINITIONS = [
    {
        "id": "earth_attunement",
        "name": "Earth Attunement",
        "description": "+1% Earth damage.",
        "cost": 1,
        "requires": [],
        "bonuses": {"earth_damage_pct": 1},
    },
    {
        "id": "fire_attunement",
        "name": "Fire Attunement",
        "description": "+1% Fire damage.",
        "cost": 1,
        "requires": [],
        "bonuses": {"fire_damage_pct": 1},
    },
    {
        "id": "water_attunement",
        "name": "Water Attunement",
        "description": "+1% Water damage.",
        "cost": 1,
        "requires": [],
        "bonuses": {"water_damage_pct": 1},
    },
    {
        "id": "air_attunement",
        "name": "Air Attunement",
        "description": "+1% Air damage.",
        "cost": 1,
        "requires": [],
        "bonuses": {"air_damage_pct": 1},
    },
    {
        "id": "battle_rhythm",
        "name": "Battle Rhythm",
        "description": "+2% overall damage.",
        "cost": 1,
        "requires": [],
        "bonuses": {"damage_pct": 2},
    },
    {
        "id": "iron_heart",
        "name": "Iron Heart",
        "description": "+4% max health.",
        "cost": 1,
        "requires": [],
        "bonuses": {"health_pct": 4},
    },
    {
        "id": "prismatic_crown",
        "name": "Prismatic Crown",
        "description": "+5% to all elemental damage and +3% overall damage.",
        "cost": 4,
        "requires": [
            "earth_attunement",
            "fire_attunement",
            "water_attunement",
            "air_attunement",
            "battle_rhythm",
            "iron_heart",
        ],
        "bonuses": {
            "earth_damage_pct": 5,
            "fire_damage_pct": 5,
            "water_damage_pct": 5,
            "air_damage_pct": 5,
            "damage_pct": 3,
        },
    },
]


DEFAULT_STATS = {
    "hands_played": 0,
    "games_won": 0,
    "damage_dealt": 0,
    "cards_discarded": 0,
    "earth_flushes": 0,
    "fire_flushes": 0,
    "water_flushes": 0,
    "air_flushes": 0,
    "straight_flushes_played": 0,
    "royal_flushes_played": 0,
    "upgrades_bought": 0,
}


def default_stats() -> dict:
    return deepcopy(DEFAULT_STATS)


def normalize_stats(stats: dict | None) -> dict:
    normalized = default_stats()
    if not stats:
        return normalized

    for key in normalized:
        value = stats.get(key, 0)
        normalized[key] = int(value) if isinstance(value, (int, float)) else 0
    return normalized


def evaluate_achievements(stats: dict, unlocked_ids: list[str] | None) -> list[str]:
    unlocked = set(unlocked_ids or [])
    for definition in ACHIEVEMENT_DEFINITIONS:
        if stats.get(definition["stat"], 0) >= definition["target"]:
            unlocked.add(definition["id"])
    return sorted(unlocked)


def get_talent_definition(talent_id: str) -> dict | None:
    return next((talent for talent in TALENT_DEFINITIONS if talent["id"] == talent_id), None)


def spent_talent_points(unlocked_talents: list[str] | None) -> int:
    owned = set(unlocked_talents or [])
    return sum(talent["cost"] for talent in TALENT_DEFINITIONS if talent["id"] in owned)


def available_talent_points(unlocked_achievements: list[str] | None, unlocked_talents: list[str] | None) -> int:
    return max(0, len(unlocked_achievements or []) - spent_talent_points(unlocked_talents))


def can_unlock_talent(
    talent_id: str,
    unlocked_achievements: list[str] | None,
    unlocked_talents: list[str] | None,
) -> tuple[bool, str | None]:
    talent = get_talent_definition(talent_id)
    if not talent:
        return False, "Talent not found"

    owned = set(unlocked_talents or [])
    if talent_id in owned:
        return False, "Talent already unlocked"

    missing_requirements = [required for required in talent["requires"] if required not in owned]
    if missing_requirements:
        return False, "Prerequisites not met"

    if available_talent_points(unlocked_achievements, unlocked_talents) < talent["cost"]:
        return False, "Not enough talent points"

    return True, None


def compute_talent_bonuses(unlocked_talents: list[str] | None) -> dict[str, int]:
    totals = {
        "damage_pct": 0,
        "health_pct": 0,
        "earth_damage_pct": 0,
        "fire_damage_pct": 0,
        "water_damage_pct": 0,
        "air_damage_pct": 0,
    }
    owned = set(unlocked_talents or [])
    for talent in TALENT_DEFINITIONS:
        if talent["id"] not in owned:
            continue
        for bonus_key, bonus_value in talent["bonuses"].items():
            totals[bonus_key] = totals.get(bonus_key, 0) + bonus_value
    return totals


def build_meta_snapshot(stats: dict, unlocked_achievements: list[str] | None, unlocked_talents: list[str] | None) -> dict:
    normalized_stats = normalize_stats(stats)
    achievement_ids = set(unlocked_achievements or [])
    talent_ids = set(unlocked_talents or [])
    current_points = available_talent_points(list(achievement_ids), list(talent_ids))

    achievements = []
    for definition in ACHIEVEMENT_DEFINITIONS:
        progress = normalized_stats.get(definition["stat"], 0)
        achievements.append({
            "id": definition["id"],
            "name": definition["name"],
            "description": definition["description"],
            "progress": min(progress, definition["target"]),
            "target": definition["target"],
            "unlocked": definition["id"] in achievement_ids,
        })

    talents = []
    for definition in TALENT_DEFINITIONS:
        unlocked = definition["id"] in talent_ids
        can_unlock, _ = can_unlock_talent(
            definition["id"],
            list(achievement_ids),
            list(talent_ids),
        )
        talents.append({
            "id": definition["id"],
            "name": definition["name"],
            "description": definition["description"],
            "cost": definition["cost"],
            "requires": definition["requires"],
            "unlocked": unlocked,
            "available": (not unlocked) and can_unlock,
        })

    return {
        "achievement_points": len(achievement_ids),
        "available_talent_points": current_points,
        "stats": normalized_stats,
        "achievement_count": len(achievement_ids),
        "achievements": achievements,
        "talents": talents,
        "talent_bonuses": compute_talent_bonuses(list(talent_ids)),
    }
