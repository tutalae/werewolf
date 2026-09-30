"""Game state, rules, and the night/day loop."""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from .console import ConsoleLike, ask_int, ask_player, ask_yes_no, format_time
from .roles import JESTER, ROLES, SPECIAL_ROLES, VILLAGE, WEREWOLVES, Action, Role

MIN_PLAYERS = 3
MAX_PLAYERS = 20
DEFAULT_DISCUSSION_SECONDS = 120


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

    def __repr__(self) -> str:
        return f"Player({self.name!r}, {self.role.name})"


# --- Rules ------------------------------------------------------------------
# Plain functions with no input or output, so they are easy to test.

# Default role mixes, as (smallest player count, roles). Everyone else is a Villager.
# Tuned with `python -m werewolf.simulate` so bot games come out close to even.
DEFAULT_MIXES = [
    (3, {"Werewolf": 1, "Seer": 1, "Witch Doctor": 1}),
    (5, {"Werewolf": 1, "Seer": 1, "Witch Doctor": 1, "Hunter": 1}),
    (8, {"Werewolf": 1, "Seer": 1, "Witch Doctor": 1}),
    (12, {"Werewolf": 2, "Seer": 1, "Witch Doctor": 1, "Hunter": 1, "Little Girl": 1, "Mayor": 1}),
]


def default_role_counts(num_players: int) -> dict[str, int]:
    mix = [counts for smallest, counts in DEFAULT_MIXES if num_players >= smallest][-1]
    return dict(mix)


def validate_counts(counts: Mapping[str, int], num_players: int) -> str | None:
    """Returns an error message, or None if the role counts work for this many players."""
    wolves = counts.get("Werewolf", 0)
    total = sum(counts.values())
    if wolves < 1:
        return "There must be at least one werewolf."
    if total > num_players:
        return f"That's {total} roles for only {num_players} players."
    if wolves >= num_players - wolves:
        return "Werewolves must start outnumbered, or they win immediately."
    return None


def build_roles(counts: Mapping[str, int], num_players: int) -> list[Role]:
    """Turn {role name: count} into a list of roles, filling the rest with Villagers."""
    roles = [ROLES[name] for name, count in counts.items() for _ in range(count)]
    return roles + [ROLES["Villager"]] * (num_players - len(roles))


def check_winner(players: Sequence[Player]) -> str | None:
    alive = [p for p in players if p.alive]
    wolves = sum(p.is_werewolf for p in alive)
    if wolves == 0:
        return VILLAGE
    if wolves >= len(alive) - wolves:
        return WEREWOLVES
    return None


def tally_votes(votes: Mapping[Player, Player | None]) -> Player | None:
    """Count votes, where `votes` maps each voter to their choice (None means skip).

    Returns the player with the most votes, or None on a tie or when skipping wins.
    """
    totals: Counter[Player | None] = Counter()
    for voter, choice in votes.items():
        totals[choice] += voter.role.vote_weight
    ranked = totals.most_common()
    if not ranked or (len(ranked) > 1 and ranked[0][1] == ranked[1][1]):
        return None
    return ranked[0][0]


def pick_attack_target(choices: Sequence[Player], rng: random.Random) -> Player | None:
    """Each werewolf picks a target; the most-picked one is attacked, ties broken at random."""
    if not choices:
        return None
    totals = Counter(choices)
    best = max(totals.values())
    return rng.choice([target for target, count in totals.items() if count == best])


def swap_roles(a: Player, b: Player) -> None:
    a.role, b.role = b.role, a.role


# --- Game -------------------------------------------------------------------

class Game:
    def __init__(self, players: list[Player], console: ConsoleLike,
                 rng: random.Random | None = None,
                 discussion_seconds: int = 0):
        self.players = players
        self.console = console
        self.rng = rng or random.Random()
        self.discussion_seconds = discussion_seconds
        self.round = 0
        self.winner: str | None = None

    @property
    def living(self) -> list[Player]:
        return [p for p in self.players if p.alive]

    def living_except(self, player: Player) -> list[Player]:
        return [p for p in self.living if p is not player]

    def play(self) -> str:
        self.reveal_roles()
        while not self.update_winner():
            self.round += 1
            self.dawn(self.night())
            if self.update_winner():
                break
            if self.discussion_seconds:
                self.console.discuss(self.discussion_seconds)
            self.vote()
        self.announce_winner()
        assert self.winner is not None
        return self.winner

    def update_winner(self) -> str | None:
        if self.winner is None:
            self.winner = check_winner(self.players)
        return self.winner

    def kill(self, player: Player) -> None:
        player.alive = False
        self.console.say(f"{player.name} has been eliminated. They were the {player.role.name}.")
        player.role.on_death(self, player)
        if player.lover and player.lover.alive:
            self.console.say(f"{player.lover.name} dies of a broken heart.")
            self.kill(player.lover)

    def private_turn(self, player: Player, action: Callable[[Player], Action]) -> Action:
        """Hand the device to one player, let them act in secret, then hide the screen."""
        self.console.ask(f"Pass the device to {player.name}. "
                         f"{player.name}, press Enter when only you can see the screen.")
        self.console.say(f"{player.name}, you are the {player.role.name}.")
        if player.lover:
            self.console.say(f"You are in love with {player.lover.name}. "
                             "If one of you dies, so does the other.")
        result = action(player)
        self.console.ask("Press Enter to hide the screen.")
        self.console.clear()
        return result

    def reveal_roles(self) -> None:
        self.console.say("Each player will now see their role in private.")

        def show(player: Player) -> Action:
            self.console.say(player.role.description)
            if player.is_werewolf:
                pack = [p.name for p in self.players if p.is_werewolf and p is not player]
                self.console.say(f"Your pack: {', '.join(pack) or 'just you'}")
            return None

        for player in self.players:
            self.private_turn(player, show)

    def night(self) -> list[Player]:
        self.console.say(f"\nNight {self.round}. Everyone close your eyes.")
        actions = []
        for player in self.living:
            action = self.private_turn(player, lambda p: p.role.night_turn(self, p))
            if action:
                actions.append(action)
        return self.resolve_night(actions)

    def resolve_night(self, actions: Sequence[tuple[Any, ...]]) -> list[Player]:
        """Apply everyone's night actions. Returns the players who die tonight."""
        for kind, *who in actions:
            if kind == "link":
                first, second = who
                first.lover, second.lover = second, first

        protected = {who[0] for kind, *who in actions if kind == "protect"}
        target = pick_attack_target([who[0] for kind, *who in actions if kind == "attack"],
                                    self.rng)
        caught = [who[0] for kind, *who in actions if kind == "caught"]

        victims: list[Player] = []
        if target and target not in protected:
            # The Cursed don't die when attacked; they join the pack
            if target.role.name == "Cursed":
                target.role = ROLES["Werewolf"]
            else:
                victims.append(target)
        victims += [p for p in caught if p not in protected and p not in victims]

        for kind, *who in actions:
            if kind == "drunk_swap":
                drunk = who[0]
                partner = self.rng.choice(
                    [p for p in self.living_except(drunk) if p not in victims])
                swap_roles(drunk, partner)
            elif kind == "swap":
                swap_roles(*who)

        return victims

    def dawn(self, victims: Sequence[Player]) -> None:
        self.console.say(f"\nDay {self.round}. The village wakes up.")
        if not victims:
            self.console.say("Nobody was killed last night.")
        for victim in victims:
            if victim.alive:  # may already have died of a broken heart
                self.console.say(f"{victim.name} was attacked by the werewolves.")
                self.kill(victim)

    def vote(self) -> None:
        self.console.say(f"\nStill alive: {', '.join(p.name for p in self.living)}")
        self.console.say("Time to vote. Type a name, or skip.")
        votes = {}
        for voter in self.living:
            votes[voter] = ask_player(self.console, f"{voter.name}, who do you vote to eliminate?",
                                      self.living_except(voter), allow_skip=True)

        totals: Counter[str] = Counter()
        for voter, choice in votes.items():
            totals[choice.name if choice else "skip"] += voter.role.vote_weight
        self.console.say("Votes: " + ", ".join(f"{name} {count}" for name, count in totals.most_common()))

        eliminated = tally_votes(votes)
        if eliminated is None:
            self.console.say("No one is eliminated today.")
            return

        self.console.say(f"The village votes out {eliminated.name}.")
        if eliminated.role.team == JESTER:
            self.winner = JESTER
        self.kill(eliminated)

    def announce_winner(self) -> None:
        messages = {
            VILLAGE: "The villagers win! Every werewolf is gone.",
            WEREWOLVES: "The werewolves win! They now equal or outnumber everyone else.",
            JESTER: "The Jester wins by getting voted out!",
        }
        assert self.winner is not None
        self.console.say(f"\nGame over. {messages[self.winner]}")
        self.console.say("Final roles:")
        for player in self.players:
            status = "alive" if player.alive else "eliminated"
            self.console.say(f"  {player.name}: {player.role.name} ({status})")


# --- Setup ------------------------------------------------------------------

def ask_names(console: ConsoleLike, num_players: int) -> list[str]:
    names: list[str] = []
    while len(names) < num_players:
        name = console.ask(f"Name of player {len(names) + 1}: ").strip()
        if not name:
            console.say("Names can't be empty.")
        elif name.lower() == "skip":
            console.say("'skip' is used for voting, so pick another name.")
        elif name.lower() in (n.lower() for n in names):
            console.say(f"{name} is already taken.")
        else:
            names.append(name)
    return names


def ask_role_counts(console: ConsoleLike, num_players: int) -> dict[str, int]:
    if ask_yes_no(console, "Use the default roles?"):
        return default_role_counts(num_players)

    while True:
        counts = {}
        remaining = num_players
        for name in ["Werewolf"] + SPECIAL_ROLES:
            counts[name] = ask_int(console, f"{name} count (0-{remaining}): ", 0, remaining)
            remaining -= counts[name]
        error = validate_counts(counts, num_players)
        if error is None:
            return counts
        console.say(f"{error} Let's try again.")


def setup(console: ConsoleLike, rng: random.Random | None = None) -> Game:
    rng = rng or random.Random()
    console.say("Welcome to the Werewolf Game!")
    num_players = ask_int(console, f"How many players? ({MIN_PLAYERS}-{MAX_PLAYERS}): ",
                          MIN_PLAYERS, MAX_PLAYERS)
    names = ask_names(console, num_players)
    roles = build_roles(ask_role_counts(console, num_players), num_players)
    discussion = ask_int(console, "Discussion time each day, in seconds (0 for none) "
                         f"[{DEFAULT_DISCUSSION_SECONDS}]: ", 0, 3600,
                         default=DEFAULT_DISCUSSION_SECONDS)

    in_play = Counter(role.name for role in roles)
    console.say("Roles in this game: " + ", ".join(f"{count} {name}" for name, count in in_play.items()))
    if discussion:
        console.say(f"Each day starts with {format_time(discussion)} of discussion.")

    rng.shuffle(roles)
    players = [Player(name, role) for name, role in zip(names, roles, strict=False)]
    return Game(players, console, rng, discussion_seconds=discussion)
