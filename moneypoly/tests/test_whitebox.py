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


class TestBank(unittest.TestCase):
    def test_pay_out_rejects_overdraft(self):
        """Edge: Bank.pay_out should raise if insufficient funds."""
        bank = Bank()
        with self.assertRaises(ValueError):
            bank.pay_out(bank.get_balance() + 1)


if __name__ == "__main__":
    unittest.main()
