# Space Vanguard — AGENTS.md

## Memory

**LEER AL INICIAR CADA SESIÓN.** Contexto de lo último trabajado en `.opencode/memory/`:
- `DECISIONS.md` — tabla de decisiones de diseño
- `GOTCHAS.md` — traps, bugs, no-obviedades
- `SESSION_LOG.md` — diario por sesión

LEER `GOTCHAS.md` antes de modificar effects/sounds/game.

## Run

```bash
python3 main.py
```

## Tests (pytest, headless)

```bash
python3 -m pytest tests/ -v
```

Env vars `SDL_VIDEODRIVER=dummy` / `SDL_AUDIODRIVER=dummy` set in `tests/conftest.py`. No display needed. 133 smoke tests covering init, loop, collisions, transitions, score, persistence, particles, power-ups, difficulty, boss, UFO, bunkers, streak, edge cases, render, performance.

## Tuning

All gameplay constants in `settings.py`: speeds, colors, timing, scoring, multiplier, grid size, power-up durations, difficulty presets, special attack.

## Game loop

`game._update(dt)` — `dt` in ms, passed to `particles.update(dt)`, `flash_fx.update(dt)`, `screen_shake.update(dt)`. Don't use `pygame.time.get_ticks()` for particle/flash timers (breaks in headless).

## Sound

12 synthesized sounds at 22050 Hz, 16-bit signed mono (`sounds.py`). Keys: `shoot`, `enemy_shoot`, `explosion`, `player_hit`, `game_over`, `win`, `level_up`, `ufo`, `powerup`, `special`, `special_beam`, `bgm`.

## Persistence

High score stored in `high_score.json` (gitignored, created at runtime).

## Structure

```
main.py → Game.run() loop
game.py  → state machine, collisions orchestration, effects triggers
collision.py → collision handlers (modular functions)
levels.py → level management (advance, reset, bunkers, transition)
shooting.py → enemy shooting logic
renderer.py → all drawing, screen shake, overlays
sprites/ → Player, Enemy/EnemyFormation, Bullet, UFO, Bunker
ui/      → InfoPanel (right-side panel)
classes/ → Difficulty enum
```

## Special Attack

- Charges over ~20s without taking damage (Z key when ready)
- Narrow (10px) piercing beam for 2s, kills enemies/bullets in column
- Player cannot move or shoot while beam active
- Charge resets on hit or level advance (unless 100% and unused)
