"""A tiny Either type for results that can fail.

A value is either Right(value), meaning success, or Left(error), meaning failure. Chain steps
with `.then`: each step runs only if everything before it succeeded, so the first error falls
straight through to the end. This mirrors pymonad's Either (see monad_concept.py), with types.

    Right("12").then(to_int).then(in_range(3, 20))   # Right(12)
    Right("xx").then(to_int).then(in_range(3, 20))   # Left("not a number")
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")
R = TypeVar("R")


@dataclass(frozen=True)
class Left(Generic[E]):
    error: E

    def map(self, f: Callable[[Any], Any]) -> Left[E]:
        return self

    def then(self, f: Callable[[Any], Any]) -> Left[E]:
        return self

    def either(self, on_left: Callable[[E], R], on_right: Callable[[Any], R]) -> R:
        return on_left(self.error)


@dataclass(frozen=True)
class Right(Generic[T]):
    value: T

    def map(self, f: Callable[[T], U]) -> Right[U]:
        """Transform the value with a function that can't fail."""
        return Right(f(self.value))

    def then(self, f: Callable[[T], Either[E, U]]) -> Either[E, U]:
        """Run the next step, which may fail."""
        return f(self.value)

    def either(self, on_left: Callable[[Any], R], on_right: Callable[[T], R]) -> R:
        return on_right(self.value)


Either = Left[E] | Right[T]


def ensure(check: Callable[[T], bool], error: E) -> Callable[[T], Either[E, T]]:
    """A step that passes the value through if `check` holds, and fails with `error` otherwise."""
    return lambda value: Right(value) if check(value) else Left(error)
