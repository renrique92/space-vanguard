# Próximos Pasos — Space Vanguard

> Analizado: 23 Jun 2026
> Contexto: juego completo con 5 niveles, 7 power-ups, boss, UFO, bunkers, streak, dificultad ajustable, ataque especial, sonido sintetizado, 133 tests.

---

## ✅ Estado actual (lo que ya tenemos)

- 5 niveles con formaciones (grid 2D de enemigos)
- 7 power-ups: Spread, Shield, Speed, Rapid, Pierce, Score, Slowmo
- UFO con spawn aleatorio y barrido de puntos
- Boss nivel 5 con disparos
- Bunkers destructibles (grid de bricks)
- Sistema de streak/combo (bonificaciones por kills consecutivos)
- Selección de dificultad: Easy / Normal / Hard
- Ataque especial (Z): beam penetrante que carga ~20s
- Fondo parallax stars (3 capas)
- Score popups, screen shake, partículas de explosión
- Máquina de estados: TITLE → INTRO → PLAYING → PAUSED → GAME_OVER / WIN
- 12 sonidos sintetizados + BGM (22050 Hz, 16-bit mono)
- Panel de info lateral (score, high score, vidas, streak, power-up, barra special)
- Persistencia: high_score.json
- 133 tests pytest en headless
- Fullscreen (F), mute (M), auto-pause al perder foco
- Score multiplier por tiempo y power-up Score

---

## 🔮 Próximas direcciones

### 1. Variedad de enemigos (prioridad alta)

Tipos con comportamientos distintos dentro de la formación:

| Tipo | Comportamiento |
|------|---------------|
| **Shooter** | Dispara hacia abajo, no al azar |
| **Kamikaze** | Se desprende de la formación y va directo al player |
| **Escudo** | 2 hits para matarlo |
| **Zigzag** | Se mueve sinusoidal al bajar |
| **Rápido** | Mayor velocidad horizontal |

**Impacto:** Cambia la estrategia de juego, el玩家 no solo dispara al azar.
**Archivos afectados:** `sprites/enemy.py`, `sprites/enemy_types.py` (nuevo), `settings.py`
**Tests:** ~10-15 tests nuevos

### 2. Fases de boss (prioridad alta)

El boss del nivel 5 cambia de fase al 50% HP:

| Fase | Comportamiento |
|------|---------------|
| **Fase 1** | Dispara 1 bala cada ~800ms, movimiento lateral |
| **Fase 2** (≤50% HP) | Dispara 3 balas en abanico, se mueve más rápido, spawn de minions |

**Impacto:** Hace que la pelea final sea memorable.
**Archivos afectados:** `sprites/boss.py`, `settings.py`
**Tests:** ~5 tests

### 3. Sistema de logros (prioridad media)

Logros persistentes en `achievements.json`:

| Logro | Condición |
|-------|-----------|
| "First Blood" | Matar tu primer enemigo |
| "Centurion" | Llegar a streak 100 |
| "Special Delivery" | Matar un enemigo con el beam especial |
| "Invincible" | Pasar un nivel sin perder vida |
| "Boss Slayer" | Matar al boss sin recibir daño |
| "Collector" | Agarrar los 7 power-ups en una partida |
| "Speedrunner" | Completar los 5 niveles en < X tiempo |

**Impacto:** Rejugabilidad, motivación extra.
**Archivos afectados:** `achievements.py` (nuevo), `game.py`, `ui/info_panel.py`
**Tests:** ~8 tests

### 4. Animaciones (prioridad media)

- **Muerte del player:** explosión más elaborada con partículas que se expanden
- **Respawn:** efecto de "materialización" del ship
- **Transición entre niveles:** animación de barrido o fade
- **Power-up pickup:** destello / anillo expansivo

**Impacto:** Polish visual, el juego se siente más profesional.
**Archivos afectados:** `effects.py`, `renderer.py`, `game.py`
**Tests:** ~3 tests (render)

### 5. Leaderboard local (prioridad media)

Top 10 scores con nombre (input de 3 letras estilo arcade):

```json
[
  {"name": "REN", "score": 12500, "date": "2026-06-23"},
  {"name": "AAA", "score": 8200, "date": "2026-06-22"}
]
```

**Impacto:** Sensación de progreso a largo plazo.
**Archivos afectados:** `leaderboard.py` (nuevo), `game.py`, `renderer.py`
**Tests:** ~5 tests

### 6. Persistencia de preferencias (prioridad baja-media)

Guardar en `prefs.json`: dificultad seleccionada, mute, fullscreen.

**Impacto:** UX, el jugador no reconfigura cada vez.
**Archivos afectados:** `preferences.py` (nuevo), `game.py`
**Tests:** ~3 tests

### 7. Soporte gamepad (prioridad baja)

Usar `pygame.joystick` para movimiento y disparo.

**Archivos afectados:** `game.py`
**Tests:** ~2 tests (mock)

### 8. Endless mode (prioridad baja)

Después del nivel 5, el juego continúa con dificultad creciente infinita. Formaciones generadas proceduralmente.

**Archivos afectados:** `game.py`, `levels.py`, `settings.py`
**Tests:** ~5 tests

### 9. Opciones de audio (prioridad baja)

Sliders separados para SFX y música en el title screen.

**Archivos afectados:** `game.py`, `sounds.py`, `renderer.py`
**Tests:** ~2 tests

### 10. Tutorial / How to Play (prioridad baja)

Pantalla con controles antes de empezar.

**Archivos afectados:** `game.py`, `renderer.py`
**Tests:** ninguno

---

## 📊 Matriz de decisión

| Feature | Esfuerzo | Impacto jugable | Complejidad técnica |
|---------|----------|----------------|-------------------|
| Variedad enemigos | Alta | Muy alto | Media |
| Fases de boss | Media | Alto | Baja |
| Logros | Media | Medio | Baja |
| Animaciones | Alta | Alto | Media |
| Leaderboard | Media | Medio | Baja |
| Preferencias | Baja | Bajo | Baja |
| Gamepad | Baja | Medio | Baja |
| Endless mode | Alta | Alto | Media |
| Audio sliders | Baja | Bajo | Baja |
| Tutorial | Baja | Bajo | Baja |

---

## 🧠 Recomendación

**Batch 1** (más impacto): Variedad de enemigos + Fases de boss
**Batch 2** (polish): Logros + Leaderboard + Preferencias
**Batch 3** (calidad de vida): Gamepad + Audio sliders
**Batch 4** (contenido extra): Endless mode + Tutorial
