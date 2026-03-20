"""Additional white-box tests to improve path coverage.

These tests are designed after inspecting internal control flow and error paths.
Run with coverage:

  python -m coverage run -m unittest discover -s tests -p "test*.py"
  python -m coverage report -m

"""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from moneypoly.bank import Bank
from moneypoly.board import Board
from moneypoly.cards import CardDeck
from moneypoly.config import (
    AUCTION_MIN_INCREMENT,
    GO_SALARY,
    INCOME_TAX_AMOUNT,
    INCOME_TAX_POSITION,
    JAIL_FINE,
    JAIL_POSITION,
    LUXURY_TAX_AMOUNT,
    LUXURY_TAX_POSITION,
    MAX_TURNS,
)
from moneypoly.dice import Dice
from moneypoly.game import Game
from moneypoly.player import Player
from moneypoly.property import Property, PropertyGroup
from moneypoly import ui


class TestDiceMorePaths(unittest.TestCase):
    def test_roll_non_doubles_resets_streak(self) -> None:
        dice = Dice()
        dice.doubles_streak = 2
        with mock.patch("moneypoly.dice.random.randint", side_effect=[1, 2]):
            total = dice.roll()
        self.assertEqual(total, 3)
        self.assertEqual(dice.doubles_streak, 0)

    def test_repr_includes_state(self) -> None:
        dice = Dice()
        dice.die1 = 1
        dice.die2 = 2
        dice.doubles_streak = 0
        text = repr(dice)
        self.assertIn("die1=1", text)
        self.assertIn("die2=2", text)


class TestBankMorePaths(unittest.TestCase):
    def test_pay_out_non_positive_returns_zero(self) -> None:
        bank = Bank()
        self.assertEqual(bank.pay_out(0), 0)
        self.assertEqual(bank.pay_out(-5), 0)

    def test_give_loan_non_positive_does_nothing(self) -> None:
        bank = Bank()
        player = mock.Mock()
        bank.give_loan(player, 0)
        player.add_money.assert_not_called()
        self.assertEqual(bank.loan_count(), 0)

    def test_give_loan_tracks_summary_and_repr(self) -> None:
        bank = Bank()
        player = Player("P")
        start_balance = player.balance

        with mock.patch("builtins.print"):
            bank.give_loan(player, 123)
            bank.summary()

        self.assertEqual(player.balance, start_balance + 123)
        self.assertEqual(bank.loan_count(), 1)
        self.assertEqual(bank.total_loans_issued(), 123)
        self.assertIn("Bank(funds=", repr(bank))


class TestBoardMorePaths(unittest.TestCase):
    def test_tile_type_special_property_and_blank(self) -> None:
        board = Board()
        self.assertEqual(board.get_tile_type(0), "go")
        self.assertEqual(board.get_tile_type(JAIL_POSITION), "jail")
        self.assertEqual(board.get_tile_type(INCOME_TAX_POSITION), "income_tax")
        self.assertEqual(board.get_tile_type(LUXURY_TAX_POSITION), "luxury_tax")

        # A known property position
        self.assertEqual(board.get_tile_type(1), "property")

        # A non-special, non-property position
        self.assertEqual(board.get_tile_type(12), "blank")

    def test_is_purchasable_and_ownership_queries(self) -> None:
        board = Board()
        player = Player("Owner")
        prop = board.get_property_at(1)
        self.assertIsNotNone(prop)

        self.assertTrue(board.is_purchasable(1))
        prop.owner = player
        self.assertFalse(board.is_purchasable(1))
        prop.owner = None
        prop.is_mortgaged = True
        self.assertFalse(board.is_purchasable(1))

        # Owned/unowned listing
        prop.is_mortgaged = False
        prop.owner = player
        self.assertIn(prop, board.properties_owned_by(player))
        self.assertNotIn(prop, board.unowned_properties())
        self.assertIn("properties", repr(board))

    def test_is_purchasable_false_for_non_property_and_is_special_tile(self) -> None:
        board = Board()
        self.assertFalse(board.is_purchasable(12))

        self.assertTrue(board.is_special_tile(0))
        self.assertFalse(board.is_special_tile(12))


class TestCardDeckMorePaths(unittest.TestCase):
    def test_empty_deck_draw_and_peek_return_none(self) -> None:
        deck = CardDeck([])
        self.assertIsNone(deck.draw())
        self.assertIsNone(deck.peek())

    def test_draw_cycles_and_peek_does_not_advance(self) -> None:
        cards = [
            {"description": "A", "action": "collect", "value": 1},
            {"description": "B", "action": "pay", "value": 2},
        ]
        deck = CardDeck(cards)

        self.assertEqual(deck.peek()["description"], "A")
        self.assertEqual(deck.peek()["description"], "A")
        self.assertEqual(deck.draw()["description"], "A")
        self.assertEqual(deck.draw()["description"], "B")
        # cycles back
        self.assertEqual(deck.draw()["description"], "A")

    def test_reshuffle_resets_index_and_repr(self) -> None:
        deck = CardDeck([
            {"description": "A", "action": "collect", "value": 1},
            {"description": "B", "action": "pay", "value": 2},
        ])
        deck.draw()
        self.assertNotEqual(deck.index, 0)
        with mock.patch("moneypoly.cards.random.shuffle") as shuf:
            deck.reshuffle()
        shuf.assert_called_once()
        self.assertEqual(deck.index, 0)
        self.assertIn("CardDeck(", repr(deck))
        self.assertEqual(len(deck), 2)
        self.assertIn(deck.cards_remaining(), (1, 2))


class TestUiMorePaths(unittest.TestCase):
    def test_safe_int_input_valid_and_invalid(self) -> None:
        with mock.patch("builtins.input", return_value="5"):
            self.assertEqual(ui.safe_int_input("x", default=0), 5)

        with mock.patch("builtins.input", return_value="not-an-int"):
            self.assertEqual(ui.safe_int_input("x", default=7), 7)

    def test_confirm_yes_and_no(self) -> None:
        with mock.patch("builtins.input", return_value="y"):
            self.assertTrue(ui.confirm("?") )
        with mock.patch("builtins.input", return_value="n"):
            self.assertFalse(ui.confirm("?") )

    def test_print_helpers_smoke(self) -> None:
        player = Player("P")
        board = Board()
        output = io.StringIO()
        with redirect_stdout(output):
            ui.print_banner("Title")
            ui.print_standings([player])
            ui.print_board_ownership(board)
            ui.print_player_card(player)
        text = output.getvalue()
        self.assertIn("Title", text)
        self.assertIn("Standings", text)
        self.assertIn("Property Register", text)
        self.assertIn("Player", text)

    def test_print_player_card_includes_jail_cards_and_properties(self) -> None:
        player = Player("P")
        player.in_jail = True
        player.jail_turns = 1
        player.get_out_of_jail_cards = 1

        board = Board()
        prop = board.get_property_at(1)
        self.assertIsNotNone(prop)
        prop.owner = player
        player.add_property(prop)

        output = io.StringIO()
        with redirect_stdout(output):
            ui.print_player_card(player)

        text = output.getvalue()
        self.assertIn("Jail cards", text)
        self.assertIn("Properties:", text)
        self.assertIn(prop.name, text)

    def test_format_currency(self) -> None:
        self.assertEqual(ui.format_currency(1500), "$1,500")


class TestPlayerAndPropertyMorePaths(unittest.TestCase):
    def test_add_and_deduct_negative_raise(self) -> None:
        player = Player("P")
        with self.assertRaises(ValueError):
            player.add_money(-1)
        with self.assertRaises(ValueError):
            player.deduct_money(-1)

    def test_move_lands_on_go_prints_landed_message(self) -> None:
        player = Player("P")
        player.position = 39
        start_balance = player.balance

        buf = io.StringIO()
        with redirect_stdout(buf):
            player.move(1)

        self.assertEqual(player.position, 0)
        self.assertEqual(player.balance, start_balance + GO_SALARY)
        self.assertIn("landed on Go", buf.getvalue())

    def test_status_line_jailed_tag_and_repr(self) -> None:
        player = Player("P")
        player.in_jail = True
        self.assertIn("[JAILED]", player.status_line())
        self.assertIn("Player(", repr(player))

    def test_property_rent_mortgage_and_full_group_multiplier(self) -> None:
        group = PropertyGroup("Test", "test")
        owner = Player("Owner")
        p1 = Property("A", 1, 100, 10, group)
        p2 = Property("B", 2, 100, 10, group)
        p1.owner = owner
        p2.owner = owner

        self.assertEqual(p1.get_rent(), 20)

        p1.is_mortgaged = True
        self.assertEqual(p1.get_rent(), 0)

    def test_property_group_counts_size_and_add_property(self) -> None:
        group = PropertyGroup("Test", "test")
        owner = Player("Owner")
        p1 = Property("A", 1, 100, 10)
        p2 = Property("B", 2, 100, 10)
        group.add_property(p1)
        group.add_property(p2)
        p1.owner = owner

        counts = group.get_owner_counts()
        self.assertEqual(counts.get(owner), 1)
        self.assertEqual(group.size(), 2)
        self.assertIn("PropertyGroup(", repr(group))
        self.assertTrue(p2.is_available())
        p2.owner = owner
        self.assertFalse(p2.is_available())
        self.assertIn("Property(", repr(p2))

    def test_property_mortgage_already_mortgaged_and_unmortgage_not_mortgaged(self) -> None:
        group = PropertyGroup("Test", "test")
        prop = Property("A", 1, 60, 2, group)

        self.assertEqual(prop.mortgage(), 30)
        self.assertEqual(prop.mortgage(), 0)

        prop.is_mortgaged = False
        self.assertEqual(prop.unmortgage(), 0)


class TestGameMenuAndRunMorePaths(unittest.TestCase):
    def test_play_turn_three_doubles_sends_to_jail(self) -> None:
        game = Game(["A", "B"])
        player = game.players[0]

        def rigged_roll():
            game.dice.doubles_streak = 3
            return 4

        with (
            mock.patch.object(game.dice, "roll", side_effect=rigged_roll),
            mock.patch.object(game.dice, "describe", return_value="2 + 2 = 4 (DOUBLES)"),
            mock.patch("moneypoly.game.ui.print_banner"),
        ):
            game.play_turn()

        self.assertTrue(player.in_jail)
        self.assertEqual(game.current_index, 1)
        self.assertEqual(game.turn_number, 1)

    def test_play_turn_doubles_grants_extra_turn(self) -> None:
        game = Game(["A", "B"])

        with (
            mock.patch("moneypoly.game.ui.print_banner"),
            mock.patch.object(game.dice, "roll", return_value=6),
            mock.patch.object(game.dice, "describe", return_value="3 + 3 = 6 (DOUBLES)"),
            mock.patch.object(game.dice, "is_doubles", return_value=True),
            mock.patch.object(game, "_move_and_resolve"),
            mock.patch.object(game, "advance_turn") as adv,
        ):
            game.play_turn()

        adv.assert_not_called()

    def test_run_one_player_and_no_players_paths(self) -> None:
        game_one = Game(["Solo"])
        out1 = io.StringIO()
        with (
            redirect_stdout(out1),
            mock.patch("moneypoly.game.ui.print_banner") as banner,
            mock.patch("moneypoly.game.ui.print_standings"),
        ):
            game_one.run()
        banner.assert_any_call("Welcome to MoneyPoly!")
        banner.assert_any_call("GAME OVER")

        game_none = Game(["A", "B"])
        game_none.players.clear()
        out2 = io.StringIO()
        with (
            redirect_stdout(out2),
            mock.patch("moneypoly.game.ui.print_banner"),
            mock.patch("moneypoly.game.ui.print_standings"),
        ):
            game_none.run()
        self.assertIn("no players remaining", out2.getvalue().lower())

    def test_interactive_menu_exercises_all_options(self) -> None:
        game = Game(["A", "B"])
        player = game.players[0]

        with (
            mock.patch("moneypoly.game.ui.print_standings") as standings,
            mock.patch("moneypoly.game.ui.print_board_ownership") as ownership,
            mock.patch.object(game, "_menu_mortgage") as menu_mortgage,
            mock.patch.object(game, "_menu_unmortgage") as menu_unmortgage,
            mock.patch.object(game, "_menu_trade") as menu_trade,
            mock.patch.object(game.bank, "give_loan") as give_loan,
            mock.patch(
                "moneypoly.game.ui.safe_int_input",
                side_effect=[1, 2, 3, 4, 5, 6, 100, 0],
            ),
        ):
            game.interactive_menu(player)

        standings.assert_called()
        ownership.assert_called()
        menu_mortgage.assert_called_once_with(player)
        menu_unmortgage.assert_called_once_with(player)
        menu_trade.assert_called_once_with(player)
        give_loan.assert_called_once()

    def test_menu_mortgage_unmortgage_trade_branches(self) -> None:
        game = Game(["A", "B"])
        player = game.players[0]

        # no properties to mortgage
        buf = io.StringIO()
        with redirect_stdout(buf):
            game._menu_mortgage(player)
        self.assertIn("No properties available", buf.getvalue())

        # mortgage selection triggers mortgage_property
        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)
        prop.owner = player
        player.add_property(prop)
        with (
            mock.patch("moneypoly.game.ui.safe_int_input", return_value=1),
            mock.patch.object(game, "mortgage_property") as mortgage,
        ):
            game._menu_mortgage(player)
        mortgage.assert_called_once()

        # no mortgaged properties to redeem
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            game._menu_unmortgage(player)
        self.assertIn("No mortgaged properties", buf2.getvalue())

        # unmortgage selection triggers unmortgage_property
        prop.is_mortgaged = True
        with (
            mock.patch("moneypoly.game.ui.safe_int_input", return_value=1),
            mock.patch.object(game, "unmortgage_property") as unmortgage,
        ):
            game._menu_unmortgage(player)
        unmortgage.assert_called_once()

        # trade branches
        game_one = Game(["Solo"])
        buf3 = io.StringIO()
        with redirect_stdout(buf3):
            game_one._menu_trade(game_one.players[0])
        self.assertIn("No other players", buf3.getvalue())

        # player has no properties to trade
        game_no_props = Game(["A", "B"])
        buf4 = io.StringIO()
        with redirect_stdout(buf4):
            with mock.patch("moneypoly.game.ui.safe_int_input", return_value=1):
                game_no_props._menu_trade(game_no_props.players[0])
        self.assertIn("has no properties", buf4.getvalue())

        # happy-path trade calls trade()
        game_trade = Game(["A", "B"])
        p = game_trade.players[0]
        partner = game_trade.players[1]
        tprop = game_trade.board.get_property_at(1)
        self.assertIsNotNone(tprop)
        tprop.owner = p
        p.add_property(tprop)

        with (
            mock.patch("moneypoly.game.ui.safe_int_input", side_effect=[1, 1, 10]),
            mock.patch.object(game_trade, "trade") as trade,
        ):
            game_trade._menu_trade(p)

        trade.assert_called_once_with(p, partner, tprop, 10)


class TestGameAdditionalBranches(unittest.TestCase):
    def test_play_turn_when_player_in_jail_handles_and_advances(self) -> None:
        game = Game(["A", "B"])
        player = game.players[0]
        player.in_jail = True

        with (
            mock.patch("moneypoly.game.ui.print_banner"),
            mock.patch.object(game, "_handle_jail_turn") as handle,
            mock.patch.object(game, "advance_turn") as adv,
        ):
            game.play_turn()

        handle.assert_called_once_with(player)
        adv.assert_called_once()

    def test_play_turn_non_doubles_advances_turn(self) -> None:
        game = Game(["A", "B"])

        def rigged_roll():
            game.dice.doubles_streak = 0
            return 5

        with (
            mock.patch("moneypoly.game.ui.print_banner"),
            mock.patch.object(game.dice, "roll", side_effect=rigged_roll),
            mock.patch.object(game.dice, "describe", return_value="2 + 3 = 5"),
            mock.patch.object(game.dice, "is_doubles", return_value=False),
            mock.patch.object(game, "_move_and_resolve"),
            mock.patch.object(game, "advance_turn") as adv,
        ):
            game.play_turn()

        adv.assert_called_once()

    def test_move_and_resolve_covers_common_tiles(self) -> None:
        game = Game(["A", "B"])
        player = game.players[0]

        # go_to_jail
        with (
            mock.patch.object(player, "move", side_effect=lambda steps: setattr(player, "position", 30)),
            mock.patch.object(game.board, "get_tile_type", return_value="go_to_jail"),
            mock.patch.object(game, "_check_bankruptcy") as check,
        ):
            game._move_and_resolve(player, 1)
            check.assert_called_with(player)
        self.assertTrue(player.in_jail)

        # income_tax
        player.in_jail = False
        player.position = 0
        with (
            mock.patch.object(player, "move", side_effect=lambda steps: setattr(player, "position", INCOME_TAX_POSITION)),
            mock.patch.object(game.board, "get_tile_type", return_value="income_tax"),
            mock.patch.object(player, "deduct_money") as deduct,
            mock.patch.object(game.bank, "collect") as collect,
            mock.patch.object(game, "_check_bankruptcy"),
        ):
            game._move_and_resolve(player, 1)
        deduct.assert_called_once_with(INCOME_TAX_AMOUNT)
        collect.assert_called_once_with(INCOME_TAX_AMOUNT)

        # luxury_tax
        with (
            mock.patch.object(player, "move", side_effect=lambda steps: setattr(player, "position", LUXURY_TAX_POSITION)),
            mock.patch.object(game.board, "get_tile_type", return_value="luxury_tax"),
            mock.patch.object(player, "deduct_money") as deduct,
            mock.patch.object(game.bank, "collect") as collect,
            mock.patch.object(game, "_check_bankruptcy"),
        ):
            game._move_and_resolve(player, 1)
        deduct.assert_called_once_with(LUXURY_TAX_AMOUNT)
        collect.assert_called_once_with(LUXURY_TAX_AMOUNT)

        # free_parking
        with (
            mock.patch.object(player, "move", side_effect=lambda steps: setattr(player, "position", 20)),
            mock.patch.object(game.board, "get_tile_type", return_value="free_parking"),
            mock.patch.object(game, "_check_bankruptcy") as check,
        ):
            game._move_and_resolve(player, 1)
            check.assert_called_with(player)

        # chance
        card = {"description": "C", "action": "collect", "value": 1}
        with (
            mock.patch.object(player, "move", side_effect=lambda steps: setattr(player, "position", 7)),
            mock.patch.object(game.board, "get_tile_type", return_value="chance"),
            mock.patch.object(game.chance_deck, "draw", return_value=card),
            mock.patch.object(game, "_apply_card") as apply,
            mock.patch.object(game, "_check_bankruptcy"),
        ):
            game._move_and_resolve(player, 1)
        apply.assert_called_once_with(player, card)

        # community_chest
        card2 = {"description": "D", "action": "pay", "value": 1}
        with (
            mock.patch.object(player, "move", side_effect=lambda steps: setattr(player, "position", 2)),
            mock.patch.object(game.board, "get_tile_type", return_value="community_chest"),
            mock.patch.object(game.community_deck, "draw", return_value=card2),
            mock.patch.object(game, "_apply_card") as apply,
            mock.patch.object(game, "_check_bankruptcy"),
        ):
            game._move_and_resolve(player, 1)
        apply.assert_called_once_with(player, card2)

        # railroad and property
        rail_prop = Property("Railroad", 5, 200, 25)
        with (
            mock.patch.object(player, "move", side_effect=lambda steps: setattr(player, "position", 5)),
            mock.patch.object(game.board, "get_tile_type", return_value="railroad"),
            mock.patch.object(game.board, "get_property_at", return_value=rail_prop),
            mock.patch.object(game, "_handle_property_tile") as handle,
            mock.patch.object(game, "_check_bankruptcy"),
        ):
            game._move_and_resolve(player, 1)
        handle.assert_called_once_with(player, rail_prop)

        prop2 = game.board.get_property_at(1)
        self.assertIsNotNone(prop2)
        with (
            mock.patch.object(player, "move", side_effect=lambda steps: setattr(player, "position", 1)),
            mock.patch.object(game.board, "get_tile_type", return_value="property"),
            mock.patch.object(game.board, "get_property_at", return_value=prop2),
            mock.patch.object(game, "_handle_property_tile") as handle,
            mock.patch.object(game, "_check_bankruptcy"),
        ):
            game._move_and_resolve(player, 1)
        handle.assert_called_once_with(player, prop2)

    def test_buy_pay_mortgage_unmortgage_trade_branches(self) -> None:
        game = Game(["A", "B"])
        player = game.players[0]
        other = game.players[1]
        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)

        # buy_property cannot afford
        player.balance = 0
        with redirect_stdout(io.StringIO()):
            self.assertFalse(game.buy_property(player, prop))

        # pay_rent early returns
        prop.is_mortgaged = True
        with redirect_stdout(io.StringIO()):
            game.pay_rent(player, prop)

        prop.is_mortgaged = False
        prop.owner = None
        with redirect_stdout(io.StringIO()):
            game.pay_rent(player, prop)

        # mortgage_property not owned / already mortgaged
        prop.owner = other
        with redirect_stdout(io.StringIO()):
            self.assertFalse(game.mortgage_property(player, prop))

        prop.owner = player
        prop.is_mortgaged = True
        with redirect_stdout(io.StringIO()):
            self.assertFalse(game.mortgage_property(player, prop))

        # unmortgage_property not owned / not mortgaged / cannot afford
        prop.owner = other
        with redirect_stdout(io.StringIO()):
            self.assertFalse(game.unmortgage_property(player, prop))

        prop.owner = player
        prop.is_mortgaged = False
        with redirect_stdout(io.StringIO()):
            self.assertFalse(game.unmortgage_property(player, prop))

        prop.is_mortgaged = True
        player.balance = 0
        with redirect_stdout(io.StringIO()):
            self.assertFalse(game.unmortgage_property(player, prop))

        # trade fails when seller doesn't own prop
        prop.owner = other
        with redirect_stdout(io.StringIO()):
            self.assertFalse(game.trade(player, other, prop, 10))

    def test_auction_too_low_and_cannot_afford_branches(self) -> None:
        game = Game(["A", "B"])
        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)

        with (
            mock.patch(
                "moneypoly.game.ui.safe_int_input",
                side_effect=[AUCTION_MIN_INCREMENT - 1, 999999],
            ),
            redirect_stdout(io.StringIO()),
        ):
            game.auction_property(prop)

    def test_apply_card_none_and_move_to_property_triggers_handle(self) -> None:
        game = Game(["A", "B"])
        player = game.players[0]

        game._apply_card(player, None)

        card = {"description": "Go to Mediterranean", "action": "move_to", "value": 1}
        with (
            mock.patch.object(game, "_handle_property_tile") as handle,
            redirect_stdout(io.StringIO()),
        ):
            game._apply_card(player, card)

        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)
        handle.assert_called_once_with(player, prop)

    def test_check_bankruptcy_resets_current_index_when_out_of_range(self) -> None:
        game = Game(["A", "B"])
        game.current_index = 1
        victim = game.players[1]
        victim.balance = 0

        with redirect_stdout(io.StringIO()):
            game._check_bankruptcy(victim)

        self.assertEqual(game.current_index, 0)
        self.assertNotIn(victim, game.players)

    def test_run_calls_standings_inside_loop(self) -> None:
        game = Game(["A", "B"])

        def stop_after_one_turn():
            game.running = False

        with (
            mock.patch("moneypoly.game.ui.print_banner"),
            mock.patch("moneypoly.game.ui.print_standings") as standings,
            mock.patch.object(game, "play_turn", side_effect=stop_after_one_turn),
            redirect_stdout(io.StringIO()),
        ):
            game.run()

        standings.assert_called()

    def test_menu_trade_invalid_indexes_return_early(self) -> None:
        game = Game(["A", "B"])
        player = game.players[0]
        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)
        prop.owner = player
        player.add_property(prop)

        # invalid partner selection
        with (
            mock.patch("moneypoly.game.ui.safe_int_input", return_value=0),
            mock.patch.object(game, "trade") as trade,
            redirect_stdout(io.StringIO()),
        ):
            game._menu_trade(player)
        trade.assert_not_called()

        # invalid property selection
        with (
            mock.patch("moneypoly.game.ui.safe_int_input", side_effect=[1, 0]),
            mock.patch.object(game, "trade") as trade,
            redirect_stdout(io.StringIO()),
        ):
            game._menu_trade(player)
        trade.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
