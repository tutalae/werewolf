"""A fake console that plays back scripted answers, for testing."""

import random

from werewolf.console import BaseConsole
from werewolf.game import Game, GameOptions, Player
from werewolf.roles import ROLES


class ScriptedConsole(BaseConsole):
    def __init__(self, answers=()):
        self.answers = list(answers)
        self.output = []

    def say(self, text="", style=None):
        self.output.append(text)

    def ask(self, prompt):
        self.output.append(prompt)
        # "Pass the device" and "Press Enter" prompts only need Enter
        if prompt.startswith(("Pass the device", "Press Enter")):
            return ""
        if not self.answers:
            raise AssertionError(f"Ran out of scripted answers at: {prompt!r}")
        return self.answers.pop(0)

    def clear(self):
        self.output.append("<clear>")

    def discuss(self, seconds):
        self.output.append(f"<discuss {seconds}>")

    def table(self, title, headers, rows):
        # e.g. "Votes: Ann 2, Cat 1"
        self.output.append(f"{title}: " + ", ".join(" ".join(map(str, row)) for row in rows))

    @property
    def text(self):
        return "\n".join(self.output)


def make_players(*specs):
    """make_players("Ann:Werewolf", "Bob:Villager") -> list of Players."""
    return [Player(name, ROLES[role]) for name, role in (spec.split(":") for spec in specs)]


def make_game(answers, *specs, seed=0, **options):
    """A game with the given players. Options default to no discussion timer."""
    console = ScriptedConsole(answers)
    options.setdefault("discussion_seconds", 0)
    game = Game(make_players(*specs), console, random.Random(seed), GameOptions(**options))
    return game, console
