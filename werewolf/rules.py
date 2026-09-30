"""The rules of the game, as pure functions over an immutable game state.

Nothing here reads input, prints, or changes anything in place: every function takes a state and
returns a new one. Randomness comes in through a `choose` function, so the same inputs always
give the same result and the rules are easy to test.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from functools import reduce
from typing import Any

from .actions import Action, Attack, Caught, DrunkSwap, Link, Protect, Swap
from .roles import ROLES, VILLAGE, WEREWOLVES, Role

# Picks one name from a list, e.g. random.Random().choice
Chooser = Callable[[Sequence[str]], str]


@dataclass(frozen=True)
class Seat:
    name: str
    role: Role
    alive: bool = True
    lover: str | None = None

    @property
    def is_werewolf(self) -> bool:
        return self.role.team == WEREWOLVES


@dataclass(frozen=True)
class GameState:
    seats: tuple[Seat, ...]

    def seat(self, name: str) -> Seat:
        return next(s for s in self.seats if s.name == name)

    @property
    def living(self) -> tuple[Seat, ...]:
        return tuple(s for s in self.seats if s.alive)

    def update(self, name: str, **changes: Any) -> GameState:
        """A copy of this state with one seat changed."""
        return GameState(tuple(replace(s, **changes) if s.name == name else s for s in self.seats))


@dataclass(frozen=True)
class NightResult:
    state: GameState
    victims: tuple[str, ...]


# --- Winning and voting -----------------------------------------------------

def check_winner(state: GameState) -> str | None:
    wolves = sum(s.is_werewolf for s in state.living)
    if wolves == 0:
        return VILLAGE
    if wolves >= len(state.living) - wolves:
        return WEREWOLVES
    return None


def tally_votes(votes: Mapping[str, str | None], weights: Mapping[str, int]) -> str | None:
    """Count votes, where `votes` maps each voter's name to their choice (None means skip).

    Returns the name with the most votes, or None on a tie or when skipping wins.
    """
    totals: Counter[str | None] = Counter()
    for voter, choice in votes.items():
        totals[choice] += weights.get(voter, 1)
    ranked = totals.most_common()
    if not ranked or (len(ranked) > 1 and ranked[0][1] == ranked[1][1]):
        return None
    return ranked[0][0]


def pick_attack_target(choices: Sequence[str], choose: Chooser) -> str | None:
    """Each werewolf picks a target; the most-picked one is attacked, ties broken by `choose`."""
    if not choices:
        return None
    totals = Counter(choices)
    best = max(totals.values())
    return choose([name for name, count in totals.items() if count == best])


# --- The night --------------------------------------------------------------

def resolve_night(state: GameState, actions: Sequence[Action], choose: Chooser,
                  kills_allowed: bool = True) -> NightResult:
    """Apply everyone's night actions, in order: lovers, then attacks, then role swaps."""
    state = link_lovers(state, actions)
    state, victims = resolve_attacks(state, actions, choose, kills_allowed)
    state = apply_swaps(state, actions, victims, choose)
    return NightResult(state, victims)


def link_lovers(state: GameState, actions: Sequence[Action]) -> GameState:
    def link(state: GameState, action: Action) -> GameState:
        if not isinstance(action, Link):
            return state
        return state.update(action.first, lover=action.second).update(action.second, lover=action.first)
    return reduce(link, actions, state)


def resolve_attacks(state: GameState, actions: Sequence[Action], choose: Chooser,
                    kills_allowed: bool) -> tuple[GameState, tuple[str, ...]]:
    if not kills_allowed:
        return state, ()

    protected = {a.target for a in actions if isinstance(a, Protect)}
    target = pick_attack_target([a.target for a in actions if isinstance(a, Attack)], choose)
    caught = [a.who for a in actions if isinstance(a, Caught)]

    # The Cursed don't die when attacked; they join the pack
    if target and target not in protected and state.seat(target).role.name == "Cursed":
        state = state.update(target, role=ROLES["Werewolf"])
        target = None

    attacked = ([target] if target else []) + caught
    victims = tuple(dict.fromkeys(name for name in attacked if name not in protected))
    return state, victims


def apply_swaps(state: GameState, actions: Sequence[Action], victims: Sequence[str],
                choose: Chooser) -> GameState:
    def apply(state: GameState, action: Action) -> GameState:
        if isinstance(action, Swap):
            return swap_roles(state, action.first, action.second)
        if isinstance(action, DrunkSwap):
            # The Drunker never swaps with someone who dies tonight
            partners = [s.name for s in state.living if s.name != action.who and s.name not in victims]
            return swap_roles(state, action.who, choose(partners))
        return state
    return reduce(apply, actions, state)


def swap_roles(state: GameState, a: str, b: str) -> GameState:
    role_a, role_b = state.seat(a).role, state.seat(b).role
    return state.update(a, role=role_b).update(b, role=role_a)


# --- Setup ------------------------------------------------------------------

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
