import unittest

from werewolf.console import ask_int, ask_player, ask_yes_no
from werewolf.game import ask_names

from tests.scripted import ScriptedConsole, make_players


class InputTest(unittest.TestCase):
    def test_ask_int_asks_again_until_valid(self):
        console = ScriptedConsole(["abc", "-1", "99", "4"])
        self.assertEqual(ask_int(console, "n: ", 3, 20), 4)

    def test_ask_yes_no(self):
        self.assertTrue(ask_yes_no(ScriptedConsole(["maybe", "Y"]), "?"))
        self.assertFalse(ask_yes_no(ScriptedConsole(["no"]), "?"))

    def test_ask_player_ignores_case_and_allows_skip(self):
        ann, bob = make_players("Ann:Villager", "Bob:Villager")
        self.assertIs(ask_player(ScriptedConsole(["nobody", "BOB"]), "?", [ann, bob]), bob)
        self.assertIsNone(ask_player(ScriptedConsole(["skip"]), "?", [ann], allow_skip=True))

    def test_ask_player_rejects_skip_when_not_allowed(self):
        ann, = make_players("Ann:Villager")
        self.assertIs(ask_player(ScriptedConsole(["skip", "ann"]), "?", [ann]), ann)

    def test_ask_names_rejects_duplicates_empty_and_skip(self):
        console = ScriptedConsole(["Ann", "ann", "", "skip", "Bob"])
        self.assertEqual(ask_names(console, 2), ["Ann", "Bob"])
        self.assertIn("ann is already taken.", console.output)


if __name__ == "__main__":
    unittest.main()
