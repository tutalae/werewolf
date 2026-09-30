"""The game loop: who takes a turn, what gets asked, and what gets announced.

The rules themselves live in rules.py as pure functions. This module is the part that talks to
players: it snapshots the players into an immutable GameState, lets the rules work out what
happens, and applies the result back to the players.
"""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from . import rules
from .actions import Action
from .console import BaseConsole, format_time, parse_name
from .roles import JESTER, SPECIAL_ROLES, VILLAGE, WEREWOLVES, Role

MIN_PLAYERS = 3
MAX_PLAYERS = 20

T = TypeVar("T")


@dataclass(frozen=True)
class GameOptions:
    discussion_seconds: int = 120
    reveal_roles_on_death: bool = True
    first_night_kills: bool = True
    secret_ballot: bool = False

    def describe(self) -> list[str]:
        discussion = (f"{format_time(self.discussion_seconds)} of discussion each day"
                      if self.discussion_seconds else "no discussion timer")
        return [
            discussion,
            "roles revealed when players die" if self.reveal_roles_on_death
            else "roles stay secret until the end",
            "werewolves hunt from the first night" if self.first_night_kills
            else "no werewolf kill on the first night",
            "secret votes" if self.secret_ballot else "open votes",
        ]


class Player:
    def __init__(self, name: str, role: Role):
        self.name = name
        self.role = role
        self.alive = True
        self.lover: Player | None = None
        # Anything a role needs to remember between nights, e.g. who the Witch Doctor protected
        self.memory: dict[str, Any] = {}

    @property
    def is_werewolf(self) -> bool:
        return self.role.team == WEREWOLVES

    def seat(self) -> rules.Seat:
        return rules.Seat(self.name, self.role, self.alive, self.lover.name if self.lover else None)

    def __repr__(self) -> str:
        return f"Player({self.name!r}, {self.role.name})"


class Game:
    def __init__(self, players: list[Player], console: BaseConsole,
                 rng: random.Random | None = None, options: GameOptions | None = None):
        self.players = players
        self.console = console
        self.rng = rng or random.Random()
        self.options = options or GameOptions()
        self.round = 0
        self.winner: str | None = None

    # --- State ---------------------------------------------------------------

    @property
    def living(self) -> list[Player]:
        return [p for p in self.players if p.alive]

    def living_except(self, player: Player) -> list[Player]:
        return [p for p in self.living if p is not player]

    def find(self, name: str) -> Player:
        return next(p for p in self.players if p.name == name)

    @property
    def state(self) -> rules.GameState:
        return rules.GameState(tuple(p.seat() for p in self.players))

    def apply(self, state: rules.GameState) -> None:
        for player in self.players:
            seat = state.seat(player.name)
            player.role = seat.role
            player.alive = seat.alive
            player.lover = self.find(seat.lover) if seat.lover else None

    @property
    def kills_tonight(self) -> bool:
        return self.options.first_night_kills or self.round > 1

    # --- Flow ----------------------------------------------------------------

    def play(self) -> str:
        self.reveal_roles()
        while not self.update_winner():
            self.round += 1
            self.dawn(self.night())
            if self.update_winner():
                break
            if self.options.discussion_seconds:
                self.console.discuss(self.options.discussion_seconds)
            self.vote()
        self.announce_winner()
        assert self.winner is not None
        return self.winner

    def update_winner(self) -> str | None:
        if self.winner is None:
            self.winner = rules.check_winner(self.state)
        return self.winner

    def kill(self, player: Player) -> None:
        player.alive = False
        role = (f"They were the {player.role.name}." if self.options.reveal_roles_on_death
                else "Their role stays secret.")
        self.console.say(f"{player.name} has been eliminated. {role}", style="death")
        player.role.on_death(self, player)
        if player.lover and player.lover.alive:
            self.console.say(f"{player.lover.name} dies of a broken heart.", style="death")
            self.kill(player.lover)

    def private_turn(self, player: Player, action: Callable[[Player], T]) -> T:
        """Hand the device to one player, let them act in secret, then hide the screen."""
        self.console.ask(f"Pass the device to {player.name}. "
                         f"{player.name}, press Enter when only you can see the screen.")
        self.console.say(f"{player.name}, you are the {player.role.name}.", style="secret")
        if player.lover:
            self.console.say(f"You are in love with {player.lover.name}. "
                             "If one of you dies, so does the other.", style="secret")
        result = action(player)
        self.console.ask("Press Enter to hide the screen.")
        self.console.clear()
        return result

    def reveal_roles(self) -> None:
        self.console.say("Each player will now see their role in private.")

        def show(player: Player) -> None:
            self.console.say(player.role.description)
            if player.is_werewolf:
                pack = [p.name for p in self.players if p.is_werewolf and p is not player]
                self.console.say(f"Your pack: {', '.join(pack) or 'just you'}", style="secret")

        for player in self.players:
            self.private_turn(player, show)

    def night(self) -> list[Player]:
        self.console.say(f"\nNight {self.round}. Everyone close your eyes.", style="night")
        actions: list[Action] = []
        for player in self.living:
            action = self.private_turn(player, lambda p: p.role.night_turn(self, p))
            if action:
                actions.append(action)
        return self.resolve_night(actions)

    def resolve_night(self, actions: list[Action]) -> list[Player]:
        """Apply the night's actions using the rules. Returns the players who die tonight."""
        result = rules.resolve_night(self.state, actions, self.rng.choice, self.kills_tonight)
        self.apply(result.state)
        return [self.find(name) for name in result.victims]

    def dawn(self, victims: list[Player]) -> None:
        self.console.say(f"\nDay {self.round}. The village wakes up.", style="day")
        if not victims:
            self.console.say("Nobody was killed last night.")
        for victim in victims:
            if victim.alive:  # may already have died of a broken heart
                self.console.say(f"{victim.name} was attacked by the werewolves.", style="death")
                self.kill(victim)

    def vote(self) -> None:
        self.console.say(f"\nStill alive: {', '.join(p.name for p in self.living)}")
        secret = self.options.secret_ballot
        self.console.say("Time for a secret vote. Each player votes in private." if secret
                         else "Time to vote. Type a name or number, or s to skip.")

        def cast(voter: Player) -> Player | None:
            return self.console.choose_player(f"{voter.name}, who do you vote to eliminate?",
                                              self.living_except(voter), allow_skip=True, who=voter)

        votes = {voter: self.private_turn(voter, cast) if secret else cast(voter)
                 for voter in self.living}

        totals: Counter[str] = Counter()
        for voter, choice in votes.items():
            totals[choice.name if choice else "skip"] += voter.role.vote_weight
        self.console.table("Votes", ["Choice", "Votes"], totals.most_common())

        eliminated = rules.tally_votes(
            {voter.name: choice.name if choice else None for voter, choice in votes.items()},
            {voter.name: voter.role.vote_weight for voter in votes})
        if eliminated is None:
            self.console.say("No one is eliminated today.")
            return

        player = self.find(eliminated)
        self.console.say(f"The village votes out {player.name}.", style="death")
        if player.role.team == JESTER:
            self.winner = JESTER
        self.kill(player)

    def announce_winner(self) -> None:
        messages = {
            VILLAGE: "The villagers win! Every werewolf is gone.",
            WEREWOLVES: "The werewolves win! They now equal or outnumber everyone else.",
            JESTER: "The Jester wins by getting voted out!",
        }
        assert self.winner is not None
        self.console.say(f"Game over. {messages[self.winner]}", style="win")
        self.console.table("Final roles", ["Player", "Role", "Status"],
                           [(p.name, p.role.name, "alive" if p.alive else "eliminated")
                            for p in self.players])


# --- Setup ------------------------------------------------------------------

def ask_names(console: BaseConsole, num_players: int) -> list[str]:
    names: list[str] = []
    while len(names) < num_players:
        names.append(console.ask_until_valid(f"Name of player {len(names) + 1}: ",
                                             lambda answer: parse_name(answer, names)))
    return names


def ask_role_counts(console: BaseConsole, num_players: int) -> dict[str, int]:
    if console.confirm("Use the default roles?"):
        return rules.default_role_counts(num_players)

    while True:
        counts = {}
        remaining = num_players
        for name in ["Werewolf"] + SPECIAL_ROLES:
            counts[name] = console.number(f"{name} count (0-{remaining}): ", 0, remaining)
            remaining -= counts[name]
        error = rules.validate_counts(counts, num_players)
        if error is None:
            return counts
        console.say(f"{error} Let's try again.", style="error")


def ask_options(console: BaseConsole) -> GameOptions:
    default = GameOptions()
    console.say("Default options: " + "; ".join(default.describe()) + ".")
    if console.confirm("Use the default options?"):
        return default
    return GameOptions(
        discussion_seconds=console.number(
            "Discussion time each day, in seconds (0 for none) "
            f"[{default.discussion_seconds}]: ", 0, 3600, default=default.discussion_seconds),
        reveal_roles_on_death=console.confirm("Reveal a player's role when they die?"),
        first_night_kills=console.confirm("Can the werewolves kill on the first night?"),
        secret_ballot=console.confirm("Vote in secret, with each player voting in private?"),
    )


def setup(console: BaseConsole, rng: random.Random | None = None) -> Game:
    rng = rng or random.Random()
    console.say("Welcome to the Werewolf Game!", style="title")
    num_players = console.number(f"How many players? ({MIN_PLAYERS}-{MAX_PLAYERS}): ",
                                 MIN_PLAYERS, MAX_PLAYERS)
    names = ask_names(console, num_players)
    roles = rules.build_roles(ask_role_counts(console, num_players), num_players)
    options = ask_options(console)

    in_play = Counter(role.name for role in roles)
    console.say("Roles in this game: " + ", ".join(f"{count} {name}" for name, count in in_play.items()))
    console.say("Options: " + "; ".join(options.describe()) + ".")

    rng.shuffle(roles)
    players = [Player(name, role) for name, role in zip(names, roles, strict=True)]
    return Game(players, console, rng, options)
