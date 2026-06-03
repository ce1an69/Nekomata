"""Nekomata entry point — dispatches CLI, TUI, or Desktop mode."""


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="nekomata-tarot")
    parser.add_argument("--cli", "-c", action="store_true", help="Launch CLI mode")
    parser.add_argument(
        "--desktop", action="store_true", help="Launch Desktop mode"
    )
    parser.add_argument(
        "-q", "--question", type=str, default="", help="Your question for the reading"
    )
    parser.add_argument(
        "-s", "--seed", type=int, default=None, help="Random seed for card draw"
    )
    parser.add_argument("-S", "--spread", type=str, default="", help="Spread type key")
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation and start interpretation immediately",
    )
    args = parser.parse_args()

    if args.cli:
        from nekomata.cli import run_cli

        run_cli(args)
    elif args.desktop:
        from nekomata.desktop import main as desktop_main

        desktop_main()
    else:
        from nekomata.tui.app import NekomataApp

        app = NekomataApp()
        app.run()


if __name__ == "__main__":
    main()
