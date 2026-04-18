from __future__ import annotations

from copy import deepcopy


SPECIALIZATIONS = [
    {
        "id": "offense",
        "name": "Offense",
        "description": "Stack pressure, chase explosive hands, and turn good draws into lethal turns.",
    },
    {
        "id": "defense",
        "name": "Defense",
        "description": "Survive longer, bend draw odds toward safer hands, and outlast greedy builds.",
    },
    {
        "id": "utility",
        "name": "Utility",
        "description": "Draw smoother, cycle harder, and twist the economy of every round.",
    },
]


ACHIEVEMENT_DEFINITIONS = [
    {"id": "hands_25", "name": "Warm-Up Duelist", "description": "Play 25 hands.", "stat": "hands_played", "target": 25, "points": 1},
    {"id": "hands_100", "name": "Table Veteran", "description": "Play 100 hands.", "stat": "hands_played", "target": 100, "points": 2},
    {"id": "hands_300", "name": "Sleeves Rolled Up", "description": "Play 300 hands.", "stat": "hands_played", "target": 300, "points": 3},
    {"id": "wins_5", "name": "First Bloodline", "description": "Win 5 games.", "stat": "games_won", "target": 5, "points": 1},
    {"id": "wins_25", "name": "Crown Collector", "description": "Win 25 games.", "stat": "games_won", "target": 25, "points": 2},
    {"id": "wins_100", "name": "Table Tyrant", "description": "Win 100 games.", "stat": "games_won", "target": 100, "points": 3},
    {"id": "damage_750", "name": "Chip Damage Adds Up", "description": "Deal 750 total damage.", "stat": "damage_dealt", "target": 750, "points": 1},
    {"id": "damage_3000", "name": "Arena Breaker", "description": "Deal 3000 total damage.", "stat": "damage_dealt", "target": 3000, "points": 2},
    {"id": "damage_10000", "name": "Boss Health Bar", "description": "Deal 10000 total damage.", "stat": "damage_dealt", "target": 10000, "points": 3},
    {"id": "discards_50", "name": "Mulligan Enjoyer", "description": "Discard 50 cards.", "stat": "cards_discarded", "target": 50, "points": 1},
    {"id": "discards_250", "name": "Deck Dentist", "description": "Discard 250 cards.", "stat": "cards_discarded", "target": 250, "points": 2},
    {"id": "full_hand_kind_1", "name": "Rigged Looking Opening", "description": "Draw a full hand of one rank.", "stat": "full_hand_of_a_kind_draws", "target": 1, "points": 2},
    {"id": "full_hand_kind_5", "name": "Eight Of A Kind, Sure", "description": "Draw 5 full hands of one rank.", "stat": "full_hand_of_a_kind_draws", "target": 5, "points": 3},
    {"id": "earth_flush_10", "name": "Stone Garden", "description": "Play 10 Earth flushes.", "stat": "earth_flushes", "target": 10, "points": 1},
    {"id": "fire_flush_10", "name": "Volcanic Taste", "description": "Play 10 Fire flushes.", "stat": "fire_flushes", "target": 10, "points": 1},
    {"id": "water_flush_10", "name": "Tidecaller", "description": "Play 10 Water flushes.", "stat": "water_flushes", "target": 10, "points": 1},
    {"id": "air_flush_10", "name": "Storm Table", "description": "Play 10 Air flushes.", "stat": "air_flushes", "target": 10, "points": 1},
    {"id": "straight_flush_3", "name": "Impossible Lines", "description": "Play 3 straight flushes.", "stat": "straight_flushes_played", "target": 3, "points": 2},
    {"id": "royal_flush_1", "name": "Crowned By Chaos", "description": "Play a royal flush.", "stat": "royal_flushes_played", "target": 1, "points": 3},
    {"id": "upgrades_25", "name": "Greedy Between Rounds", "description": "Buy 25 upgrades.", "stat": "upgrades_bought", "target": 25, "points": 1},
]


TALENT_DEFINITIONS = [
    {
        "id": "offense_root",
        "specialization": "offense",
        "name": "Open Wound",
        "description": "+2% overall damage per rank.",
        "cost": 1,
        "max_ranks": 3,
        "requires": [],
        "row": 0,
        "column": 1,
        "bonuses": {"damage_pct": 2},
    },
    {
        "id": "offense_firebrand",
        "specialization": "offense",
        "name": "Firebrand",
        "description": "+3% Fire damage and +6% Fire draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["offense_root"],
        "row": 1,
        "column": 0,
        "bonuses": {"fire_damage_pct": 3, "fire_draw_pct": 6},
    },
    {
        "id": "offense_stonefist",
        "specialization": "offense",
        "name": "Stonefist",
        "description": "+3% Earth damage and +6% Earth draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["offense_root"],
        "row": 1,
        "column": 2,
        "bonuses": {"earth_damage_pct": 3, "earth_draw_pct": 6},
    },
    {
        "id": "offense_royal_favor",
        "specialization": "offense",
        "name": "Royal Favor",
        "description": "+7% queen, king, and ace draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["offense_root"],
        "row": 1,
        "column": 3,
        "bonuses": {"royal_draw_pct": 7},
    },
    {
        "id": "offense_killing_rhythm",
        "specialization": "offense",
        "name": "Killing Rhythm",
        "description": "+4% high card damage and +6% high card draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["offense_firebrand"],
        "row": 2,
        "column": 0,
        "bonuses": {"high_card_damage_pct": 4, "high_card_draw_pct": 6},
    },
    {
        "id": "offense_savage_pairs",
        "specialization": "offense",
        "name": "Savage Pairs",
        "description": "+5% pair and two-pair damage per rank.",
        "cost": 1,
        "max_ranks": 3,
        "requires": ["offense_root"],
        "row": 2,
        "column": 1,
        "bonuses": {"pair_damage_pct": 5},
    },
    {
        "id": "offense_primal_weight",
        "specialization": "offense",
        "name": "Primal Weight",
        "description": "+4% low card damage and +6% low card draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["offense_stonefist"],
        "row": 2,
        "column": 2,
        "bonuses": {"low_card_damage_pct": 4, "low_card_draw_pct": 6},
    },
    {
        "id": "offense_heavens_ladder",
        "specialization": "offense",
        "name": "Heaven's Ladder",
        "description": "+8% straight damage per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["offense_royal_favor"],
        "row": 2,
        "column": 3,
        "bonuses": {"straight_damage_pct": 8},
    },
    {
        "id": "offense_storm_flush",
        "specialization": "offense",
        "name": "Storm Flush",
        "description": "+8% flush and straight-flush damage per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["offense_savage_pairs"],
        "row": 3,
        "column": 1,
        "bonuses": {"flush_damage_pct": 8},
    },
    {
        "id": "offense_all_in",
        "specialization": "offense",
        "name": "All In",
        "description": "+12% overall damage, but you take 10% more damage.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["offense_killing_rhythm", "offense_primal_weight"],
        "row": 3,
        "column": 2,
        "bonuses": {"damage_pct": 12, "damage_taken_pct": 10},
    },
    {
        "id": "offense_capstone",
        "specialization": "offense",
        "name": "Prismatic Gambit",
        "description": "+15% overall damage, +20% royal draw chance, and +20% straight/flush damage.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["offense_storm_flush", "offense_all_in", "offense_heavens_ladder"],
        "row": 4,
        "column": 2,
        "bonuses": {
            "damage_pct": 15,
            "royal_draw_pct": 20,
            "straight_damage_pct": 20,
            "flush_damage_pct": 20,
        },
    },
    {
        "id": "defense_root",
        "specialization": "defense",
        "name": "Thick Skin",
        "description": "+4% max health per rank.",
        "cost": 1,
        "max_ranks": 3,
        "requires": [],
        "row": 0,
        "column": 1,
        "bonuses": {"health_pct": 4},
    },
    {
        "id": "defense_brace",
        "specialization": "defense",
        "name": "Brace",
        "description": "-2% incoming damage and +5% Water draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["defense_root"],
        "row": 1,
        "column": 0,
        "bonuses": {"damage_taken_pct": -2, "water_draw_pct": 5},
    },
    {
        "id": "defense_stone_lungs",
        "specialization": "defense",
        "name": "Stone Lungs",
        "description": "+20 max health per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["defense_root"],
        "row": 1,
        "column": 1,
        "bonuses": {"health_flat": 20},
    },
    {
        "id": "defense_long_breath",
        "specialization": "defense",
        "name": "Long Breath",
        "description": "+1 discard each rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["defense_root"],
        "row": 1,
        "column": 2,
        "bonuses": {"max_discards_flat": 1},
    },
    {
        "id": "defense_bottom_deck_blessing",
        "specialization": "defense",
        "name": "Bottom-Deck Blessing",
        "description": "+8% low card draw chance and +4% low card damage per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["defense_root"],
        "row": 1,
        "column": 3,
        "bonuses": {"low_card_draw_pct": 8, "low_card_damage_pct": 4},
    },
    {
        "id": "defense_iron_wall",
        "specialization": "defense",
        "name": "Iron Wall",
        "description": "-3% incoming damage per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["defense_brace"],
        "row": 2,
        "column": 0,
        "bonuses": {"damage_taken_pct": -3},
    },
    {
        "id": "defense_warden",
        "specialization": "defense",
        "name": "Warden's Posture",
        "description": "+6% max health and +5% Earth draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["defense_stone_lungs"],
        "row": 2,
        "column": 1,
        "bonuses": {"health_pct": 6, "earth_draw_pct": 5},
    },
    {
        "id": "defense_counterweight",
        "specialization": "defense",
        "name": "Counterweight",
        "description": "+8% full house and three-of-a-kind damage per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["defense_long_breath"],
        "row": 2,
        "column": 2,
        "bonuses": {"full_house_damage_pct": 8},
    },
    {
        "id": "defense_overdraw",
        "specialization": "defense",
        "name": "Overdraw",
        "description": "+1 hand size.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["defense_bottom_deck_blessing"],
        "row": 2,
        "column": 3,
        "bonuses": {"hand_size_flat": 1},
    },
    {
        "id": "defense_last_stand",
        "specialization": "defense",
        "name": "Last Stand",
        "description": "+10% max health and +12% 2/3 draw chance.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["defense_iron_wall", "defense_warden"],
        "row": 3,
        "column": 1,
        "bonuses": {"health_pct": 10, "tiny_draw_pct": 12},
    },
    {
        "id": "defense_capstone",
        "specialization": "defense",
        "name": "Unbreakable",
        "description": "+12% max health, -5% incoming damage, and +1 hand size.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["defense_counterweight", "defense_overdraw", "defense_last_stand"],
        "row": 4,
        "column": 2,
        "bonuses": {"health_pct": 12, "damage_taken_pct": -5, "hand_size_flat": 1},
    },
    {
        "id": "utility_root",
        "specialization": "utility",
        "name": "Quick Fingers",
        "description": "+1 discard per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": [],
        "row": 0,
        "column": 1,
        "bonuses": {"max_discards_flat": 1},
    },
    {
        "id": "utility_tempest",
        "specialization": "utility",
        "name": "Tempest Instinct",
        "description": "+3% Air damage and +8% Air draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["utility_root"],
        "row": 1,
        "column": 0,
        "bonuses": {"air_damage_pct": 3, "air_draw_pct": 8},
    },
    {
        "id": "utility_tide_memory",
        "specialization": "utility",
        "name": "Tide Memory",
        "description": "+3% Water damage and +8% Water draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["utility_root"],
        "row": 1,
        "column": 1,
        "bonuses": {"water_damage_pct": 3, "water_draw_pct": 8},
    },
    {
        "id": "utility_lucky_pockets",
        "specialization": "utility",
        "name": "Lucky Pockets",
        "description": "+1 extra gold per hand played per rank.",
        "cost": 1,
        "max_ranks": 3,
        "requires": ["utility_root"],
        "row": 1,
        "column": 2,
        "bonuses": {"gold_gain_flat": 1},
    },
    {
        "id": "utility_arcane_filter",
        "specialization": "utility",
        "name": "Arcane Filter",
        "description": "+4% to all elemental draw chances per rank.",
        "cost": 1,
        "max_ranks": 3,
        "requires": ["utility_root"],
        "row": 1,
        "column": 3,
        "bonuses": {
            "earth_draw_pct": 4,
            "fire_draw_pct": 4,
            "water_draw_pct": 4,
            "air_draw_pct": 4,
        },
    },
    {
        "id": "utility_smooth_draw",
        "specialization": "utility",
        "name": "Smooth Draw",
        "description": "+4% low card damage and +8% low card draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["utility_tempest"],
        "row": 2,
        "column": 0,
        "bonuses": {"low_card_damage_pct": 4, "low_card_draw_pct": 8},
    },
    {
        "id": "utility_clever_finish",
        "specialization": "utility",
        "name": "Clever Finish",
        "description": "+4% high card damage and +8% high card draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["utility_tide_memory"],
        "row": 2,
        "column": 1,
        "bonuses": {"high_card_damage_pct": 4, "high_card_draw_pct": 8},
    },
    {
        "id": "utility_stacked_hand",
        "specialization": "utility",
        "name": "Stacked Hand",
        "description": "+1 hand size.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["utility_lucky_pockets"],
        "row": 2,
        "column": 2,
        "bonuses": {"hand_size_flat": 1},
    },
    {
        "id": "utility_crown_hustle",
        "specialization": "utility",
        "name": "Crown Hustle",
        "description": "+7% queen, king, and ace draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["utility_arcane_filter"],
        "row": 2,
        "column": 3,
        "bonuses": {"royal_draw_pct": 7},
    },
    {
        "id": "utility_loaded_dice",
        "specialization": "utility",
        "name": "Loaded Dice",
        "description": "+10% 2/3 draw chance and +1 extra gold per hand played.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["utility_smooth_draw", "utility_clever_finish"],
        "row": 3,
        "column": 1,
        "bonuses": {"tiny_draw_pct": 10, "gold_gain_flat": 1},
    },
    {
        "id": "utility_capstone",
        "specialization": "utility",
        "name": "Fate Dealer",
        "description": "+1 discard, +1 hand size, +2 gold per hand played, and +12% royal draw chance.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["utility_loaded_dice", "utility_stacked_hand", "utility_crown_hustle"],
        "row": 4,
        "column": 2,
        "bonuses": {
            "max_discards_flat": 1,
            "hand_size_flat": 1,
            "gold_gain_flat": 2,
            "royal_draw_pct": 12,
        },
    },
]


DEFAULT_STATS = {
    "hands_played": 0,
    "games_won": 0,
    "damage_dealt": 0,
    "cards_discarded": 0,
    "full_hand_of_a_kind_draws": 0,
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


def decode_talent_state(raw_talents: list | dict | None) -> tuple[dict[str, int], str | None]:
    if isinstance(raw_talents, dict):
        specialization = raw_talents.get("specialization")
        if isinstance(raw_talents.get("ranks"), dict):
            ranks = raw_talents.get("ranks", {})
            return {talent_id: int(rank) for talent_id, rank in ranks.items() if int(rank) > 0}, specialization

        unlocked = raw_talents.get("unlocked", [])
        return {talent_id: 1 for talent_id in list(unlocked or [])}, specialization

    if isinstance(raw_talents, list):
        return {talent_id: 1 for talent_id in raw_talents}, None

    return {}, None


def encode_talent_state(talent_ranks: dict[str, int], specialization: str | None) -> dict:
    return {
        "ranks": {talent_id: rank for talent_id, rank in sorted(talent_ranks.items()) if rank > 0},
        "specialization": specialization,
    }


def get_talent_definition(talent_id: str) -> dict | None:
    return next((talent for talent in TALENT_DEFINITIONS if talent["id"] == talent_id), None)


def total_achievement_points(unlocked_achievements: list[str] | None) -> int:
    unlocked_ids = set(unlocked_achievements or [])
    return sum(
        definition["points"]
        for definition in ACHIEVEMENT_DEFINITIONS
        if definition["id"] in unlocked_ids
    )


def spent_talent_points(talent_ranks: dict[str, int] | None) -> int:
    return sum(int(rank) for rank in (talent_ranks or {}).values())


def available_talent_points(
    unlocked_achievements: list[str] | None,
    talent_ranks: dict[str, int] | None,
) -> int:
    return max(0, total_achievement_points(unlocked_achievements) - spent_talent_points(talent_ranks))


def can_unlock_talent(
    talent_id: str,
    unlocked_achievements: list[str] | None,
    talent_ranks: dict[str, int] | None,
    selected_specialization: str | None,
) -> tuple[bool, str | None]:
    talent = get_talent_definition(talent_id)
    if not talent:
        return False, "Talent not found"

    current_ranks = talent_ranks or {}
    current_rank = int(current_ranks.get(talent_id, 0))
    if current_rank >= int(talent.get("max_ranks", 1)):
        return False, "Talent is already maxed"

    if selected_specialization and talent["specialization"] != selected_specialization:
        return False, "Specialization already chosen"

    missing_requirements = [
        required
        for required in talent["requires"]
        if int(current_ranks.get(required, 0)) <= 0
    ]
    if missing_requirements:
        return False, "Prerequisites not met"

    if available_talent_points(unlocked_achievements, current_ranks) < int(talent["cost"]):
        return False, "Not enough talent points"

    return True, None


def compute_talent_bonuses(talent_ranks: dict[str, int] | None) -> dict[str, int]:
    totals = {
        "damage_pct": 0,
        "health_pct": 0,
        "health_flat": 0,
        "earth_damage_pct": 0,
        "fire_damage_pct": 0,
        "water_damage_pct": 0,
        "air_damage_pct": 0,
        "earth_draw_pct": 0,
        "fire_draw_pct": 0,
        "water_draw_pct": 0,
        "air_draw_pct": 0,
        "low_card_damage_pct": 0,
        "high_card_damage_pct": 0,
        "low_card_draw_pct": 0,
        "high_card_draw_pct": 0,
        "royal_draw_pct": 0,
        "tiny_draw_pct": 0,
        "pair_damage_pct": 0,
        "straight_damage_pct": 0,
        "flush_damage_pct": 0,
        "full_house_damage_pct": 0,
        "max_discards_flat": 0,
        "damage_taken_pct": 0,
        "hand_size_flat": 0,
        "gold_gain_flat": 0,
    }
    owned = talent_ranks or {}
    for talent in TALENT_DEFINITIONS:
        rank = int(owned.get(talent["id"], 0))
        if rank <= 0:
            continue
        for bonus_key, bonus_value in talent["bonuses"].items():
            totals[bonus_key] = totals.get(bonus_key, 0) + (bonus_value * rank)
    return totals


def build_meta_snapshot(
    stats: dict,
    unlocked_achievements: list[str] | None,
    talent_ranks: dict[str, int] | None,
    selected_specialization: str | None,
) -> dict:
    normalized_stats = normalize_stats(stats)
    achievement_ids = set(unlocked_achievements or [])
    talent_ranks = talent_ranks or {}
    current_points = available_talent_points(list(achievement_ids), talent_ranks)

    achievements = []
    for definition in ACHIEVEMENT_DEFINITIONS:
        progress = normalized_stats.get(definition["stat"], 0)
        achievements.append({
            "id": definition["id"],
            "name": definition["name"],
            "description": definition["description"],
            "progress": min(progress, definition["target"]),
            "target": definition["target"],
            "points": definition["points"],
            "unlocked": definition["id"] in achievement_ids,
        })

    talents = []
    for definition in TALENT_DEFINITIONS:
        current_rank = int(talent_ranks.get(definition["id"], 0))
        can_unlock, _ = can_unlock_talent(
            definition["id"],
            list(achievement_ids),
            talent_ranks,
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
            "max_ranks": definition["max_ranks"],
            "current_rank": current_rank,
            "unlocked": current_rank > 0,
            "available": can_unlock,
        })

    return {
        "achievement_points": total_achievement_points(list(achievement_ids)),
        "available_talent_points": current_points,
        "stats": normalized_stats,
        "achievement_count": len(achievement_ids),
        "achievements": achievements,
        "talents": talents,
        "specializations": SPECIALIZATIONS,
        "selected_specialization": selected_specialization,
        "talent_bonuses": compute_talent_bonuses(talent_ranks),
    }
