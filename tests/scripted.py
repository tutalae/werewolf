"""A fake console that plays back scripted answers, for testing."""

from werewolf.game import Game, Player
from werewolf.roles import ROLES


class ScriptedConsole:
    def __init__(self, answers=()):
        self.answers = list(answers)
        self.output = []

    def say(self, text=""):
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

    @property
    def text(self):
        return "\n".join(self.output)


def make_players(*specs):
    """make_players("Ann:Werewolf", "Bob:Villager") -> list of Players."""
    return [Player(name, ROLES[role]) for name, role in (spec.split(":") for spec in specs)]


def make_game(answers, *specs, seed=0):
    import random
    console = ScriptedConsole(answers)
    return Game(make_players(*specs), console, random.Random(seed)), console
