import unittest

from werewolf.roles import SPECIAL_ROLES
from werewolf.simulate import simulate


class SimulateTest(unittest.TestCase):
    def test_bot_games_always_finish(self):
        winners = simulate({"Werewolf": 2, **{role: 1 for role in SPECIAL_ROLES}}, 16, games=50)
        self.assertEqual(sum(winners.values()), 50)

    def test_same_seed_gives_same_results(self):
        counts = {"Werewolf": 1, "Seer": 1}
        self.assertEqual(simulate(counts, 6, 30, seed=3), simulate(counts, 6, 30, seed=3))


if __name__ == "__main__":
    unittest.main()
