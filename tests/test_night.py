"""Roles' night turns, and the game applying the rules' results to real players."""

import unittest

from tests.scripted import make_game
from werewolf.actions import Attack, Caught, Link, Protect, Swap


class GameResolveNightTest(unittest.TestCase):
    def test_victims_come_back_as_players(self):
        game, _ = make_game([], "Wolf:Werewolf", "Vil:Villager", "Dan:Villager")
        self.assertEqual(game.resolve_night([Attack("Vil")]), [game.players[1]])

    def test_swaps_and_lovers_are_applied_to_players(self):
        game, _ = make_game([], "Wolf:Werewolf", "Seer:Seer", "Vil:Villager", "Dan:Villager")
        wolf, seer, vil, dan = game.players
        game.resolve_night([Swap("Seer", "Vil"), Link("Vil", "Dan")])
        self.assertEqual((seer.role.name, vil.role.name), ("Villager", "Seer"))
        self.assertIs(vil.lover, dan)
        self.assertIs(dan.lover, vil)

    def test_first_night_is_peaceful_when_option_is_off(self):
        game, _ = make_game([], "Wolf:Werewolf", "Girl:Little Girl", "Vil:Villager",
                            first_night_kills=False)
        game.round = 1
        self.assertEqual(game.resolve_night([Attack("Vil"), Caught("Girl")]), [])
        game.round = 2
        self.assertEqual(game.resolve_night([Attack("Vil")]), [game.players[2]])


class RoleTurnTest(unittest.TestCase):
    def test_witch_doctor_cannot_protect_same_player_twice_in_a_row(self):
        game, console = make_game(["yes", "vil", "yes", "vil", "wolf"],
                                  "Wolf:Werewolf", "Doc:Witch Doctor", "Vil:Villager")
        doc = game.players[1]
        self.assertEqual(doc.role.night_turn(game, doc), Protect("Vil"))
        # Second night: "vil" isn't offered, so the doctor is asked again and picks Wolf
        self.assertEqual(doc.role.night_turn(game, doc), Protect("Wolf"))
        self.assertIn("You protected Vil last night, so you can't protect them again.",
                      console.output)

    def test_seer_sees_lycan_as_werewolf(self):
        game, console = make_game(["ly"], "Wolf:Werewolf", "Seer:Seer", "Ly:Lycan",
                                  "Dan:Villager")
        seer = game.players[1]
        seer.role.night_turn(game, seer)
        self.assertIn("Ly IS a werewolf.", console.output)
        self.assertEqual(seer.memory["inspected"], {"Ly": True})

    def test_cupid_only_acts_on_first_night(self):
        game, _ = make_game(["ann", "bob"], "Wolf:Werewolf", "Cu:Cupid", "Ann:Villager",
                            "Bob:Villager")
        cupid = game.players[1]
        game.round = 1
        self.assertEqual(cupid.role.night_turn(game, cupid), Link("Ann", "Bob"))
        game.round = 2
        self.assertIsNone(cupid.role.night_turn(game, cupid))

    def test_little_girl_learns_a_werewolf(self):
        game, console = make_game(["yes"], "Wolf:Werewolf", "Girl:Little Girl", "Vil:Villager")
        girl = game.players[1]
        girl.role.night_turn(game, girl)
        self.assertIn("You spot Wolf among the werewolves.", console.output)
        self.assertEqual(girl.memory["spotted"], {"Wolf"})

    def test_werewolf_does_not_hunt_on_peaceful_first_night(self):
        game, console = make_game([], "Wolf:Werewolf", "Vil:Villager", "Dan:Villager",
                                  first_night_kills=False)
        game.round = 1
        wolf = game.players[0]
        self.assertIsNone(wolf.role.night_turn(game, wolf))
        self.assertIn("It's the first night. The pack meets, but doesn't hunt yet.", console.output)


if __name__ == "__main__":
    unittest.main()
