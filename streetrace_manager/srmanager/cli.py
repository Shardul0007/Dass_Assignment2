"""Minimal CLI for StreetRace Manager.

This CLI is intentionally small; it's mainly to demonstrate module integration.
"""

from __future__ import annotations

import argparse

from .manager import StreetRaceManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="srmanager", description="StreetRace Manager")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("register-driver", help="Register a driver")
    p.add_argument("name")

    p = sub.add_parser("set-driver-skill", help="Set driver skill")
    p.add_argument("name")
    p.add_argument("skill")
    p.add_argument("level", type=int)

    p = sub.add_parser("add-car", help="Add a car")
    p.add_argument("car_id")
    p.add_argument("model")

    p = sub.add_parser("create-race", help="Create a race")
    p.add_argument("race_id")
    p.add_argument("name")
    p.add_argument("--min-skill", type=int, default=0)
    p.add_argument("--min-condition", type=int, default=1)

    p = sub.add_parser("enter-race", help="Enter a race")
    p.add_argument("race_id")
    p.add_argument("driver")
    p.add_argument("car_id")

    p = sub.add_parser("start-race", help="Start a race")
    p.add_argument("race_id")

    p = sub.add_parser("complete-race", help="Complete a race")
    p.add_argument("race_id")
    p.add_argument("outcome", choices=["win", "loss"])
    p.add_argument("--prize", type=int, default=0)
    p.add_argument("--damage", type=int, default=0)

    p = sub.add_parser("cash", help="Show current cash")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    manager = StreetRaceManager()

    if args.command == "register-driver":
        manager.register_driver(args.name)
        print("OK")
        return 0

    if args.command == "set-driver-skill":
        manager.register_driver(args.name)
        manager.set_driver_skill(args.name, args.skill, args.level)
        print("OK")
        return 0

    if args.command == "add-car":
        manager.add_car(args.car_id, args.model)
        print("OK")
        return 0

    if args.command == "create-race":
        manager.create_race(args.race_id, args.name, min_driver_skill=args.min_skill, min_car_condition=args.min_condition)
        print("OK")
        return 0

    if args.command == "enter-race":
        # Minimal "demo" flow: auto-register driver and create car if missing.
        if args.driver not in manager.drivers:
            manager.register_driver(args.driver)
        if args.car_id not in manager.cars:
            manager.add_car(args.car_id, model="Unknown")
        if args.race_id not in manager.races:
            manager.create_race(args.race_id, name="Unknown")
        manager.enter_race(args.race_id, args.driver, args.car_id)
        print("OK")
        return 0

    if args.command == "start-race":
        manager.start_race(args.race_id)
        print("OK")
        return 0

    if args.command == "complete-race":
        manager.complete_race(args.race_id, args.outcome, prize_money=args.prize, damage=args.damage)
        print("OK")
        return 0

    if args.command == "cash":
        print(manager.cash)
        return 0

    raise AssertionError("Unhandled command")


if __name__ == "__main__":
    raise SystemExit(main())
