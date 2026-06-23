# Gotchas — Space Vanguard

Trampas, bugs y comportamientos no obvios. **LEER antes de modificar cualquier cosa.**

---

## Headless / CI

### SDL_VIDEODRIVER=dummy es obligatorio antes de pygame.init()
En entornos sin display (CI, scripts), `pygame.display.init()` falla si no se setea:
```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 -c "import pygame; pygame.display.init(); ..."
```
- **MITIGACIÓN:** Usar siempre estas env vars en cualquier test/script headless.
- **NO USAR** `os.environ["SDL_VIDEODRIVER"] = "dummy"` después de importar pygame — debe estar antes.

### dt-based timers en effects, NO pygame.time.get_ticks()
`effects.py` usa `dt` (delta time de `clock.tick()`) para partículas, muzzle flash y screen shake. `pygame.time.get_ticks()` devuelve **0** con `SDL_VIDEODRIVER=dummy`.
- **Archivos afectados:** `effects.py:20,51,75`
- **MITIGACIÓN:** Pasar `dt` como argumento posicional a `update()`. `args[0] if args else 16` como fallback.

---

## Gameplay

### _pending_shots en accuracy tracking
Las balas se agregan a `_pending_shots` al disparar (`game.py:108`). Cuando una bala muere (off-screen o colisión), `_resolve_shots()` la cuenta como "disparada". Las balas destruidas por `player_bullets.empty()` en `_advance_level()` (transición entre niveles) **también pasan por `_resolve_shots()`** porque el empty ocurre en el frame anterior.
- **EFECTO:** Balas vivas en transición se cuentan como falladas. Es correcto — nunca tuvieron chance de pegar.
- **EDGE CASE:** Una bala que pega en el mismo frame que se limpia el grupo: `groupcollide` la mata primero, `has_hit = True`, luego `_resolve_shots()` la cuenta como fired. Hits incrementa antes. OK.

### GameState enum living en settings.py (no game.py)
`GameState` (INTRO, PLAYING, PAUSED, GAME_OVER, WIN) está en `settings.py` para evitar imports circulares con `renderer.py`. Cualquier import debe venir de `settings`, no de `game`.
- **IMPORTAR:** `from settings import GameState`

### self.transition_timer > 0 reemplaza self.transitioning
Ya no existe `self.transitioning` ni `self._game_started`. El temporizador `self.transition_timer` sirve como flag: > 0 = en transición. El estado `INTRO` distingue intro inicial vs transición entre niveles.
- **INTRO:** `state == GameState.INTRO` → "LEVEL N" + no se dibujan enemigos
- **LEVEL TRANSITION:** `state == GameState.PLAYING` + `transition_timer > 0` → "LEVEL N CLEAR" + enemigos visibles
- **NO USAR** `state == "PLAYING"` — siempre comparar con `GameState.PLAYING`

### Renderer no tiene acceso a game internals
`Renderer.draw()` recibe explícitamente todo lo que necesita. No tiene referencia a `Game`. No agregar lógica de juego al renderer.
- **NO MOVER** actualizaciones de estado, colisiones o lógica de juego al renderer.
- **DIBUJAR** solo draw calls de pygame.

### TITLE state necesita pygame.display.flip() explícito
Cuando `draw()` detecta `state == GameState.TITLE`, dibuja directamente en `self.screen` y hace `return` temprano (sin pasar por `_present`). **Debe llamar a `pygame.display.flip()`** antes de return, o la pantalla se queda en negro.

Archivo: `renderer.py:32`

### reset(reset_lives=False) en level advance
`game.py:319` llama `self.player.reset(reset_lives=False)` para preservar vidas al avanzar de nivel. No confundir con `_reset()` (game over/win) que sí reinicia vidas a 3.
- **NO USAR** `Player.reset()` sin argumentos en level advance — reinicia vidas a 3.

### Speed scaling formula
En `sprites/enemy.py:61`:
```python
mult = 1 + 0.7 * (1 - remaining / initial_count)
```
- **Máximo:** 1.7× (cuando solo queda 1 enemigo)
- **Mínimo:** 1.0× (formación completa)
- **NO es** `1 + 2 * (1 - remaining / initial_count)` como en versiones anteriores.

### UFO no está en un sprite group
`sprites/ufo.py` crea UFO como sprite pero no lo agrega a ningún `pygame.sprite.Group`. `alive()` siempre devuelve `False`. No usar `alive()` para detectar off-screen; usar `rect.left > GAME_WIDTH` o `rect.right < 0`.
- **CHECK:** `game.py:_update_ufo()` usa posiciones de rect, no `alive()`.

### Bunkers: grupo de bricks por bunker
Cada bunker es un `Bunker()` con `self.bricks` (pygame.sprite.Group). Se usa `groupcollide()` entre bullets y bricks para destrucción progresiva. No hay sprite único para el bunker completo.
- **RENDER:** `bunker.bricks.draw(game_surf)` en renderer.

### Animación enemigos: dt en formation.update()
`game.py` ahora pasa `dt` a `formation.update(dt)`, que lo propaga a `self.enemies.update(dt)`. Cada Enemy alterna entre `frame_a` y `frame_b` cada `ENEMY_ANIM_INTERVAL` ms.
- **NO OLVIDAR** pasar `dt` si se llama `formation.update()` desde otro lugar.

### BGM loop gestionado por SoundManager
`SoundManager.play_bgm()` / `stop_bgm()` controlan un channel dedicado (`self._bgm_channel`). BGM se inicia al finalizar INTRO y se detiene en GAME_OVER/WIN.
- **NO USAR** `sounds["bgm"].play(loops=-1)` directamente — usar `play_bgm()`.
- **NO ASUME** mixer disponible — método seguro si `self.available = False`.

### ENEMY_SHOOT_RATE_PER_ENEMY = 0.00025
La tasa de disparo total es `ENEMY_SHOOT_RATE_BASE + ENEMY_SHOOT_RATE_PER_ENEMY * len(enemies)`. Con 20 enemigos: `0.015 + 20 * 0.00025 = 0.02` → ~2% por frame.
- **NO duplicar** este valor sin rebalancear todo.
- **ESCALA CON ENEMIGOS:** Más enemigos vivos = más disparos. La formación dispara menos al irse limpiando.

---

## Screen Shake

### Offset aplicado al blit, no a sprites
`ScreenShake.get_offset()` devuelve `(int(x), int(y))` y se aplica en la posición del `game_surf.blit()` en `game.py:234`. El panel derecho NO se sacude porque se dibuja directamente sobre `self.screen`.
- **NO APLICAR** offset a sprites individuales.
- **CLAMPING:** El offset no se clamp ea explícitamente, pero game_surf es 700px y screen es 1000px → hay 300px de margen a la derecha. Visualmente correcto.

---

## Sonido

### SoundManager degrada gracefulmente
Si `pygame.mixer.init()` falla, `self.available = False` y `play()` es no-op.
- **EFECTO:** Juego funcional sin sonido. No crashea.
- **NO ASUME** que `play()` siempre funciona. Verificar `self.available` si se añade lógica nueva de sonido.


