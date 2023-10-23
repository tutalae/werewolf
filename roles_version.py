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
        num_wolves = int(input("Enter the number of wolves: "))
        num_villagers = int(input("Enter the number of villagers: "))
        num_seers = int(input("Enter the number of seers: "))
        num_jesters = int(input("Enter the number of jesters: "))
        num_drunkers = int(input("Enter the number of drunkers: "))

        # Validate input
        if (
            num_players < num_wolves + num_villagers + num_seers + num_jesters + num_drunkers
            or num_wolves < 1
            or num_villagers < 0
            or num_seers < 0
            or num_jesters < 0
            or num_drunkers < 0
        ):
            print("Invalid input. Please ensure the numbers are correct.")
            return

        # Create players and add them to the list
        for i in range(num_wolves):
            player_name = input(f"Enter the name of Wolf {i + 1}: ")
            self.players.append(Player(player_name, 'Werewolf'))

        for i in range(num_villagers):
            player_name = input(f"Enter the name of Villager {i + 1}: ")
            self.players.append(Player(player_name, 'Villager'))

        for i in range(num_seers):
            player_name = input(f"Enter the name of Seer {i + 1}: ")
            self.players.append(Player(player_name, 'Seer'))

        for i in range(num_jesters):
            player_name = input(f"Enter the name of Jester {i + 1}: ")
            self.players.append(Player(player_name, 'Jester'))

        for i in range(num_drunkers):
            player_name = input(f"Enter the name of Drunker {i + 1}: ")
            self.players.append(Player(player_name, 'Drunker'))

        # Call assign_roles to assign roles to players
        self.assign_roles()

    def assign_roles(self):
        roles = [player.role for player in self.players]

        # Assign roles to players
        for player in self.players:
            role = random.choice(roles)
            player.role = role
            roles.remove(role)

            print(f"{player.name}: {role}")

    def night_phase(self):
        print("\nNight phase:")

        # Count the number of werewolves
        num_werewolves = sum(1 for player in self.players if player.survived and player.role == 'Werewolf')
        num_villagers = sum(1 for player in self.players if player.survived and player.role == 'Villager')

        if num_werewolves == 0 or num_werewolves >= num_villagers:
            print("Game over! Werewolves have taken over or no werewolves left.")
            return

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

        # Seer action
        seer = next((player for player in self.players if player.survived and player.role == 'Seer'), None)
        if seer:
            target_name = input(f"{seer.name}, the Seer, choose a player to inspect: ")
            target = next((p for p in self.players if p.name == target_name and p.survived), None)

            if target:
                seer.seer_inspect(target)
            else:
                print("Invalid target. The Seer chooses not to inspect anyone.")

        # # Drunker action can choose
        # drunker = next((player for player in self.players if player.survived and player.role == 'Drunker'),
        #                None)
        # if drunker:
        #     target_name = input(f"{drunker.name}, the Drunker, choose a player to swap roles with: ")
        #     target = next((p for p in self.players if p.name == target_name and p.survived), None)
        #
        #     if target:
        #         print(f"{drunker.name} and {target.name} are swapping roles!")
        #         drunker_role, target_role = drunker.role, target.role
        #         drunker.role, target.role = target_role, drunker_role
        #     else:
        #         print("Invalid target. The Drunker chooses not to swap roles.")

        # Drunker action
        drunker = next((player for player in self.players if player.survived and player.role == 'Drunker'), None)
        if drunker:
            swap_decision = input(f"{drunker.name}, the Drunker, do you want to swap roles? (yes/no): ").lower()
            if swap_decision == 'yes':
                # Choose a random player to swap roles with
                target = random.choice([p for p in self.players if p != drunker and p.survived])
                print(f"{drunker.name} and {target.name} are swapping roles!")
                drunker_role, target_role = drunker.role, target.role
                drunker.role, target.role = target_role, drunker_role
            else:
                print(f"{drunker.name} chooses not to swap roles.")

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
            werewolves = [player.name for player in self.players if player.role == 'Werewolf' and player.survived]
            print("Werewolves revealed:", ", ".join(werewolves), "\n")

            # Day phase
            self.day_phase()

            # Count and display the number of players for each role
            num_werewolves = sum(1 for player in self.players if player.survived and player.role == 'Werewolf')
            num_villagers = sum(1 for player in self.players if player.survived and player.role == 'Villager')
            num_seer = sum(1 for player in self.players if player.survived and player.role == 'Seer')
            num_jester = sum(1 for player in self.players if player.survived and player.role == 'Jester')
            num_drunker = sum(1 for player in self.players if player.survived and player.role == 'Drunker')

            # Check if the game should continue
            remaining_players = [player for player in self.players if player.survived]
            if num_werewolves == num_villagers:
                break
            if num_werewolves == 0:
                break

            print('')
            print(f"\nNumber of Werewolves: {num_werewolves}")
            print(f"Number of Villagers: {num_villagers}")
            print(f"Number of Seers: {num_seer}")
            print(f"Number of Jesters: {num_jester}")
            print(f"Number of Drunkers: {num_drunker}")
            print('')

            self.display_survivors()

            round_number += 1

if __name__ == "__main__":
    game = WerewolfGame()
    game.intro()
    game.play()
