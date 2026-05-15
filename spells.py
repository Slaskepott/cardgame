from __future__ import annotations


SPELL_DEFINITIONS = [
    {
        "id": "kindle",
        "name": "Kindle",
        "description": "+20% damage on your next hand this turn.",
        "effect_type": "hand",
        "animation": "kindle",
        "unlock_source": "starter",
    },
    {
        "id": "guard_pulse",
        "name": "Guard Pulse",
        "description": "Gain 12 armor immediately.",
        "effect_type": "instant",
        "animation": "guard_pulse",
        "unlock_source": "starter",
    },
    {
        "id": "second_breath",
        "name": "Second Breath",
        "description": "Heal 10 health immediately.",
        "effect_type": "instant",
        "animation": "second_breath",
        "unlock_source": "level",
        "level_reward_id": "spell_second_breath",
    },
    {
        "id": "heavy_blow",
        "name": "Heavy Blow",
        "description": "Your next hand this turn must play exactly 1 card. Its damage is multiplied by 8.",
        "effect_type": "hand",
        "animation": "heavy_blow",
        "unlock_source": "level",
        "level_reward_id": "spell_heavy_blow",
    },
    {
        "id": "perfect_pairing",
        "name": "Perfect Pairing",
        "description": "Your next hand this turn counts as at least two pair.",
        "effect_type": "hand",
        "animation": "perfect_pairing",
        "unlock_source": "level",
        "level_reward_id": "spell_perfect_pairing",
    },
    {
        "id": "stone_delay",
        "name": "Stone Delay",
        "description": "Reduce the next incoming hit against you by 25%.",
        "effect_type": "instant",
        "animation": "stone_delay",
        "unlock_source": "level",
        "level_reward_id": "spell_stone_delay",
    },
    {
        "id": "overcharge",
        "name": "Overcharge",
        "description": "+35% damage on your next hand this turn, then lose 5 health.",
        "effect_type": "hand",
        "animation": "overcharge",
        "unlock_source": "talent",
        "talent_id": "offense_encore",
    },
    {
        "id": "blood_price",
        "name": "Blood Price",
        "description": "Lose 8 health and gain +1 discard this turn.",
        "effect_type": "instant",
        "animation": "blood_price",
        "unlock_source": "talent",
        "talent_id": "defense_last_stand",
    },
    {
        "id": "double_stake",
        "name": "Double Stake",
        "description": "After your next hand this turn, gain 4 gold and lose 6 health.",
        "effect_type": "hand",
        "animation": "double_stake",
        "unlock_source": "talent",
        "talent_id": "utility_root",
    },
    {
        "id": "final_push",
        "name": "Final Push",
        "description": "If your opponent is below 30% health, your next hand this turn deals +50% damage.",
        "effect_type": "hand",
        "animation": "final_push",
        "unlock_source": "campaign",
        "campaign_node_id": "cinder_marquis",
    },
]

SPELLS_BY_ID = {spell["id"]: spell for spell in SPELL_DEFINITIONS}
STARTER_SPELL_IDS = ["kindle", "guard_pulse"]
MAX_EQUIPPED_SPELLS = 2


def get_spell_definition(spell_id: str) -> dict | None:
    return SPELLS_BY_ID.get(spell_id)


def list_spells() -> list[dict]:
    return [dict(spell) for spell in SPELL_DEFINITIONS]


def default_spell_state() -> dict:
    return {"equipped_spell_ids": list(STARTER_SPELL_IDS[:MAX_EQUIPPED_SPELLS])}


def compute_unlocked_spell_ids(
    level_reward_ids: list[str] | None,
    talent_ranks: dict[str, int] | None,
    campaign_progress: dict | None,
) -> list[str]:
    reward_set = set(level_reward_ids or [])
    talent_ranks = talent_ranks or {}
    cleared_node_ids = set((campaign_progress or {}).get("cleared_node_ids", []))

    unlocked = list(STARTER_SPELL_IDS)
    for spell in SPELL_DEFINITIONS:
        unlock_source = spell.get("unlock_source")
        if unlock_source == "level" and spell.get("level_reward_id") in reward_set:
            unlocked.append(spell["id"])
        elif unlock_source == "talent" and int(talent_ranks.get(spell.get("talent_id", ""), 0)) > 0:
            unlocked.append(spell["id"])
        elif unlock_source == "campaign" and spell.get("campaign_node_id") in cleared_node_ids:
            unlocked.append(spell["id"])

    seen: set[str] = set()
    return [spell_id for spell_id in unlocked if not (spell_id in seen or seen.add(spell_id))]


def normalize_spell_state(spell_state: dict | None, unlocked_spell_ids: list[str] | None = None) -> dict:
    normalized = default_spell_state()
    unlocked_set = set(unlocked_spell_ids or [])
    raw_equipped = []
    if isinstance(spell_state, dict):
        raw_equipped = spell_state.get("equipped_spell_ids", [])

    equipped: list[str] = []
    seen: set[str] = set()
    for spell_id in raw_equipped or []:
        if spell_id not in SPELLS_BY_ID or spell_id in seen:
            continue
        if unlocked_set and spell_id not in unlocked_set:
            continue
        equipped.append(spell_id)
        seen.add(spell_id)
        if len(equipped) >= MAX_EQUIPPED_SPELLS:
            break

    if not equipped:
        fallback_pool = unlocked_spell_ids or STARTER_SPELL_IDS
        for spell_id in fallback_pool:
            if spell_id in SPELLS_BY_ID and spell_id not in seen:
                equipped.append(spell_id)
                seen.add(spell_id)
            if len(equipped) >= MAX_EQUIPPED_SPELLS:
                break

    normalized["equipped_spell_ids"] = equipped
    return normalized


def build_spell_snapshot(
    unlocked_spell_ids: list[str],
    equipped_spell_ids: list[str],
) -> list[dict]:
    unlocked_set = set(unlocked_spell_ids)
    equipped_set = set(equipped_spell_ids)
    return [
        {
            **spell,
            "unlocked": spell["id"] in unlocked_set,
            "equipped": spell["id"] in equipped_set,
        }
        for spell in SPELL_DEFINITIONS
    ]
