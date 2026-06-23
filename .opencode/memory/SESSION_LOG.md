# Session Log — Space Vanguard

---

## [2026-06-22] Sesión — Fase 7c + 8a: Alias TP eliminado + Sistema Streak/Combo

**Branch:** `main` (commit directo `1e565e6`)
**Archivos modificados:** `settings.py`, `game.py`, `collision.py`, `levels.py`, `renderer.py`, `ui/info_panel.py`, `docs/plan.md`

### Qué se hizo

1. **Fase 7c — Eliminar alias `TP`** — Reemplazadas 14 referencias `TP.SPREAD` → `PowerUpType.SPREAD` en `POWERUP_DURATIONS` y `POWERUP_SHIP_COLORS` dentro de `settings.py`. Línea `TP = PowerUpType` eliminada. Consistencia de estilo restaurada.

2. **Fase 8a — Sistema de Streak/Combo**:
   - `game.streak`: contador de kills consecutivas sin recibir daño
   - Incrementa por cada enemigo destruido en `handle_enemy_collisions`
   - Se resetea a 0 al recibir daño (`handle_player_hit`) y al resetear partida
   - Persiste entre niveles (no se resetea en `advance_level`)
   - Bonus por kill: `int(enemy.points * mult) + min(streak, 99)` pts extra
   - Display "STREAK" en panel derecho, se vuelve amarillo si ≥ 10
   - 103 tests green + smoke test OK

## [2026-06-22] Sesión — Fase 7b: Extraer level management a levels.py

**Branch:** `main` (commit directo `eb2bdcf`)
**Archivos creados:** `levels.py`
**Archivos modificados:** `game.py`, `tests/test_game.py`

### Qué se hizo

1. **Level management extraído a `levels.py`** — 4 funciones modulares:
   - `advance_level(game)` — incrementa nivel, resetea timers, nueva formación, bunkers
   - `reset_game(game)` — reset completo del juego (score, estado, formación nivel 1)
   - `create_bunkers()` — factory de bunkers (antes `_create_bunkers` estático)
   - `handle_transition_end(game)` — maneja fin de transición (INTRO→PLAYING o level advance)

2. **game.py simplificado** — se removieron 3 métodos (`_advance_level`, `_reset`, `_create_bunkers`), ~70 LOC menos. La lógica de transición en `_update` ahora delega en `handle_transition_end(self)`.

3. **Tests actualizados** — las 12 referencias a `game._advance_level()` y `game._reset()` reemplazadas por `advance_level(game)` y `reset_game(game)`.

### Métricas

| Archivo | Antes | Después |
|---------|-------|---------|
| `game.py` | 420 LOC | 368 LOC (-52) |
| `levels.py` | — | 54 LOC (nuevo) |

## [2026-06-22] Sesión — Fase 7: Refactor collision system + type hints

**Branch:** `main`
**Commits:** Sin commit (sin autorización)
**Archivos creados:** `collision.py`
**Archivos modificados:** `game.py`

### Qué se hizo

1. **Collision system extraído a `collision.py`** — 7 funciones modulares que reciben `Game` instance:
   - `handle_bunker_collisions` — colisiones balas ↔ bricks
   - `handle_enemy_collisions` — colisiones balas player ↔ enemigos (score, powerup spawn, score popups, particles)
   - `handle_boss_collisions` — colisiones balas player ↔ boss (hits, particles, score popups)
   - `handle_powerup_collection` — player ↔ powerup (activación, sonido, mensaje)
   - `handle_player_hit` — player ↔ balas enemigas (vida, explosión, screen shake, game over)
   - `handle_ufo_collision` — UFO ↔ balas player (score, particles, respawn schedule)
   - `handle_game_state_checks` — game over por formación, level advance, boss win

2. **Type hints añadidos** — Todos los métodos de `Game` ahora tienen firmas con tipos (`-> None`, `-> list`, `-> int`).

3. **Imports no usados removidos** — `spawn_explosion`, `Boss`, `PowerUp` ya no se importan en `game.py`.

### Métricas

| Archivo | Antes | Después |
|---------|-------|---------|
| `game.py` | 553 LOC | 420 LOC (-133) |
| `collision.py` | — | 143 LOC (nuevo) |

### Decisiones
- Funciones modulares > clase CollisionSystem (menos boilerplate, acceso directo a `game.*`).
- Cada función muta `game` in-place, sin return value (salvo `handle_ufo_collision` que retorna bool para early-exit).
- Type hints solo en `game.py` (core); `collision.py` mantiene duck typing.

## [2026-06-23] Sesión — Eliminar accuracy + streak miss detection

**Branch:** `main`
**Commits:** (aún sin commit)

### Qué se hizo

1. **Accuracy removido del panel** — Eliminado contador de puntería. Streak movido a su lugar. Eliminado `_pending_shots`, `shots_fired`, `shots_hit`, `_resolve_shots`, propiedad `accuracy` de game.py.

2. **Streak resetea al fallar disparos** — Snapshot de `player_bullets` antes de `update()`. Tras colisiones, checkea balas que murieron sin `has_hit=True` → streak = 0.

3. **Fix: boss collision** — `bullet.has_hit = True` en `handle_boss_collisions`.

4. **Tests**: 2 nuevos (miss resets, hit preserves), 6 eliminados (accuracy). Total: 133.

### Archivos
- `ui/info_panel.py` — accuracy out, streak up
- `renderer.py` — sin accuracy param
- `game.py` — miss detection + dead code cleanup
- `collision.py` — boss has_hit fix, remove shots_hit
- `levels.py` — remove shots_fired/shots_hit/_pending_shots
- `tests/test_game.py` — 2 new, 6 removed

---

## [2026-06-23] Sesión — Fase 9 completa: shooting.py + tests

**Branch:** `main` (commit `338f075`)
**Archivos creados:** `shooting.py`
**Archivos modificados:** `game.py`, `levels.py`, `tests/test_game.py`, `docs/plan.md`

### Qué se hizo

**Fase 9.1 — Extraer enemy shooting logic:**
- Creado `shooting.py` con `handle_enemy_shooting(game)` siguiendo patrón de `collision.py`
- Reemplazó líneas 220-243 de `game.py` (slowmo check + level-based bullet variants + sound)
- Boss shooting (timer + `boss.update(dt)`) permanece en `game.py`
- 103 tests green + smoke OK

**Fase 9.2 — Tests de edge cases, render, performance:**
- 23 tests de edge cases: TITLE early return, formación vacía/bunkers vacíos, GAME_OVER por reach enemies, _create_bullet al límite, score popups expiran, estrellas wraparound, auto-step empty, dificultad EASY/HARD lives, streak incrementa/resetea/persiste/caps 99, boss shoot/take_hit/kill
- 8 tests de renderizado: cada estado (TITLE/INTRO/PLAYING/PAUSED/GAME_OVER/WIN) + boss+powerups+popups
- 3 tests de performance: 100 frames <2s, stress 50 bullets ambas direcciones, stress 20 explosiones
- Total: 137 tests (103 → 137)

**Además:**
- Fix: bunkers centrados en game area (restar `bunker_w // 2` en `levels.py::create_bunkers()`)
- Fase 8 marcada completa en plan.md
- Fase 9 completa en plan.md

### Próximos Pasos
- Sin roadmap definido más allá de Fase 9.
---

## [2026-06-22] Sesión — Fase 8b: Dificultad seleccionable

**Branch:** `main` (commit `3bb2c33`)
**Archivos creados:** `classes/difficulty.py`
**Archivos modificados:** `classes/__init__.py`, `settings.py`, `sprites/enemy.py`, `game.py`, `levels.py`, `renderer.py`, `docs/plan.md`

### Qué se hizo

1. **Fix: bunkers centrados** — Se restó `bunker_w // 2` para centrar cada bunker en su posición `spacing * i`. Antes el borde izquierdo estaba en esa posición. Simetría perfecta: 135px de margen a cada lado.
2. **Fix: pygame.display.flip()** en TITLE state — Se restauró `flip()` y el render de estrellas en pantalla completa que se había perdido en el refactor.

3. **`Difficulty` enum** — `classes/difficulty.py` con EASY, NORMAL, HARD.
2. **`DIFFICULTY_PRESETS`** en settings — Multiplicadores: speed (0.8-1.3x), shoot rate (0.7-1.5x), auto_step (1.3-0.7x), vidas (5/3/2).
3. **Title screen** — LEFT/RIGHT ciclan dificultad, display `< EASY >` / `< NORMAL >` / `< HARD >` con color verde/dorado/rojo. SPACE inicia con la dificultad seleccionada.
4. **`EnemyFormation.__init__`** acepta `diff_mult` opcional que escala speed, shoot y auto_step_ms.
5. **`levels.py`** pasa el preset de dificultad a `EnemyFormation` y setea `player.lives` en `reset_game`/`advance_level`.
6. **103 tests green + smoke OK**.

### Pendientes
- [x] Extraer level management (`_advance_level`, `_reset`, level transition) a `levels.py`.
- [x] Eliminar alias `TP` en settings.py (Fase 7c).
- [x] Sistema de streak/combo (Fase 8a).
- [x] Dificultad seleccionable.
- [ ] ~~Power-ups combinables~~ (descartado).
- [ ] Extraer enemy shooting logic a su propia función.

---

## [2026-06-21] Sesión — Fase 2: UFO, Bunkers, Animación enemigos, BGM

**Branch:** `main`
**Commits:** `8b236b6` (HEAD, Fase 1 commit)

### Qué se hizo

1. **UFO Saucer** — Nave voladora que cruza la pantalla arriba. Spawneo aleatorio (8-15s). Dirección random izquierda/derecha. Puntos aleatorios (50-300). Sonido propio (sweep 200→600Hz). Se destruye con 1 bala del player.

2. **Bunkers** — 3 barricadas con patrón tipo arco (45 bricks c/u). Colisión con balas player y enemigas. Se regeneran cada nivel. Colocación espaciada automática.

3. **Animación enemigos** — 2 frames por enemy. `frame_a`: ojos centrados. `frame_b`: ojos desplazados. Alternan cada 500ms. `formation.update(dt)` propaga dt a cada Enemy.

4. **BGM** — Loop de 8 notas (110-165 Hz, 140bpm) generado con square wave + armónicos. Inicia al salir de INTRO. Se detiene en GAME_OVER/WIN.

### Métricas

| Antes | Después |
|-------|---------|
| `game.py`: 271 LOC | `game.py`: 349 LOC (+78, UFO + bunkers + BGM) |
| `sprites/`: 2 files | `sprites/`: 4 files (+ufo.py, +bunker.py) |
| `sounds.py`: 75 LOC | `sounds.py`: 105 LOC (+30, BGM generation) |
| `renderer.py`: 108 LOC | `renderer.py`: 113 LOC (+5, ufo + bunkers draw) |
| `settings.py`: 132 LOC | `settings.py`: 151 LOC (+19, ufo + bunker + anim constants) |
| `tests/test_game.py`: 354 LOC | `tests/test_game.py`: 510 LOC (+156, 21 new tests) |
| **Tests: 54** | **Tests: 75** |

### Decisiones
- UFO sin sprite group (check off-screen via rect, no `alive()`)
- Bunkers = bricks en grupo, collides con groupcollide
- Animación enemigos: 500ms intervalo, 2 frames
- BGM: loop interno generado, channel dedicado, play_bgm/stop_bgm

### Pendientes
- Fase 3: Power-ups, boss final, parallax stars, menús

---

## [2026-06-21] Sesión — Fase 1: tests, player invuln, state enum, Renderer

**Branch:** `main`
**Archivos modificados:** `game.py`, `sprites/player.py`, `settings.py`, `tests/conftest.py`, `tests/test_game.py`, `pytest.ini`, `AGENTS.md`, `README.md`, `.opencode/memory/DECISIONS.md`, `.opencode/memory/GOTCHAS.md`, `.opencode/memory/SESSION_LOG.md`, `renderer.py`

### Qué se hizo

1. **Tests headless (pytest)** — 54 tests en `tests/test_game.py` con `conftest.py` que setea `SDL_VIDEODRIVER=dummy`. Cubren init, loop, colisiones, transiciones, score, persistence, particles. `pytest.ini` configurado.

2. **Player invulnerability dt-based** — `Player.update()` ahora recibe `dt` como primer argumento y usa `self.invuln_timer` (countdown) en vez de `pygame.time.get_ticks()`. Consistente con el resto del codebase. Funciona en headless.

3. **State machine unificada** — Eliminadas 4 flags (`self.state` string, `self.transitioning`, `self._game_started`, `self.paused`). Reemplazadas por `GameState` enum (`INTRO`, `PLAYING`, `PAUSED`, `GAME_OVER`, `WIN`) en `settings.py`. Transiciones manejadas via `self.transition_timer`.

4. **Renderer extraído** — `renderer.py` con `Renderer` class. `Game._draw()` delegó todo su contenido (70+ lines) a `Renderer.draw()`. Separación clara: renderer no tiene acceso a game internals, recibe parámetros explícitos.

### Métricas

| Antes | Después |
|-------|---------|
| `game.py`: 341 LOC | `game.py`: 271 LOC (-70) |
| `sprites/player.py`: 54 LOC | `sprites/player.py`: 55 LOC (+1, invuln timer) |
| `settings.py`: 122 LOC | `settings.py`: 132 LOC (+10, GameState enum) |
| Tests: 0 | Tests: 54 |
| Frameworks de estado: 4 flags | 1 enum |

### Decisiones
- `GameState` en `settings.py` para evitar import circular game → renderer → game
- `Renderer._present()` maneja screen shake, divider, info panel, overlays, flip
- Tests isolan high_score con `monkeypatch` + `tmp_path`
- `conftest.py` fixture skipea INTRO por defecto (tests parten de PLAYING)

### Pendientes
- Fase 2: UFO saucer, bunkers, animación enemigos, música
- Fase 3: power-ups, boss, parallax, menús

---

**Branch:** `main`
**Commits:** `aa81599` (HEAD)
**Archivos modificados:** `README.md`, `.opencode/memory/DECISIONS.md`, `.opencode/memory/GOTCHAS.md`, `.opencode/memory/SESSION_LOG.md`, `AGENTS.md`, `.gitignore`

### Qué se hizo
1. **Análisis de referencia Niikiis** — Se exploraron repos en `/Users/rafaelsendrea/Code/Niikiis/` para entender el sistema de memoria basado en `.claude/memory/` (DECISIONS.md, GOTCHAS.md, SESSION_LOG.md, AGENTS.md).
2. **Adaptación a opencode** — Se replicó la estructura en `.opencode/memory/` en lugar de `.claude/memory/`. Mismas convenciones: español, markdown, tabla para decisions, secciones para gotchas, diario narrativo para session log.
3. **README actualizado** — Se regeneró completo con architecture summary, game loop flow, state machine, 5 level formations, scoring system, sound specs, effects system, design decisions.
4. **Poblado de memoria** — DECISIONS.md con 18 decisiones, GOTCHAS.md con 10 gotchas en 5 dominios, SESSION_LOG.md con 3 entradas (esta es la 3ª).
5. **Commit & push** — `cc78e5a` + `aa81599` pusheados a `origin/main`.

### Decisiones
- `.opencode/memory/` con 3 archivos obligatorios (DECISIONS, GOTCHAS, SESSION_LOG) + AGENTS.md enriquecido con boot memory.
- `.opencode/` añadido a `.gitignore`.
- AGENTS.md referencia a `.opencode/memory/` en sección "Memory".
- Memoria en español (convención Niikiis).

### Descubrimientos
- Player.invulnerability usa `pygame.time.get_ticks()` (inconsistente con el resto dt-based). Potencial bug en headless, pero no crítico para gameplay real.
- `.claude/agents/` en repos Niikiis contiene runbooks ejecutables con comandos shell concretos (no solo guías).
- Niikiis tiene un `commands/save.md` como ritual de cierre de sesión. Podríamos adoptarlo.

### Pendientes
- [ ] **Play test** de los 5 niveles — balanceo fino de formaciones y tasas de disparo.
- [ ] **Win screen** — pulir la pantalla de victoria tras nivel 5.

---

## [2026-06-15] Sesión — Multi-level system, accuracy, difficulty tuning

**Branch:** `main`
**Commits:** `cd37de3`, `8973489`
**Archivos modificados:** `game.py`, `settings.py`, `sounds.py`, `sprites/enemy.py`, `sprites/player.py`, `ui/info_panel.py`, `utils.py`

### Qué se hizo
1. **Sistema multi-nivel** — 5 formaciones distintas (Full Block, Diamond, Skull, Checker Columns, Two-row Fortress) definidas en `settings.py` como configs con pattern/colors/points.
2. **Level transitions** — 2s de pausa con "LEVEL N CLEAR" / "Get ready..." + sonido `level_up`. Enemigos ocultos durante intro inicial.
3. **+1 vida por nivel** — Al limpiar un nivel, +1 vida (max 5). `Player.reset(reset_lives=False)` para preservar vidas.
4. **Score multiplier por nivel** — 3.0× → floor 0.3×, decay 1.0×/10s. Resetea en cada nivel.
5. **Accuracy meter** — Deferred counting con `_pending_shots`. Balas se cuentan como "fired" al morir, no al crearse.
6. **Difficulty tuning** — Speed multiplier 2→0.7, shoot rate 0.0005→0.00025, auto-step 3000→4000ms.
7. **R restart removido del panel** — Solo funciona en GAME_OVER/WIN.
8. **Level indicator** — Badge "L1"–"L5" en top-left del game area.
9. **Imports no usados limpiados** — En `game.py`, `ui/info_panel.py`, `settings.py`.
10. **PRIMERA VEZ que el juego tiene 5 niveles jugables completos.**

### Decisiones
- Speed scaling factor `0.7` para curva menos agresiva (máx 1.7×).
- Auto-step cada 4s (más lento) para dar tiempo al jugador.
- Cada nivel es más difícil no por velocidad base, sino por patrón (menos enemigos = más velocidad relativa + más concentración de disparos).

### Problemas y Soluciones
| Problema | Causa raíz | Solución |
|----------|------------|----------|
| Vidas se reiniciaban a 3 al avanzar nivel | `Player.reset()` sin args | `reset(reset_lives=False)` |
| Multiplicador se mantenía entre niveles | `elapsed_time` no se reseteaba | `self.elapsed_time = 0` en `_advance_level()` |
| Balas vivas al cambiar nivel contaban como fallos | No había limpieza | `player_bullets.empty()` + `_resolve_shots()` captura las muertas |

---

## [2026-06-15] Sesión — Proyecto inicial

**Branch:** `main`
**Commits:** `45fc3f9`, `ae68dd5`, `8973489`
**Archivos creados:** Todos los archivos del proyecto.

### Qué se hizo
- Scaffolding completo del proyecto Space Vanguard.
- `settings.py` con todas las constantes de gameplay.
- `main.py`, `game.py`, `sounds.py`, `effects.py`, `utils.py`.
- `sprites/player.py`, `sprites/enemy.py`, `sprites/bullet.py`.
- `ui/info_panel.py` con panel derecho (score, high score, lives, multiplier, accuracy, controls).
- Sonido sintetizado (7 sonidos, 22050Hz, 16-bit mono).
- Efectos: partículas de explosión, muzzle flash, screen shake.
- README y AGENTS.md iniciales.
- Git init, commit, push a `github.com/renrique92/space-vanguard`.
