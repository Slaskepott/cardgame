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
ELEMENT_OPTIONS = ["Fire", "Air", "Earth", "Water"]

LEVEL_MILESTONE_DEFINITIONS = [
    {
        "id": "iron_training",
        "level": 2,
        "name": "Iron Training",
        "description": "+6 max health and +8 armor.",
    },
    {
        "id": "starlit_edges",
        "level": 3,
        "name": "Starlit Edges",
        "description": "Your cards gain a cleaner metallic edge treatment.",
    },
    {
        "id": "spell_second_breath",
        "level": 4,
        "name": "Second Breath",
        "description": "Unlocks the spell Second Breath: heal 10 health immediately once per match.",
    },
    {
        "id": "joker",
        "level": 5,
        "name": "The Joker",
        "description": "Adds a wild Joker to your round pool. It can stand in for any card you have unlocked.",
    },
    {
        "id": "duelist_lacquer",
        "level": 6,
        "name": "Duelist Lacquer",
        "description": "Your hand picks up a richer polished finish.",
    },
    {
        "id": "spell_heavy_blow",
        "level": 7,
        "name": "Heavy Blow",
        "description": "Unlocks the spell Heavy Blow: your next 1-card hand this turn deals 8x damage.",
    },
    {
        "id": "killer_instinct",
        "level": 8,
        "name": "Killer Instinct",
        "description": "+2% overall damage.",
    },
    {
        "id": "spell_perfect_pairing",
        "level": 9,
        "name": "Perfect Pairing",
        "description": "Unlocks the spell Perfect Pairing: your next hand this turn counts as at least two pair.",
    },
    {
        "id": "flame",
        "level": 10,
        "name": "The Flame",
        "description": "Adds The Flame to your round pool. It counts as any Fire card.",
    },
    {
        "id": "spell_stone_delay",
        "level": 11,
        "name": "Stone Delay",
        "description": "Unlocks the spell Stone Delay: reduce the next incoming hit by 25% once per match.",
    },
    {
        "id": "constellation_foil",
        "level": 12,
        "name": "Constellation Foil",
        "description": "Your cards pick up a subtle celestial foil shimmer.",
    },
    {
        "id": "battle_hardened",
        "level": 13,
        "name": "Battle Hardened",
        "description": "+10 max health and +12 armor.",
    },
    {
        "id": "prismatic_knack",
        "level": 14,
        "name": "Prismatic Knack",
        "description": "+3% overall damage.",
    },
    {
        "id": "fifteen",
        "level": 15,
        "name": "15",
        "description": "Adds rank-15 cards in each classic element. They simply hit harder than aces.",
    },
    {
        "id": "plasma",
        "level": 16,
        "name": "Plasma",
        "description": "Unlocks the Plasma element and adds a full Plasma suit to your round pool.",
    },
    {
        "id": "plasma_attunement",
        "level": 17,
        "name": "Plasma Attunement",
        "description": "+18% Plasma draw chance.",
    },
    {
        "id": "arc_furnace",
        "level": 18,
        "name": "Arc Furnace",
        "description": "+18% Plasma damage.",
    },
    {
        "id": "afterimage_coil",
        "level": 19,
        "name": "Afterimage Coil",
        "description": "Adds 2 bonus 15 of Plasma cards to your personal round pool.",
    },
    {
        "id": "singularity_engine",
        "level": 20,
        "name": "Singularity Engine",
        "description": "+2 base value on every Plasma card.",
    },
]


ACHIEVEMENT_DEFINITIONS = [
    {"id": "tutorial_complete_1", "name": "Table Ready", "description": "Complete the tutorial.", "stat": "tutorial_completions", "target": 1, "points": 1},
    {"id": "hands_25", "name": "Warm-Up Duelist", "description": "Play 25 hands.", "stat": "hands_played", "target": 25, "points": 1},
    {"id": "hands_100", "name": "Table Veteran", "description": "Play 100 hands.", "stat": "hands_played", "target": 100, "points": 2},
    {"id": "hands_300", "name": "Sleeves Rolled Up", "description": "Play 300 hands.", "stat": "hands_played", "target": 300, "points": 3},
    {"id": "hands_600", "name": "Card Table Resident", "description": "Play 600 hands.", "stat": "hands_played", "target": 600, "points": 3},
    {"id": "hands_1000", "name": "Shuffled Into History", "description": "Play 1000 hands.", "stat": "hands_played", "target": 1000, "points": 3},
    {"id": "wins_5", "name": "First Bloodline", "description": "Win 5 games.", "stat": "games_won", "target": 5, "points": 1},
    {"id": "wins_25", "name": "Crown Collector", "description": "Win 25 games.", "stat": "games_won", "target": 25, "points": 2},
    {"id": "wins_100", "name": "Table Tyrant", "description": "Win 100 games.", "stat": "games_won", "target": 100, "points": 3},
    {"id": "wins_250", "name": "Match Devourer", "description": "Win 250 games.", "stat": "games_won", "target": 250, "points": 3},
    {"id": "wins_healthy_75", "name": "Cruise Control", "description": "Win a game with 75% health remaining.", "stat": "max_win_health_remaining_pct", "target": 75, "points": 1},
    {"id": "wins_healthy_90", "name": "Barely Scratched", "description": "Win a game with 90% health remaining.", "stat": "max_win_health_remaining_pct", "target": 90, "points": 2},
    {"id": "wins_healthy_100", "name": "Untouchable", "description": "Win a game with full health remaining.", "stat": "max_win_health_remaining_pct", "target": 100, "points": 3},
    {"id": "losses_10", "name": "Back To Queue", "description": "Lose 10 games.", "stat": "games_lost", "target": 10, "points": 1},
    {"id": "losses_50", "name": "Still Came Back", "description": "Lose 50 games.", "stat": "games_lost", "target": 50, "points": 2},
    {"id": "damage_750", "name": "Chip Damage Adds Up", "description": "Deal 750 total damage.", "stat": "damage_dealt", "target": 750, "points": 1},
    {"id": "damage_3000", "name": "Arena Breaker", "description": "Deal 3000 total damage.", "stat": "damage_dealt", "target": 3000, "points": 2},
    {"id": "damage_10000", "name": "Boss Health Bar", "description": "Deal 10000 total damage.", "stat": "damage_dealt", "target": 10000, "points": 3},
    {"id": "damage_25000", "name": "Life Total Eraser", "description": "Deal 25000 total damage.", "stat": "damage_dealt", "target": 25000, "points": 3},
    {"id": "discards_50", "name": "Mulligan Enjoyer", "description": "Discard 50 cards.", "stat": "cards_discarded", "target": 50, "points": 1},
    {"id": "discards_250", "name": "Deck Dentist", "description": "Discard 250 cards.", "stat": "cards_discarded", "target": 250, "points": 2},
    {"id": "discards_500", "name": "Hand Sculptor", "description": "Discard 500 cards.", "stat": "cards_discarded", "target": 500, "points": 3},
    {"id": "full_hand_kind_1", "name": "Rigged Looking Opening", "description": "Draw 5 or more cards of one rank in a hand.", "stat": "full_hand_of_a_kind_draws", "target": 1, "points": 2},
    {"id": "full_hand_kind_3", "name": "Five Of A Mood", "description": "Draw 5 or more cards of one rank in a hand 3 times.", "stat": "full_hand_of_a_kind_draws", "target": 3, "points": 3},
    {"id": "full_hand_kind_10", "name": "The Deck Apologizes", "description": "Draw 5 or more cards of one rank in a hand 10 times.", "stat": "full_hand_of_a_kind_draws", "target": 10, "points": 3},
    {"id": "shop_rerolls_1", "name": "Window Shopper", "description": "Reroll the shop 1 time.", "stat": "shop_rerolls_used", "target": 1, "points": 1},
    {"id": "shop_rerolls_5", "name": "Inventory Gremlin", "description": "Reroll the shop 5 times.", "stat": "shop_rerolls_used", "target": 5, "points": 2},
    {"id": "shop_rerolls_10", "name": "Mall Wizard", "description": "Reroll the shop 10 times.", "stat": "shop_rerolls_used", "target": 10, "points": 3},
    {"id": "armor_peak_20", "name": "Tinplate", "description": "Reach 20 armor in a game.", "stat": "max_armor_in_game", "target": 20, "points": 1},
    {"id": "armor_peak_40", "name": "Siege Shell", "description": "Reach 40 armor in a game.", "stat": "max_armor_in_game", "target": 40, "points": 2},
    {"id": "armor_peak_70", "name": "Walking Fortress", "description": "Reach 70 armor in a game.", "stat": "max_armor_in_game", "target": 70, "points": 3},
    {"id": "health_peak_140", "name": "Second Breakfast", "description": "Reach 140 health in a game.", "stat": "max_health_in_game", "target": 140, "points": 1},
    {"id": "health_peak_200", "name": "Boss Phase", "description": "Reach 200 health in a game.", "stat": "max_health_in_game", "target": 200, "points": 2},
    {"id": "health_peak_280", "name": "Raid Encounter", "description": "Reach 280 health in a game.", "stat": "max_health_in_game", "target": 280, "points": 3},
    {"id": "single_hand_damage_80", "name": "That Connected", "description": "Deal 80 damage in a single hand.", "stat": "max_single_hand_damage", "target": 80, "points": 1},
    {"id": "single_hand_damage_140", "name": "Table Flip Damage", "description": "Deal 140 damage in a single hand.", "stat": "max_single_hand_damage", "target": 140, "points": 2},
    {"id": "single_hand_damage_220", "name": "Delete Health Bar", "description": "Deal 220 damage in a single hand.", "stat": "max_single_hand_damage", "target": 220, "points": 3},
    {"id": "earth_flush_10", "name": "Stone Garden", "description": "Play 10 Earth flushes.", "stat": "earth_flushes", "target": 10, "points": 1},
    {"id": "fire_flush_10", "name": "Volcanic Taste", "description": "Play 10 Fire flushes.", "stat": "fire_flushes", "target": 10, "points": 1},
    {"id": "water_flush_10", "name": "Tidecaller", "description": "Play 10 Water flushes.", "stat": "water_flushes", "target": 10, "points": 1},
    {"id": "air_flush_10", "name": "Storm Table", "description": "Play 10 Air flushes.", "stat": "air_flushes", "target": 10, "points": 1},
    {"id": "earth_flush_25", "name": "Mountain Casino", "description": "Play 25 Earth flushes.", "stat": "earth_flushes", "target": 25, "points": 2},
    {"id": "fire_flush_25", "name": "Pyromaniac Etiquette", "description": "Play 25 Fire flushes.", "stat": "fire_flushes", "target": 25, "points": 2},
    {"id": "water_flush_25", "name": "Undertow Discipline", "description": "Play 25 Water flushes.", "stat": "water_flushes", "target": 25, "points": 2},
    {"id": "air_flush_25", "name": "Weather Report", "description": "Play 25 Air flushes.", "stat": "air_flushes", "target": 25, "points": 2},
    {"id": "straight_flush_3", "name": "Impossible Lines", "description": "Play 3 straight flushes.", "stat": "straight_flushes_played", "target": 3, "points": 2},
    {"id": "straight_flush_10", "name": "Geometry Of Violence", "description": "Play 10 straight flushes.", "stat": "straight_flushes_played", "target": 10, "points": 3},
    {"id": "royal_flush_1", "name": "Crowned By Chaos", "description": "Play a royal flush.", "stat": "royal_flushes_played", "target": 1, "points": 3},
    {"id": "royal_flush_3", "name": "Blue-Blooded Menace", "description": "Play 3 royal flushes.", "stat": "royal_flushes_played", "target": 3, "points": 3},
    {"id": "upgrades_25", "name": "Greedy Between Rounds", "description": "Buy 25 upgrades.", "stat": "upgrades_bought", "target": 25, "points": 1},
    {"id": "upgrades_75", "name": "Shopkeeper's Favorite", "description": "Buy 75 upgrades.", "stat": "upgrades_bought", "target": 75, "points": 2},
    {"id": "upgrades_200", "name": "Built Different", "description": "Buy 200 upgrades.", "stat": "upgrades_bought", "target": 200, "points": 3},
    {"id": "elo_1600", "name": "Ranked Spark", "description": "Reach 1600 Elo.", "stat": "elo_rating", "target": 1600, "points": 1},
    {"id": "elo_1800", "name": "Ladder Predator", "description": "Reach 1800 Elo.", "stat": "elo_rating", "target": 1800, "points": 2},
    {"id": "elo_2000", "name": "Table Myth", "description": "Reach 2000 Elo.", "stat": "elo_rating", "target": 2000, "points": 3},
    {"id": "campaign_nodes_1", "name": "First Step Into The House", "description": "Clear 1 campaign node.", "stat": "campaign_nodes_cleared", "target": 1, "points": 1},
    {"id": "campaign_nodes_4", "name": "Region Breaker", "description": "Clear 5 campaign nodes.", "stat": "campaign_nodes_cleared", "target": 5, "points": 2},
    {"id": "campaign_nodes_8", "name": "Path Reader", "description": "Clear 9 campaign nodes.", "stat": "campaign_nodes_cleared", "target": 9, "points": 2},
    {"id": "campaign_nodes_12", "name": "House Cleared", "description": "Clear all 12 campaign nodes.", "stat": "campaign_nodes_cleared", "target": 12, "points": 3},
    {"id": "campaign_bosses_1", "name": "Boss Breaker", "description": "Defeat 1 campaign boss.", "stat": "campaign_bosses_defeated", "target": 1, "points": 1},
    {"id": "campaign_bosses_2", "name": "Boss Hunter", "description": "Defeat 2 campaign bosses.", "stat": "campaign_bosses_defeated", "target": 2, "points": 2},
    {"id": "campaign_bosses_3", "name": "Boss Exterminator", "description": "Defeat all 3 campaign bosses.", "stat": "campaign_bosses_defeated", "target": 3, "points": 3},
    {"id": "campaign_completion_1", "name": "Beat The House Edge", "description": "Complete the campaign.", "stat": "campaign_completions", "target": 1, "points": 3},
]


EXPERIENCE_REWARDS = {
    "hands_played": 12,
    "games_won": 80,
    "games_lost": 35,
}

ACHIEVEMENT_XP_BY_POINTS = {
    1: 60,
    2: 130,
    3: 240,
}


TALENT_DEFINITIONS = [
    {
        "id": "offense_root",
        "specialization": "offense",
        "name": "Open Wound",
        "description": "+3% overall damage per rank.",
        "cost": 1,
        "max_ranks": 3,
        "requires": [],
        "row": 0,
        "column": 2,
        "bonuses": {"damage_pct": 3},
    },
    {
        "id": "offense_shop_scout",
        "specialization": "offense",
        "name": "Shop Scout",
        "description": "+1 shop reroll.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["offense_root"],
        "row": 1,
        "column": 0,
        "bonuses": {"shop_rerolls_flat": 1},
    },
    {
        "id": "offense_prism_cut",
        "specialization": "offense",
        "name": "Prism Cut",
        "description": "Choose an element. +5% elemental damage and +9% elemental draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["offense_root"],
        "row": 1,
        "column": 2,
        "elemental_choice": {"damage_pct": 5, "draw_pct": 9},
    },
    {
        "id": "offense_royal_favor",
        "specialization": "offense",
        "name": "Royal Favor",
        "description": "+10% queen, king, and ace draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["offense_savage_pairs"],
        "row": 3,
        "column": 1,
        "bonuses": {"royal_draw_pct": 10},
    },
    {
        "id": "offense_killing_rhythm",
        "specialization": "offense",
        "name": "Killing Rhythm",
        "description": "+6% high card damage and +9% high card draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["offense_prism_cut"],
        "row": 2,
        "column": 0,
        "bonuses": {"high_card_damage_pct": 6, "high_card_draw_pct": 9},
    },
    {
        "id": "offense_savage_pairs",
        "specialization": "offense",
        "name": "Savage Pairs",
        "description": "+8% pair and two-pair damage per rank.",
        "cost": 1,
        "max_ranks": 3,
        "requires": ["offense_prism_cut"],
        "row": 2,
        "column": 1,
        "bonuses": {"pair_damage_pct": 8},
    },
    {
        "id": "offense_primal_weight",
        "specialization": "offense",
        "name": "Primal Weight",
        "description": "+6% low card damage and +9% low card draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["offense_prism_cut"],
        "row": 2,
        "column": 3,
        "bonuses": {"low_card_damage_pct": 6, "low_card_draw_pct": 9},
    },
    {
        "id": "offense_heavens_ladder",
        "specialization": "offense",
        "name": "Heaven's Ladder",
        "description": "+12% straight damage per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["offense_prism_cut"],
        "row": 2,
        "column": 4,
        "bonuses": {"straight_damage_pct": 12},
    },
    {
        "id": "offense_storm_flush",
        "specialization": "offense",
        "name": "Storm Flush",
        "description": "+12% flush and straight-flush damage per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["offense_heavens_ladder"],
        "row": 3,
        "column": 4,
        "bonuses": {"flush_damage_pct": 12},
    },
    {
        "id": "offense_encore",
        "specialization": "offense",
        "name": "Encore",
        "description": "+5% chance to play a hand twice per rank. Unlocks the Overcharge spell.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["offense_primal_weight"],
        "row": 3,
        "column": 3,
        "bonuses": {"play_twice_chance_pct": 5},
    },
    {
        "id": "offense_all_in",
        "specialization": "offense",
        "name": "All In",
        "description": "+18% overall damage, but you take 10% more damage.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["offense_killing_rhythm", "offense_primal_weight"],
        "row": 3,
        "column": 2,
        "bonuses": {"damage_pct": 18, "damage_taken_pct": 10},
    },
    {
        "id": "offense_capstone",
        "specialization": "offense",
        "name": "Prismatic Gambit",
        "description": "+22% overall damage, +30% royal draw chance, and +30% straight/flush damage.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["offense_royal_favor", "offense_storm_flush", "offense_all_in"],
        "row": 4,
        "column": 2,
        "bonuses": {
            "damage_pct": 22,
            "royal_draw_pct": 30,
            "straight_damage_pct": 30,
            "flush_damage_pct": 30,
        },
    },
    {
        "id": "offense_endless_pressure",
        "specialization": "offense",
        "name": "Endless Pressure",
        "description": "+1% overall damage per rank.",
        "cost": 1,
        "max_ranks": 999,
        "requires": ["offense_capstone"],
        "row": 5,
        "column": 2,
        "bonuses": {"damage_pct": 1},
    },
    {
        "id": "defense_root",
        "specialization": "defense",
        "name": "Thick Skin",
        "description": "+6% max health per rank.",
        "cost": 1,
        "max_ranks": 3,
        "requires": [],
        "row": 0,
        "column": 2,
        "bonuses": {"health_pct": 6},
    },
    {
        "id": "defense_supply_line",
        "specialization": "defense",
        "name": "Supply Line",
        "description": "+1 shop reroll.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["defense_root"],
        "row": 1,
        "column": 0,
        "bonuses": {"shop_rerolls_flat": 1},
    },
    {
        "id": "defense_bastion_lore",
        "specialization": "defense",
        "name": "Bastion Lore",
        "description": "Choose an element. +18 max health and +8% elemental draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["defense_root"],
        "row": 1,
        "column": 2,
        "bonuses": {"health_flat": 18},
        "elemental_choice": {"draw_pct": 8},
    },
    {
        "id": "defense_stone_lungs",
        "specialization": "defense",
        "name": "Stone Lungs",
        "description": "+14% low-card resistance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["defense_bastion_lore"],
        "row": 2,
        "column": 1,
        "bonuses": {"low_card_resistance_pct": 14},
    },
    {
        "id": "defense_long_breath",
        "specialization": "defense",
        "name": "Long Breath",
        "description": "+1 discard each rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["defense_bastion_lore"],
        "row": 2,
        "column": 0,
        "bonuses": {"max_discards_flat": 1},
    },
    {
        "id": "defense_bottom_deck_blessing",
        "specialization": "defense",
        "name": "Bottom-Deck Blessing",
        "description": "+12% low card draw chance and +6% low card damage per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["defense_long_breath"],
        "row": 3,
        "column": 0,
        "bonuses": {"low_card_draw_pct": 12, "low_card_damage_pct": 6},
    },
    {
        "id": "defense_iron_wall",
        "specialization": "defense",
        "name": "Iron Wall",
        "description": "+10 armor per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["defense_bastion_lore"],
        "row": 2,
        "column": 4,
        "bonuses": {"armor_flat": 10},
    },
    {
        "id": "defense_warden",
        "specialization": "defense",
        "name": "Warden's Posture",
        "description": "+8 armor and +12% straight and flush resistance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["defense_stone_lungs"],
        "row": 3,
        "column": 1,
        "bonuses": {"armor_flat": 8, "straight_resistance_pct": 12, "flush_resistance_pct": 12},
    },
    {
        "id": "defense_counterweight",
        "specialization": "defense",
        "name": "Counterweight",
        "description": "+14% high-card resistance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["defense_iron_wall"],
        "row": 3,
        "column": 4,
        "bonuses": {"high_card_resistance_pct": 14},
    },
    {
        "id": "defense_overdraw",
        "specialization": "defense",
        "name": "Overdraw",
        "description": "+1 hand size.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["defense_bastion_lore"],
        "row": 2,
        "column": 3,
        "bonuses": {"hand_size_flat": 1},
    },
    {
        "id": "defense_last_stand",
        "specialization": "defense",
        "name": "Last Stand",
        "description": "+15 armor, +18% chance to draw 2 or 3, and +14% full house/four-of-a-kind resistance. Unlocks the Blood Price spell.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["defense_warden", "defense_overdraw"],
        "row": 4,
        "column": 2,
        "bonuses": {
            "tiny_draw_pct": 18,
            "armor_flat": 15,
            "full_house_resistance_pct": 14,
            "four_kind_resistance_pct": 14,
        },
    },
    {
        "id": "defense_capstone",
        "specialization": "defense",
        "name": "Unbreakable",
        "description": "+18% max health, +30 armor, and +1 hand size.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["defense_bottom_deck_blessing", "defense_counterweight", "defense_last_stand"],
        "row": 5,
        "column": 2,
        "bonuses": {"health_pct": 18, "armor_flat": 30, "hand_size_flat": 1},
    },
    {
        "id": "defense_deep_roots",
        "specialization": "defense",
        "name": "Deep Roots",
        "description": "+1% max health per rank.",
        "cost": 1,
        "max_ranks": 999,
        "requires": ["defense_capstone"],
        "row": 6,
        "column": 2,
        "bonuses": {"health_pct": 1},
    },
    {
        "id": "utility_crown_hustle",
        "specialization": "utility",
        "name": "Crown Hustle",
        "description": "+7% queen, king, and ace draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": [],
        "row": 0,
        "column": 2,
        "bonuses": {"royal_draw_pct": 7},
    },
    {
        "id": "utility_deck_glance",
        "specialization": "utility",
        "name": "Deck Glance",
        "description": "+1 shop reroll.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["utility_crown_hustle"],
        "row": 1,
        "column": 0,
        "bonuses": {"shop_rerolls_flat": 1},
    },
    {
        "id": "utility_arcane_filter",
        "specialization": "utility",
        "name": "Arcane Filter",
        "description": "Choose an element. +3% elemental damage and +8% elemental draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["utility_crown_hustle"],
        "row": 1,
        "column": 2,
        "elemental_choice": {"damage_pct": 3, "draw_pct": 8},
    },
    {
        "id": "utility_lucky_pockets",
        "specialization": "utility",
        "name": "Lucky Pockets",
        "description": "+1 extra gold per hand played.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["utility_arcane_filter"],
        "row": 2,
        "column": 0,
        "bonuses": {"gold_gain_flat": 1},
    },
    {
        "id": "utility_smooth_draw",
        "specialization": "utility",
        "name": "Smooth Draw",
        "description": "+12% low card damage and +24% low card draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["utility_arcane_filter"],
        "row": 2,
        "column": 1,
        "bonuses": {"low_card_damage_pct": 12, "low_card_draw_pct": 24},
    },
    {
        "id": "utility_clever_finish",
        "specialization": "utility",
        "name": "Clever Finish",
        "description": "+4% high card damage and +8% high card draw chance per rank.",
        "cost": 1,
        "max_ranks": 2,
        "requires": ["utility_arcane_filter"],
        "row": 2,
        "column": 3,
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
        "row": 3,
        "column": 0,
        "bonuses": {"hand_size_flat": 1},
    },
    {
        "id": "utility_root",
        "specialization": "utility",
        "name": "Quick Fingers",
        "description": "+1 discard per rank. Unlocks the Double Stake spell.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["utility_arcane_filter"],
        "row": 2,
        "column": 4,
        "bonuses": {"max_discards_flat": 1},
    },
    {
        "id": "utility_loaded_dice",
        "specialization": "utility",
        "name": "Loaded Dice",
        "description": "+30% chance to draw 2 or 3.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["utility_smooth_draw", "utility_clever_finish"],
        "row": 3,
        "column": 2,
        "bonuses": {"tiny_draw_pct": 30},
    },
    {
        "id": "utility_wild_script",
        "specialization": "utility",
        "name": "Wild Script",
        "description": "+25% Joker draw chance per rank.",
        "cost": 1,
        "max_ranks": 4,
        "requires": ["utility_root"],
        "row": 3,
        "column": 4,
        "bonuses": {"joker_draw_pct": 25},
    },
    {
        "id": "utility_capstone",
        "specialization": "utility",
        "name": "Fate Dealer",
        "description": "+1 hand size and +22% royal draw chance.",
        "cost": 1,
        "max_ranks": 1,
        "requires": ["utility_stacked_hand", "utility_wild_script"],
        "row": 4,
        "column": 2,
        "bonuses": {
            "hand_size_flat": 1,
            "royal_draw_pct": 22,
        },
    },
    {
        "id": "utility_stack_the_deck",
        "specialization": "utility",
        "name": "Stack The Deck",
        "description": "+1% chance to draw 2 or 3 per rank.",
        "cost": 1,
        "max_ranks": 999,
        "requires": ["utility_capstone"],
        "row": 5,
        "column": 2,
        "bonuses": {"tiny_draw_pct": 1},
    },
]


DEFAULT_STATS = {
    "tutorial_completions": 0,
    "hands_played": 0,
    "games_won": 0,
    "games_lost": 0,
    "damage_dealt": 0,
    "cards_discarded": 0,
    "full_hand_of_a_kind_draws": 0,
    "shop_rerolls_used": 0,
    "max_armor_in_game": 0,
    "max_health_in_game": 0,
    "max_single_hand_damage": 0,
    "max_win_health_remaining_pct": 0,
    "earth_flushes": 0,
    "fire_flushes": 0,
    "water_flushes": 0,
    "air_flushes": 0,
    "straight_flushes_played": 0,
    "royal_flushes_played": 0,
    "upgrades_bought": 0,
    "experience_total": 0,
    "elo_rating": 1500,
    "campaign_nodes_cleared": 0,
    "campaign_bosses_defeated": 0,
    "campaign_completions": 0,
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


def experience_for_level(level: int) -> int:
    if level <= 1:
        return 0

    total = 0
    for current_level in range(1, level):
        total += 100 + ((current_level - 1) * 35)
    return total


def level_from_experience(experience_total: int) -> int:
    level = 1
    while experience_total >= experience_for_level(level + 1):
        level += 1
    return level


def level_progress(experience_total: int) -> tuple[int, int, int]:
    level = level_from_experience(experience_total)
    current_level_floor = experience_for_level(level)
    next_level_floor = experience_for_level(level + 1)
    into_level = max(0, experience_total - current_level_floor)
    needed = max(1, next_level_floor - current_level_floor)
    return level, into_level, needed


def unlocked_level_reward_ids(level: int) -> list[str]:
    return [
        milestone["id"]
        for milestone in LEVEL_MILESTONE_DEFINITIONS
        if level >= int(milestone["level"])
    ]


def build_level_milestones(level: int) -> list[dict]:
    return [
        {
            **milestone,
            "unlocked": level >= int(milestone["level"]),
        }
        for milestone in LEVEL_MILESTONE_DEFINITIONS
    ]


def compute_level_reward_bonuses(reward_ids: list[str] | None) -> dict[str, int]:
    reward_set = set(reward_ids or [])
    bonuses = {
        "damage_pct": 0,
        "health_pct": 0,
        "health_flat": 0,
        "armor_flat": 0,
        "fire_draw_pct": 0,
        "air_draw_pct": 0,
        "earth_draw_pct": 0,
        "water_draw_pct": 0,
        "plasma_draw_pct": 0,
        "plasma_damage_pct": 0,
        "plasma_bonus_value": 0,
    }

    if "iron_training" in reward_set:
        bonuses["health_flat"] += 6
        bonuses["armor_flat"] += 8
    if "killer_instinct" in reward_set:
        bonuses["damage_pct"] += 2
    if "battle_hardened" in reward_set:
        bonuses["health_flat"] += 10
        bonuses["armor_flat"] += 12
    if "prismatic_knack" in reward_set:
        bonuses["damage_pct"] += 3
    if "plasma_attunement" in reward_set:
        bonuses["plasma_draw_pct"] += 18
    if "arc_furnace" in reward_set:
        bonuses["plasma_damage_pct"] += 18
    if "singularity_engine" in reward_set:
        bonuses["plasma_bonus_value"] += 2

    return bonuses


def calculate_experience_gain(
    stat_changes: dict[str, int],
    previous_achievements: list[str] | None,
    updated_achievements: list[str] | None,
) -> int:
    experience = 0

    for stat_key, per_point in EXPERIENCE_REWARDS.items():
        experience += int(stat_changes.get(stat_key, 0)) * per_point

    previous_ids = set(previous_achievements or [])
    for definition in ACHIEVEMENT_DEFINITIONS:
        if definition["id"] in set(updated_achievements or []) and definition["id"] not in previous_ids:
            experience += ACHIEVEMENT_XP_BY_POINTS.get(int(definition["points"]), 0)

    return experience


def evaluate_achievements(stats: dict, unlocked_ids: list[str] | None) -> list[str]:
    unlocked = set(unlocked_ids or [])
    for definition in ACHIEVEMENT_DEFINITIONS:
        if stats.get(definition["stat"], 0) >= definition["target"]:
            unlocked.add(definition["id"])
    return sorted(unlocked)


def normalize_talent_element(element: str | None) -> str | None:
    if not element:
        return None
    normalized = str(element).strip().lower()
    for option in ELEMENT_OPTIONS:
        if option.lower() == normalized:
            return option
    return None


def get_talent_selected_element(definition: dict, talent_elements: dict[str, str] | None) -> str | None:
    elemental_choice = definition.get("elemental_choice")
    if not elemental_choice:
        return None

    selected = normalize_talent_element((talent_elements or {}).get(definition["id"]))
    return selected or ELEMENT_OPTIONS[0]


def expand_talent_bonuses(definition: dict, selected_element: str | None) -> dict[str, int]:
    bonuses = dict(definition.get("bonuses", {}))
    elemental_choice = definition.get("elemental_choice")
    if not elemental_choice:
        return bonuses

    resolved_element = normalize_talent_element(selected_element) or ELEMENT_OPTIONS[0]
    resolved_key = resolved_element.lower()

    if "damage_pct" in elemental_choice:
        bonuses[f"{resolved_key}_damage_pct"] = bonuses.get(f"{resolved_key}_damage_pct", 0) + int(
            elemental_choice["damage_pct"]
        )
    if "draw_pct" in elemental_choice:
        bonuses[f"{resolved_key}_draw_pct"] = bonuses.get(f"{resolved_key}_draw_pct", 0) + int(
            elemental_choice["draw_pct"]
        )
    return bonuses


def decode_talent_state(raw_talents: list | dict | None) -> tuple[dict[str, int], str | None, dict[str, str]]:
    if isinstance(raw_talents, dict):
        raw_elements = raw_talents.get("elements", {})
        talent_elements = (
            {
                talent_id: normalized
                for talent_id, element in raw_elements.items()
                if isinstance(talent_id, str)
                and (normalized := normalize_talent_element(element)) is not None
            }
            if isinstance(raw_elements, dict)
            else {}
        )
        if isinstance(raw_talents.get("ranks"), dict):
            ranks = raw_talents.get("ranks", {})
            return {
                talent_id: int(rank) for talent_id, rank in ranks.items() if int(rank) > 0
            }, None, talent_elements

        unlocked = raw_talents.get("unlocked", [])
        return {talent_id: 1 for talent_id in list(unlocked or [])}, None, talent_elements

    if isinstance(raw_talents, list):
        return {talent_id: 1 for talent_id in raw_talents}, None, {}

    return {}, None, {}


def encode_talent_state(
    talent_ranks: dict[str, int],
    specialization: str | None,
    talent_elements: dict[str, str] | None = None,
) -> dict:
    return {
        "ranks": {talent_id: rank for talent_id, rank in sorted(talent_ranks.items()) if rank > 0},
        "specialization": specialization,
        "elements": {
            talent_id: element
            for talent_id, element in sorted((talent_elements or {}).items())
            if normalize_talent_element(element)
        },
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


def compute_talent_bonuses(
    talent_ranks: dict[str, int] | None,
    talent_elements: dict[str, str] | None = None,
) -> dict[str, int]:
    totals = {
        "damage_pct": 0,
        "health_pct": 0,
        "health_flat": 0,
        "armor_flat": 0,
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
        "joker_draw_pct": 0,
        "play_twice_chance_pct": 0,
        "shop_rerolls_flat": 0,
        "pair_damage_pct": 0,
        "straight_damage_pct": 0,
        "flush_damage_pct": 0,
        "full_house_damage_pct": 0,
        "low_card_resistance_pct": 0,
        "high_card_resistance_pct": 0,
        "straight_resistance_pct": 0,
        "flush_resistance_pct": 0,
        "full_house_resistance_pct": 0,
        "four_kind_resistance_pct": 0,
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
        selected_element = get_talent_selected_element(talent, talent_elements)
        for bonus_key, bonus_value in expand_talent_bonuses(talent, selected_element).items():
            totals[bonus_key] = totals.get(bonus_key, 0) + (bonus_value * rank)
    return totals


def build_meta_snapshot(
    stats: dict,
    unlocked_achievements: list[str] | None,
    talent_ranks: dict[str, int] | None,
    selected_specialization: str | None,
    talent_elements: dict[str, str] | None = None,
) -> dict:
    normalized_stats = normalize_stats(stats)
    achievement_ids = set(unlocked_achievements or [])
    talent_ranks = talent_ranks or {}
    current_points = available_talent_points(list(achievement_ids), talent_ranks)
    experience_total = int(normalized_stats.get("experience_total", 0))
    level, experience_in_level, experience_for_next_level = level_progress(experience_total)

    achievements = []
    for definition in ACHIEVEMENT_DEFINITIONS:
        progress = normalized_stats.get(definition["stat"], 0)
        achievements.append({
            "id": definition["id"],
            "stat": definition["stat"],
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
            "element_options": ELEMENT_OPTIONS if definition.get("elemental_choice") else [],
            "selected_element": get_talent_selected_element(definition, talent_elements),
        })

    return {
        "level": level,
        "elo_rating": int(normalized_stats.get("elo_rating", 1500)),
        "experience_total": experience_total,
        "experience_in_level": experience_in_level,
        "experience_for_next_level": experience_for_next_level,
        "achievement_points": total_achievement_points(list(achievement_ids)),
        "available_talent_points": current_points,
        "stats": normalized_stats,
        "achievement_count": len(achievement_ids),
        "achievements": achievements,
        "talents": talents,
        "specializations": SPECIALIZATIONS,
        "selected_specialization": selected_specialization,
        "talent_bonuses": compute_talent_bonuses(talent_ranks, talent_elements),
        "level_milestones": build_level_milestones(level),
        "unlocked_level_rewards": unlocked_level_reward_ids(level),
    }
