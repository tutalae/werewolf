# werewolf

A pass-the-device Werewolf party game for the terminal. Everyone sits around one computer; each
player takes their secret turns alone and the screen is cleared before the next person looks.

## Running it

Needs Python 3.8+ and nothing else.

```bash
python3 -m werewolf
```

You'll be asked for the number of players (3–20), their names, and whether to use the default
roles or pick your own. Type player names in any case; type `skip` to skip a vote or the Hunter's
shot. Press Ctrl+C to quit.

## How a game goes

1. **Role reveal.** The device is passed to each player in turn. They see their role in private,
   then press Enter to hide it.
2. **Night.** Every living player takes a private turn, even players with nothing to do, so
   nobody can tell who has a power. Actions all take effect at the end of the night.
3. **Day.** The village learns who was killed, and that player's role is revealed. Then every
   living player votes to eliminate someone, or skips. The player with the most votes is out;
   a tie or a win for "skip" means nobody goes.
4. Repeat until someone wins.

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
| Witch Doctor | Village | Each night, may protect one player from the attack. If the protected player *isn't* attacked, they turn into a werewolf. |
| Drunker | Village | Each night, may swap roles with a random player. |
| Troublemaker | Village | Each night, may swap the roles of two other players. |
| Mayor | Village | Their vote counts twice. |
| Hunter | Village | When eliminated, shoots one other player. |
| Jester | Jester | Wins alone by being voted out. |

Swaps happen silently. Players find out their new role at the start of their next night turn.

**Default roles:** 1 werewolf per 3 players (at least 1, at most 2), plus a Seer from 5 players up.
Everyone else is a Villager.

## Project layout

```
werewolf/
  __main__.py   entry point for `python3 -m werewolf`
  game.py       players, rules, the night/day loop, and setup
  roles.py      one class per role; add a role by subclassing Role
  console.py    terminal input/output and input validation
tests/          unit tests and scripted full games
monad_concept.py  standalone pymonad experiment, not used by the game
```

## Tests

```bash
python3 -m unittest
```

The tests use only the standard library. `tests/scripted.py` has a fake console that plays back
scripted answers, so whole games can be tested without typing.

`monad_concept.py` needs `pymonad`: `pip install -r requirements.txt`.
