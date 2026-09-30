import random

from .console import make_console
from .game import setup


def main() -> None:
    try:
        setup(make_console(), random.Random()).play()
    except (KeyboardInterrupt, EOFError):
        print("\nGame cancelled.")


if __name__ == "__main__":
    main()
