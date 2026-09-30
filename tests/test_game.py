"""Full scripted games, from role reveal to the winner."""

import random
import unittest

from tests.scripted import ScriptedConsole, make_game
from werewolf.game import GameOptions, setup
from werewolf.roles import JESTER, SPECIAL_ROLES, VILLAGE, WEREWOLVES
from werewolf.rules import default_role_counts


class FullGameTest(unittest.TestCase):
    def test_werewolves_win_by_reaching_parity_overnight(self):
        # Night 1: the wolf kills Bob, leaving 1 wolf vs 1 villager. No day vote happens.
        game, console = make_game(["bob"], "Ann:Werewolf", "Bob:Villager", "Cat:Villager")
        self.assertEqual(game.play(), WEREWOLVES)
        self.assertNotIn("Time to vote", console.text)

    def test_village_wins_by_voting_out_the_werewolf(self):
        answers = ["bob",                   # Ann (wolf) attacks Bob
                   "cat", "ann", "ann"]     # Ann, Cat and Dan vote
        game, console = make_game(answers, "Ann:Werewolf", "Bob:Villager", "Cat:Villager",
                                  "Dan:Villager")
        self.assertEqual(game.play(), VILLAGE)
        self.assertIn("Votes: Ann 2, Cat 1", console.output)

    def test_jester_wins_when_voted_out(self):
        answers = ["bob",                        # Ann (wolf) attacks Bob
                   "jo", "ann", "jo", "jo"]      # Ann, Jo, Dan and Eve vote
        game, _ = make_game(answers, "Ann:Werewolf", "Bob:Villager", "Jo:Jester", "Dan:Villager",
                            "Eve:Villager")
        self.assertEqual(game.play(), JESTER)

    def test_hunter_shoots_when_killed(self):
        answers = ["hal",                   # Ann (wolf) attacks Hal the Hunter
                   "ann"]                   # Hal shoots Ann on the way out
        game, console = make_game(answers, "Ann:Werewolf", "Hal:Hunter", "Cat:Villager",
                                  "Dan:Villager")
        self.assertEqual(game.play(), VILLAGE)
        self.assertIn("Hal shoots Ann!", console.output)

    def test_tied_vote_eliminates_no_one(self):
        answers = ["bob",                   # night 1: Ann attacks Bob
                   "cat", "ann", "skip",    # Ann, Cat, Dan vote: tie between Cat and Ann and skip
                   "cat"]                   # night 2: Ann attacks Cat -> parity
        game, console = make_game(answers, "Ann:Werewolf", "Bob:Villager", "Cat:Villager",
                                  "Dan:Villager")
        self.assertEqual(game.play(), WEREWOLVES)
        self.assertIn("No one is eliminated today.", console.output)

    def test_lovers_die_together(self):
        answers = ["ann", "bob",             # Cupid links Ann and Bob (Cupid's turn comes first)
                   "ann"]                    # the wolf attacks Ann; Bob dies of a broken heart
        game, console = make_game(answers, "Cu:Cupid", "Wolf:Werewolf", "Ann:Villager",
                                  "Bob:Villager")
        self.assertEqual(game.play(), WEREWOLVES)
        self.assertIn("Bob dies of a broken heart.", console.output)

    def test_discussion_happens_before_each_vote(self):
        answers = ["bob", "cat", "ann", "ann"]
        game, console = make_game(answers, "Ann:Werewolf", "Bob:Villager", "Cat:Villager",
                                  "Dan:Villager", discussion_seconds=90)
        game.play()
        discuss = console.output.index("<discuss 90>")
        self.assertLess(discuss, console.output.index("Time to vote. Type a name or number, or s to skip."))

    def test_no_discussion_when_set_to_zero(self):
        game, console = make_game(["bob", "cat", "ann", "ann"], "Ann:Werewolf", "Bob:Villager",
                                  "Cat:Villager", "Dan:Villager")
        game.play()
        self.assertFalse(any(line.startswith("<discuss") for line in console.output))

    def test_roles_only_shown_in_private_turns(self):
        game, console = make_game(["bob"], "Ann:Werewolf", "Bob:Villager", "Cat:Villager")
        game.play()
        # Every "you are the ..." line sits between a hand-off prompt and a screen clear
        private = False
        for line in console.output:
            if line.startswith("Pass the device"):
                private = True
            elif line == "<clear>":
                private = False
            elif "you are the" in line:
                self.assertTrue(private, line)

    def test_setup_with_default_roles(self):
        console = ScriptedConsole(["x", "6", "Ann", "Bob", "Cat", "Dan", "Eve", "Fay", "yes", "yes"])
        game = setup(console, random.Random(1))
        names = sorted(p.role.name for p in game.players)
        expected = default_role_counts(6)
        for role, count in expected.items():
            self.assertEqual(names.count(role), count, role)
        self.assertEqual(game.options, GameOptions())

    def test_setup_with_custom_roles_retries_invalid_counts(self):
        # 4 players: first try 2 wolves (invalid), then 1 wolf + 1 Mayor
        roles_asked = 1 + len(SPECIAL_ROLES)
        mayor = SPECIAL_ROLES.index("Mayor") + 1
        first_try = ["2"] + ["0"] * (roles_asked - 1)
        second_try = ["1"] + ["0"] * (roles_asked - 1)
        second_try[mayor] = "1"
        options = ["no", "0", "no", "no", "yes"]  # custom: no timer, hide roles, peaceful night 1, secret
        custom = ["no"] + first_try + second_try + options
        console = ScriptedConsole(["4", "Ann", "Bob", "Cat", "Dan"] + custom)
        game = setup(console, random.Random(1))
        self.assertEqual(sorted(p.role.name for p in game.players),
                         ["Mayor", "Villager", "Villager", "Werewolf"])
        self.assertIn("outnumbered", console.text)
        self.assertEqual(game.options, GameOptions(discussion_seconds=0, reveal_roles_on_death=False,
                                                   first_night_kills=False, secret_ballot=True))


class OptionsTest(unittest.TestCase):
    def test_roles_stay_secret_on_death_when_option_is_off(self):
        game, console = make_game(["bob", "cat", "ann", "ann"], "Ann:Werewolf", "Bob:Villager",
                                  "Cat:Villager", "Dan:Villager", reveal_roles_on_death=False)
        game.play()
        self.assertIn("Bob has been eliminated. Their role stays secret.", console.output)
        self.assertNotIn("They were the", console.text)
        self.assertIn("Final roles: Ann Werewolf eliminated, Bob Villager eliminated, "
                      "Cat Villager alive, Dan Villager alive", console.output)

    def test_no_kill_on_first_night(self):
        answers = ["cat", "ann", "ann", "ann"]   # day 1: Ann, Bob, Cat, Dan vote Ann out
        game, console = make_game(answers, "Ann:Werewolf", "Bob:Villager", "Cat:Villager",
                                  "Dan:Villager", first_night_kills=False)
        self.assertEqual(game.play(), VILLAGE)
        self.assertIn("Nobody was killed last night.", console.output)

    def test_secret_ballot_votes_in_private(self):
        answers = ["bob", "cat", "ann", "ann"]
        game, console = make_game(answers, "Ann:Werewolf", "Bob:Villager", "Cat:Villager",
                                  "Dan:Villager", secret_ballot=True)
        self.assertEqual(game.play(), VILLAGE)
        self.assertIn("Time for a secret vote. Each player votes in private.", console.output)
        # Each vote prompt comes right after that voter is handed the device
        for voter in ("Ann", "Cat", "Dan"):
            prompt = next(i for i, line in enumerate(console.output)
                          if line.startswith(f"{voter}, who do you vote"))
            handoff = max(i for i, line in enumerate(console.output[:prompt])
                          if line.startswith("Pass the device"))
            self.assertTrue(console.output[handoff].startswith(f"Pass the device to {voter}."))
            self.assertNotIn("<clear>", console.output[handoff:prompt])


if __name__ == "__main__":
    unittest.main()
