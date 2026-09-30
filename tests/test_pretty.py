import io
import sys
import unittest
from unittest import mock

from werewolf.console import Console, make_console

try:
    from rich.console import Console as RichTerminal

    from werewolf.pretty import RichConsole
except ImportError:
    RichConsole = None


class MakeConsoleTest(unittest.TestCase):
    def test_falls_back_to_plain_console_without_rich(self):
        with mock.patch.dict(sys.modules, {"werewolf.pretty": None}):
            self.assertIsInstance(make_console(), Console)
            self.assertNotEqual(type(make_console()).__name__, "RichConsole")


@unittest.skipIf(RichConsole is None, "rich is not installed")
class RichConsoleTest(unittest.TestCase):
    def setUp(self):
        self.console = RichConsole()
        self.console.terminal = RichTerminal(file=io.StringIO(), width=60, record=True)

    def output(self):
        return self.console.terminal.export_text()

    def test_make_console_uses_rich_when_installed(self):
        self.assertIsInstance(make_console(), RichConsole)

    def test_names_are_not_read_as_markup(self):
        self.console.say("[bold]Bob[/bold] was attacked", style="death")
        self.assertIn("[bold]Bob[/bold] was attacked", self.output())

    def test_title_and_table(self):
        self.console.say("Welcome!", style="title")
        self.console.table("Votes", ["Choice", "Votes"], [("Ann", 2), ("skip", 1)])
        text = self.output()
        for expected in ("Welcome!", "Votes", "Choice", "Ann", "skip"):
            self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()
