"""White-box tests for core MoneyPoly mechanics.

These tests are designed from internal code structure to exercise key branches,
edge cases, and state transitions.
"""

from __future__ import annotations

import unittest
from unittest import mock

from moneypoly.bank import Bank
from moneypoly.dice import Dice
from moneypoly.game import Game
from moneypoly.player import Player
from moneypoly.property import Property, PropertyGroup
from moneypoly.config import GO_SALARY


class TestDice(unittest.TestCase):
    def test_roll_uses_six_sided_dice(self):
        """White-box: verify Dice.roll calls randint(1, 6) for both dice."""
        dice = Dice()
        with mock.patch("moneypoly.dice.random.randint", return_value=1) as rint:
            dice.roll()

        # randint should be called twice with inclusive bounds 1..6
        self.assertGreaterEqual(rint.call_count, 2)
        for call in rint.call_args_list[:2]:
            self.assertEqual(call.args, (1, 6))


class TestPlayerMovement(unittest.TestCase):
    def test_passing_go_awards_salary(self):
        """Edge/branch: wrap-around should award GO_SALARY when passing Go."""
        player = Player("P")
        start_balance = player.balance
        player.position = 39

        player.move(2)  # wraps to 1

        self.assertEqual(player.position, 1)
        self.assertEqual(player.balance, start_balance + GO_SALARY)


class TestPropertyGroupLogic(unittest.TestCase):
    def test_all_owned_by_requires_full_group(self):
        """White-box: PropertyGroup.all_owned_by should require ALL properties."""
        group = PropertyGroup("Test", "test")
        owner = Player("Owner")
        other = Player("Other")

        prop1 = Property("A", 1, 100, 10, group)
        prop2 = Property("B", 2, 100, 10, group)

        prop1.owner = owner
        prop2.owner = other

        self.assertFalse(group.all_owned_by(owner))


class TestGameEconomy(unittest.TestCase):
    def test_buy_property_allows_exact_balance(self):
        """Edge case: player with exactly the price should be able to buy."""
        game = Game(["A", "B"])
        player = game.players[0]
        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)
        prop = prop  # help type checkers

        player.balance = prop.price

        ok = game.buy_property(player, prop)

        self.assertTrue(ok)
        self.assertEqual(prop.owner, player)

    def test_pay_rent_transfers_to_owner(self):
        """Branch: rent payment should reduce payer and increase owner."""
        game = Game(["A", "B"])
        tenant = game.players[0]
        owner = game.players[1]
        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)
        prop.owner = owner

        rent = prop.get_rent()
        tenant_start = tenant.balance
        owner_start = owner.balance

        game.pay_rent(tenant, prop)

        self.assertEqual(tenant.balance, tenant_start - rent)
        self.assertEqual(owner.balance, owner_start + rent)

    def test_find_winner_returns_highest_net_worth(self):
        """Branch: winner should be the max net worth, not min."""
        game = Game(["A", "B", "C"])
        game.players[0].balance = 100
        game.players[1].balance = 500
        game.players[2].balance = 300

        winner = game.find_winner()

        self.assertIsNotNone(winner)
        self.assertEqual(winner.name, "B")


class TestJailBranches(unittest.TestCase):
    def test_jail_use_get_out_of_jail_card_path(self):
        """Branch: jailed player uses card, leaves jail, then moves/resolves."""
        game = Game(["A", "B"])
        player = game.players[0]
        player.in_jail = True
        player.get_out_of_jail_cards = 1

        with (
            mock.patch("moneypoly.game.ui.confirm", side_effect=[True]),
            mock.patch.object(game.dice, "roll", return_value=2),
            mock.patch.object(game, "_move_and_resolve") as move_resolve,
        ):
            game._handle_jail_turn(player)

        self.assertFalse(player.in_jail)
        self.assertEqual(player.get_out_of_jail_cards, 0)
        self.assertEqual(player.jail_turns, 0)
        move_resolve.assert_called_once_with(player, 2)

    def test_jail_pay_fine_yes_path(self):
        """Branch: jailed player chooses to pay fine and is released."""
        game = Game(["A", "B"])
        player = game.players[0]
        player.in_jail = True
        start_balance = player.balance

        with (
            mock.patch("moneypoly.game.ui.confirm", side_effect=[True]),
            mock.patch.object(game.dice, "roll", return_value=3),
            mock.patch.object(game, "_move_and_resolve") as move_resolve,
        ):
            game._handle_jail_turn(player)

        self.assertFalse(player.in_jail)
        self.assertEqual(player.jail_turns, 0)
        # Paying the fine should reduce player balance
        self.assertLess(player.balance, start_balance)
        move_resolve.assert_called_once_with(player, 3)

    def test_jail_serve_three_turns_then_mandatory_release(self):
        """Branch: decline actions until mandatory release on 3rd turn."""
        game = Game(["A", "B"])
        player = game.players[0]
        player.in_jail = True
        player.jail_turns = 2
        start_balance = player.balance

        with (
            mock.patch("moneypoly.game.ui.confirm", return_value=False),
            mock.patch.object(game.dice, "roll", return_value=4),
            mock.patch.object(game, "_move_and_resolve") as move_resolve,
        ):
            game._handle_jail_turn(player)

        self.assertFalse(player.in_jail)
        self.assertEqual(player.jail_turns, 0)
        self.assertLess(player.balance, start_balance)
        move_resolve.assert_called_once_with(player, 4)


class TestPropertyTileBranches(unittest.TestCase):
    def test_unowned_property_buy_branch(self):
        """Branch: unowned property -> input 'b' -> buy_property called."""
        game = Game(["A", "B"])
        player = game.players[0]
        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)

        with (
            mock.patch("builtins.input", return_value="b"),
            mock.patch.object(game, "buy_property", return_value=True) as buy,
        ):
            game._handle_property_tile(player, prop)
        buy.assert_called_once()

    def test_unowned_property_auction_branch(self):
        """Branch: unowned property -> input 'a' -> auction_property called."""
        game = Game(["A", "B"])
        player = game.players[0]
        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)

        with (
            mock.patch("builtins.input", return_value="a"),
            mock.patch.object(game, "auction_property") as auction,
        ):
            game._handle_property_tile(player, prop)
        auction.assert_called_once_with(prop)

    def test_unowned_property_skip_branch(self):
        """Branch: unowned property -> input not b/a -> no purchase/auction."""
        game = Game(["A", "B"])
        player = game.players[0]
        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)

        with (
            mock.patch("builtins.input", return_value="s"),
            mock.patch.object(game, "buy_property") as buy,
            mock.patch.object(game, "auction_property") as auction,
        ):
            game._handle_property_tile(player, prop)
        buy.assert_not_called()
        auction.assert_not_called()

    def test_property_owned_by_self_branch(self):
        """Branch: landing on own property -> no rent charged."""
        game = Game(["A", "B"])
        player = game.players[0]
        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)
        prop.owner = player

        with mock.patch.object(game, "pay_rent") as pay_rent:
            game._handle_property_tile(player, prop)
        pay_rent.assert_not_called()

    def test_property_owned_by_other_branch(self):
        """Branch: landing on other's property -> pay_rent called."""
        game = Game(["A", "B"])
        tenant = game.players[0]
        owner = game.players[1]
        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)
        prop.owner = owner

        with mock.patch.object(game, "pay_rent") as pay_rent:
            game._handle_property_tile(tenant, prop)
        pay_rent.assert_called_once_with(tenant, prop)


class TestAuctionBranches(unittest.TestCase):
    def test_auction_no_bids_branch(self):
        """Branch: all players pass (0) -> property remains unowned."""
        game = Game(["A", "B"])
        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)

        with mock.patch("moneypoly.game.ui.safe_int_input", side_effect=[0, 0]):
            game.auction_property(prop)

        self.assertIsNone(prop.owner)

    def test_auction_highest_bid_wins_branch(self):
        """Branch: valid bids -> highest bidder becomes owner."""
        game = Game(["A", "B"])
        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)
        # Bids: A=10, B=20
        with mock.patch("moneypoly.game.ui.safe_int_input", side_effect=[10, 20]):
            game.auction_property(prop)

        self.assertIsNotNone(prop.owner)
        self.assertEqual(prop.owner.name, "B")


class TestCardBranches(unittest.TestCase):
    def test_apply_card_collect_branch(self):
        game = Game(["A", "B"])
        player = game.players[0]
        start_balance = player.balance
        card = {"description": "Collect", "action": "collect", "value": 50}
        game._apply_card(player, card)
        self.assertEqual(player.balance, start_balance + 50)

    def test_apply_card_pay_branch(self):
        game = Game(["A", "B"])
        player = game.players[0]
        start_balance = player.balance
        card = {"description": "Pay", "action": "pay", "value": 25}
        game._apply_card(player, card)
        self.assertEqual(player.balance, start_balance - 25)

    def test_apply_card_jail_branch(self):
        game = Game(["A", "B"])
        player = game.players[0]
        card = {"description": "Jail", "action": "jail", "value": 0}
        game._apply_card(player, card)
        self.assertTrue(player.in_jail)

    def test_apply_card_jail_free_branch(self):
        game = Game(["A", "B"])
        player = game.players[0]
        card = {"description": "Jail free", "action": "jail_free", "value": 0}
        game._apply_card(player, card)
        self.assertEqual(player.get_out_of_jail_cards, 1)

    def test_apply_card_move_to_pays_go_when_wrapping(self):
        """Branch: move_to with value < old position should pay GO_SALARY."""
        game = Game(["A", "B"])
        player = game.players[0]
        player.position = 39
        start_balance = player.balance
        card = {"description": "Move", "action": "move_to", "value": 0}
        game._apply_card(player, card)
        self.assertEqual(player.position, 0)
        self.assertEqual(player.balance, start_balance + GO_SALARY)

    def test_apply_card_birthday_branch_only_players_who_can_afford_pay(self):
        game = Game(["A", "B", "C"])
        birthday_player = game.players[0]
        poor = game.players[1]
        rich = game.players[2]
        poor.balance = 5
        rich.balance = 100
        start_bday = birthday_player.balance
        start_poor = poor.balance
        start_rich = rich.balance
        card = {"description": "Birthday", "action": "birthday", "value": 10}
        game._apply_card(birthday_player, card)

        self.assertEqual(poor.balance, start_poor)  # can't afford
        self.assertEqual(rich.balance, start_rich - 10)
        self.assertEqual(birthday_player.balance, start_bday + 10)

    def test_apply_card_collect_from_all_branch(self):
        game = Game(["A", "B", "C"])
        player = game.players[0]
        other1 = game.players[1]
        other2 = game.players[2]
        other1.balance = 100
        other2.balance = 100
        start = player.balance
        card = {"description": "Collect all", "action": "collect_from_all", "value": 7}
        game._apply_card(player, card)
        self.assertEqual(player.balance, start + 14)


class TestBankruptcyAndTrades(unittest.TestCase):
    def test_check_bankruptcy_eliminates_player_and_releases_properties(self):
        game = Game(["A", "B"])
        bankrupt = game.players[0]
        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)
        prop.owner = bankrupt
        bankrupt.add_property(prop)
        bankrupt.balance = 0

        game._check_bankruptcy(bankrupt)

        self.assertTrue(bankrupt.is_eliminated)
        self.assertNotIn(bankrupt, game.players)
        self.assertIsNone(prop.owner)

    def test_trade_transfers_cash_and_property(self):
        """Branch: successful trade transfers cash from buyer to seller."""
        game = Game(["Seller", "Buyer"])
        seller = game.players[0]
        buyer = game.players[1]
        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)
        prop.owner = seller
        seller.add_property(prop)
        cash = 50
        seller_start = seller.balance
        buyer_start = buyer.balance

        ok = game.trade(seller, buyer, prop, cash)

        self.assertTrue(ok)
        self.assertEqual(prop.owner, buyer)
        self.assertEqual(buyer.balance, buyer_start - cash)
        self.assertEqual(seller.balance, seller_start + cash)

    def test_trade_fails_if_buyer_cannot_afford(self):
        game = Game(["Seller", "Buyer"])
        seller = game.players[0]
        buyer = game.players[1]
        buyer.balance = 10
        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)
        prop.owner = seller
        seller.add_property(prop)

        ok = game.trade(seller, buyer, prop, 50)
        self.assertFalse(ok)

    def test_mortgage_and_unmortgage_branches(self):
        game = Game(["A", "B"])
        player = game.players[0]
        prop = game.board.get_property_at(1)
        self.assertIsNotNone(prop)
        prop.owner = player
        player.add_property(prop)

        start_balance = player.balance
        ok = game.mortgage_property(player, prop)
        self.assertTrue(ok)
        self.assertTrue(prop.is_mortgaged)
        self.assertGreater(player.balance, start_balance)

        # Unmortgage should work if player can afford
        ok2 = game.unmortgage_property(player, prop)
        self.assertTrue(ok2)
        self.assertFalse(prop.is_mortgaged)


class TestBank(unittest.TestCase):
    def test_pay_out_rejects_overdraft(self):
        """Edge: Bank.pay_out should raise if insufficient funds."""
        bank = Bank()
        with self.assertRaises(ValueError):
            bank.pay_out(bank.get_balance() + 1)


if __name__ == "__main__":
    unittest.main()
