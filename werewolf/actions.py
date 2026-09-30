"""What players do at night. Roles create these; rules.resolve_night applies them.

Actions refer to players by name, so the rules never touch the mutable Player objects.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Attack:
    target: str


@dataclass(frozen=True)
class Protect:
    target: str


@dataclass(frozen=True)
class Link:
    """Cupid makes two players lovers."""
    first: str
    second: str


@dataclass(frozen=True)
class Caught:
    """The Little Girl was caught peeking."""
    who: str


@dataclass(frozen=True)
class DrunkSwap:
    who: str


@dataclass(frozen=True)
class Swap:
    first: str
    second: str


Action = Attack | Protect | Link | Caught | DrunkSwap | Swap
