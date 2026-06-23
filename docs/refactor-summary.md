# Refactor Summary — Space Vanguard

## Goal

Apply design principles (SRP, KISS, Composition over Inheritance) to reduce coupling, make code testable, and ease future extensions (new power-ups, enemies, game modes).

## Changes by file

### `events.py` — new
- `CollisionEvent` dataclass with fields `points`, `x`, `y`, `color`, `sound`, `explosion_count`.
- All `collision.py` functions return `list[CollisionEvent]` instead of mutating `game` directly.

### `collision.py` — rewritten
- 6 independent functions, each receives explicit parameters (no `game`).
- Return `(list[CollisionEvent], int)` — events + updated streak.
- `check_enemy_collisions` went from 75 lines mutating `game` to ~35 functional lines.
- `check_player_hit` receives `player, enemy_bullets, kamikazes, minions` and returns `bool` + streak reset.

### `score.py` — new
- `ScoreKeeper` groups: `score`, `high_score`, `streak`, `multiplier`, `score_popups`, `persistence` (`high_score.json`).
- Replaces loose attributes `game.score`, `game.high_score`, `game.score_popups`, etc.
- Tests patch `score.HIGH_SCORE_FILE` via `conftest.py`.

### `starfield.py` — new
- `StarField` encapsulates star generation, update, and `draw_on(surface)`.
- Removes inline loop in `renderer.py`.

### `powerup_manager.py` — new
- `PowerUpManager` with `cooldown`, `try_spawn(x, y)`, `message_timer`, `message_text`.
- Replaces logic scattered across `game.py` and `collision.py`.

### `ufo_manager.py` — new
- `UfoManager` with spawn/despawn timers, single `ufo` reference.
- `update(dt, level)`, `despawn()`, `reset()`.

### `boss_manager.py` — new
- `BossManager` handles boss lifecycle, shooting (3 patterns), minion spawning.
- `update(dt, player_center_x, enemy_bullets, minion_group)`.
- Boss tests now inject `boss_manager` instead of manipulating `game.boss`.

### `sprites/player.py` — refactored
- `TimedEffects` dataclass with 7 fields (`spread`, `shield`, `speed`, `rapid`, `pierce`, `score`, `slowmo`).
- `POWERUP_FIELD_MAP: dict[PowerUpType, str]` maps each power-up to its corresponding field.
- Removes 7 dynamic `setattr` calls in `apply_powerup` — now uses `setattr(self.effects, field, duration)`.

### `shooting.py` — refactored
- `handle_enemy_shooting` receives explicit params `(formation, player, level, enemy_bullets, sound, last_dt_ms)`.
- No reference to `game`.

### `levels.py` — simplified
- Only `create_bunkers` remains.
- `advance_level(game)`, `reset_game(game)`, `handle_transition_end(game)` delegate to `Game` methods.

### `renderer.py` — refactored
- `SceneState` dataclass with 23 fields describing the entire frame to draw.
- `draw(scene: SceneState)` — single function instead of separate state-based functions.
- Removes `game` parameter — caller constructs `SceneState`.

### `game.py` — rewritten (orchestrator)
- `__init__`: instantiates all managers.
- `_update(dt)`: delegates to managers and collision checks, processes `list[CollisionEvent]` (score, popups, sound, particles).
- `_build_scene()`: builds `SceneState` for the renderer.
- `_advance_level()`, `_reset_game()`: extracted transition logic.
- `__init__` dropped from ~100 to ~50 lines.

### `tests/test_game.py` — adapted
- `game.score_keeper.score` replaces `game.score`.
- `game.score_keeper.streak` replaces `game.streak`.
- Tests that call collision checks directly now also call `ufo_manager.despawn()`.
- `test_powerup_spawns_on_enemy_kill` adapted to the new event flow.
- 147 tests passing.

### `tests/conftest.py` — updated
- Patches `score.HIGH_SCORE_FILE` via monkeypatch (previously patched `game.HIGH_SCORE_FILE`).

## Bugs fixed during refactor

1. **Enemy not removed after collision** (`collision.py:check_enemy_collisions`). Missing `enemy.kill()` when `killed=True`. Event was generated (score increased) but the sprite stayed alive.
2. **UFO stayed alive after collision in test** — test called `check_ufo_collision` but didn't invoke `ufo_manager.despawn()`, which is the caller's responsibility.

## Principles applied

| Principle | Example |
|-----------|---------|
| **Single Responsibility** | Each manager (ScoreKeeper, UfoManager, BossManager) does one thing. |
| **KISS** | TimedEffects dataclass replaces 7 dynamic setattr calls. |
| **Composition > Inheritance** | Game composes managers instead of inheriting or having monolithic methods. |
| **Dependency Inversion** | Collision functions receive parameters, don't depend on `game`. |
| **Tell, Don't Ask** | Game sets up, managers handle their internal state. |

## Final structure

```
main.py → Game.run() loop
game.py  → state machine, _update orchestrator, SceneState builder
collision.py → 6 collision check functions, return events
events.py → CollisionEvent dataclass
score.py  → ScoreKeeper (score, streak, popups, persistence)
starfield.py → StarField
powerup_manager.py → PowerUpManager
ufo_manager.py → UfoManager
boss_manager.py → BossManager
renderer.py → SceneState + draw()
shooting.py → enemy shooting logic (no game)
levels.py → create_bunkers + delegation to Game
sprites/ → Player, Enemy/EnemyFormation, Bullet, UFO, Bunker, Kamikaze, Minion
ui/ → InfoPanel
classes/ → Enums (GameState, Difficulty, PowerUpType, EnemyType)
settings.py → constants
sounds.py → audio synthesis
```
