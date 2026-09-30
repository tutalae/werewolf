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
import re
from collections import Counter

from .game import Game, Player, build_roles, default_role_counts, validate_counts
from .roles import JESTER, ROLES, VILLAGE, WEREWOLVES

CHOICES = re.compile(r"\[(.*)\]: $")
ACTOR = re.compile(r"^(?:Pass the device to |)(.+?)(?:\. |, who do you)")
SPOTTED = re.compile(r"^You spot (.+) among the werewolves\.$")


class BotConsole:
    """Answers the game's prompts on behalf of whoever is acting."""

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.game: Game | None = None
        self.actor: Player | None = None

    def say(self, text: str = "") -> None:
        # The Little Girl remembers who she spotted
        match = SPOTTED.match(text)
        if match and self.actor:
            self.actor.memory.setdefault("known_wolves", set()).add(self.find(match.group(1)))

    def clear(self) -> None:
        pass

    def discuss(self, seconds: int) -> None:
        pass

    def find(self, name: str) -> Player:
        assert self.game is not None
        return next(p for p in self.game.players if p.name.lower() == name.lower())

    def ask(self, prompt: str) -> str:
        actor = ACTOR.match(prompt)
        if actor and self.game and any(p.name == actor.group(1) for p in self.game.players):
            self.actor = self.find(actor.group(1))
        if "yes/no" in prompt:
            return self.rng.choice(["yes", "no"])
        match = CHOICES.search(prompt)
        if not match:
            return ""  # "press Enter" prompts
        names = [n for n in match.group(1).replace(", or skip", "").split(", ")]
        return self.choose(prompt, [self.find(n) for n in names]).name

    def choose(self, prompt: str, options: list[Player]) -> Player:
        me = self.actor
        assert me is not None
        known: list[Player] = [p for p in me.memory.get("known_wolves", ()) if p in options]

        if "inspect" in prompt:
            unseen = [p for p in options if p not in me.memory.get("inspected", ())]
            target = self.rng.choice(unseen or options)
            me.memory.setdefault("inspected", set()).add(target)
            if target.role.looks_like_werewolf:
                me.memory.setdefault("known_wolves", set()).add(target)
            return target
        if "vote" in prompt or "shoot" in prompt:
            if me.is_werewolf:
                options = [p for p in options if not p.is_werewolf] or options
            elif known:
                return self.rng.choice(known)
        return self.rng.choice(options)


def simulate(counts: dict[str, int], num_players: int, games: int, seed: int = 0) -> Counter[str]:
    rng = random.Random(seed)
    winners: Counter[str] = Counter()
    for _ in range(games):
        roles = build_roles(counts, num_players)
        rng.shuffle(roles)
        console = BotConsole(rng)
        game = Game([Player(f"P{i}", role) for i, role in enumerate(roles)], console, rng)
        console.game = game
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
