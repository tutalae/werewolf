"""Every role in the game: its team, how much its vote counts, and what it does at night.

To add a role, subclass Role, override what it does differently, and add it to ALL_ROLES.
"""

from .console import ask_player, ask_yes_no

VILLAGE = "Village"
WEREWOLVES = "Werewolves"
JESTER = "Jester"


class Role:
    name = "Villager"
    team = VILLAGE
    description = "You have no special power. Find the werewolves and vote them out."
    vote_weight = 1

    def night_turn(self, game, player):
        """Take this role's private turn at night.

        Returns an action tuple for Game.resolve_night, or None.
        """
        game.console.say("You have nothing to do tonight. Sleep well.")
        return None

    def on_death(self, game, player):
        """Called right after a player holding this role is eliminated."""

    def __repr__(self):
        return self.name


class Villager(Role):
    pass


class Werewolf(Role):
    name = "Werewolf"
    team = WEREWOLVES
    description = ("Each night, choose someone to attack. "
                   "You win when werewolves equal or outnumber everyone else.")

    def night_turn(self, game, player):
        pack = [p.name for p in game.living if p.is_werewolf and p is not player]
        if pack:
            game.console.say(f"Your pack: {', '.join(pack)}")
        prey = [p for p in game.living if not p.is_werewolf]
        return ("attack", ask_player(game.console, "Choose a player to attack", prey))


class Seer(Role):
    name = "Seer"
    description = "Each night, learn whether one player is a werewolf."

    def night_turn(self, game, player):
        target = ask_player(game.console, "Choose a player to inspect", game.living_except(player))
        verdict = "IS a werewolf" if target.is_werewolf else "is not a werewolf"
        game.console.say(f"{target.name} {verdict}.")
        return None


class WitchDoctor(Role):
    name = "Witch Doctor"
    description = ("Each night, you may protect one player from the werewolves. "
                   "If the player you protect is not attacked, they turn into a werewolf.")

    def night_turn(self, game, player):
        if not ask_yes_no(game.console, "Do you want to protect someone tonight?"):
            return None
        return ("protect", ask_player(game.console, "Choose a player to protect", game.living))


class Drunker(Role):
    name = "Drunker"
    description = "Each night, you may swap your role with a random player."

    def night_turn(self, game, player):
        if ask_yes_no(game.console, "Do you want to swap roles with a random player?"):
            return ("drunk_swap", player)
        return None


class Troublemaker(Role):
    name = "Troublemaker"
    description = "Each night, you may swap the roles of two other players."

    def night_turn(self, game, player):
        if not ask_yes_no(game.console, "Do you want to swap two players' roles?"):
            return None
        others = game.living_except(player)
        first = ask_player(game.console, "First player", others)
        second = ask_player(game.console, "Second player", [p for p in others if p is not first])
        return ("swap", first, second)


class Mayor(Role):
    name = "Mayor"
    description = "Your vote counts twice."
    vote_weight = 2


class Hunter(Role):
    name = "Hunter"
    description = "When you are eliminated, you take one last shot at another player."

    def on_death(self, game, player):
        if not game.living:
            return
        game.console.say(f"{player.name} was the Hunter and takes one last shot!")
        target = ask_player(game.console, f"{player.name}, who do you shoot?", game.living,
                            allow_skip=True)
        if target:
            game.console.say(f"{player.name} shoots {target.name}!")
            game.kill(target)


class Jester(Role):
    name = "Jester"
    team = JESTER
    description = "You win if the village votes you out."


ALL_ROLES = [Werewolf(), Villager(), Seer(), WitchDoctor(), Drunker(), Troublemaker(), Mayor(),
             Hunter(), Jester()]
ROLES = {role.name: role for role in ALL_ROLES}

# Roles you can add when setting up a custom game; everyone left over is a Villager
SPECIAL_ROLES = [role.name for role in ALL_ROLES if role.name not in ("Werewolf", "Villager")]
