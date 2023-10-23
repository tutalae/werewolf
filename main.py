import random
import time

class Player:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.health = 100
        self.survived = True

    def werewolf_attack(self):
        print_slow(f"Oh no! {self.name}, a werewolf is attacking!")
        outcome = random.choice([f"{self.name}, you fend off the werewolf and survive.",
                                 f"{self.name}, the werewolf bites you. Game over!"])
        print_slow(outcome)
        if "Game over" in outcome:
            self.survived = False

    def display_status(self):
        print_slow(f"{self.name}, your current health: {self.health}\n")


class WerewolfGame:
    def __init__(self):
        self.players = []

    def assign_roles(self, num_players):
        roles = ['Villager'] * num_players
        num_werewolves = min(2, num_players // 3)

        for _ in range(num_werewolves):
            index = random.randint(0, num_players - 1)
            roles[index] = 'Werewolf'

        return roles

    def intro(self):
        print_slow("Welcome to the Werewolf Game!")

        num_players = int(input("Enter the number of players: "))

        player_names = []
        roles = self.assign_roles(num_players)

        for i in range(num_players):
            name = input(f"Enter the name of Player {i + 1}: ")
            player = Player(name, roles[i])
            self.players.append(player)

        print_slow("Roles have been assigned:")
        for player in self.players:
            print(f"{player.name}: {player.role}")

        print_slow("It's a full moon night, and rumors are spreading about werewolves.")
        print_slow("Your goal is to survive until morning. Good luck!\n")

    def play(self):
        while True:
            for player in self.players:
                if player.survived:
                    player.werewolf_attack()

                    if not player.survived:
                        print_slow(f"{player.name}, your health has reached zero. Game over!")

                    player.display_status()

            # Check if the game should continue
            remaining_players = [player for player in self.players if player.survived]
            if len(remaining_players) <= 1:
                break

if __name__ == "__main__":
    game = WerewolfGame()
    game.intro()
    game.play()
