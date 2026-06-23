# Space Vanguard — Plan de Evolución

## Estado Actual

**Núcleo sólido**: game loop, state machine, 5 niveles, 7 power-ups, UFO, bunkers, partículas, screen shake, sonido sintetizado, BGM, HUD, persistencia, sistema de streak, 103 tests headless. +2000 LOC, 0 assets externos.

---

## Áreas de Mejora (checkeado contra código real)

### Bugs — ✅ Resueltos
1. ✅ `get_ticks()` migrado a dt-based (Fase 1)
2. ✅ `_anim_timer` usa `-=` (no `= 0`)

### Deuda Técnica
3. `settings.py` monolítico (196 LOC) — manejable, no urgente
4. ~~`Game` class (~400 LOC)~~ → Ahora 370 LOC con 3 módulos extraídos (`collision.py`, `levels.py`, `renderer.py`) ✅
5. ~~Cero type hints~~ → Todos los métodos de `Game` tienen type hints ✅
6. ~~`EnemyFormation.reset()`~~ → No existe en el código actual ✅
7. ~~`utils.draw_text()`~~ → `utils.py` no existe ✅
8. ~~Alias `TP`~~ → Eliminado (Fase 7c) ✅
9. ~~`BUNKER_HIT_COLOR` no usado~~ → Sí se usa en `bunker.py` ✅

### UX — ✅ Implementado
10. ✅ Score popups flotantes (Fase 4)
11. ✅ Death animation con partículas (Fase 4)
12. ✅ Parallax stars 3 capas (Fase 4)
13. ✅ Title screen (Fase 6)
14. ✅ Boss final nivel 5 (Fase 5)
15. ✅ Transiciones entre niveles (Fase 4-5)
16. ✅ Screen shake + flash al recibir daño (Fase 4-5)
17. ✅ Variedad de balas: wiggle, fast, normal (Fase 5)

### Testing
18. Pendiente: tests de renderizado, performance, edge cases
19. Tests algo acoplados, pero refactor ayudó

---

## Roadmap

### ✅ Fase 4 — Polish & Fixes (completada)
### ✅ Fase 5 — Boss & Dificultad (completada)
### ✅ Fase 6 — Menús & Config (completada)
### ✅ Fase 7 — Refactor Estructural (completada)

### Fase 8 — Gameplay Avanzado (en progreso)
- [x] Sistema de combos / streak bonus — +1-99pts extra por kill, resetea al recibir daño
- [ ] Dificultad seleccionable (Easy/Normal/Hard)

---

## Criterios de Calidad

- Cada cambio verificado con `python3 -m pytest tests/ -v`
- Smoke test manual: `python3 main.py` 10s sin crash
- Commits atómicos por feature
- Sin regresión en tests existentes
