from __future__ import annotations

from copy import deepcopy


CAMPAIGN_ICON_REWARDS = {
    "default": "😎",
    "region_one": "🔥",
    "region_two": "🜂",
    "campaign_clear": "👑",
}

CAMPAIGN_BORDER_REWARDS = {
    "default": "default",
    "boss_one": "bronze-flare",
    "boss_two": "azure-ring",
    "campaign_clear": "royal-gilded",
}


CAMPAIGN_NODES = [
    {
        "id": "ember_wake",
        "region": 1,
        "index": 1,
        "name": "Ember Wake",
        "type": "bo3",
        "best_of": 3,
        "wins_to_clinch": 2,
        "description": "+55% Fire draw chance, +25% Fire damage.",
        "bot_name": "Ember Wake",
        "bot_avatar": "🔥",
        "bot_difficulty": "easy",
        "mutators": {
            "bot": {
                "element_draw_bonus": {"Fire": 0.55},
                "element_damage_bonus": {"Fire": 0.25},
            }
        },
    },
    {
        "id": "second_deal",
        "region": 1,
        "index": 2,
        "name": "Second Deal",
        "type": "bo3",
        "best_of": 3,
        "wins_to_clinch": 2,
        "description": "+1 shop reroll and +1 gold gained when playing hands.",
        "bot_name": "Second Deal",
        "bot_avatar": "🪙",
        "bot_difficulty": "easy",
        "mutators": {
            "bot": {
                "shop_rerolls_flat": 1,
                "gold_gain_flat": 1,
            }
        },
    },
    {
        "id": "moss_ledger",
        "region": 1,
        "index": 3,
        "name": "Moss Ledger",
        "type": "bo5",
        "best_of": 5,
        "wins_to_clinch": 3,
        "description": "+35 health, +18 armor, +14% low-card resistance, +12% high-card resistance.",
        "bot_name": "Moss Ledger",
        "bot_avatar": "🌿",
        "bot_difficulty": "medium",
        "mutators": {
            "bot": {
                "armor_flat": 18,
                "health_flat": 35,
                "low_card_resistance_pct": 14,
                "high_card_resistance_pct": 12,
            }
        },
    },
    {
        "id": "cinder_marquis",
        "region": 1,
        "index": 4,
        "name": "The Cinder Marquis",
        "type": "boss",
        "best_of": 9,
        "wins_to_clinch": 5,
        "description": "Soft Flush enabled, +1 shop selection, guaranteed rare-or-better shop option, +70% Fire draw chance.",
        "bot_name": "The Cinder Marquis",
        "bot_avatar": "👹",
        "bot_difficulty": "medium",
        "mutators": {
            "bot": {
                "soft_flush_enabled": True,
                "shop_selection_size_bonus": 1,
                "shop_guaranteed_min_rarity": "rare",
                "element_draw_bonus": {"Fire": 0.7},
            }
        },
        "clear_rewards": {
            "icons": ["🔥"],
            "borders": ["bronze-flare"],
        },
    },
    {
        "id": "slipstream_table",
        "region": 2,
        "index": 5,
        "name": "Slipstream Table",
        "type": "bo3",
        "best_of": 3,
        "wins_to_clinch": 2,
        "description": "+55% Air draw chance, +35% high-card draw chance, +18% high-card damage.",
        "bot_name": "Slipstream Table",
        "bot_avatar": "💨",
        "bot_difficulty": "medium",
        "mutators": {
            "bot": {
                "element_draw_bonus": {"Air": 0.55},
                "high_card_draw_pct": 35,
                "high_card_damage_pct": 18,
            }
        },
    },
    {
        "id": "house_of_echoes",
        "region": 2,
        "index": 6,
        "name": "House of Echoes",
        "type": "bo3",
        "best_of": 3,
        "wins_to_clinch": 2,
        "description": "+18% chance to play a hand twice, +15% pair damage, +10% straight damage.",
        "bot_name": "House of Echoes",
        "bot_avatar": "🪞",
        "bot_difficulty": "medium",
        "mutators": {
            "bot": {
                "play_twice_chance_pct": 18,
                "pair_damage_pct": 15,
                "straight_damage_pct": 10,
            }
        },
    },
    {
        "id": "floodmarked_vault",
        "region": 2,
        "index": 7,
        "name": "Floodmarked Vault",
        "type": "bo5",
        "best_of": 5,
        "wins_to_clinch": 3,
        "description": "+60% Water draw chance, +20% Water damage, +20% flush damage.",
        "bot_name": "Floodmarked Vault",
        "bot_avatar": "💧",
        "bot_difficulty": "medium",
        "mutators": {
            "bot": {
                "element_draw_bonus": {"Water": 0.6},
                "element_damage_bonus": {"Water": 0.2},
                "flush_damage_pct": 20,
            }
        },
    },
    {
        "id": "archivist_of_gaps",
        "region": 2,
        "index": 8,
        "name": "The Archivist of Gaps",
        "type": "boss",
        "best_of": 9,
        "wins_to_clinch": 5,
        "description": "Gap Straight enabled, +1 hand size, +18% straight damage.",
        "bot_name": "The Archivist of Gaps",
        "bot_avatar": "📚",
        "bot_difficulty": "hard",
        "mutators": {
            "bot": {
                "gap_straight_enabled": True,
                "hand_size_flat": 1,
                "straight_damage_pct": 18,
            }
        },
        "clear_rewards": {
            "icons": ["🜂"],
            "borders": ["azure-ring"],
        },
    },
    {
        "id": "stonewire_hollow",
        "region": 3,
        "index": 9,
        "name": "Stonewire Hollow",
        "type": "bo3",
        "best_of": 3,
        "wins_to_clinch": 2,
        "description": "+55% Earth draw chance, +14 armor, +18% low-card resistance.",
        "bot_name": "Stonewire Hollow",
        "bot_avatar": "🪨",
        "bot_difficulty": "medium",
        "mutators": {
            "bot": {
                "element_draw_bonus": {"Earth": 0.55},
                "armor_flat": 14,
                "low_card_resistance_pct": 18,
            }
        },
    },
    {
        "id": "prism_tax",
        "region": 3,
        "index": 10,
        "name": "Prism Tax",
        "type": "bo3",
        "best_of": 3,
        "wins_to_clinch": 2,
        "description": "+25% Fire/Air/Earth/Water draw chance and +12% Fire/Air/Earth/Water damage.",
        "bot_name": "Prism Tax",
        "bot_avatar": "🔷",
        "bot_difficulty": "hard",
        "mutators": {
            "bot": {
                "element_draw_bonus": {"Fire": 0.25, "Air": 0.25, "Earth": 0.25, "Water": 0.25},
                "element_damage_bonus": {"Fire": 0.12, "Air": 0.12, "Earth": 0.12, "Water": 0.12},
            }
        },
    },
    {
        "id": "the_fifth_seat",
        "region": 3,
        "index": 11,
        "name": "The Fifth Seat",
        "type": "bo5",
        "best_of": 5,
        "wins_to_clinch": 3,
        "description": "+1 hand size, +1 shop selection, starts with Fortress Heart relic.",
        "bot_name": "The Fifth Seat",
        "bot_avatar": "🪑",
        "bot_difficulty": "hard",
        "mutators": {
            "bot": {
                "hand_size_flat": 1,
                "shop_selection_size_bonus": 1,
                "free_relic_id": "fortress_heart",
            }
        },
    },
    {
        "id": "the_house_edge",
        "region": 3,
        "index": 12,
        "name": "The House Edge",
        "type": "boss",
        "best_of": 9,
        "wins_to_clinch": 5,
        "description": "Gap Straight enabled, Soft Flush enabled, starts with Plasma Lattice relic, +2 shop selections, +1 hand size.",
        "bot_name": "The House Edge",
        "bot_avatar": "🎰",
        "bot_difficulty": "hard",
        "mutators": {
            "bot": {
                "gap_straight_enabled": True,
                "soft_flush_enabled": True,
                "free_relic_id": "plasma_lattice",
                "shop_selection_size_bonus": 2,
                "hand_size_flat": 1,
            }
        },
        "clear_rewards": {
            "icons": ["👑"],
            "borders": ["royal-gilded"],
        },
    },
]


CAMPAIGN_NODES_BY_ID = {node["id"]: node for node in CAMPAIGN_NODES}


def default_campaign_progress() -> dict:
    return {
        "current_node_id": CAMPAIGN_NODES[0]["id"],
        "cleared_node_ids": [],
        "completed": False,
    }


def default_profile_state() -> dict:
    return {
        "unlocked_icons": [CAMPAIGN_ICON_REWARDS["default"]],
        "unlocked_borders": [CAMPAIGN_BORDER_REWARDS["default"]],
        "selected_icon": CAMPAIGN_ICON_REWARDS["default"],
        "selected_border": CAMPAIGN_BORDER_REWARDS["default"],
    }


def normalize_campaign_progress(progress: dict | None) -> dict:
    normalized = default_campaign_progress()
    if not progress:
        return normalized

    current_node_id = progress.get("current_node_id")
    if current_node_id in CAMPAIGN_NODES_BY_ID:
        normalized["current_node_id"] = current_node_id

    cleared = [
        node_id
        for node_id in progress.get("cleared_node_ids", [])
        if node_id in CAMPAIGN_NODES_BY_ID
    ]
    normalized["cleared_node_ids"] = sorted(set(cleared), key=lambda node_id: CAMPAIGN_NODES_BY_ID[node_id]["index"])
    normalized["completed"] = bool(progress.get("completed"))
    return normalized


def normalize_profile_state(profile: dict | None) -> dict:
    normalized = default_profile_state()
    if not profile:
        return normalized

    unlocked_icons = [icon for icon in profile.get("unlocked_icons", []) if isinstance(icon, str) and icon]
    unlocked_borders = [border for border in profile.get("unlocked_borders", []) if isinstance(border, str) and border]
    if unlocked_icons:
        normalized["unlocked_icons"] = sorted(set([*normalized["unlocked_icons"], *unlocked_icons]))
    if unlocked_borders:
        normalized["unlocked_borders"] = sorted(set([*normalized["unlocked_borders"], *unlocked_borders]))

    selected_icon = profile.get("selected_icon")
    selected_border = profile.get("selected_border")
    if selected_icon in normalized["unlocked_icons"]:
        normalized["selected_icon"] = selected_icon
    if selected_border in normalized["unlocked_borders"]:
        normalized["selected_border"] = selected_border
    return normalized


def get_campaign_node(node_id: str) -> dict | None:
    node = CAMPAIGN_NODES_BY_ID.get(node_id)
    return deepcopy(node) if node else None


def list_campaign_nodes() -> list[dict]:
    return [deepcopy(node) for node in CAMPAIGN_NODES]


def is_campaign_node_unlocked(progress: dict, node_id: str) -> bool:
    normalized = normalize_campaign_progress(progress)
    return node_id == normalized["current_node_id"] or node_id in normalized["cleared_node_ids"]


def next_campaign_node_id(node_id: str) -> str | None:
    node = CAMPAIGN_NODES_BY_ID.get(node_id)
    if not node:
        return None
    next_index = node["index"] + 1
    for candidate in CAMPAIGN_NODES:
        if candidate["index"] == next_index:
            return candidate["id"]
    return None


def apply_campaign_clear(progress: dict | None, profile: dict | None, node_id: str) -> tuple[dict, dict, dict]:
    normalized_progress = normalize_campaign_progress(progress)
    normalized_profile = normalize_profile_state(profile)
    node = CAMPAIGN_NODES_BY_ID[node_id]

    cleared = set(normalized_progress["cleared_node_ids"])
    cleared.add(node_id)
    normalized_progress["cleared_node_ids"] = sorted(
        cleared, key=lambda candidate: CAMPAIGN_NODES_BY_ID[candidate]["index"]
    )

    next_node = next_campaign_node_id(node_id)
    if next_node:
        normalized_progress["current_node_id"] = next_node
    else:
        normalized_progress["current_node_id"] = node_id
        normalized_progress["completed"] = True

    rewards = node.get("clear_rewards", {})
    if rewards.get("icons"):
        normalized_profile["unlocked_icons"] = sorted(
            set([*normalized_profile["unlocked_icons"], *rewards["icons"]])
        )
    if rewards.get("borders"):
        normalized_profile["unlocked_borders"] = sorted(
            set([*normalized_profile["unlocked_borders"], *rewards["borders"]])
        )

    if normalized_progress["completed"]:
        normalized_profile["unlocked_icons"] = sorted(
            set([*normalized_profile["unlocked_icons"], CAMPAIGN_ICON_REWARDS["campaign_clear"]])
        )
        normalized_profile["unlocked_borders"] = sorted(
            set([*normalized_profile["unlocked_borders"], CAMPAIGN_BORDER_REWARDS["campaign_clear"]])
        )

    if normalized_profile["selected_icon"] not in normalized_profile["unlocked_icons"]:
        normalized_profile["selected_icon"] = normalized_profile["unlocked_icons"][0]
    if normalized_profile["selected_border"] not in normalized_profile["unlocked_borders"]:
        normalized_profile["selected_border"] = normalized_profile["unlocked_borders"][0]

    return normalized_progress, normalized_profile, deepcopy(node)
