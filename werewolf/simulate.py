"""Play many bot games to see how balanced a role mix is.

    python -m werewolf.simulate                 # default roles for 5-16 players
    python -m werewolf.simulate 8 Werewolf=2 Seer=1 Hunter=1

The bots are simple, so the numbers are a rough guide, not the truth:
- Werewolves attack and vote for random non-werewolves.
- The Seer (and the Little Girl) vote for a werewolf they know about, if any.
- Everyone else votes for a random player. Real villagers who talk should do better than this.
- Bots answer yes/no questions at random.
"""

from __future__ import annotations

import argparse
import random
from collections import Counter
from collections.abc import Sequence
from typing import Literal, overload

from .console import BaseConsole, Style
from .game import Game, Player
from .roles import JESTER, ROLES, VILLAGE, WEREWOLVES
from .rules import build_roles, default_role_counts, validate_counts


class BotConsole(BaseConsole):
    """Makes every decision for whichever player is asked, and ignores all output."""

    def __init__(self, rng: random.Random):
        self.rng = rng

    def say(self, text: str = "", style: Style = None) -> None:
        pass

    def ask(self, prompt: str) -> str:
        return ""  # only "press Enter" prompts reach here

    def confirm(self, prompt: str, who: Player | None = None) -> bool:
        return self.rng.random() < 0.5

    @overload
    def choose_player(self, prompt: str, candidates: Sequence[Player],
                      allow_skip: Literal[False] = False, who: Player | None = None) -> Player: ...
    @overload
    def choose_player(self, prompt: str, candidates: Sequence[Player],
                      allow_skip: Literal[True], who: Player | None = None) -> Player | None: ...
    def choose_player(self, prompt: str, candidates: Sequence[Player],
                      allow_skip: bool = False, who: Player | None = None) -> Player | None:
        options = list(candidates)
        if who is None:
            return self.rng.choice(options)

        inspected = who.memory.get("inspected", {})
        if "inspect" in prompt:
            unseen = [p for p in options if p.name not in inspected]
            return self.rng.choice(unseen or options)

        if "vote" in prompt or "shoot" in prompt:
            if who.is_werewolf:
                options = [p for p in options if not p.is_werewolf] or options
            else:
                known = {name for name, wolf in inspected.items() if wolf} | who.memory.get("spotted", set())
                suspects = [p for p in options if p.name in known]
                if suspects:
                    return self.rng.choice(suspects)
        return self.rng.choice(options)


def simulate(counts: dict[str, int], num_players: int, games: int, seed: int = 0) -> Counter[str]:
    rng = random.Random(seed)
    winners: Counter[str] = Counter()
    for _ in range(games):
        roles = build_roles(counts, num_players)
        rng.shuffle(roles)
        game = Game([Player(f"P{i}", role) for i, role in enumerate(roles)], BotConsole(rng), rng)
        winners[game.play()] += 1
    return winners


def report(num_players: int, counts: dict[str, int], winners: Counter[str]) -> str:
    total = sum(winners.values())
    rates = "  ".join(f"{team} {winners[team] / total:5.1%}" for team in (VILLAGE, WEREWOLVES, JESTER))
    mix = ", ".join(f"{n} {name}" for name, n in counts.items() if n)
    return f"{num_players:>2} players  {rates}   ({mix})"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("players", nargs="?", type=int, help="number of players")
    parser.add_argument("roles", nargs="*", help="role counts like Werewolf=2 Seer=1")
    parser.add_argument("--games", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    if args.players is None:
        for n in range(5, 17):
            counts = default_role_counts(n)
            print(report(n, counts, simulate(counts, n, args.games, args.seed)))
        return

    counts = {}
    for item in args.roles:
        name, _, count = item.partition("=")
        if name not in ROLES:
            parser.error(f"unknown role {name!r}; choose from {', '.join(ROLES)}")
        counts[name] = int(count or 1)
    counts = counts or default_role_counts(args.players)
    error = validate_counts(counts, args.players)
    if error:
        parser.error(error)
    print(report(args.players, counts, simulate(counts, args.players, args.games, args.seed)))


if __name__ == "__main__":
    main()
