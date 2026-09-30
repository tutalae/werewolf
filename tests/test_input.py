import unittest

from tests.scripted import ScriptedConsole, make_players
from werewolf.console import parse_int, parse_name, parse_player, parse_yes_no
from werewolf.either import Left, Right
from werewolf.game import ask_names


class ParseTest(unittest.TestCase):
    def test_parse_int(self):
        self.assertEqual(parse_int("4", 3, 20), Right(4))
        self.assertEqual(parse_int(" 20 ", 3, 20), Right(20))
        for bad in ("abc", "-1", "99", ""):
            self.assertEqual(parse_int(bad, 3, 20), Left("Please enter a whole number from 3 to 20."))

    def test_parse_int_default_on_blank(self):
        self.assertEqual(parse_int("", 0, 600, default=120), Right(120))
        self.assertEqual(parse_int("30", 0, 600, default=120), Right(30))

    def test_parse_yes_no(self):
        self.assertEqual(parse_yes_no("Y"), Right(True))
        self.assertEqual(parse_yes_no("no"), Right(False))
        self.assertIsInstance(parse_yes_no("maybe"), Left)

    def test_parse_player_by_name_number_or_skip(self):
        ann, bob = make_players("Ann:Villager", "Bob:Villager")
        self.assertEqual(parse_player("BOB", [ann, bob]), Right(bob))
        self.assertEqual(parse_player("1", [ann, bob]), Right(ann))
        self.assertEqual(parse_player("3", [ann, bob]), Left("Pick a number from 1 to 2."))
        self.assertEqual(parse_player("s", [ann], allow_skip=True), Right(None))
        self.assertEqual(parse_player("skip", [ann]), Left("That isn't one of the choices."))

    def test_parse_name(self):
        self.assertEqual(parse_name(" Ann ", []), Right("Ann"))
        self.assertEqual(parse_name("", []), Left("Names can't be empty."))
        self.assertEqual(parse_name("42", []), Left("Names can't be just a number."))
        self.assertEqual(parse_name("Skip", []), Left("'Skip' is used for skipping, so pick another name."))
        self.assertEqual(parse_name("ann", ["Ann"]), Left("ann is already taken."))


class ConsoleTest(unittest.TestCase):
    def test_number_asks_again_until_valid(self):
        console = ScriptedConsole(["abc", "-1", "99", "4"])
        self.assertEqual(console.number("n: ", 3, 20), 4)
        self.assertEqual(console.output.count("Please enter a whole number from 3 to 20."), 3)

    def test_confirm(self):
        self.assertTrue(ScriptedConsole(["maybe", "Y"]).confirm("?"))
        self.assertFalse(ScriptedConsole(["no"]).confirm("?"))

    def test_choose_player_shows_numbered_choices(self):
        ann, bob = make_players("Ann:Villager", "Bob:Villager")
        console = ScriptedConsole(["nobody", "2"])
        self.assertIs(console.choose_player("Pick", [ann, bob], allow_skip=True), bob)
        self.assertEqual(console.output[0], "Pick (1 Ann, 2 Bob, s skip): ")

    def test_ask_names_rejects_bad_names(self):
        console = ScriptedConsole(["Ann", "ann", "", "skip", "7", "Bob"])
        self.assertEqual(ask_names(console, 2), ["Ann", "Bob"])
        self.assertIn("ann is already taken.", console.output)

    def test_plain_table_lines_up_columns(self):
        console = ScriptedConsole()
        super(ScriptedConsole, console).table("Votes", ["Choice", "Votes"], [("Ann", 2), ("skip", 10)])
        self.assertEqual(console.output, ["Votes:", "  Choice  Votes", "  Ann     2", "  skip    10"])


if __name__ == "__main__":
    unittest.main()
