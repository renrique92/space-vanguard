# Space Vanguard

Classic Space Invaders clone built with Python and Pygame. Geometric shapes only — no external assets.

## Features

- 8×5 enemy grid with row-based colors and point values
- Score multiplier (starts at 3×, decays over time)
- Synthesized sound effects (no audio files)
- Visual effects: explosions, muzzle flash, screen shake
- Persistent high score

## Requirements

- Python 3.9+
- pygame 2.x

## Install

```bash
pip install pygame
```

## Run

```bash
python3 main.py
```

## Controls

| Key | Action |
|-----|--------|
| ← → | Move |
| SPACE | Shoot |
| R | Restart (game over / win) |

## Project structure

```
main.py          — entry point
settings.py      — game constants
game.py          — game loop and state machine
sounds.py        — sound synthesis
effects.py       — particles, flash, shake
utils.py         — draw_text helper
sprites/         — player, enemy, bullet classes
ui/              — info panel
```
