"""White-box tests for the MoneyPoly entry point (main.py).

Covers the program-level control-flow (A-series):
- prompt + name parsing
- normal Game creation + run
- KeyboardInterrupt handling
- ValueError handling
- __main__ guard execution
"""

from __future__ import annotations

import runpy
import unittest
from unittest import mock

import main as entry


class TestEntryPointParsing(unittest.TestCase):
    def test_get_player_names_parses_and_filters(self) -> None:
        with (
            mock.patch("builtins.print") as pr,
            mock.patch("builtins.input", return_value="  Alice, , Bob , ,  "),
        ):
            names = entry.get_player_names()

        pr.assert_called()  # prompt printed
        self.assertEqual(names, ["Alice", "Bob"])

    def test_get_player_names_empty_input_returns_empty_list(self) -> None:
        with (
            mock.patch("builtins.print"),
            mock.patch("builtins.input", return_value="   "),
        ):
            names = entry.get_player_names()

        self.assertEqual(names, [])


class TestEntryPointMainFlow(unittest.TestCase):
    def test_main_normal_execution_creates_game_and_runs(self) -> None:
        fake_game = mock.Mock()

        with (
            mock.patch("main.get_player_names", return_value=["A", "B"]),
            mock.patch("main.Game", return_value=fake_game) as Game,
            mock.patch("builtins.print"),
        ):
            entry.main()

        Game.assert_called_once_with(["A", "B"])
        fake_game.run.assert_called_once()

    def test_main_handles_keyboard_interrupt(self) -> None:
        fake_game = mock.Mock()
        fake_game.run.side_effect = KeyboardInterrupt

        with (
            mock.patch("main.get_player_names", return_value=["A", "B"]),
            mock.patch("main.Game", return_value=fake_game),
            mock.patch("builtins.print") as pr,
        ):
            entry.main()

        printed = "\n".join(" ".join(map(str, c.args)) for c in pr.call_args_list)
        self.assertIn("Game interrupted", printed)

    def test_main_handles_value_error(self) -> None:
        with (
            mock.patch("main.get_player_names", return_value=["A", "B"]),
            mock.patch("main.Game", side_effect=ValueError("bad setup")),
            mock.patch("builtins.print") as pr,
        ):
            entry.main()

        printed = "\n".join(" ".join(map(str, c.args)) for c in pr.call_args_list)
        self.assertIn("Setup error:", printed)
        self.assertIn("bad setup", printed)

    def test_running_as_script_triggers_main_via_guard(self) -> None:
        fake_game = mock.Mock()

        with (
            mock.patch("builtins.print"),
            mock.patch("builtins.input", return_value="A, B"),
            mock.patch("moneypoly.game.Game", return_value=fake_game),
        ):
            runpy.run_module("main", run_name="__main__")

        fake_game.run.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
