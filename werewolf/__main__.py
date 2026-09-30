import random

from .console import Console
from .game import setup


def main():
    try:
        setup(Console(), random.Random()).play()
    except (KeyboardInterrupt, EOFError):
        print("\nGame cancelled.")


if __name__ == "__main__":
    main()
