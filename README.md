# Space Vanguard

Classic Space Invaders clone built with Python and Pygame. Pure geometric shapes — zero external assets (images, fonts, audio files). 5 levels, synthesized sound, visual effects, persistent high score.

---

## Vibe Coding & AI Tooling

This project was built entirely through **Vibe Coding** — iterative prompting with an AI assistant via [opencode](https://opencode.ai). No code was written directly by a human; every line was generated, reviewed, and refined through natural language conversations.

### Tools

| Tool | Role |
|------|------|
| [opencode](https://opencode.ai) | AI coding assistant (CLI-based, agentic) |
| Model | `deepseek-v4-flash-free` |
| Platform | macOS (darwin), local |

### Memory System

`.opencode/memory/` stores persistent project context read by opencode at session start:

| File | Purpose |
|------|---------|
| `DECISIONS.md` | Design decisions log — rationale for every architectural choice |
| `GOTCHAS.md` | Traps, bugs, non-obvious behaviors — **read before editing effects/sounds/game** |
| `SESSION_LOG.md` | Diary of each session — what was done, metrics, decisions, findings |

### Agent Instructions

`AGENTS.md` at the repo root configures opencode's behavior for this project:
- Test commands, run commands, game loop conventions, sound engine details
- Memory system references, code structure, special attack rules
- **Caveman mode** (terse Spanish responses by default)

### Installed Skills

Skills are reusable automation workflows installed via opencode's registry. Each lives under `.agents/skills/<name>/`:

| Skill | Source | Purpose |
|-------|--------|---------|
| `python-executor` | `inferen-sh/skills` | Sandboxed Python execution for data processing, scraping, image/video/3D operations |
| `python-testing-patterns` | `wshobson/agents` | pytest strategies: fixtures, mocking, TDD, comprehensive test suites |

Locked via `skills-lock.json` with content-hash verification.

### Transparency

All AI-generated context, decisions, gotchas, and agent configuration are tracked in version control alongside the source code. Nothing is hidden — the full development process is reproducible from the commit history and memory logs.

---

| Property | Value |
|----------|-------|
| Language | Python 3.9+ |
| Framework | Pygame 2.x |
| Lines of code | ~3000 |
| External assets | None |
| Test framework | pytest (133 tests, headless via SDL_VIDEODRIVER=dummy) |

---

## File Structure

```
space_vanguard/
├── main.py              # Entry point, pygame init → Game.run() → pygame.quit()
├── game.py              # Core: state machine, game loop, orchestration, input
├── settings.py          # All tunable constants: speeds, colors, levels, scoring, power-ups, difficulty, special attack
├── sounds.py            # Synthesized sound engine (12 sounds, BGM, no audio files)
├── effects.py           # Particle system, muzzle flash, screen shake
├── collision.py         # Modular collision handlers (enemy, boss, bunker, UFO, power-up, player hit, state checks)
├── levels.py            # Level management: advance, reset, bunkers, transition end
├── shooting.py          # Enemy shooting logic (slowmo-aware, bullet variants)
├── renderer.py          # All drawing, screen shake, overlays, title screen
├── utils.py             # Single helper: draw_text()
├── requirements.txt     # pygame>=2.0,<3.0
├── high_score.json      # Persistent high score (gitignored, created at runtime)
├── classes/
│   └── difficulty.py    # Difficulty enum (EASY/NORMAL/HARD)
├── sprites/
│   ├── player.py        # Player ship — movement, invulnerability, polygon drawing, special charge
│   ├── enemy.py         # Enemy (single) + EnemyFormation (grid logic, shooting, auto-step, animation)
│   ├── bullet.py        # Bullet — player (cyan, upward) / enemy (orange, downward, wiggle/fast variants)
│   ├── ufo.py           # UFO saucer — random direction, random points, sweep sound
│   └── bunker.py        # Destructible bunker — brick grid with progressive destruction
└── ui/
    └── info_panel.py    # Right-side HUD: score, high score, lives, multiplier, streak, power-up badge
```

---

## Architecture Summary

### Modules & Responsibilities

| Module | Key Classes / Functions | Role |
|--------|------------------------|------|
| `main.py` | `main()` | Bootstrap Pygame, create `Game`, run loop, quit. |
| `game.py` | `Game` | State machine, game loop, input, orchestration of all modules. |
| `settings.py` | — | Single source of truth for all gameplay constants. |
| `sounds.py` | `SoundManager` | Generates 12 synthesized sounds + BGM at 22050 Hz, 16-bit signed mono. |
| `effects.py` | `Particle`, `MuzzleFlash`, `ScreenShake`, `spawn_explosion()` | Visual VFX. |
| `collision.py` | `handle_*` (7 functions) | All collision logic: enemy/boss/bunker/UFO/power-up/player-hit/state-checks. |
| `levels.py` | `advance_level()`, `reset_game()`, `create_bunkers()`, `handle_transition_end()` | Level lifecycle. |
| `shooting.py` | `handle_enemy_shooting()` | Enemy shooting: slowmo factor, bullet variants (wiggle/fast). |
| `renderer.py` | `Renderer` | All drawing: game area, info panel, overlays, shake, title screen. |
| `utils.py` | `draw_text()` | Text rendering helper (centered or left-aligned). |
| `classes/difficulty.py` | `Difficulty` enum | EASY, NORMAL, HARD with presets in settings. |
| `sprites/player.py` | `Player` | Ship movement, hit/invulnerability, special charge/beam state, power-up support. |
| `sprites/enemy.py` | `Enemy`, `EnemyFormation` | Enemy + formation: movement, shooting, auto-step-down, 2-frame animation, speed scaling. |
| `sprites/bullet.py` | `Bullet` | Projectile with direction, ownership, off-screen cleanup, wiggle/fast variants. |
| `sprites/ufo.py` | `UFO` | Flying saucer: random direction/points, sweep sound. |
| `sprites/bunker.py` | `Bunker` | Brick-grid bunker with progressive destruction. |
| `ui/info_panel.py` | `InfoPanel` | Right-side stats panel: score, high score, lives, multiplier, streak, power-up badge, controls. |

### Key Relationships

```
Game
 ├── owns: Player, EnemyFormation, SoundManager, ScreenShake, UFO
 ├── owns: 5 sprite Groups (player_bullets, enemy_bullets, particles, flash_fx, powerups)
 ├── owns: InfoPanel (rendered separately via Renderer)
 ├── delegates collision to collision.py (7 handler functions)
 ├── delegates level logic to levels.py (advance, reset, bunkers, transition)
 ├── delegates enemy shooting to shooting.py (slowmo-aware, variants)
 ├── creates Bullet instances on shoot
 ├── calls spawn_explosion() → Particle Group on enemy death
 └── updates everything via _update(dt)

EnemyFormation
 └── owns: pygame.sprite.Group of Enemy instances
     └── Enemy has: rect, points, get_shoot_position(), 2 animation frames

Renderer
 └── receives explicit state from Game, draws game_surf + info panel + overlays
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
2. `player.update(dt)` — invulnerability blink, power-up timers
3. `formation.update(dt)` — move formation, reverse at edges, speed up as enemies die, 2-frame animation
4. `auto_step_timer += dt` — periodic auto-step-down every 4s
5. `handle_enemy_shooting(game)` — slowmo-aware, bullet variants (wiggle/fast)
6. `player_bullets.update()` + `enemy_bullets.update()` — move bullets, kill off-screen
7. `particles.update(dt)` + `flash_fx.update(dt)` — age VFX sprites
8. **Collision handlers** (from collision.py):
   - Bunker collisions: player/enemy bullets ↔ bricks
   - Enemy collisions: player bullets ↔ enemies (score ×multiplier, streak bonus, power-up spawn)
   - Boss collisions: player bullets ↔ boss (HP, particles)
   - UFO collision: player bullets ↔ UFO (score, particles)
   - Power-up collection: player ↔ power-up (activation, timers, ship color)
   - Player hit: enemy bullets ↔ player (life, invulnerability, streak reset, screen shake)
9. **State checks** — `formation.reached_game_over()` (enemies reached bottom?), check level clear, boss defeated
10. **Special beam** (if active) — narrow piercing column kills enemies/bullets every 100ms
11. **Charge update** — `player.add_special_charge(dt)` accumulates charge over ~20s if not damaged

### State Machine

| State | Meaning | Transitions |
|-------|---------|-------------|
| `TITLE` | Difficulty selection screen | SPACE → `INTRO`, LEFT/RIGHT cycles difficulty |
| `INTRO` | Initial level intro ("LEVEL N / Get ready...") | → `PLAYING` after 2000ms |
| `PLAYING` | Normal gameplay | → `transitioning` (level clear), `GAME_OVER`, `WIN` |
| `PAUSED` | Toggle with P | Freezes `_update`, draws overlay |
| `GAME_OVER` | Player dead or enemies reached bottom | Press R → `TITLE` |
| `WIN` | All 5 levels cleared | Press R → `TITLE` |

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
| Z | Special attack beam (when charged, 10px piercing, 2s duration) |
| P | Pause / Resume |
| R | Restart (game over or win screen) |
| F | Toggle fullscreen |
| M | Toggle mute |
| ESC | Quit game |

---

## Scoring System

### Score Multiplier

- Starts at **3.0×** at the start of each level.
- Decays linearly over time: `mult = max(0.3, 3.0 - elapsed_seconds / 10)`.
- Resets to 3.0× at each new level.
- Displayed in the info panel (gold when ≥1.0, red when below).

### Streak / Combo System

- **Streak counter:** increments by 1 for each consecutive enemy kill without taking damage.
- **Resets to 0** when the player is hit, or when a player bullet expires without hitting anything (miss detection).
- **Persists across levels** (does not reset on level advance).
- **Bonus points:** `min(streak, 99)` extra points added on top of base enemy points (capped at 99).
- Displayed in the info panel as "STREAK" with counter. Turns yellow when ≥10.

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

`SoundManager` in `sounds.py` — fully procedural audio synthesis, zero audio files. 12 sounds + BGM.

| Sound | Waveform | Frequency | Duration | Notes |
|-------|----------|-----------|----------|-------|
| `shoot` | Square | 880 Hz | 0.08s | Player laser |
| `enemy_shoot` | Square | 440 Hz | 0.10s | Enemy laser |
| `explosion` | Noise | — | 0.20s | White noise with linear decay |
| `player_hit` | Sine | 150 Hz | 0.30s | Low thud |
| `game_over` | Sine sweep | 440→110 Hz | 0.60s | Descending sweep |
| `win` | Sine sweep | 330→880 Hz | 0.60s | Ascending sweep |
| `ufo` | Square sweep | 200→600 Hz | 0.40s | UFO pass-by |
| `level_up` | Square sweep | 660→1320 Hz | 0.30s | Quick ascending |
| `powerup` | Sine sweep | 440→880 Hz | 0.15s | Power-up collect |
| `special` | Sine | 660 Hz | 0.25s | Special beam activation |
| `special_beam` | Multi-sine | 220+330+440 Hz | 0.80s | Beam hum (looped) |
| `bgm` | Square + harmonics | 110-165 Hz | ~3.4s | 8-note loop at 140bpm |

**Technical details:** 22050 Hz sample rate, 16-bit signed (`array("h")`), mono, 512-byte buffer. `SoundManager` gracefully degrades if Pygame mixer fails to init (`self.available = False`). BGM uses a dedicated channel with `play_bgm()`/`stop_bgm()`.

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
- Offset applied to `game_surf` blit position in `Renderer.draw()`.

### Level Transition

- 2000ms transition at game start ("LEVEL 1 / Get ready...") and between levels ("LEVEL N CLEAR / Get ready...").
- During transition, only particles and flash_fx update (no gameplay).
- Player bullets and enemy bullets are emptied on transition.

### Special Beam

- When activated (Z key, charge ≥ 100%), a 10px-wide piercing beam extends from player ship to top of screen.
- Kills all enemies and enemy bullets in its column every 100ms.
- Player cannot move or shoot while beam is active.
- Beam lasts 2 seconds and drains the charge bar.

### Power-Ups

7 power-up types dropped by enemies on death (20% spawn chance, 20s cooldown):

| Type | Color | Effect | Duration |
|------|-------|--------|----------|
| Spread | Orange | 3-way shot (angles: -15°, 0°, +15°) | 8s |
| Shield | Cyan | Absorbs 1 hit, then expires | Until hit |
| Speed | Lime | 2× ship speed | 6s |
| Rapid | Pink | Shot delay 80ms | 5s |
| Pierce | Purple | Bullets pass through enemies | 6s |
| Score | Gold | Fixed 2× multiplier (overrides decay) | 10s |
| Slowmo | Teal | 0.5× enemy speed, 0.25× shoot rate | 6s |

- Ship color changes to match active power-up; reverts on expiry.
- Collecting a new power-up replaces the current one.
- All expire on level advance or game reset.

### Difficulty Selection

Accessible on the TITLE screen using LEFT/RIGHT arrows. Three presets in `settings.DIFFICULTY_PRESETS`:

| Setting | EASY | NORMAL | HARD |
|---------|------|--------|------|
| Enemy speed | 0.8× | 1.0× | 1.3× |
| Enemy shoot rate | 0.7× | 1.0× | 1.5× |
| Auto-step interval | 1.3× slower | 1.0× | 0.7× faster |
| Initial lives | 5 | 3 | 2 |

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

Required before any Pygame display call in headless environments. Autoconfigured in `tests/conftest.py` for pytest.

### Running Tests

```bash
python3 -m pytest tests/ -v
```

133 smoke tests covering init, game loop, collisions, level transitions, scoring, persistence, particles, power-ups, difficulty, boss, UFO, bunkers, streak, edge cases, render, and performance. All headless (no display needed).

---

## Interesting Design Decisions

### `dt`-Based Timers (not `pygame.time.get_ticks()`)

All particle/flash/shake timing uses `dt` (delta time from `clock.tick()`) passed to `update(dt)`. This is critical for headless operation — `pygame.time.get_ticks()` returns 0 in a dummy video driver environment, which would break timers. Player invulnerability also uses `dt`-based timing (see `sprites/player.py`).

### `game_surf` Double-Buffering

The game renders to an intermediate `game_surf` (700×700) instead of directly to the screen. This allows:
1. Screen shake offset applied to the full game surface.
2. Clean separation between game area and info panel (300px sidebar).
3. The game surface is blitted at `(sx, sy)` with shake offset; the info panel is drawn directly on `screen`.

### Modular Collision & Level Systems

Collision handlers and level management were extracted from `Game` into dedicated modules (`collision.py`, `levels.py`, `shooting.py`). Each function receives the `Game` instance and mutates it in-place — no return values, minimal boilerplate. This keeps `game.py` focused on orchestration rather than implementation.

### Streak / Combo System

A linear streak counter rewards consecutive kills without taking damage. Bonus points scale with streak (capped at 99). The streak resets on damage OR on any player bullet that expires without hitting anything ("miss detection" via before/after snapshot of bullet group). This encourages precision while penalizing spam.

### Special Attack Beam

The charge-based special attack fills over ~20s of not taking damage. When fully charged (Z key), a 10px piercing beam destroys all enemies and bullets in its column for 2 seconds. Design constraints:
- Charge resets to 0 on any damage taken (no charge while invulnerable).
- On level advance, charge is kept at 100% only if fully charged and never used; otherwise resets to 0.
- Player cannot move or shoot while beam is active (forces deliberate aim).

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

### Difficulty Presets

Three selectable difficulty levels (Easy/Normal/Hard) accessible from the title screen. Each preset scales enemy speed, shoot rate, auto-step interval, and starting lives. Selection is displayed with color-coded arrows (`< EASY >` green, `< NORMAL >` gold, `< HARD >` red).

### Self-Contained Sound Synthesis

All 12 sounds are generated from mathematical functions — sine/square waves, noise, frequency sweeps, and multi-harmonic hums. No WAV/MP3 files, no external dependencies. BGM is an 8-note loop at 140bpm played on a dedicated channel via `play_bgm()`/`stop_bgm()`.

### Boss Enemy (Level 5)

Level 5 replaces normal enemies with a single boss. The boss has HP, shoots with shorter intervals and bullet variants (fast bullets, wiggle bullets), and triggers WIN state on defeat. Boss shooting is timer-based (unlike formation shooting) and managed directly in `game.py`.

### Power-Up System

7 power-up types spawn on enemy death (20% chance, 20s cooldown between spawns). Each type has unique visual (ship color change), gameplay effect, and duration. Collecting a new power-up replaces the current one. All expire on level advance or reset.
