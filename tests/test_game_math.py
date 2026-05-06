import asyncio

from card import Card
from game import Game
from player import Player
from upgrades import Upgrade


def make_upgrade(name: str, effect: str) -> Upgrade:
    return Upgrade(
        id=999,
        name=name,
        tier=1,
        rarity="test",
        effect=effect,
        cost=0,
    )


def test_draw_weight_combines_suit_and_rank_modifiers():
    player = Player(
        "tester",
        talent_bonuses={
            "fire_draw_pct": 20,
            "low_card_draw_pct": 30,
            "royal_draw_pct": 40,
        },
    )

    low_fire_card = Card("3", "Fire")
    royal_fire_card = Card("Q", "Fire")
    plain_water_card = Card("8", "Water")

    assert player.get_draw_weight(low_fire_card) == 1.2 * 1.3
    assert player.get_draw_weight(royal_fire_card) == 1.2 * 1.4
    assert player.get_draw_weight(plain_water_card) == 1.0


def test_draw_weight_uses_upgrade_based_high_card_bonus():
    player = Player("tester")
    player.upgrades = [make_upgrade("High Draw Specialist", "+25% High Card Draw Chance")]
    player.apply_upgrades()

    assert player.get_draw_weight(Card("K", "Earth")) == 1.25
    assert player.get_draw_weight(Card("7", "Earth")) == 1.0


def test_joker_unlock_adds_three_jokers_to_special_deck():
    player = Player("tester", level_unlocks=["joker"])

    joker_cards = [card for card in player.special_deck if card.rank == "Joker" and card.suit == "Wild"]

    assert len(joker_cards) == 3


def test_draw_weight_uses_joker_specific_talent_bonus():
    player = Player(
        "tester",
        talent_bonuses={"joker_draw_pct": 50},
        level_unlocks=["joker"],
    )

    assert player.get_draw_weight(Card("Joker", "Wild")) == 1.5
    assert player.get_draw_weight(Card("Flame", "Fire")) == 1.0


def test_armor_reduction_scales_with_diminishing_returns():
    player = Player("tester")

    assert player.get_armor_damage_reduction() == 0.0

    player.armor = 20
    light_armor = player.get_armor_damage_reduction()

    player.armor = 80
    medium_armor = player.get_armor_damage_reduction()

    player.armor = 220
    heavy_armor = player.get_armor_damage_reduction()

    assert 0 < light_armor < medium_armor < heavy_armor < 0.8


def test_apply_upgrades_returns_armor_and_damage_reduction():
    player = Player(
        "tester",
        talent_bonuses={"armor_flat": 12},
        level_reward_bonuses={"armor_flat": 8},
    )
    player.upgrades = [make_upgrade("Increase Armor", "+18 Armor")]

    payload = player.apply_upgrades()

    assert payload["armor"] == 38
    assert payload["armor_reduction_pct"] > 0
    assert payload["upgrades"][0]["name"] == "Increase Armor"


def test_calculate_damage_applies_damage_and_elemental_modifiers():
    game = Game()
    player = Player("tester")
    player.upgrades = [
        make_upgrade("Increase Damage", "+20% Damage"),
        make_upgrade("Increase Fire Damage", "+30% Fire Damage"),
    ]
    player.apply_upgrades()
    game.players[player.name] = player

    selected_cards = [
        {"rank": "10", "suit": "Fire"},
        {"rank": "J", "suit": "Fire"},
        {"rank": "Q", "suit": "Fire"},
        {"rank": "K", "suit": "Fire"},
        {"rank": "A", "suit": "Fire"},
    ]

    damage, hand_type, multiplier = game.calculate_damage(selected_cards, player.name)

    assert hand_type == "royal flush"
    assert multiplier == 10
    assert damage == 150


def test_calculate_damage_applies_low_card_and_pair_modifiers():
    game = Game()
    player = Player(
        "tester",
        talent_bonuses={
            "pair_damage_pct": 25,
            "low_card_damage_pct": 50,
        },
    )
    game.players[player.name] = player

    selected_cards = [
        {"rank": "2", "suit": "Fire"},
        {"rank": "2", "suit": "Water"},
        {"rank": "5", "suit": "Earth"},
        {"rank": "7", "suit": "Air"},
        {"rank": "9", "suit": "Fire"},
    ]

    damage, hand_type, multiplier = game.calculate_damage(selected_cards, player.name)

    assert hand_type == "pair"
    assert multiplier == 2
    assert damage == 20


def test_joker_resolves_to_best_possible_five_of_a_kind():
    game = Game()
    player = Player("tester")
    game.players[player.name] = player

    selected_cards = [
        {"rank": "A", "suit": "Fire"},
        {"rank": "A", "suit": "Water"},
        {"rank": "A", "suit": "Earth"},
        {"rank": "A", "suit": "Air"},
        {"rank": "Joker", "suit": "Wild"},
    ]

    damage, hand_type, multiplier = game.calculate_damage(selected_cards, player.name)

    assert hand_type == "five of a kind"
    assert multiplier == 8
    assert damage == 88


def test_flame_resolves_to_royal_flush_when_possible():
    game = Game()
    player = Player("tester")
    game.players[player.name] = player

    selected_cards = [
        {"rank": "10", "suit": "Fire"},
        {"rank": "J", "suit": "Fire"},
        {"rank": "Q", "suit": "Fire"},
        {"rank": "K", "suit": "Fire"},
        {"rank": "Flame", "suit": "Fire"},
    ]

    damage, hand_type, multiplier = game.calculate_damage(selected_cards, player.name)

    assert hand_type == "royal flush"
    assert multiplier == 10
    assert damage == 100


def test_flush_house_gets_both_flush_and_full_house_modifiers():
    game = Game()
    player = Player(
        "tester",
        talent_bonuses={
            "flush_damage_pct": 20,
            "full_house_damage_pct": 50,
        },
    )
    game.players[player.name] = player

    selected_cards = [
        {"rank": "9", "suit": "Fire"},
        {"rank": "9", "suit": "Fire"},
        {"rank": "9", "suit": "Fire"},
        {"rank": "K", "suit": "Fire"},
        {"rank": "K", "suit": "Fire"},
    ]

    damage, hand_type, multiplier = game.calculate_damage(selected_cards, player.name)

    assert hand_type == "flush house"
    assert multiplier == 9
    assert damage == 146


def test_reset_game_rotates_starter_and_awards_bonus_reroll_to_previous_second_player(monkeypatch):
    async def fake_open_upgrade_store(self):
        self.start_shop_phase()

    monkeypatch.setattr(Game, "open_upgrade_store", fake_open_upgrade_store)

    game = Game()
    game.add_player("alice")
    game.add_player("bob")

    asyncio.run(game.reset_game())
    assert game.get_current_player_id() == "bob"
    assert game.shop_rerolls_remaining == {"alice": 0, "bob": 1}

    asyncio.run(game.reset_game())
    assert game.get_current_player_id() == "alice"
    assert game.shop_rerolls_remaining == {"alice": 1, "bob": 0}


def test_shop_reroll_selection_consumes_available_rerolls():
    game = Game()
    game.add_player("alice")
    game.shop_rerolls_remaining = {"alice": 1}

    rerolled_selection = game.reroll_shop_selection("alice")

    assert isinstance(rerolled_selection, list)
    assert len(rerolled_selection) == 5
    assert game.shop_rerolls_remaining["alice"] == 0
    assert game.reroll_shop_selection("alice") == {"error": "No rerolls remaining"}
