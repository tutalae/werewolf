import random
import unittest

from tests.scripted import make_players
from werewolf.game import (
    build_roles,
    check_winner,
    default_role_counts,
    pick_attack_target,
    tally_votes,
    validate_counts,
)
from werewolf.roles import VILLAGE, WEREWOLVES


class CheckWinnerTest(unittest.TestCase):
    def test_village_wins_when_no_werewolves_left(self):
        players = make_players("A:Werewolf", "B:Villager", "C:Villager")
        players[0].alive = False
        self.assertEqual(check_winner(players), VILLAGE)

    def test_werewolves_win_at_parity(self):
        players = make_players("A:Werewolf", "B:Villager", "C:Villager")
        players[1].alive = False
        self.assertEqual(check_winner(players), WEREWOLVES)

    def test_game_continues_while_werewolves_are_outnumbered(self):
        players = make_players("A:Werewolf", "B:Seer", "C:Villager")
        self.assertIsNone(check_winner(players))

    def test_special_roles_count_as_non_werewolves(self):
        players = make_players("A:Werewolf", "B:Jester", "C:Hunter")
        self.assertIsNone(check_winner(players))


class TallyVotesTest(unittest.TestCase):
    def setUp(self):
        self.a, self.b, self.c, self.d = make_players("A:Villager", "B:Villager", "C:Villager",
                                                      "D:Mayor")

    def test_most_votes_is_eliminated(self):
        votes = {self.a: self.c, self.b: self.c, self.c: self.a}
        self.assertIs(tally_votes(votes), self.c)

    def test_tie_eliminates_no_one(self):
        votes = {self.a: self.b, self.b: self.a}
        self.assertIsNone(tally_votes(votes))

    def test_skip_can_win(self):
        votes = {self.a: None, self.b: None, self.c: self.a}
        self.assertIsNone(tally_votes(votes))

    def test_mayor_vote_counts_twice(self):
        votes = {self.a: self.b, self.b: self.a, self.d: self.b}
        self.assertIs(tally_votes(votes), self.b)

    def test_no_votes(self):
        self.assertIsNone(tally_votes({}))


class RoleSetupTest(unittest.TestCase):
    def test_build_roles_fills_with_villagers(self):
        names = [r.name for r in build_roles({"Werewolf": 1, "Seer": 1}, 5)]
        self.assertEqual(sorted(names), ["Seer", "Villager", "Villager", "Villager", "Werewolf"])

    def test_default_counts_are_valid(self):
        for n in range(3, 21):
            self.assertIsNone(validate_counts(default_role_counts(n), n), n)

    def test_validate_counts(self):
        self.assertIn("at least one", validate_counts({"Werewolf": 0}, 5))
        self.assertIn("only 3 players", validate_counts({"Werewolf": 1, "Seer": 3}, 3))
        self.assertIn("outnumbered", validate_counts({"Werewolf": 2}, 4))
        self.assertIsNone(validate_counts({"Werewolf": 1, "Hunter": 1}, 4))


class PickAttackTargetTest(unittest.TestCase):
    def test_majority_choice_wins(self):
        a, b = make_players("A:Villager", "B:Villager")
        self.assertIs(pick_attack_target([a, b, a], random.Random(0)), a)

    def test_no_choices(self):
        self.assertIsNone(pick_attack_target([], random.Random(0)))


if __name__ == "__main__":
    unittest.main()
