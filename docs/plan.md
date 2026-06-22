# Space Vanguard — Plan de Evolución

## Estado Actual

**Núcleo sólido**: game loop, state machine, 5 niveles, 7 power-ups, UFO, bunkers, partículas, screen shake, sonido sintetizado, BGM, HUD, persistencia, 103 tests headless. ~1800 LOC, 0 assets externos.

---

## Áreas de Mejora

### Bugs
1. `game.py` usa `pygame.time.get_ticks()` para shot timing — rompe en headless, inconsistente con resto dt-based
2. `enemy.py:32` resetea `_anim_timer = 0` en vez de `-= ENEMY_ANIM_INTERVAL` — pierde <500ms si hay lag

### Deuda Técnica
3. `settings.py` monolítico (~640 LOC) — levels (250 LOC) + colores + constantes mezclados
4. `Game` class (~400 LOC, 10+ responsabilidades)
5. Cero type hints (~1800 LOC)
6. `EnemyFormation.reset()` nunca llamado — dead code
7. `utils.draw_text()` importado en ninguna parte — dead code
8. Alias `TP = PowerUpType` en settings inconsistente con el resto
9. `BUNKER_HIT_COLOR` definido pero nunca usado

### UX Faltante
10. Sin score popups flotantes ("+30") al matar enemigos
11. Sin death animation (player solo parpadea)
12. Sin parallax scrolling (estrellas estáticas)
13. Sin menú principal / title screen
14. Sin boss final (nivel 5 termina igual)
15. Transiciones entre niveles básicas
16. Sin feedback de daño al jugador
17. Sin variedad de balas enemigas

### Testing
18. Sin tests de renderizado, performance, edge cases (dt=0)
19. Tests acoplados a implementación

---

## Roadmap

### Fase 4 — Polish & Fixes
- [ ] Migrar `get_ticks()` → dt-based en shot timing
- [ ] Fix anim timer drift (`-=` en vez de `= 0`)
- [ ] Score popups flotantes ("+30") al matar enemigos
- [ ] Death animation (explosión player con partículas)
- [ ] Bunker daño visual con `BUNKER_HIT_COLOR`
- [ ] Parallax stars (3 capas de velocidad)
- [ ] Remover dead code (`reset()`, `utils.py`)

### Fase 5 — Boss & Dificultad
- [ ] Boss al final del nivel 5 (enemigo grande multi-hit)
- [ ] Curva de dificultad progresiva entre niveles
- [ ] Variedad de balas enemigas (onduladas, rápido/lento)

### Fase 6 — Menús & Config
- [ ] Title screen (Start, High Scores, Controls)
- [ ] Fullscreen toggle
- [ ] Volumen / mute
- [ ] Pausa automática al perder foco

### Fase 7 — Refactor Estructural
- [ ] Extraer level data → `levels.py`
- [ ] Extraer collision system de Game
- [ ] Type hints progresivos
- [ ] Unificar estilo (eliminar alias `TP`)

### Fase 8 — Gameplay Avanzado
- [ ] Sistema de combos / streak bonus
- [ ] Power-ups combinables (2 activos simultáneos)
- [ ] Dificultad seleccionable

---

## Criterios de Calidad

- Cada cambio verificado con `python3 -m pytest tests/ -v`
- Smoke test manual: `python3 main.py` 10s sin crash
- Commits atómicos por feature
- Sin regresión en tests existentes
