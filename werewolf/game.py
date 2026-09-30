"""Game state, rules, and the night/day loop."""

import random
from collections import Counter

from .console import ask_int, ask_player, ask_yes_no
from .roles import JESTER, ROLES, SPECIAL_ROLES, VILLAGE, WEREWOLVES

MIN_PLAYERS = 3
MAX_PLAYERS = 20


class Player:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.alive = True

    @property
    def is_werewolf(self):
        return self.role.team == WEREWOLVES

    def __repr__(self):
        return f"Player({self.name!r}, {self.role.name})"


# --- Rules ------------------------------------------------------------------
# Plain functions with no input or output, so they are easy to test.

def default_role_counts(num_players):
    """A sensible mix of roles for a quick game."""
    counts = {"Werewolf": max(1, min(2, num_players // 3))}
    if num_players >= 5:
        counts["Seer"] = 1
    return counts


def validate_counts(counts, num_players):
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


def build_roles(counts, num_players):
    """Turn {role name: count} into a list of roles, filling the rest with Villagers."""
    roles = [ROLES[name] for name, count in counts.items() for _ in range(count)]
    return roles + [ROLES["Villager"]] * (num_players - len(roles))


def check_winner(players):
    alive = [p for p in players if p.alive]
    wolves = sum(p.is_werewolf for p in alive)
    if wolves == 0:
        return VILLAGE
    if wolves >= len(alive) - wolves:
        return WEREWOLVES
    return None


def tally_votes(votes):
    """Count votes, where `votes` maps each voter to their choice (None means skip).

    Returns the player with the most votes, or None on a tie or when skipping wins.
    """
    totals = Counter()
    for voter, choice in votes.items():
        totals[choice] += voter.role.vote_weight
    ranked = totals.most_common()
    if not ranked or (len(ranked) > 1 and ranked[0][1] == ranked[1][1]):
        return None
    return ranked[0][0]


def pick_attack_target(choices, rng):
    """Each werewolf picks a target; the most-picked one is attacked, ties broken at random."""
    if not choices:
        return None
    totals = Counter(choices)
    best = max(totals.values())
    return rng.choice([target for target, count in totals.items() if count == best])


def swap_roles(a, b):
    a.role, b.role = b.role, a.role


# --- Game -------------------------------------------------------------------

class Game:
    def __init__(self, players, console, rng=None):
        self.players = players
        self.console = console
        self.rng = rng or random.Random()
        self.round = 0
        self.winner = None

    @property
    def living(self):
        return [p for p in self.players if p.alive]

    def living_except(self, player):
        return [p for p in self.living if p is not player]

    def play(self):
        self.reveal_roles()
        while not self.update_winner():
            self.round += 1
            self.dawn(self.night())
            if self.update_winner():
                break
            self.vote()
        self.announce_winner()
        return self.winner

    def update_winner(self):
        if self.winner is None:
            self.winner = check_winner(self.players)
        return self.winner

    def kill(self, player):
        player.alive = False
        self.console.say(f"{player.name} has been eliminated. They were the {player.role.name}.")
        player.role.on_death(self, player)

    def private_turn(self, player, action):
        """Hand the device to one player, let them act in secret, then hide the screen."""
        self.console.ask(f"Pass the device to {player.name}. "
                         f"{player.name}, press Enter when only you can see the screen.")
        self.console.say(f"{player.name}, you are the {player.role.name}.")
        result = action(player)
        self.console.ask("Press Enter to hide the screen.")
        self.console.clear()
        return result

    def reveal_roles(self):
        self.console.say("Each player will now see their role in private.")

        def show(player):
            self.console.say(player.role.description)
            if player.is_werewolf:
                pack = [p.name for p in self.players if p.is_werewolf and p is not player]
                self.console.say(f"Your pack: {', '.join(pack) or 'just you'}")

        for player in self.players:
            self.private_turn(player, show)

    def night(self):
        self.console.say(f"\nNight {self.round}. Everyone close your eyes.")
        actions = []
        for player in self.living:
            action = self.private_turn(player, lambda p: p.role.night_turn(self, p))
            if action:
                actions.append(action)
        return self.resolve_night(actions)

    def resolve_night(self, actions):
        """Apply everyone's night actions. Returns the players the werewolves killed."""
        protected = {action[1] for action in actions if action[0] == "protect"}
        target = pick_attack_target([a[1] for a in actions if a[0] == "attack"], self.rng)
        victims = [target] if target and target not in protected else []

        # The Witch Doctor's protection turns anyone who wasn't attacked into a werewolf
        for player in protected:
            if player is not target:
                player.role = ROLES["Werewolf"]

        for action in actions:
            if action[0] == "drunk_swap":
                drunk = action[1]
                partner = self.rng.choice(
                    [p for p in self.living_except(drunk) if p not in victims])
                swap_roles(drunk, partner)
            elif action[0] == "swap":
                swap_roles(action[1], action[2])

        return victims

    def dawn(self, victims):
        self.console.say(f"\nDay {self.round}. The village wakes up.")
        if not victims:
            self.console.say("Nobody was killed last night.")
        for victim in victims:
            self.console.say(f"{victim.name} was attacked by the werewolves.")
            self.kill(victim)

    def vote(self):
        self.console.say(f"\nStill alive: {', '.join(p.name for p in self.living)}")
        self.console.say("Time to vote. Type a name, or skip.")
        votes = {}
        for voter in self.living:
            votes[voter] = ask_player(self.console, f"{voter.name}, who do you vote to eliminate?",
                                      self.living_except(voter), allow_skip=True)

        totals = Counter()
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

    def announce_winner(self):
        messages = {
            VILLAGE: "The villagers win! Every werewolf is gone.",
            WEREWOLVES: "The werewolves win! They now equal or outnumber everyone else.",
            JESTER: "The Jester wins by getting voted out!",
        }
        self.console.say(f"\nGame over. {messages[self.winner]}")
        self.console.say("Final roles:")
        for player in self.players:
            status = "alive" if player.alive else "eliminated"
            self.console.say(f"  {player.name}: {player.role.name} ({status})")


# --- Setup ------------------------------------------------------------------

def ask_names(console, num_players):
    names = []
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


def ask_role_counts(console, num_players):
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


def setup(console, rng=None):
    rng = rng or random.Random()
    console.say("Welcome to the Werewolf Game!")
    num_players = ask_int(console, f"How many players? ({MIN_PLAYERS}-{MAX_PLAYERS}): ",
                          MIN_PLAYERS, MAX_PLAYERS)
    names = ask_names(console, num_players)
    roles = build_roles(ask_role_counts(console, num_players), num_players)

    in_play = Counter(role.name for role in roles)
    console.say("Roles in this game: " + ", ".join(f"{count} {name}" for name, count in in_play.items()))

    rng.shuffle(roles)
    return Game([Player(name, role) for name, role in zip(names, roles)], console, rng)
