import random

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

    def seer_inspect(self, target):
        print(f"{self.name}, the Seer, is inspecting {target.name}...")

        if target.role == 'Werewolf':
            print(f"{target.name} is a Werewolf!")
        else:
            print(f"{target.name} is not a Werewolf!")

    def vote_out(self, target):
        print(f"{self.name} votes to eliminate {target.name}!")

    def display_status(self):
        status = "Survived" if self.survived else "Eliminated"
        print(f"{self.name} ({self.role}): {status}")

class WerewolfGame:
    def __init__(self):
        self.players = []

    def intro(self):
        print("Welcome to the Werewolf Game!")

        num_players = int(input("Enter the number of players: "))

        # Create players and add them to the list
        for i in range(num_players):
            player_name = input(f"Enter the name of Player {i + 1}: ")
            self.players.append(Player(player_name, 'Unknown'))

        # Call assign_roles to assign roles to players
        self.assign_roles(num_players)

    def assign_roles(self, num_players):
        roles = ['Villager'] * num_players
        num_werewolves = min(2, num_players // 4)  # Adjusted for the addition of Seer

        werewolves_indices = random.sample(range(num_players), num_werewolves)
        for index in werewolves_indices:
            roles[index] = 'Werewolf'

        # Assign the role of Seer
        villager_indices = [i for i, role in enumerate(roles) if role == 'Villager']
        if villager_indices:
            seer_index = random.choice(villager_indices)
            roles[seer_index] = 'Seer'
            print(f"The Seer is {self.players[seer_index].name}")

        # Ensure there is exactly one Seer
        seer_count = roles.count('Seer')
        while seer_count != 1:
            # Reassign the role of Seer
            seer_index = random.choice([i for i, role in enumerate(roles) if role == 'Villager'])
            roles[seer_index] = 'Seer'
            seer_count = roles.count('Seer')

        # Assign roles to players
        for i, role in enumerate(roles):
            self.players[i].role = role

        # Print roles before returning
        for i, role in enumerate(roles):
            print(f"{self.players[i].name}: {role}")

        return roles

    def night_phase(self):
        print("\nNight phase:")

        # Count the number of werewolves
        num_werewolves = sum(1 for player in self.players if player.survived and player.role == 'Werewolf')
        num_villagers = sum(1 for player in self.players if player.survived and player.role == 'Villager')

        if num_werewolves == 0 or num_werewolves >= num_villagers:
            print("Game over! Werewolves have taken over or no werewolves left.")
            return

        # Seer action
        seer = next((player for player in self.players if player.survived and player.role == 'Seer'), None)
        if seer:
            target_name = input(f"{seer.name}, the Seer, choose a player to inspect: ")
            target = next((p for p in self.players if p.name == target_name and p.survived), None)

            if target:
                seer.seer_inspect(target)
            else:
                print("Invalid target. The Seer chooses not to inspect anyone.")

        # Werewolf actions
        if num_werewolves >= 2:
            # If there are two or more werewolves, they collectively choose one target
            werewolves = [player for player in self.players if player.survived and player.role == 'Werewolf']
            target_name = input("Werewolves, collectively choose a player to attack: ")
            target = next((p for p in self.players if p.name == target_name and p.survived), None)

            if target:
                for werewolf in werewolves:
                    werewolf.werewolf_attack(target)
            else:
                print("Invalid target. The werewolves attack a random player.")
                target = random.choice([p for p in self.players if p.survived])
                for werewolf in werewolves:
                    werewolf.werewolf_attack(target)
        else:
            # Each werewolf chooses a target to attack
            for player in self.players:
                if player.survived and player.role == 'Werewolf':
                    target_name = input(f"{player.name}, choose a player to attack: ")
                    target = next((p for p in self.players if p.name == target_name and p.survived), None)

                    if target:
                        player.werewolf_attack(target)
                    else:
                        print("Invalid target. The werewolf attacks a random player.")
                        target = random.choice([p for p in self.players if p != player and p.survived])
                        player.werewolf_attack(target)

    def day_phase(self):
        print("\nDay phase:")
        votes = {player: 0 for player in self.players if player.survived}

        # Simulate the voting
        print("Players, collectively choose a player to vote out:")
        target_name = input("Enter the name of the player you want to vote out: ")
        target = next((p for p in self.players if p.name == target_name and p.survived), None)

        if target:
            for player in self.players:
                if player.survived:
                    player.vote_out(target)
                    votes[target] += 1
        else:
            print("Invalid target. No one is voted out this round.")

        # Eliminate the player with the most votes
        max_votes_player = max(votes, key=votes.get)
        print(f"\n{max_votes_player.name} has been voted out!\n")
        max_votes_player.survived = False

    def display_survivors(self):
        print("\nSurvivors:")
        for player in self.players:
            player.display_status()

    def play(self):
        round_number = 1
        while True:
            print(f"\nNight {round_number}:")
            self.night_phase()

            # Check if the game should continue
            remaining_players = [player for player in self.players if player.survived]
            if len(remaining_players) <= 1:
                break

            # Display status after each night
            for player in self.players:
                player.display_status()

            print(f"\nNumber of people survived after Night {round_number}: {len(remaining_players)}\n")

            # Reveal the identities of the werewolves
            werewolves = [player.name for player in self.players if player.role == 'Werewolf']
            print("Werewolves revealed:", ", ".join(werewolves), "\n")

            # Day phase
            self.day_phase()

            # Count and display the number of players for each role
            num_werewolves = sum(1 for player in self.players if player.survived and player.role == 'Werewolf')
            num_villagers = sum(1 for player in self.players if player.survived and player.role == 'Villager')
            num_seer = sum(1 for player in self.players if player.survived and player.role == 'Seer')

            # Check if the game should continue
            remaining_players = [player for player in self.players if player.survived]
            if num_werewolves == num_villagers:
                break
            if num_werewolves == 0:
                break

            print(f"\nNumber of Werewolves: {num_werewolves}")
            print(f"Number of Villagers: {num_villagers}")
            print(f"Number of Seers: {num_seer}")

            round_number += 1

if __name__ == "__main__":
    game = WerewolfGame()
    game.intro()
    game.play()
