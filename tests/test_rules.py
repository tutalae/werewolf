"""The pure rules, tested directly on immutable game states."""

import random
import unittest

from werewolf import rules
from werewolf.actions import Attack, Caught, DrunkSwap, Link, Protect, Swap
from werewolf.roles import ROLES, VILLAGE, WEREWOLVES


def state(*specs, dead=()):
    """state("Ann:Werewolf", "Bob:Villager", dead=["Bob"])"""
    seats = []
    for spec in specs:
        name, role = spec.split(":")
        seats.append(rules.Seat(name, ROLES[role], alive=name not in dead))
    return rules.GameState(tuple(seats))


def first(names):
    return sorted(names)[0]


class GameStateTest(unittest.TestCase):
    def test_update_returns_a_new_state(self):
        before = state("Ann:Werewolf", "Bob:Villager")
        after = before.update("Bob", alive=False)
        self.assertTrue(before.seat("Bob").alive)
        self.assertFalse(after.seat("Bob").alive)

    def test_seats_are_immutable(self):
        seat = state("Ann:Werewolf").seat("Ann")
        with self.assertRaises(AttributeError):
            seat.alive = False


class CheckWinnerTest(unittest.TestCase):
    def test_village_wins_when_no_werewolves_left(self):
        s = state("A:Werewolf", "B:Villager", "C:Villager", dead=["A"])
        self.assertEqual(rules.check_winner(s), VILLAGE)

    def test_werewolves_win_at_parity(self):
        s = state("A:Werewolf", "B:Villager", "C:Villager", dead=["B"])
        self.assertEqual(rules.check_winner(s), WEREWOLVES)

    def test_game_continues_while_werewolves_are_outnumbered(self):
        self.assertIsNone(rules.check_winner(state("A:Werewolf", "B:Seer", "C:Villager")))

    def test_special_roles_count_as_non_werewolves(self):
        self.assertIsNone(rules.check_winner(state("A:Werewolf", "B:Jester", "C:Hunter")))


class TallyVotesTest(unittest.TestCase):
    def test_most_votes_is_eliminated(self):
        self.assertEqual(rules.tally_votes({"A": "C", "B": "C", "C": "A"}, {}), "C")

    def test_tie_eliminates_no_one(self):
        self.assertIsNone(rules.tally_votes({"A": "B", "B": "A"}, {}))

    def test_skip_can_win(self):
        self.assertIsNone(rules.tally_votes({"A": None, "B": None, "C": "A"}, {}))

    def test_weighted_vote_breaks_tie(self):
        self.assertEqual(rules.tally_votes({"A": "B", "B": "A", "D": "B"}, {"D": 2}), "B")

    def test_no_votes(self):
        self.assertIsNone(rules.tally_votes({}, {}))


class ResolveNightTest(unittest.TestCase):
    def setUp(self):
        self.state = state("Wolf:Werewolf", "Doc:Witch Doctor", "Seer:Seer", "Drunk:Drunker",
                           "Vil:Villager", "Cur:Cursed")

    def night(self, *actions, kills_allowed=True):
        return rules.resolve_night(self.state, actions, first, kills_allowed)

    def test_attack_kills_target(self):
        self.assertEqual(self.night(Attack("Vil")).victims, ("Vil",))

    def test_attack_does_not_change_the_input_state(self):
        self.night(Attack("Cur"), Swap("Seer", "Vil"))
        self.assertEqual(self.state.seat("Cur").role.name, "Cursed")
        self.assertEqual(self.state.seat("Seer").role.name, "Seer")

    def test_protected_target_survives(self):
        self.assertEqual(self.night(Protect("Vil"), Attack("Vil")).victims, ())

    def test_protection_does_not_change_roles(self):
        result = self.night(Protect("Seer"), Attack("Vil"))
        self.assertEqual(result.state.seat("Seer").role.name, "Seer")

    def test_split_pack_picks_most_chosen_target(self):
        self.assertEqual(self.night(Attack("Vil"), Attack("Seer"), Attack("Vil")).victims, ("Vil",))

    def test_troublemaker_swap(self):
        result = self.night(Swap("Seer", "Vil"))
        self.assertEqual(result.state.seat("Seer").role.name, "Villager")
        self.assertEqual(result.state.seat("Vil").role.name, "Seer")

    def test_drunk_never_swaps_with_tonights_victim(self):
        for seed in range(20):
            s = state("Wolf:Werewolf", "Drunk:Drunker", "Vil:Villager")
            result = rules.resolve_night(s, [Attack("Vil"), DrunkSwap("Drunk")],
                                         random.Random(seed).choice)
            self.assertEqual(result.state.seat("Vil").role.name, "Villager")
            self.assertEqual(result.state.seat("Wolf").role.name, "Drunker")

    def test_cupid_links_lovers(self):
        result = self.night(Link("Seer", "Vil"))
        self.assertEqual(result.state.seat("Seer").lover, "Vil")
        self.assertEqual(result.state.seat("Vil").lover, "Seer")

    def test_cursed_joins_werewolves_instead_of_dying(self):
        result = self.night(Attack("Cur"))
        self.assertEqual(result.victims, ())
        self.assertTrue(result.state.seat("Cur").is_werewolf)

    def test_caught_little_girl_dies_unless_protected(self):
        self.assertEqual(self.night(Attack("Vil"), Caught("Seer")).victims, ("Vil", "Seer"))
        self.assertEqual(self.night(Protect("Seer"), Caught("Seer")).victims, ())

    def test_no_kills_when_not_allowed(self):
        result = self.night(Attack("Vil"), Caught("Seer"), Swap("Seer", "Vil"), kills_allowed=False)
        self.assertEqual(result.victims, ())
        self.assertEqual(result.state.seat("Vil").role.name, "Seer")  # other actions still happen


class RoleSetupTest(unittest.TestCase):
    def test_build_roles_fills_with_villagers(self):
        names = [r.name for r in rules.build_roles({"Werewolf": 1, "Seer": 1}, 5)]
        self.assertEqual(sorted(names), ["Seer", "Villager", "Villager", "Villager", "Werewolf"])

    def test_default_counts_are_valid(self):
        for n in range(3, 21):
            self.assertIsNone(rules.validate_counts(rules.default_role_counts(n), n), n)

    def test_validate_counts(self):
        self.assertIn("at least one", rules.validate_counts({"Werewolf": 0}, 5))
        self.assertIn("only 3 players", rules.validate_counts({"Werewolf": 1, "Seer": 3}, 3))
        self.assertIn("outnumbered", rules.validate_counts({"Werewolf": 2}, 4))
        self.assertIsNone(rules.validate_counts({"Werewolf": 1, "Hunter": 1}, 4))


if __name__ == "__main__":
    unittest.main()
