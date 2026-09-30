import unittest

from tests.scripted import make_game


class ResolveNightTest(unittest.TestCase):
    def setUp(self):
        self.game, _ = make_game([], "Wolf:Werewolf", "Doc:Witch Doctor", "Seer:Seer",
                                 "Drunk:Drunker", "Vil:Villager")
        self.wolf, self.doc, self.seer, self.drunk, self.vil = self.game.players

    def test_attack_kills_target(self):
        self.assertEqual(self.game.resolve_night([("attack", self.vil)]), [self.vil])

    def test_protected_target_survives(self):
        victims = self.game.resolve_night([("protect", self.vil), ("attack", self.vil)])
        self.assertEqual(victims, [])

    def test_protection_does_not_change_roles(self):
        self.game.resolve_night([("protect", self.seer), ("attack", self.vil)])
        self.assertEqual(self.seer.role.name, "Seer")

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

    def test_cupid_links_lovers(self):
        self.game.resolve_night([("link", self.seer, self.vil)])
        self.assertIs(self.seer.lover, self.vil)
        self.assertIs(self.vil.lover, self.seer)

    def test_cursed_joins_werewolves_instead_of_dying(self):
        game, _ = make_game([], "Wolf:Werewolf", "Cur:Cursed", "Vil:Villager", "Dan:Villager")
        cursed = game.players[1]
        self.assertEqual(game.resolve_night([("attack", cursed)]), [])
        self.assertTrue(cursed.is_werewolf)

    def test_caught_little_girl_dies_unless_protected(self):
        game, _ = make_game([], "Wolf:Werewolf", "Girl:Little Girl", "Vil:Villager",
                            "Dan:Villager")
        wolf, girl, vil, dan = game.players
        self.assertEqual(game.resolve_night([("attack", vil), ("caught", girl)]), [vil, girl])
        self.assertEqual(game.resolve_night([("protect", girl), ("caught", girl)]), [])


class RoleTurnTest(unittest.TestCase):
    def test_witch_doctor_cannot_protect_same_player_twice_in_a_row(self):
        game, console = make_game(["yes", "vil", "yes", "vil", "wolf"],
                                  "Wolf:Werewolf", "Doc:Witch Doctor", "Vil:Villager")
        doc = game.players[1]
        self.assertEqual(doc.role.night_turn(game, doc), ("protect", game.players[2]))
        # Second night: "vil" isn't offered, so the doctor is asked again and picks Wolf
        self.assertEqual(doc.role.night_turn(game, doc), ("protect", game.players[0]))
        self.assertIn("You protected Vil last night, so you can't protect them again.",
                      console.output)

    def test_seer_sees_lycan_as_werewolf(self):
        game, console = make_game(["ly"], "Wolf:Werewolf", "Seer:Seer", "Ly:Lycan",
                                  "Dan:Villager")
        seer = game.players[1]
        seer.role.night_turn(game, seer)
        self.assertIn("Ly IS a werewolf.", console.output)

    def test_cupid_only_acts_on_first_night(self):
        game, _ = make_game(["ann", "bob"], "Wolf:Werewolf", "Cu:Cupid", "Ann:Villager",
                            "Bob:Villager")
        cupid = game.players[1]
        game.round = 1
        self.assertEqual(cupid.role.night_turn(game, cupid),
                         ("link", game.players[2], game.players[3]))
        game.round = 2
        self.assertIsNone(cupid.role.night_turn(game, cupid))

    def test_little_girl_learns_a_werewolf(self):
        game, console = make_game(["yes"], "Wolf:Werewolf", "Girl:Little Girl", "Vil:Villager")
        girl = game.players[1]
        girl.role.night_turn(game, girl)
        self.assertIn("You spot Wolf among the werewolves.", console.output)


if __name__ == "__main__":
    unittest.main()
