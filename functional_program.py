import random
from pymonad.either import Left, Right

# Set to True to print every player's role (useful for debugging)
SHOW_ROLES = False

class Player:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.survived = True

    def werewolf_attack(self, target):
        print(f"Oh no! {self.name}, a werewolf is attacking {target.name}!")

        # Simplified: Werewolf attack outcome is now deterministic (instant death)
        print(f"{target.name} is bitten by the werewolf. Game over!")
        target.survived = False

    def vote_out(self, target):
        print(f"{self.name} votes to eliminate {target.name}!")

    def display_status(self):
        status = "Survived" if self.survived else "Eliminated"
        print(f"{self.name} ({self.role}): {status}")

class WerewolfGame:
    def __init__(self):
        self.players = []

    def assign_roles(self, num_players):
        roles = ['Villager'] * num_players
        num_werewolves = min(2, num_players // 3)

        werewolves_indices = random.sample(range(num_players), num_werewolves)
        for index in werewolves_indices:
            roles[index] = 'Werewolf'

        return roles

    def intro(self):
        print("Welcome to the Werewolf Game!")

        num_players = int(input("Enter the number of players: "))

        player_names = []
        roles = self.assign_roles(num_players)

        for i in range(num_players):
            name = input(f"Enter the name of Player {i + 1}: ")
            player = Player(name, roles[i])
            self.players.append(player)

        print("\nRoles have been assigned.")
        if SHOW_ROLES:
            for player in self.players:
                print(f"{player.name}: {player.role}")

        print("\nIt's a full moon night, and the werewolves are on the hunt.\n")

    def check_winner(self):
        num_werewolves = sum(1 for player in self.players if player.survived and player.role == 'Werewolf')
        num_villagers = sum(1 for player in self.players if player.survived and player.role != 'Werewolf')

        if num_werewolves == 0:
            return 'Villagers'
        if num_werewolves >= num_villagers:
            return 'Werewolves'
        return None

    def find_target(self, target_name):
        # Werewolves can only attack living non-werewolves
        return next((p for p in self.players
                     if p.name == target_name and p.survived and p.role != 'Werewolf'), None)

    def random_target(self):
        return random.choice([p for p in self.players if p.survived and p.role != 'Werewolf'])

    def night_phase(self):
        print("\nNight phase:")

        num_werewolves = sum(1 for player in self.players if player.survived and player.role == 'Werewolf')

        if num_werewolves >= 2:
            # If there are two or more werewolves, they collectively choose one target
            werewolves = [player for player in self.players if player.survived and player.role == 'Werewolf']
            target_name = input("Werewolves, collectively choose a player to attack: ")
            target = self.find_target(target_name)

            if target:
                for werewolf in werewolves:
                    werewolf.werewolf_attack(target)
            else:
                print("Invalid target. The werewolves attack a random player.")
                target = self.random_target()
                for werewolf in werewolves:
                    werewolf.werewolf_attack(target)
        else:
            # The lone werewolf chooses a target to attack
            werewolf = next(p for p in self.players if p.survived and p.role == 'Werewolf')
            target_name = input(f"{werewolf.name}, choose a player to attack: ")
            target = self.find_target(target_name)

            if target:
                werewolf.werewolf_attack(target)
            else:
                print("Invalid target. The werewolf attacks a random player.")
                werewolf.werewolf_attack(self.random_target())

    def day_phase(self):
        print("\nDay phase:")
        votes = {player: 0 for player in self.players if player.survived}

        # Simulate the voting
        print("Players, collectively choose a player to vote out:")
        target_name = input("Enter the name of the player you want to vote out: ")

        # Validate the target name
        target = next((p for p in self.players if p.name == target_name and p.survived), None)
        if not target:
            return Left("Invalid target. No one is voted out this round.")

        # Perform the voting
        for player in self.players:
            if player.survived:
                player.vote_out(target)
                votes[target] += 1

        # Eliminate the player with the most votes
        max_votes_player = max(votes, key=votes.get)
        print(f"\n{max_votes_player.name} has been voted out!\n")
        max_votes_player.survived = False

        return Right("Voting successful")

    def display_survivors(self):
        print("\nSurvivors:")
        for player in self.players:
            player.display_status()

    def play(self):
        round_number = 1
        winner = self.check_winner()
        while winner is None:
            print(f"\nNight {round_number}:")
            self.night_phase()

            # Display status after each night
            for player in self.players:
                player.display_status()

            remaining_players = [player for player in self.players if player.survived]
            print(f"\nNumber of people survived after Night {round_number}: {len(remaining_players)}\n")

            winner = self.check_winner()
            if winner:
                break

            # Day phase
            self.day_phase()

            # Display survivors after each day
            self.display_survivors()

            winner = self.check_winner()
            if winner:
                break

            num_werewolves = sum(1 for player in self.players if player.survived and player.role == 'Werewolf')
            num_villagers = sum(1 for player in self.players if player.survived and player.role != 'Werewolf')
            print(f"\nNumber of Werewolves: {num_werewolves}")
            print(f"Number of Villagers: {num_villagers}")

            round_number += 1

        print(f"\nGame over! The {winner} win!")
        werewolves = [player.name for player in self.players if player.role == 'Werewolf']
        print("The werewolves were:", ", ".join(werewolves))

if __name__ == "__main__":
    game = WerewolfGame()
    game.intro()
    game.play()
