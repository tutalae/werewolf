import sys, random

class Player:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.survived = True
        self.protected_by_witch_doctor = False  # New attribute

    def werewolf_attack(self, target):
        print(f"Oh no! {self.name}, a werewolf is attacking {target.name}!")

        if target.protected_by_witch_doctor:
            print(f"But wait! {target.name} is protected by the Witch Doctor. They survive the attack!")
            target.protected_by_witch_doctor = False
        else:
            print('\n' * 3)
            print(f"{target.name} is bitten by the werewolf. Game over!")
            target.survived = False
            print('\n' * 3)

    def seer_inspect(self, target):
        print(f"{self.name}, the Seer, is inspecting {target.name}...")

        if target.role == 'Werewolf':
            print(f"{target.name} is a Werewolf!")
        else:
            print(f"{target.name} is not a Werewolf!")

    def hunter_shot(self, players, post_mortem=False):
        if not post_mortem and not self.survived:
            print(f"{self.name}, the Hunter, cannot shoot because they are already eliminated.")
            return

        if not post_mortem and self.survived:  # Added check for Hunter being alive
            print(f"{self.name}, the Hunter, is choosing a player to shoot!")

            # Display the list of available players
            print("Available players:")
            for player in players:
                if player.survived:
                    print(player.name)

            # Prompt the Hunter to choose a target
            target_name = input("Enter the name of the player you want to shoot: ")
            target = next((p for p in players if p.name == target_name and p.survived), None)

            if target:
                print(f"{self.name}, the Hunter, is shooting {target.name}!")

                # Hunter shot outcome is now deterministic (instant death)
                print('\n' * 3)
                print(f"{target.name} is shot by the Hunter. Game over!")
                target.survived = False
                print('\n' * 3)
            else:
                print("Invalid target. The Hunter chooses not to shoot anyone.")
        elif post_mortem and self.survived:  # Added check for Hunter being alive
            print(f"{self.name}, the Hunter, takes a post-mortem shot!")

            # Display the list of available players
            print("Available players:")
            for player in players:
                if player.survived and player.role != 'Hunter':
                    print(player.name)

            # Prompt the Hunter to choose a target
            target_name = input("Enter the name of the player you want to shoot post-mortem: ")
            target = next((p for p in players if p.name == target_name and p.survived), None)

            if target:
                print(f"{self.name}, the Hunter, takes a post-mortem shot and shoots {target.name}!")

                # Hunter post-mortem shot outcome is now deterministic (instant death)
                print('\n' * 3)
                print(f"{target.name} is shot by the Hunter post-mortem. Game over!")
                target.survived = False
                print('\n' * 3)
            else:
                print("Invalid target. The Hunter post-mortem chooses not to shoot anyone.")
        else:
            print(f"{self.name}, the Hunter, cannot shoot because they are already eliminated.")
            
    def troublemaker_action(self, werewolf_game):
        print(f"{self.name}, the Troublemaker, is causing trouble!")

        # Choose two players to swap roles
        player1_name = input("Enter the name of the first player to swap roles: ")
        player1 = next((p for p in werewolf_game.players if p.name == player1_name and p.survived), None)

        player2_name = input("Enter the name of the second player to swap roles: ")
        player2 = next((p for p in werewolf_game.players if p.name == player2_name and p.survived), None)

        if player1 and player2:
            print(f"{self.name} is swapping the roles of {player1.name} and {player2.name}!")
            player1_role, player2_role = player1.role, player2.role
            player1.role, player2.role = player2_role, player1_role
        else:
            print("Invalid players. The Troublemaker chooses not to swap roles.")

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
        num_troublemakers = int(input("Enter the number of troublemakers: "))
        num_mayor = int(input("Enter the number of mayor: "))
        num_hunter = int(input("Enter the number of hunter: "))
        num_witch_doctor = int(input("Enter the number of witch doctor: "))

        # Validate input
        if (
            num_players < num_wolves + num_villagers + num_seers + num_jesters + num_drunkers + num_troublemakers \
            + num_mayor + num_hunter + num_witch_doctor
            or num_wolves < 1
            or num_villagers < 0
            or num_seers < 0
            or num_jesters < 0
            or num_drunkers < 0
            or num_troublemakers < 0
            or num_mayor < 0
            or num_hunter < 0
            or num_witch_doctor < 0
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

        for i in range(num_troublemakers):
            player_name = input(f"Enter the name of Troublemaker {i + 1}: ")
            self.players.append(Player(player_name, 'Troublemaker'))

        for i in range(num_mayor):
            player_name = input(f"Enter the name of Mayor {i + 1}: ")
            self.players.append(Player(player_name, 'Mayor'))

        for i in range(num_hunter):
            player_name = input(f"Enter the name of Hunter {i + 1}: ")
            self.players.append(Player(player_name, 'Hunter'))
        
        for i in range(num_witch_doctor):
            player_name = input(f"Enter the name of Witch Doctor {i + 1}: ")
            self.players.append(Player(player_name, 'Witch Doctor'))

        print('\n' * 10)
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
            print('\n'*10)

    def night_phase(self):
        print("\nNight phase:")
        
        print("\n"*3)
        
        # Doctor action
        witch_doctor = next((player for player in self.players if player.survived and player.role == 'Witch Doctor'), None)
        if witch_doctor:
            print("Under the cloak of night, the village sleeps. Witch Doctor, wake up!")
            protect_decision = input(f"{witch_doctor.name}, the Witch Doctor, do you want to protect someone this night? (yes/no): ").lower()

            if protect_decision == 'yes':
                target_name = input("Choose a player to protect: ")
                target = next((p for p in self.players if p.name == target_name and p.survived), None)

                if target:
                    target.protected_by_witch_doctor = True  # Fix: set the attribute to True
                    print(f"{witch_doctor.name} protects {target.name}!")
                    print(f"If {target.name} is not attacked, they potentially turn into a werewolf.")
                else:
                    print("Invalid target. The Witch Doctor chooses not to protect anyone.")
            else:
                print(f"{witch_doctor.name} chooses not to protect anyone this night.")
                
            print("The mystical energy fades, and the Witch Doctor fades back into the shadows.")

            print("\n"*3)
            
        # Count the number of werewolves
        num_werewolves = sum(1 for player in self.players if player.survived and player.role == 'Werewolf')

        # Count the number of villagers (all non-werewolf classes)
        num_villagers = sum(1 for player in self.players if player.survived and player.role != 'Werewolf')

        if num_werewolves == 0 or num_werewolves >= num_villagers:
            print("Game over! Werewolves have taken over or no werewolves left.")
            return

        max_hunters = len([player for player in self.players if player.role == 'Hunter' and player.survived])

        # Werewolf actions
        print("Under the pale moonlight, the village falls silent. Werewolves, wake up!")
        print("The werewolves are now seeking their prey...")
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
                    target_name = input(f"Werewolf {player.name}, choose a player to attack: ")
                    target = next((p for p in self.players if p.name == target_name and p.survived), None)

                    if target:
                        player.werewolf_attack(target)
                    else:
                        print("Invalid target. The werewolf attacks a random player.")
                        target = random.choice([p for p in self.players if p != player and p.survived])
                        player.werewolf_attack(target)
                        
        # Check if protected players turn into werewolves
        for player in self.players:
            if player.protected_by_witch_doctor and player.survived:
                print(f"{player.name} was protected by the Doctor and did not get attacked. They turn into a Werewolf!")
                player.role = 'Werewolf'

                # Reset protection for the next round
                player.protected_by_witch_doctor = False
                
        print("All werewolves retreat into the shadows.")

        # Hunter takes a shot after being attacked by werewolves
        hunters = [player for player in self.players if player.role == 'Hunter' and player.survived]

        # Identify deceased Hunter
        dead_hunters = [hunter for hunter in hunters if not hunter.survived]

        # Check if there is at least one deceased Hunter
        if dead_hunters:
            # Choose one deceased Hunter to take a post-mortem shot
            dead_hunter = dead_hunters[0]
            dead_hunter.hunter_shot(self.players, post_mortem=True)

        # Seer action
        seer = next((player for player in self.players if player.survived and player.role == 'Seer'), None)
        if seer:
            print("\n"*3)
            print("Seer, wake up and use your mystical sight!")
            
            target_name = input(f"{seer.name}, the Seer, choose a player to inspect: ")
            target = next((p for p in self.players if p.name == target_name and p.survived), None)

            if target:
                seer.seer_inspect(target)
            else:
                print("Invalid target. The Seer chooses not to inspect anyone.")
            
            print("Seer, go back to sleep.\n")
            print("\n"*3)

        # Drunker action
        drunkers = [player for player in self.players if player.survived and player.role == 'Drunker']
        for drunker in drunkers:
            print("\n"*3)
            print(f"{drunker.name}, the Drunker, wake up and stumble around!")
            
            swap_decision = input(f"{drunker.name}, do you want to swap roles? (yes/no): ").lower()
            
            if swap_decision == 'yes':
                # Choose a random player to swap roles with
                target = random.choice([p for p in self.players if p != drunker and p.survived])
                print(f"{drunker.name} and {target.name} are swapping roles!")
                drunker_role, target_role = drunker.role, target.role
                drunker.role, target.role = target_role, drunker_role
            else:
                print(f"{drunker.name} chooses not to swap roles.")
                
            print(f"{drunker.name}, go back to sleep.\n")
            print("\n"*3)

        # Troublemaker action
        troublemaker = next((player for player in self.players if player.survived and player.role == 'Troublemaker'),
                            None)
        if troublemaker:
            
            print("\n"*3)
            print("Troublemaker, wake up and start causing trouble!")
            
            perform_action = input(
                f"{troublemaker.name}, the Troublemaker, do you want to perform the action? (yes/no): ").lower()
            if perform_action == 'yes':
                troublemaker.troublemaker_action(self)
            else:
                print(f"{troublemaker.name} chooses not to perform the action.")
                
            print("Troublemaker, go back to sleep.\n")
            print("\n"*3)

                
        print("The night comes to an end")

    def day_phase(self):
        print("\nDay phase:")        
        print("\nDay phase has begun. The sun rises, and the villagers gather.")
        
        votes = {player: 0 for player in self.players if player.survived}

        # Ask players if they want to vote someone out
        vote_choice = input("Villagers, do you want to vote someone out? (yes/no): ").lower()

        if vote_choice == 'yes':
            # Simulate the voting
            print("Players, collectively choose a player to vote out:")
            target_name = input("Enter the name of the player you want to vote out: ")
            target = next((p for p in self.players if p.name == target_name and p.survived), None)

            if target:
                for player in self.players:
                    if player.survived:
                        # player.vote_out(target)
                        votes[target] += 1
            else:
                print("Invalid target. No one is voted out this round.")

            # Eliminate the player with the most votes
            max_votes_player = max(votes, key=votes.get)
            print(f"\n{max_votes_player.name} has been voted out!\n")
            max_votes_player.survived = False
        elif vote_choice == 'no':
            print("Villagers decide not to vote anyone out this round.")
        else:
            print("Invalid choice. Players decide not to vote anyone out this round.")
            
        # Hunter takes a shot during the night
        hunters = [player for player in self.players if player.role == 'Hunter' and player.survived]

        for hunter in hunters:
            # Ask for confirmation
            user_input = input(f"{hunter.name}, do you want to take a shot during the day? (yes/no): ").lower()

            if user_input == 'yes':
                # Call the hunter_shot method only if the player confirms
                hunter.hunter_shot(self.players)
            else:
                print(f"{hunter.name} decided not to take a shot during the day.")
        
        # End of Day phase
        print("\nThe sun sets, and the villagers disperse. The night approaches.")
        print("\n"*3)


    def check_game_status(self):
        num_werewolves = sum(1 for player in self.players if player.survived and player.role == 'Werewolf')
        num_villagers = sum(1 for player in self.players if player.survived and player.role == 'Villager')
        num_seer = sum(1 for player in self.players if player.survived and player.role == 'Seer')
        num_jester = sum(1 for player in self.players if player.survived and player.role == 'Jester')
        num_drunker = sum(1 for player in self.players if player.survived and player.role == 'Drunker')
        num_troublemaker = sum(1 for player in self.players if player.survived and player.role == 'Troublemaker')
        num_mayor = sum(1 for player in self.players if player.survived and player.role == 'Mayor')
        num_hunter = sum(1 for player in self.players if player.survived and player.role == 'Hunter')
        num_witch_doctor = sum(1 for player in self.players if player.survived and player.role == 'Witch Doctor')

        remaining_non_werewolf_roles = num_villagers + num_seer + num_jester + num_drunker + num_troublemaker \
                                       + num_mayor + num_hunter + num_witch_doctor

        print('')
        print(f"\nNumber of Werewolves: {num_werewolves}")
        print(f"Number of Villagers: {num_villagers}")
        print(f"Number of Seers: {num_seer}")
        print(f"Number of Jesters: {num_jester}")
        print(f"Number of Drunkers: {num_drunker}")
        print(f"Number of Troublemakers: {num_troublemaker}")
        print(f"Number of Mayors: {num_mayor}")
        print(f"Number of Hunters: {num_hunter}")
        print(f"Number of Witch Doctor: {num_witch_doctor}")
        print('')

        if num_werewolves == 0:
            print("No more werewolves!")
            print("Game End!!")
            sys.exit()

        if remaining_non_werewolf_roles <= num_werewolves:
            print("All remaining players are equal or less than werewolves!")
            print("Game End!!")
            sys.exit()

        return not (
                num_werewolves == 0 or remaining_non_werewolf_roles == num_werewolves
        )

    def display_survivors(self):
        print("\n"*5)
        print("Survivors:")
        for player in self.players:
            print("\n"*5)
            player.display_status()
        print("\n"*5)
        
        for player in self.players:
            player.display_status()

    def play(self):
        round_number = 1
        while True:
            print(f"\nNight {round_number}:")
            self.night_phase()

            # Check if the game should continue
            remaining_players = [player for player in self.players if player.survived]
            print(f"\nNumber of people survived after Night {round_number}: {len(remaining_players)}\n")
            if len(remaining_players) <= 1:
                break

            # Display status after each night
            for player in self.players:
                print('\n'*5)
                player.display_status()
            print('\n'*5)

            # Reveal the identities of the werewolves
            werewolves = [player.name for player in self.players if player.role == 'Werewolf' and player.survived]
            print("Werewolves revealed:", ", ".join(werewolves), "\n")

            print('checking status ...')
            self.check_game_status()

            # Day phase
            self.day_phase()

            # Check if the game should continue
            remaining_players = [player for player in self.players if player.survived]
            print(f"\nNumber of people survived after Days {round_number}: {len(remaining_players)}\n")
            if len(remaining_players) <= 1:
                break

            self.check_game_status()

            self.display_survivors()

            round_number += 1

if __name__ == "__main__":
    game = WerewolfGame()
    game.intro()
    game.play()
