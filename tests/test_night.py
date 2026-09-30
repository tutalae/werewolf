import unittest

from tests.scripted import make_game


class ResolveNightTest(unittest.TestCase):
    def setUp(self):
        self.game, _ = make_game([], "Wolf:Werewolf", "Doc:Witch Doctor", "Seer:Seer",
                                 "Drunk:Drunker", "Vil:Villager")
        self.wolf, self.doc, self.seer, self.drunk, self.vil = self.game.players

    def test_attack_kills_target(self):
        self.assertEqual(self.game.resolve_night([("attack", self.vil)]), [self.vil])

    def test_protected_target_survives_and_stays_human(self):
        victims = self.game.resolve_night([("protect", self.vil), ("attack", self.vil)])
        self.assertEqual(victims, [])
        self.assertEqual(self.vil.role.name, "Villager")

    def test_protected_player_who_was_not_attacked_becomes_werewolf(self):
        self.game.resolve_night([("protect", self.seer), ("attack", self.vil)])
        self.assertEqual(self.seer.role.name, "Werewolf")

    def test_troublemaker_swap(self):
        self.game.resolve_night([("swap", self.seer, self.vil)])
        self.assertEqual((self.seer.role.name, self.vil.role.name), ("Villager", "Seer"))

    def test_drunk_never_swaps_with_tonights_victim(self):
        for seed in range(20):
            game, _ = make_game([], "Wolf:Werewolf", "Drunk:Drunker", "Vil:Villager", seed=seed)
            wolf, drunk, vil = game.players
            game.resolve_night([("attack", vil), ("drunk_swap", drunk)])
            self.assertEqual(vil.role.name, "Villager")
            self.assertEqual(wolf.role.name, "Drunker")


if __name__ == "__main__":
    unittest.main()
