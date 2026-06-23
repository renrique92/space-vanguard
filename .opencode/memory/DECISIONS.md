# Decisiones de Diseño — Space Vanguard

<!-- Decisiones vigentes. Actualizar cuando cambie algo. -->

| Fecha | Decisión | Razón | Contexto |
|-------|----------|-------|----------|
| 2026-06-21 | **UFO saucer con puntos aleatorios** | Nave voladora que cruza la pantalla. Puntos variables (50-300), spawn aleatorio cada 8-15s. Dirección random. | `sprites/ufo.py`, `game.py:_update_ufo` |
| 2026-06-21 | **Bunkers con patrón tipo arco** | 3 bunkers con patrón brick. Destrucción progresiva por colisiones. Ambos tipos de balas destruyen bricks. | `sprites/bunker.py`, `settings.py:BUNKER_*` |
| 2026-06-21 | **Animación enemigos: 2 frames alternados** | Cada Enemy tiene `frame_a`/`frame_b`. Alterna cada 500ms via dt timer. Posición de ojos cambiada entre frames. | `sprites/enemy.py:15-32` |
| 2026-06-21 | **BGM sintetizado con loop interno** | Bucle de 8 notas (110-165 Hz) a 140bpm, square wave con armónicos. Loop -1 en channel dedicado. | `sounds.py:_generate_bgm()` |
| 2026-06-21 | **GameState enum en settings.py** | Evita import circular con renderer.py. 5 estados: INTRO, PLAYING, PAUSED, GAME_OVER, WIN. | `settings.py:125-131` |
| 2026-06-21 | **Renderer class separada de Game** | Separa dibujado de lógica de juego. Renderer recibe parámetros explícitos, sin acceso a Game. | `renderer.py` |
| 2026-06-21 | **Player.invulnerability dt-based** | Migrado de get_ticks() a dt acumulado. Consistente con effects.py, funciona en headless. | `sprites/player.py:32-41` |
| 2026-06-21 | **Tests headless con pytest** | 54 tests con SDL_VIDEODRIVER=dummy en conftest.py. Cubren init, loop, colisiones, transiciones, score. | `tests/` |
| 2026-06-21 | **Sistema de memoria `.opencode/memory/`** | 3 archivos: DECISIONS.md (tabla), GOTCHAS.md (secciones por dominio), SESSION_LOG.md (diario). Convención Niikiis adaptada. | `.opencode/memory/` |
| 2026-06-21 | **R restart solo en GAME_OVER/WIN** | Evitar resets accidentales durante partida. R fuera de controles del panel. | `game.py:91` |
| 2026-06-21 | **Speed scaling: factor 0.7** | Curva menos agresiva que 2.0. Velocidad máxima 1.7× en lugar de 3.0×. | `sprites/enemy.py:61` |
| 2026-06-21 | **ENEMY_SHOOT_RATE_PER_ENEMY = 0.00025** | Disparos enemigos menos frecuentes por unidad. | `settings.py:116` |
| 2026-06-21 | **ENEMY_AUTO_STEP_INTERVAL = 4000ms** | Paso automático más lento (antes 3000ms). | `settings.py:45` |
| 2026-06-21 | **reset(reset_lives=False) en level advance** | Evita que las vidas se reinicien a 3 al avanzar de nivel. | `game.py:319`, `sprites/player.py:23` |
| 2026-06-21 | **.gitignore: .claude/, .opencode/, .agents/ gitignoreados** | Directorios de herramientas de IA no deben versionarse. | `.gitignore:6-9` |
| 2026-06-15 | **5 niveles con config pattern/colors/points** | Formaciones definidas como matrices 2D en settings.py, fáciles de modificar. | `settings.py:55-107` |
| 2026-06-15 | **+1 vida por nivel (max 5)** | Recompensa por sobrevivir, pero con tope duro. | `game.py:203-205` |
| 2026-06-15 | **Score multiplier por nivel (3.0×→0.3×, decay 1.0×/10s)** | Rompe el techo de 800 puntos. Obliga a jugar rápido. Resetea en cada nivel. | `game.py:115-117`, `settings.py:120-122` |
| 2026-06-15 | **Deferred accuracy con _pending_shots** | Balas destruidas en transición no cuentan como disparos fallados. | `game.py:66`, `game.py:308-312` |
| 2026-06-15 | **game_surf intermedia para screen shake** | Shake offset aplicado al blit de game_surf, no a sprites individuales. Panel no se sacude. | `game.py:68`, `game.py:232-234` |
| 2026-06-15 | **dt-based timers en effects (no get_ticks)** | pygame.time.get_ticks() devuelve 0 en headless (SDL_VIDEODRIVER=dummy). | `effects.py:20-21`, `effects.py:51` |
| 2026-06-15 | **Game area 700px + Panel 300px** | Split 70/30. game_surf = 700×700, panel dibujado directo en screen. | `settings.py:7-8`, `game.py:68` |
| 2026-06-15 | **Sonido sintetizado sin assets externos** | 7 sonidos generados con array.array + math. Frecuencia 22050Hz, 16-bit signed mono. | `sounds.py:38-73` |
| 2026-06-15 | **SHOT_DELAY 250ms + max 3 balas simultáneas** | Fuerza precisión sobre spam. | `settings.py:35-36`, `game.py:99-101` |
| 2026-06-15 | **State machine: PLAYING / GAME_OVER / WIN / transitioning** | Transiciones de 2s con "LEVEL N CLEAR" / "Get ready..." y sonido. | `game.py:33`, `game.py:199-211` |
| 2026-06-22 | **Collision system extraído a módulo separado** | 7 funciones modulares que reciben Game instance. Cada función muta game in-place. Menos boilerplate que una clase CollisionSystem. | `collision.py` |
| 2026-06-22 | **Level management extraído a módulo separado** | advance_level(), reset_game(), create_bunkers(), handle_transition_end(). Mismo patrón que collision.py. | `levels.py` |
| 2026-06-22 | **Streak system: bonus lineal por kills consecutivas** | +1-99 pts extra por kill, resetea al recibir daño. Se muestra en panel. Persiste entre niveles. | `collision.py:handle_enemy_collisions`, `ui/info_panel.py` |
