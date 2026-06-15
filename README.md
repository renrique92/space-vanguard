# Space Vanguard

Classic Space Invaders clone built with Python and Pygame. Pure geometric shapes — zero external assets (images, fonts, audio files). 5 levels, synthesized sound, visual effects, persistent high score.

---

## Project Overview

| Property | Value |
|----------|-------|
| Language | Python 3.9+ |
| Framework | Pygame 2.x |
| Lines of code | ~780 |
| External assets | None |
| Test framework | None (ad-hoc/headless) |

---

## File Structure

```
space_vanguard/
├── main.py              # Entry point, pygame init → Game.run() → pygame.quit()
├── game.py              # Core: state machine, game loop, collision, level transitions
├── settings.py          # All tunable constants: speeds, colors, levels, scoring
├── sounds.py            # Synthesized sound engine (7 sounds, no audio files)
├── effects.py           # Particle system, muzzle flash, screen shake
├── utils.py             # Single helper: draw_text()
├── requirements.txt     # pygame>=2.0,<3.0
├── high_score.json      # Persistent high score (gitignored, created at runtime)
├── sprites/
│   ├── player.py        # Player ship — movement, invulnerability, polygon drawing
│   ├── enemy.py         # Enemy (single) + EnemyFormation (grid logic, shooting, auto-step)
│   └── bullet.py        # Bullet — player (cyan, upward) / enemy (orange, downward)
└── ui/
    └── info_panel.py    # Right-side HUD: score, high score, lives, multiplier, accuracy
```

---

## Architecture Summary

### Modules & Responsibilities

| Module | Key Classes / Functions | Role |
|--------|------------------------|------|
| `main.py` | `main()` | Bootstrap Pygame, create `Game`, run loop, quit. |
| `game.py` | `Game` | State machine, game loop, collision detection, level transitions, all orchestration. |
| `settings.py` | — | Single source of truth for all gameplay constants. |
| `sounds.py` | `SoundManager` | Generates 7 synthesized sounds at 22050 Hz, 16-bit signed mono. |
| `effects.py` | `Particle`, `MuzzleFlash`, `ScreenShake`, `spawn_explosion()` | Visual VFX. |
| `utils.py` | `draw_text()` | Text rendering helper (centered or left-aligned). |
| `sprites/player.py` | `Player` | Ship movement, hit/invulnerability flash, reset. |
| `sprites/enemy.py` | `Enemy`, `EnemyFormation` | Individual enemy + formation grid with movement, shooting, auto-step-down. |
| `sprites/bullet.py` | `Bullet` | Projectile with direction, ownership, off-screen cleanup. |
| `ui/info_panel.py` | `InfoPanel` | Right-side stats panel with all HUD elements. |

### Key Relationships

```
Game
 ├── owns: Player, EnemyFormation, SoundManager, ScreenShake
 ├── owns: 3 sprite Groups (player_bullets, enemy_bullets, particles, flash_fx)
 ├── owns: InfoPanel (rendered separately, no sprite group)
 ├── creates Bullet instances on shoot
 ├── calls spawn_explosion() → Particle Group on enemy death
 └── updates everything via _update(dt)

EnemyFormation
 └── owns: pygame.sprite.Group of Enemy instances
     └── Enemy has: rect, points, get_shoot_position()
```

---

## Game Loop

```
main()
 └── Game.run()
      └── while running:
           ├── clock.tick(60) → dt (milliseconds)
           ├── _handle_events()
           ├── _update(dt)       # if not paused and (PLAYING or transitioning)
           └── _draw()
```

### `_update(dt)` Flow (normal play)

1. `screen_shake.update(dt)` — decay active shake
2. `player.update()` — invulnerability blink
3. `formation.update()` — move formation, reverse at edges, speed up as enemies die
4. `auto_step_timer += dt` — periodic auto-step-down every 4s
5. `formation.try_shoot()` — random enemy fires
6. `player_bullets.update()` + `enemy_bullets.update()` — move bullets, kill off-screen
7. `particles.update(dt)` + `flash_fx.update(dt)` — age VFX sprites
8. **Player bullets ↔ Enemies** — `groupcollide`, kill both, add score (×multiplier), spawn explosion particles
9. **Player ↔ Enemy bullets** — `spritecollide`, take hit, shake screen
10. Check `formation.reached_game_over()` — enemies reached bottom?
11. Check `formation.enemies empty` — level cleared?

### State Machine

| State | Meaning | Transitions |
|-------|---------|-------------|
| `transitioning` | Initial level intro or between-level clear screen | → `PLAYING` after 2000ms |
| `PLAYING` | Normal gameplay | → `transitioning` (level clear), `GAME_OVER`, `WIN` |
| `GAME_OVER` | Player dead or enemies reached bottom | Press R → `_reset()` |
| `WIN` | All 5 levels cleared | Press R → `_reset()` |
| `PAUSED` | Toggle with P | Freezes `_update`, draws overlay |

---

## Levels (5 Formations)

All 5 level definitions in `settings.py` under `LEVELS`. Each has a `pattern` (2D grid of 1/0), `colors` (per row), and `points` (per row).

### Level 1 — Full Block
```
[1,1,1,1,1,1,1,1]
[1,1,1,1,1,1,1,1]
[1,1,1,1,1,1,1,1]
[1,1,1,1,1,1,1,1]
[1,1,1,1,1,1,1,1]
```
5 rows × 8 columns = 40 enemies. Classic invader wall.

### Level 2 — Diamond
```
[0,0,0,1,1,0,0,0]
[0,0,1,1,1,1,0,0]
[0,1,1,1,1,1,1,0]
[0,0,1,1,1,1,0,0]
[0,0,0,1,1,0,0,0]
```
Diamond / football shape. 16 enemies.

### Level 3 — Skull / Alien Face
```
[0,0,1,1,1,1,0,0]
[0,1,1,1,1,1,1,0]
[1,1,1,1,1,1,1,1]
[0,1,1,0,0,1,1,0]
[0,0,1,0,0,1,0,0]
```
Resembles an alien face with eyes and mouth gaps. 22 enemies.

### Level 4 — Checker Columns (10-wide)
```
[1,0,1,0,1,0,1,0,1,0]
[1,0,1,0,1,0,1,0,1,0]
[1,0,1,0,1,0,1,0,1,0]
[1,0,1,0,1,0,1,0,1,0]
```
4 rows × 10 columns, alternating empty columns. 20 enemies. Wider grid (10 columns instead of 8).

### Level 5 — Two-row Fortress (10-wide)
```
[1,1,1,1,1,1,1,1,1,1]
[1,1,1,1,1,1,1,1,1,1]
```
2 rows × 10 columns = 20 enemies. Each enemy worth more (35/30 points). Red + orange only.

### Row Colors & Points

| Row index (top→bottom) | Color | Points (L1–L4) | Points (L5) |
|------------------------|-------|-----------------|-------------|
| 0 (top) | Red | 30 | 35 |
| 1 | Orange | 25 | 30 |
| 2 | Yellow | 20 | — |
| 3 | Lime | 15 | — |
| 4 (bottom) | Cyan | 10 | — |

---

## Controls

| Key | Action |
|-----|--------|
| ← → | Move ship left/right |
| SPACE | Shoot (up to 3 bullets on screen, 250ms delay) |
| P | Pause / Resume |
| R | Restart (game over or win screen) |
| ESC | Quit game |

---

## Scoring System

### Score Multiplier

- Starts at **3.0×** at the start of each level.
- Decays linearly over time: `mult = max(0.3, 3.0 - elapsed_seconds / 10)`.
- Resets to 3.0× at each new level.
- Displayed in the info panel (gold when ≥1.0, red when below).

### Accuracy Tracking

- **Deferred counting:** `shots_fired` is not incremented at bullet creation. Instead, bullets are added to `_pending_shots` (a `set`). When a bullet dies (goes off-screen or hits something), `_resolve_shots()` counts it as "fired" on its death frame.
- This means misses that fly off-screen still count as shots fired; bullets that hit get double-counted? No — the bullet dies in `groupcollide` (killed by `True` in `groupcollide`), then `_resolve_shots` catches it and increments `shots_fired`. Hits increment `shots_hit` in the collision handler. So a bullet that hits counts as both 1 fired + 1 hit. A bullet that flies off-screen counts as 1 fired + 0 hit.
- Accuracy displayed as percentage (`shots_hit / shots_fired * 100`). Defaults to 100% when zero shots fired.

### Per-Level Reset

- Score **accumulates** across levels (never reset).
- `elapsed_time` resets to 0 at each new level (so multiplier restarts at 3.0×).
- Player gains **1 extra life** on level clear (capped at `MAX_LIVES = 5`).

### High Score

- Loaded from `high_score.json` at startup.
- Saved when reaching GAME_OVER or WIN, only if current score exceeds stored value.
- File is gitignored.

---

## Sound System

`SoundManager` in `sounds.py` — fully procedural audio synthesis, zero audio files.

| Sound | Waveform | Frequency | Duration | Notes |
|-------|----------|-----------|----------|-------|
| `shoot` | Square | 880 Hz | 0.08s | Player laser |
| `enemy_shoot` | Square | 440 Hz | 0.10s | Enemy laser |
| `explosion` | Noise | — | 0.20s | White noise with linear decay |
| `player_hit` | Sine | 150 Hz | 0.30s | Low thud |
| `game_over` | Sine sweep | 440→110 Hz | 0.60s | Descending sweep |
| `win` | Sine sweep | 330→880 Hz | 0.60s | Ascending sweep |
| `level_up` | Square sweep | 660→1320 Hz | 0.30s | Quick ascending |

**Technical details:** 22050 Hz sample rate, 16-bit signed (`array("h")`), mono, 512-byte buffer. `SoundManager` gracefully degrades if Pygame mixer fails to init (`self.available = False`).

---

## Effects System

### Particles (`effects.py`)

- `Particle` is a `pygame.sprite.Sprite` with position, velocity (polar: angle + speed), age, and lifetime.
- `spawn_explosion(x, y, color, count=10)` creates a group of 10 particles with random angles, speeds (1.5–4.5), lifetimes (200–400ms), and sizes (2–4px).
- Particles fade out via `set_alpha()` based on age/life ratio.
- `update(dt)` — age-based, kills self when expired.

### Muzzle Flash

- `MuzzleFlash` sprite: 14×8 translucent yellow-white ellipse at the ship's cannon.
- Two-phase lifetime: first 40ms full opacity, next 40ms fade out → kill at 80ms.

### Screen Shake

- `ScreenShake` — not a sprite, standalone class.
- `trigger(intensity, duration_ms)` — activates with initial strength.
- `update(dt)` — decays linearly, random jitter offsets shrink with decay.
- Offset applied to `game_surf` blit position in `_draw()`.

### Level Transition

- 2000ms transition at game start ("LEVEL 1 / Get ready...") and between levels ("LEVEL N CLEAR / Get ready...").
- During transition, only particles and flash_fx update (no gameplay).
- Player bullets and enemy bullets are emptied on transition.

---

## Dependencies & Running

### Install

```bash
pip install -r requirements.txt
# or just:
pip install "pygame>=2.0,<3.0"
```

### Run

```bash
python3 main.py
```

### Headless (no display) for CI/Scripts

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -c "
import pygame
pygame.display.init()
pygame.display.set_mode((1000, 700))
# ... then run game logic
"
```

Required before any Pygame display call in headless environments. No test framework — all tests are ad-hoc.

---

## Interesting Design Decisions

### `dt`-Based Timers (not `pygame.time.get_ticks()`)

All particle/flash/shake timing uses `dt` (delta time from `clock.tick()`) passed to `update(dt)`. This is critical for headless operation — `pygame.time.get_ticks()` returns 0 in a dummy video driver environment, which would break timers. The exception is player invulnerability (`INVULNERABLE_MS`), which still uses `pygame.time.get_ticks()` — this could be a bug in headless mode.

### `game_surf` Double-Buffering

The game renders to an intermediate `game_surf` (700×700) instead of directly to the screen. This allows:
1. Screen shake offset applied to the full game surface.
2. Clean separation between game area and info panel (300px sidebar).
3. The game surface is blitted at `(sx, sy)` with shake offset; the info panel is drawn directly on `screen`.

### Deferred Accuracy Tracking (`_pending_shots`)

Accuracy isn't tracked at bullet creation time. Instead, bullets go into `_pending_shots`. When they die (off-screen or collision), `_resolve_shots()` counts them as "fired". This elegantly handles the edge case where bullets are destroyed by level transitions (`player_bullets.empty()` in `_advance_level`): those bullets die without ever being counted as "fired", which is arguably correct since they never had a chance to hit anything.

### Speed Scaling with Remaining Enemies

```python
mult = 1 + 0.7 * (1 - remaining / initial_count)
# speed = ENEMY_BASE_SPEED * mult
```

As enemies are destroyed, the formation speeds up linearly from 1.0× (full) to 1.7× (last enemy). This creates natural difficulty progression within each level.

### 3-Bullet Limit + Shot Delay

Players can have at most 3 bullets on screen simultaneously, with a 250ms cooldown between shots. This forces precision over spam.

### Level Gain of Life

Clearing a level grants an extra life (up to 5 total). Combined with only 3 starting lives, this rewards survival through early levels but keeps the cap tight.

### Self-Contained Sound Synthesis

All 7 sounds are generated from mathematical functions — sine/square waves, noise, and frequency sweeps. No WAV/MP3 files, no external dependencies. This makes the project fully portable and zero-asset.
