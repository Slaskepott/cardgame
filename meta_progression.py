from __future__ import annotations

from copy import deepcopy


SPECIALIZATIONS = [
    {
        "id": "offense",
        "name": "Offense",
        "description": "Push damage a little higher and end rounds faster.",
    },
    {
        "id": "defense",
        "name": "Defense",
        "description": "Stay alive longer with tougher scaling and damage reduction.",
    },
    {
        "id": "utility",
        "name": "Utility",
        "description": "Cycle harder, smooth awkward hands, and squeeze value out of turns.",
    },
]


ACHIEVEMENT_DEFINITIONS = [
    {"id": "hands_25", "name": "Warm-Up Duelist", "description": "Play 25 hands.", "stat": "hands_played", "target": 25},
    {"id": "hands_100", "name": "Table Veteran", "description": "Play 100 hands.", "stat": "hands_played", "target": 100},
    {"id": "hands_300", "name": "Sleeves Rolled Up", "description": "Play 300 hands.", "stat": "hands_played", "target": 300},
    {"id": "wins_5", "name": "First Bloodline", "description": "Win 5 games.", "stat": "games_won", "target": 5},
    {"id": "wins_25", "name": "Crown Collector", "description": "Win 25 games.", "stat": "games_won", "target": 25},
    {"id": "wins_100", "name": "Table Tyrant", "description": "Win 100 games.", "stat": "games_won", "target": 100},
    {"id": "damage_750", "name": "Chip Damage Adds Up", "description": "Deal 750 total damage.", "stat": "damage_dealt", "target": 750},
    {"id": "damage_3000", "name": "Arena Breaker", "description": "Deal 3000 total damage.", "stat": "damage_dealt", "target": 3000},
    {"id": "damage_10000", "name": "Boss Health Bar", "description": "Deal 10000 total damage.", "stat": "damage_dealt", "target": 10000},
    {"id": "discards_50", "name": "Mulligan Enjoyer", "description": "Discard 50 cards.", "stat": "cards_discarded", "target": 50},
    {"id": "discards_250", "name": "Deck Dentist", "description": "Discard 250 cards.", "stat": "cards_discarded", "target": 250},
    {"id": "earth_flush_10", "name": "Stone Garden", "description": "Play 10 Earth flushes.", "stat": "earth_flushes", "target": 10},
    {"id": "fire_flush_10", "name": "Volcanic Taste", "description": "Play 10 Fire flushes.", "stat": "fire_flushes", "target": 10},
    {"id": "water_flush_10", "name": "Tidecaller", "description": "Play 10 Water flushes.", "stat": "water_flushes", "target": 10},
    {"id": "air_flush_10", "name": "Storm Table", "description": "Play 10 Air flushes.", "stat": "air_flushes", "target": 10},
    {"id": "straight_flush_3", "name": "Impossible Lines", "description": "Play 3 straight flushes.", "stat": "straight_flushes_played", "target": 3},
    {"id": "royal_flush_1", "name": "Crowned By Chaos", "description": "Play a royal flush.", "stat": "royal_flushes_played", "target": 1},
    {"id": "upgrades_25", "name": "Greedy Between Rounds", "description": "Buy 25 upgrades.", "stat": "upgrades_bought", "target": 25},
]


TALENT_DEFINITIONS = [
    {
        "id": "offense_root",
        "specialization": "offense",
        "name": "Open Wound",
        "description": "+2% overall damage.",
        "cost": 1,
        "requires": [],
        "row": 0,
        "column": 1,
        "bonuses": {"damage_pct": 2},
    },
    {
        "id": "offense_firebrand",
        "specialization": "offense",
        "name": "Firebrand",
        "description": "+3% Fire damage.",
        "cost": 1,
        "requires": ["offense_root"],
        "row": 1,
        "column": 0,
        "bonuses": {"fire_damage_pct": 3},
    },
    {
        "id": "offense_stonefist",
        "specialization": "offense",
        "name": "Stonefist",
        "description": "+3% Earth damage.",
        "cost": 1,
        "requires": ["offense_root"],
        "row": 1,
        "column": 2,
        "bonuses": {"earth_damage_pct": 3},
    },
    {
        "id": "offense_killing_rhythm",
        "specialization": "offense",
        "name": "Killing Rhythm",
        "description": "+4% high card damage.",
        "cost": 1,
        "requires": ["offense_firebrand"],
        "row": 2,
        "column": 0,
        "bonuses": {"high_card_damage_pct": 4},
    },
    {
        "id": "offense_primal_weight",
        "specialization": "offense",
        "name": "Primal Weight",
        "description": "+4% low card damage.",
        "cost": 1,
        "requires": ["offense_stonefist"],
        "row": 2,
        "column": 2,
        "bonuses": {"low_card_damage_pct": 4},
    },
    {
        "id": "offense_capstone",
        "specialization": "offense",
        "name": "Cataclysm",
        "description": "+8% overall damage and +2% to all elemental damage.",
        "cost": 3,
        "requires": ["offense_killing_rhythm", "offense_primal_weight"],
        "row": 3,
        "column": 1,
        "bonuses": {
            "damage_pct": 8,
            "earth_damage_pct": 2,
            "fire_damage_pct": 2,
            "water_damage_pct": 2,
            "air_damage_pct": 2,
        },
    },
    {
        "id": "defense_root",
        "specialization": "defense",
        "name": "Thick Skin",
        "description": "+4% max health.",
        "cost": 1,
        "requires": [],
        "row": 0,
        "column": 1,
        "bonuses": {"health_pct": 4},
    },
    {
        "id": "defense_brace",
        "specialization": "defense",
        "name": "Brace",
        "description": "-2% incoming damage.",
        "cost": 1,
        "requires": ["defense_root"],
        "row": 1,
        "column": 0,
        "bonuses": {"damage_taken_pct": -2},
    },
    {
        "id": "defense_long_breath",
        "specialization": "defense",
        "name": "Long Breath",
        "description": "+1 discard each round.",
        "cost": 1,
        "requires": ["defense_root"],
        "row": 1,
        "column": 2,
        "bonuses": {"max_discards_flat": 1},
    },
    {
        "id": "defense_warden",
        "specialization": "defense",
        "name": "Warden's Posture",
        "description": "+6% max health.",
        "cost": 1,
        "requires": ["defense_brace"],
        "row": 2,
        "column": 0,
        "bonuses": {"health_pct": 6},
    },
    {
        "id": "defense_stalwart",
        "specialization": "defense",
        "name": "Stalwart Core",
        "description": "-3% incoming damage.",
        "cost": 1,
        "requires": ["defense_long_breath"],
        "row": 2,
        "column": 2,
        "bonuses": {"damage_taken_pct": -3},
    },
    {
        "id": "defense_capstone",
        "specialization": "defense",
        "name": "Unbreakable",
        "description": "+10% max health and -5% incoming damage.",
        "cost": 3,
        "requires": ["defense_warden", "defense_stalwart"],
        "row": 3,
        "column": 1,
        "bonuses": {"health_pct": 10, "damage_taken_pct": -5},
    },
    {
        "id": "utility_root",
        "specialization": "utility",
        "name": "Quick Fingers",
        "description": "+1 discard each round.",
        "cost": 1,
        "requires": [],
        "row": 0,
        "column": 1,
        "bonuses": {"max_discards_flat": 1},
    },
    {
        "id": "utility_tempest",
        "specialization": "utility",
        "name": "Tempest Instinct",
        "description": "+3% Air damage.",
        "cost": 1,
        "requires": ["utility_root"],
        "row": 1,
        "column": 0,
        "bonuses": {"air_damage_pct": 3},
    },
    {
        "id": "utility_tide_memory",
        "specialization": "utility",
        "name": "Tide Memory",
        "description": "+3% Water damage.",
        "cost": 1,
        "requires": ["utility_root"],
        "row": 1,
        "column": 2,
        "bonuses": {"water_damage_pct": 3},
    },
    {
        "id": "utility_smooth_draw",
        "specialization": "utility",
        "name": "Smooth Draw",
        "description": "+4% low card damage.",
        "cost": 1,
        "requires": ["utility_tempest"],
        "row": 2,
        "column": 0,
        "bonuses": {"low_card_damage_pct": 4},
    },
    {
        "id": "utility_clever_finish",
        "specialization": "utility",
        "name": "Clever Finish",
        "description": "+4% high card damage.",
        "cost": 1,
        "requires": ["utility_tide_memory"],
        "row": 2,
        "column": 2,
        "bonuses": {"high_card_damage_pct": 4},
    },
    {
        "id": "utility_capstone",
        "specialization": "utility",
        "name": "Loaded Dice",
        "description": "+1 discard, +4% to all elemental damage.",
        "cost": 3,
        "requires": ["utility_smooth_draw", "utility_clever_finish"],
        "row": 3,
        "column": 1,
        "bonuses": {
            "max_discards_flat": 1,
            "earth_damage_pct": 4,
            "fire_damage_pct": 4,
            "water_damage_pct": 4,
            "air_damage_pct": 4,
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


def decode_talent_state(raw_talents: list | dict | None) -> tuple[list[str], str | None]:
    if isinstance(raw_talents, dict):
        unlocked = raw_talents.get("unlocked", [])
        specialization = raw_talents.get("specialization")
        return list(unlocked or []), specialization
    return list(raw_talents or []), None


def encode_talent_state(unlocked_talents: list[str], specialization: str | None) -> dict:
    return {
        "unlocked": sorted(set(unlocked_talents)),
        "specialization": specialization,
    }


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
    selected_specialization: str | None,
) -> tuple[bool, str | None]:
    talent = get_talent_definition(talent_id)
    if not talent:
        return False, "Talent not found"

    owned = set(unlocked_talents or [])
    if talent_id in owned:
        return False, "Talent already unlocked"

    if selected_specialization and talent["specialization"] != selected_specialization:
        return False, "Specialization already chosen"

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
        "low_card_damage_pct": 0,
        "high_card_damage_pct": 0,
        "max_discards_flat": 0,
        "damage_taken_pct": 0,
    }
    owned = set(unlocked_talents or [])
    for talent in TALENT_DEFINITIONS:
        if talent["id"] not in owned:
            continue
        for bonus_key, bonus_value in talent["bonuses"].items():
            totals[bonus_key] = totals.get(bonus_key, 0) + bonus_value
    return totals


def build_meta_snapshot(
    stats: dict,
    unlocked_achievements: list[str] | None,
    unlocked_talents: list[str] | None,
    selected_specialization: str | None,
) -> dict:
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
            selected_specialization,
        )
        talents.append({
            "id": definition["id"],
            "specialization": definition["specialization"],
            "name": definition["name"],
            "description": definition["description"],
            "cost": definition["cost"],
            "requires": definition["requires"],
            "row": definition["row"],
            "column": definition["column"],
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
        "specializations": SPECIALIZATIONS,
        "selected_specialization": selected_specialization,
        "talent_bonuses": compute_talent_bonuses(list(talent_ids)),
    }
