# Re-work Handoff

**Generado:** 2026-06-23
**Rama:** main
**Issue/Tarea:** Batch 1 — Enemy variety (5 types) + boss phases + kamikaze upgrade

## Tarea activa

Implementar y mejorar enemigos variados. Batch 1 completo (5 tipos funcionales).
Completar sprites únicos por tipo + kamikaze con homing/aceleración.

## Estado del working tree

```
 M classes/__init__.py
 M collision.py
 M game.py
 M level_generator.py
 M levels.py
 M renderer.py
 M settings.py
 M shooting.py
 M skills-lock.json
 M sprites/boss.py
 M sprites/enemy.py
 M tests/test_game.py
?? .agents/skills/python-design-patterns/
?? classes/enemy_type.py
?? docs/web-deploy-plan.md
```

## Archivos tocados

- `classes/enemy_type.py` — EnemyType enum (NORMAL, SHOOTER, KAMIKAZE, SHIELD, ZIGZAG, FAST)
- `settings.py` — Enemy type chance constants, kamikaze acceleration/steering constants
- `level_generator.py` — Type distribution per cell, scales with level
- `sprites/enemy.py` — Enemy (5 types via _redraw_frames), EnemyFormation (type creation, kamikaze detach), KamikazeEnemy (homing/acceleration)
- `sprites/boss.py` — Boss (phase system, BossMinion)
- `shooting.py` — Shooter enemy independent firing
- `collision.py` — Shield take_hit, kamikaze/minion/beam collisions
- `game.py` — Kamikazes/minions groups, boss phase 2 spread+minion, kamikaze off-screen explosion, MuzzleFlash on detach
- `renderer.py` — Render kamikazes/minions groups
- `levels.py` — Clear kamikazes/minions on advance/reset
- `tests/test_game.py` — 147 tests (12 nuevos: enemy types, boss phases, kamikaze steering/acceleration, unique sprites)

## Decisiones

- **Tipos con sprites únicos:** Cada EnemyType tiene su propia silueta dibujada con pygame.draw.polygon/rect, usando _COLORKEY=(1,0,1) para transparencia. _dim() redibuja frames completos con color atenuado.
- **Kamikaze upgrade:** steering suave hacia player (`dx*0.08`, max 4px/frame), aceleración progresiva (base=3, max=10, accel=0.15/s), explosión al salir de pantalla + MuzzleFlash al despegarse.
- **Shield 2 HP bullet survival:** bala muere al impactar pero shield sobrevive (se oscurece). Piercing still has_hit on first enemy (gotcha tracked).
- **Boss phases:** visual/behavioral (no new sprite). Phase 2 at ≤50% HP: 1.5x speed, purple tint, 3-bullet spread, minions every 3s.
- **Pure random generation:** generate_level() usa random.Random() sin seed. Niveles distintos cada partida.

## Pendientes / bloqueos

- Nada bloqueado. Batch 1 funcional con tests pasando.

## Próximo paso

Commit y push de Batch 1, luego probar gameplay manual para verificar sprites, kamikaze homing y boss phases en acción.

## Comandos y referencias

- Run: `python3 main.py`
- Tests: `python3 -m pytest tests/ -v`
- Settings clave: `ENEMY_KAMIKAZE_BASE_SPEED=3`, `ENEMY_KAMIKAZE_MAX_SPEED=10`, `ENEMY_KAMIKAZE_ACCEL=0.15`, `ENEMY_KAMIKAZE_STEER=4`
- _COLORKEY = (1, 0, 1) en sprites/enemy.py
