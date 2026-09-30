"""Terminal input and output, kept apart from the game rules so tests can script it."""


class Console:
    """Reads from and writes to the terminal."""

    def say(self, text=""):
        print(text)

    def ask(self, prompt):
        return input(prompt)

    def clear(self):
        # Clear the screen and the scrollback so the next player can't scroll up
        print("\033[H\033[2J\033[3J", end="", flush=True)


def ask_int(console, prompt, low, high):
    while True:
        answer = console.ask(prompt).strip()
        if answer.isdigit() and low <= int(answer) <= high:
            return int(answer)
        console.say(f"Please enter a whole number from {low} to {high}.")


def ask_yes_no(console, prompt):
    while True:
        answer = console.ask(f"{prompt} (yes/no): ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        console.say("Please answer yes or no.")


def ask_player(console, prompt, candidates, allow_skip=False):
    """Ask for one of `candidates` by name (any case). Returns None if the player skips."""
    by_name = {p.name.lower(): p for p in candidates}
    choices = ", ".join(p.name for p in candidates)
    if allow_skip:
        choices += ", or skip"

    while True:
        answer = console.ask(f"{prompt} [{choices}]: ").strip().lower()
        if allow_skip and answer == "skip":
            return None
        if answer in by_name:
            return by_name[answer]
        console.say("That isn't one of the choices.")
