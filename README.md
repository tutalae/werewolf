# werewolf

A pass-the-device Werewolf party game for the terminal. Everyone sits around one computer; each
player takes their secret turns alone and the screen is cleared before the next person looks.

## Running it

Needs Python 3.10+. Nothing else is required, but if [rich](https://github.com/Textualize/rich)
is installed you get colours, boxed titles and tables; without it the game uses plain text.

```bash
python3 -m werewolf
```

Or install it, with rich, to get a `werewolf` command:

```bash
pip install .
```

You'll be asked for the number of players (3–20), their names, whether to use the default roles
or pick your own, and whether to change the game options. When choosing a player, type their name
(any case) or their number from the list; type `s` or `skip` to skip a vote or the Hunter's shot.
Press Ctrl+C to quit.

## How a game goes

1. **Role reveal.** The device is passed to each player in turn. They see their role in private,
   then press Enter to hide it.
2. **Night.** Every living player takes a private turn, even players with nothing to do, so
   nobody can tell who has a power. Actions all take effect at the end of the night.
3. **Day.** The village learns who died, and each dead player's role is revealed (unless that
   option is off).
4. **Discussion.** A countdown runs while everyone argues about who the werewolves are. The
   default is 2 minutes; press Enter to end it early, or set it to 0 during setup to skip it.
5. **Vote.** Every living player votes to eliminate someone, or skips. With secret votes, each
   player votes in a private turn and only the totals are shown. The player with the most votes
   is out; a tie or a win for "skip" means nobody goes.
6. Repeat until someone wins.

**Game options**

Setup offers the defaults, or lets you change each one:

| Option | Default | |
| --- | --- | --- |
| Discussion time | 2:00 | Length of each day's countdown; 0 turns it off. |
| Reveal roles on death | on | When off, dead players' roles stay secret until the game ends. |
| Kill on the first night | on | When off, the werewolves only meet on night 1, and the Little Girl can't be caught. |
| Secret votes | off | When on, everyone votes in private instead of out loud. |

**Who wins**

- **Village:** every werewolf is eliminated.
- **Werewolves:** werewolves equal or outnumber everyone else. This is checked after the night
  as well as after the vote.
- **Jester:** the Jester is voted out.

## Roles

| Role | Team | Power |
| --- | --- | --- |
| Werewolf | Werewolves | Each night, picks someone to attack. If the pack disagrees, the most-picked target is attacked; ties are broken at random. |
| Villager | Village | None. |
| Seer | Village | Each night, learns whether one player is a werewolf. |
| Witch Doctor | Village | Each night, may protect one player (themselves included) from the attack, but not the same player two nights in a row. |
| Drunker | Village | Each night, may swap roles with a random player. |
| Troublemaker | Village | Each night, may swap the roles of two other players. |
| Mayor | Village | Their vote counts twice. |
| Hunter | Village | When eliminated, shoots one other player. |
| Cupid | Village | On the first night, picks two lovers. If one dies, the other dies of a broken heart. |
| Little Girl | Village | Each night, may peek to learn one werewolf's name, with a 25% chance of being caught and killed. |
| Lycan | Village | No power, but the Seer sees them as a werewolf. |
| Cursed | Village | If attacked by the werewolves, doesn't die but becomes a werewolf. |
| Jester | Jester | Wins alone by being voted out. |

Swaps and new lovers happen silently. Players find out their new role, or who they love, at the
start of their next private turn.

## Default roles and balance

Everyone not listed is a Villager.

| Players | Default roles |
| --- | --- |
| 3–4 | 1 Werewolf, Seer, Witch Doctor |
| 5–7 | 1 Werewolf, Seer, Witch Doctor, Hunter |
| 8–11 | 1 Werewolf, Seer, Witch Doctor |
| 12–20 | 2 Werewolves, Seer, Witch Doctor, Hunter, Little Girl, Mayor |

These were tuned with the simulator, which plays thousands of games with simple bots. For 5–20
players, the village wins roughly 38–58% of bot games. 3–4 player games favour the werewolves, because
their first kill happens before anyone can vote.

The bots vote almost at random, so real players who discuss should do better for the village than
these numbers suggest. Try your own mix:

```bash
python3 -m werewolf.simulate                               # every default mix, 5-16 players
python3 -m werewolf.simulate 10 Werewolf=2 Seer=1 Cursed=1  # a custom mix
```

## Project layout

```
werewolf/
  __main__.py   entry point for `python3 -m werewolf`
  rules.py      the rules, as pure functions over an immutable GameState
  actions.py    what players do at night (Attack, Protect, Swap, ...), as immutable values
  game.py       the game loop: turns, questions, announcements, options, and setup
  roles.py      one class per role; add a role by subclassing Role
  console.py    input parsing (returns Either), plain console, discussion timer
  either.py     a small typed Either type for results that can fail
  pretty.py     the rich console (used only if rich is installed)
  simulate.py   bot games for checking balance
tests/          unit tests and scripted full games
monad_concept.py  standalone pymonad experiment, not used by the game
```

## How the code is organised

The game follows a *functional core, imperative shell* design:

- **`rules.py` is the functional core.** `resolve_night`, `tally_votes` and `check_winner` take
  an immutable `GameState` and return a new one, and they never print or ask anything. The night
  is a pipeline, `link_lovers` → `resolve_attacks` → `apply_swaps`, where each step returns a
  fresh state. Randomness is passed in as a `choose` function, so the same inputs always give the
  same result.
- **`game.py` is the imperative shell.** It talks to the players, collects their actions,
  snapshots the players into a `GameState`, hands it to the rules, and applies the result.
- **Input checks use `Either`.** Parsers like `parse_int` and `parse_name` return `Right(value)`
  or `Left(error message)` and chain their checks with `.then`, so the first failing check becomes
  the message the player sees:

  ```python
  Right(text).then(ensure(str.isdigit, error)).map(int).then(ensure(in_range, error))
  ```

## Development

```bash
python3 -m unittest    # tests; the rich tests are skipped if rich isn't installed
pip install ruff mypy rich
ruff check .           # lint
mypy                   # type check (strict)
```

GitHub Actions runs all three on every push and pull request. Tests run on Linux, macOS and
Windows with Python 3.10 and 3.14, once without rich and once with it. Each run also adds a
balance report to the job summary.

`monad_concept.py` needs `pymonad`: `pip install -r requirements.txt`.
