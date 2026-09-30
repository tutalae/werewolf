"""Every role in the game: its team, how much its vote counts, and what it does at night.

To add a role, subclass Role, override what it does differently, and add it to ALL_ROLES.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .console import ask_player, ask_yes_no

if TYPE_CHECKING:
    from .game import Game, Player

# An action a role takes at night, e.g. ("attack", target). Game.resolve_night applies them.
Action = tuple[Any, ...] | None

VILLAGE = "Village"
WEREWOLVES = "Werewolves"
JESTER = "Jester"

# Chance the Little Girl is caught when she peeks
LITTLE_GIRL_CATCH_CHANCE = 0.25


class Role:
    name = "Villager"
    team = VILLAGE
    description = "You have no special power. Find the werewolves and vote them out."
    vote_weight = 1

    @property
    def looks_like_werewolf(self) -> bool:
        """What the Seer sees."""
        return self.team == WEREWOLVES

    def night_turn(self, game: Game, player: Player) -> Action:
        """Take this role's private turn at night. Returns an action, or None."""
        game.console.say("You have nothing to do tonight. Sleep well.")
        return None

    def on_death(self, game: Game, player: Player) -> None:
        """Called right after a player holding this role is eliminated."""

    def __repr__(self) -> str:
        return self.name


class Villager(Role):
    pass


class Werewolf(Role):
    name = "Werewolf"
    team = WEREWOLVES
    description = ("Each night, choose someone to attack. "
                   "You win when werewolves equal or outnumber everyone else.")

    def night_turn(self, game: Game, player: Player) -> Action:
        pack = [p.name for p in game.living if p.is_werewolf and p is not player]
        if pack:
            game.console.say(f"Your pack: {', '.join(pack)}")
        prey = [p for p in game.living if not p.is_werewolf]
        return ("attack", ask_player(game.console, "Choose a player to attack", prey))


class Seer(Role):
    name = "Seer"
    description = "Each night, learn whether one player is a werewolf."

    def night_turn(self, game: Game, player: Player) -> Action:
        target = ask_player(game.console, "Choose a player to inspect", game.living_except(player))
        verdict = "IS a werewolf" if target.role.looks_like_werewolf else "is not a werewolf"
        game.console.say(f"{target.name} {verdict}.")
        return None


class WitchDoctor(Role):
    name = "Witch Doctor"
    description = ("Each night, you may protect one player (yourself included) from the "
                   "werewolves, but not the same player two nights in a row.")

    def night_turn(self, game: Game, player: Player) -> Action:
        last = player.memory.get("last_protected")
        player.memory["last_protected"] = None
        if not ask_yes_no(game.console, "Do you want to protect someone tonight?"):
            return None
        if last is not None and last.alive:
            game.console.say(f"You protected {last.name} last night, so you can't protect them again.")
        choices = [p for p in game.living if p is not last]
        target = ask_player(game.console, "Choose a player to protect", choices)
        player.memory["last_protected"] = target
        return ("protect", target)


class Drunker(Role):
    name = "Drunker"
    description = "Each night, you may swap your role with a random player."

    def night_turn(self, game: Game, player: Player) -> Action:
        if ask_yes_no(game.console, "Do you want to swap roles with a random player?"):
            return ("drunk_swap", player)
        return None


class Troublemaker(Role):
    name = "Troublemaker"
    description = "Each night, you may swap the roles of two other players."

    def night_turn(self, game: Game, player: Player) -> Action:
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

    def on_death(self, game: Game, player: Player) -> None:
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


class Cupid(Role):
    name = "Cupid"
    description = ("On the first night, choose two lovers. If one of them dies, "
                   "the other dies of a broken heart.")

    def night_turn(self, game: Game, player: Player) -> Action:
        if game.round != 1:
            return super().night_turn(game, player)
        first = ask_player(game.console, "Choose the first lover", game.living)
        second = ask_player(game.console, "Choose the second lover",
                            [p for p in game.living if p is not first])
        return ("link", first, second)


class LittleGirl(Role):
    name = "Little Girl"
    description = ("Each night, you may peek to learn the name of one werewolf, "
                   f"but there's a {LITTLE_GIRL_CATCH_CHANCE:.0%} chance they catch and kill you.")

    def night_turn(self, game: Game, player: Player) -> Action:
        wolves = [p for p in game.living if p.is_werewolf]
        if not wolves or not ask_yes_no(game.console, "Do you want to peek at the werewolves?"):
            return None
        game.console.say(f"You spot {game.rng.choice(wolves).name} among the werewolves.")
        if game.rng.random() < LITTLE_GIRL_CATCH_CHANCE:
            return ("caught", player)
        return None


class Lycan(Role):
    name = "Lycan"
    description = "You're on the village's side, but the Seer sees you as a werewolf."

    @property
    def looks_like_werewolf(self) -> bool:
        return True


class Cursed(Role):
    name = "Cursed"
    description = ("You're on the village's side, but if the werewolves attack you, "
                   "you don't die: you join them.")


ALL_ROLES = [Werewolf(), Villager(), Seer(), WitchDoctor(), Drunker(), Troublemaker(), Mayor(),
             Hunter(), Jester(), Cupid(), LittleGirl(), Lycan(), Cursed()]
ROLES = {role.name: role for role in ALL_ROLES}

# Roles you can add when setting up a custom game; everyone left over is a Villager
SPECIAL_ROLES = [role.name for role in ALL_ROLES if role.name not in ("Werewolf", "Villager")]
