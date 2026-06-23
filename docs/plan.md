# Space Vanguard — Evolution Plan

## Current State

**Solid core**: game loop, state machine, 5 levels, 7 power-ups, UFO, bunkers, particles, screen shake, synthesized sound, BGM, HUD, persistence, streak system, 103 headless tests. +2000 LOC, 0 external assets.

---

## Improvement Areas (verified against real code)

### Bugs — Resolved
1. ✅ `get_ticks()` migrated to dt-based (Phase 1)
2. ✅ `_anim_timer` uses `-=` (not `= 0`)

### Technical Debt
3. `settings.py` monolithic (196 LOC) — manageable, not urgent
4. ~~`Game` class (~400 LOC)~~ → Now 370 LOC with 3 extracted modules (`collision.py`, `levels.py`, `renderer.py`)
5. ~~Zero type hints~~ → All `Game` methods have type hints
6. ~~`EnemyFormation.reset()`~~ → Doesn't exist in current code
7. ~~`utils.draw_text()`~~ → `utils.py` doesn't exist
8. ~~`TP` alias~~ → Removed (Phase 7c)
9. ~~`BUNKER_HIT_COLOR` unused~~ → It is used in `bunker.py`

### UX — Implemented
10. Floating score popups (Phase 4)
11. Death animation with particles (Phase 4)
12. Parallax stars 3 layers (Phase 4)
13. Title screen (Phase 6)
14. Level 5 final boss (Phase 5)
15. Level transitions (Phase 4-5)
16. Screen shake + flash on damage (Phase 4-5)
17. Bullet variety: wiggle, fast, normal (Phase 5)

### Testing
18. Pending: render, performance, edge case tests
19. Tests somewhat coupled, but refactor helped

---

## Roadmap

### Phase 4 — Polish & Fixes (completed)
### Phase 5 — Boss & Difficulty (completed)
### Phase 6 — Menus & Config (completed)
### Phase 7 — Structural Refactor (completed)

### Phase 8 — Advanced Gameplay (completed)
- [x] Combo/streak system — +1-99pts extra per kill, resets on damage
- [x] Selectable difficulty (Easy/Normal/Hard) — cycle with LEFT/RIGHT on title
- [x] Fix: bunkers centered in game area
- [x] Fix: pygame.display.flip() in TITLE state

### Phase 9 — Refinement (completed)
- [x] Extract enemy shooting logic to separate function (`shooting.py`)
- [x] Edge case tests — 23 new tests
- [x] Render tests — 8 tests: each state no crash + boss/powerups/popups
- [x] Performance tests — 3 tests: 100 frames <2s, stress bullets, stress particles

---

## Quality Criteria

- Each change verified with `python3 -m pytest tests/ -v`
- Manual smoke test: `python3 main.py` 10s no crash
- Atomic commits per feature
- No regression on existing tests
