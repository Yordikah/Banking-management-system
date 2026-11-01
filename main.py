"""Banking Management System entry point.

    python main.py          # text menu
    python main.py --gui    # desktop window (Tkinter)
"""

import argparse
import sys

from banking.errors import DatabaseError


def main() -> int:
    parser = argparse.ArgumentParser(description="Banking Management System (Python + MySQL)")
    parser.add_argument("--gui", action="store_true", help="open the Tkinter desktop interface")
    args = parser.parse_args()

    # Fail fast with a clear message if MySQL is unreachable.
    try:
        from banking.database import get_connection
        get_connection().close()
    except DatabaseError as err:
        print(f"{err}\nCheck your settings in the .env file (see .env.example).")
        return 1

    if args.gui:
        from banking.gui import launch
        launch()
    else:
        from banking.cli import main_menu
        try:
            main_menu()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
