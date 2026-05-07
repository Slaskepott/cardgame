import asyncio
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from card import Card
from game import Game
from main import (
    games,
    list_games,
    choose_best_bot_hand,
    finalize_match,
    leave_game,
    start_bot_game,
    summarize_drawn_hand,
    summarize_player_peaks,
)
from player import Player
from upgrades import Upgrade
from meta_progression import evaluate_achievements
import main as main_module


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


def test_talent_shop_reroll_bonus_is_applied_to_initial_shop_rerolls():
    game = Game()
    game.add_player("alice", talent_bonuses={"shop_rerolls_flat": 1})
    game.add_player("bob")
    game.shop_bonus_reroll_player_id = "bob"

    assert game.get_initial_shop_rerolls("alice") == 1
    assert game.get_initial_shop_rerolls("bob") == 1


def test_summarize_drawn_hand_counts_five_of_a_rank_as_achievement_progress():
    hand = [
        {"rank": "7", "suit": "Fire"},
        {"rank": "7", "suit": "Air"},
        {"rank": "7", "suit": "Earth"},
        {"rank": "7", "suit": "Water"},
        {"rank": "7", "suit": "Fire"},
        {"rank": "Q", "suit": "Water"},
        {"rank": "A", "suit": "Air"},
        {"rank": "3", "suit": "Earth"},
    ]

    assert summarize_drawn_hand(hand) == {"full_hand_of_a_kind_draws": 1}


def test_summarize_drawn_hand_ignores_four_of_a_rank():
    hand = [
        {"rank": "7", "suit": "Fire"},
        {"rank": "7", "suit": "Air"},
        {"rank": "7", "suit": "Earth"},
        {"rank": "7", "suit": "Water"},
        {"rank": "Q", "suit": "Water"},
        {"rank": "A", "suit": "Air"},
        {"rank": "3", "suit": "Earth"},
        {"rank": "5", "suit": "Fire"},
    ]

    assert summarize_drawn_hand(hand) == {}


def test_summarize_player_peaks_uses_current_armor_and_max_health():
    player = Player("tester", talent_bonuses={"armor_flat": 12, "health_flat": 25})
    peaks = summarize_player_peaks(player)

    assert peaks["max_armor_in_game"] == player.armor
    assert peaks["max_health_in_game"] == player.max_health


def test_peak_stat_achievements_unlock_from_thresholds():
    unlocked = evaluate_achievements(
        {
            "shop_rerolls_used": 6,
            "max_armor_in_game": 45,
            "max_health_in_game": 210,
            "max_single_hand_damage": 145,
            "max_win_health_remaining_pct": 92,
        },
        [],
    )

    assert "shop_rerolls_5" in unlocked
    assert "armor_peak_40" in unlocked
    assert "health_peak_200" in unlocked
    assert "single_hand_damage_140" in unlocked
    assert "wins_healthy_90" in unlocked


def test_start_bot_game_creates_private_match_and_hides_it_from_public_list(monkeypatch):
    games.clear()
    monkeypatch.setattr(main_module, "schedule_bot_action", lambda *_args, **_kwargs: None)

    response = asyncio.run(start_bot_game("medium", "henrik"))

    assert response["game_id"] in games
    game = games[response["game_id"]]
    assert game.is_bot_match is True
    assert game.public_visibility is False
    public_games = list_games()["games"]
    assert response["game_id"] not in {entry["game_id"] for entry in public_games}

    games.clear()


def test_finalize_match_skips_ranked_progress_for_bot_matches(monkeypatch):
    games.clear()
    game = Game(is_bot_match=True, bot_player_id="bot-medium", bot_difficulty="medium", public_visibility=False)
    game.add_player("henrik")
    game.add_player("bot-medium", avatar="🤖")
    games["bot-test"] = game

    called = {"count": 0}

    def fail_if_called(*_args, **_kwargs):
        called["count"] += 1
        raise AssertionError("update_match_progress should not be called for bot matches")

    monkeypatch.setattr(main_module, "update_match_progress", fail_if_called)

    payload = asyncio.run(finalize_match("bot-test", "henrik", "bot-medium", "Practice over"))

    assert called["count"] == 0
    assert payload["elo_changes"]["henrik"]["after"] is None
    assert games["bot-test"].phase == "match_over"

    games.clear()


def test_leaving_bot_match_removes_private_game(monkeypatch):
    games.clear()
    monkeypatch.setattr(main_module, "schedule_bot_action", lambda *_args, **_kwargs: None)
    response = asyncio.run(start_bot_game("easy", "henrik"))
    game_id = response["game_id"]

    leave_response = asyncio.run(leave_game(game_id, "henrik"))

    assert "left bot match" in leave_response["message"]
    assert game_id not in games


def test_bot_can_choose_a_legal_hand():
    game = Game(is_bot_match=True, bot_player_id="bot-hard", bot_difficulty="hard", public_visibility=False)
    game.add_player("henrik")
    game.add_player("bot-hard", avatar="🤖")
    bot = game.players["bot-hard"]
    bot.hand = [
        Card("10", "Fire"),
        Card("J", "Fire"),
        Card("Q", "Fire"),
        Card("K", "Fire"),
        Card("A", "Fire"),
        Card("2", "Water"),
        Card("3", "Earth"),
        Card("5", "Air"),
    ]

    best_hand = choose_best_bot_hand(game, "bot-hard", "hard")

    assert best_hand is not None
    assert 1 <= len(best_hand["cards"]) <= 5
    assert best_hand["hand_type"] == "royal flush"
