# werewolf

A pass-the-device Werewolf party game for the terminal. Everyone sits around one computer; each
player takes their secret turns alone and the screen is cleared before the next person looks.

## Running it

Needs Python 3.10+ and nothing else.

```bash
python3 -m werewolf
```

Or install it to get a `werewolf` command:

```bash
pip install .
```

You'll be asked for the number of players (3–20), their names, whether to use the default roles
or pick your own, and how long each day's discussion lasts. Type player names in any case; type
`skip` to skip a vote or the Hunter's shot. Press Ctrl+C to quit.

## How a game goes

1. **Role reveal.** The device is passed to each player in turn. They see their role in private,
   then press Enter to hide it.
2. **Night.** Every living player takes a private turn, even players with nothing to do, so
   nobody can tell who has a power. Actions all take effect at the end of the night.
3. **Day.** The village learns who died, and each dead player's role is revealed.
4. **Discussion.** A countdown runs while everyone argues about who the werewolves are. The
   default is 2 minutes; press Enter to end it early, or set it to 0 during setup to skip it.
5. **Vote.** Every living player votes to eliminate someone, or skips. The player with the most
   votes is out; a tie or a win for "skip" means nobody goes.
6. Repeat until someone wins.

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
players, the village wins 37–58% of bot games. 3–4 player games favour the werewolves, because
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
  game.py       players, rules, the night/day loop, and setup
  roles.py      one class per role; add a role by subclassing Role
  console.py    terminal input/output, input checks, and the discussion timer
  simulate.py   bot games for checking balance
tests/          unit tests and scripted full games
monad_concept.py  standalone pymonad experiment, not used by the game
```

## Development

```bash
python3 -m unittest    # tests, standard library only
pip install ruff mypy
ruff check .           # lint
mypy                   # type check (strict)
```

GitHub Actions runs all three on every push and pull request. Tests run on Linux, macOS and
Windows with Python 3.10 and 3.14. Each run also adds a balance report to the job summary.

`monad_concept.py` needs `pymonad`: `pip install -r requirements.txt`.
