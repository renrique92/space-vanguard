# Next Steps — Space Vanguard

> Analyzed: 23 Jun 2026
> Context: complete game with 5 levels, 7 power-ups, boss, UFO, bunkers, streak, adjustable difficulty, special attack, synthesized sound, 133 tests.

---

## ✅ Current state (what we already have)

- 5 levels with formations (2D enemy grid)
- 7 power-ups: Spread, Shield, Speed, Rapid, Pierce, Score, Slowmo
- UFO with random spawn and score sweep
- Level 5 boss with shooting patterns
- Destructible bunkers (brick grid)
- Streak/combo system (bonus points for consecutive kills)
- Difficulty selection: Easy / Normal / Hard
- Special attack (Z): piercing beam that charges ~20s
- Parallax star background (3 layers)
- Score popups, screen shake, explosion particles
- State machine: TITLE → INTRO → PLAYING → PAUSED → GAME_OVER / WIN
- 12 synthesized sounds + BGM (22050 Hz, 16-bit mono)
- Side info panel (score, high score, lives, streak, power-up, special bar)
- Persistence: high_score.json
- 133 pytest tests in headless mode
- Fullscreen (F), mute (M), auto-pause on focus loss
- Score multiplier by time and Score power-up

---

## Next directions

### 1. Enemy variety (high priority)

Types with distinct behaviors inside the formation:

| Type | Behavior |
|------|----------|
| **Shooter** | Shoots downward, not randomly |
| **Kamikaze** | Detaches from formation, heads to player |
| **Shield** | 2 hits to kill |
| **Zigzag** | Sinusoidal movement while descending |
| **Fast** | Higher horizontal speed |

**Impact:** Changes player strategy, no random shooting.
**Affected files:** `sprites/enemy.py`, `sprites/enemy_types.py` (new), `settings.py`
**Tests:** ~10-15 new tests

### 2. Boss phases (high priority)

Level 5 boss changes phase at 50% HP:

| Phase | Behavior |
|-------|----------|
| **Phase 1** | Shoots 1 bullet every ~800ms, lateral movement |
| **Phase 2** (≤50% HP) | Shoots 3 bullets in fan, faster movement, spawns minions |

**Impact:** Makes the final fight memorable.
**Affected files:** `sprites/boss.py`, `settings.py`
**Tests:** ~5 tests

### 3. Achievement system (medium priority)

Persistent achievements in `achievements.json`:

| Achievement | Condition |
|-------------|-----------|
| "First Blood" | Kill your first enemy |
| "Centurion" | Reach streak 100 |
| "Special Delivery" | Kill an enemy with the special beam |
| "Invincible" | Complete a level without losing a life |
| "Boss Slayer" | Kill the boss without taking damage |
| "Collector" | Collect all 7 power-ups in one game |
| "Speedrunner" | Complete all 5 levels in < X time |

**Impact:** Replayability, extra motivation.
**Affected files:** `achievements.py` (new), `game.py`, `ui/info_panel.py`
**Tests:** ~8 tests

### 4. Animations (medium priority)

- **Player death:** more elaborate explosion with expanding particles
- **Respawn:** ship "materialization" effect
- **Level transition:** wipe or fade animation
- **Power-up pickup:** flash / expanding ring

**Impact:** Visual polish, game feels more professional.
**Affected files:** `effects.py`, `renderer.py`, `game.py`
**Tests:** ~3 tests (render)

### 5. Local leaderboard (medium priority)

Top 10 scores with name (3-letter arcade-style input):

```json
[
  {"name": "REN", "score": 12500, "date": "2026-06-23"},
  {"name": "AAA", "score": 8200, "date": "2026-06-22"}
]
```

**Impact:** Long-term progress feeling.
**Affected files:** `leaderboard.py` (new), `game.py`, `renderer.py`
**Tests:** ~5 tests

### 6. Preference persistence (low-medium priority)

Save in `prefs.json`: selected difficulty, mute, fullscreen.

**Impact:** UX, player doesn't reconfigure every time.
**Affected files:** `preferences.py` (new), `game.py`
**Tests:** ~3 tests

### 7. Gamepad support (low priority)

Use `pygame.joystick` for movement and shooting.

**Affected files:** `game.py`
**Tests:** ~2 tests (mock)

### 8. Endless mode (low priority)

After level 5, the game continues with infinite increasing difficulty. Procedurally generated formations.

**Affected files:** `game.py`, `levels.py`, `settings.py`
**Tests:** ~5 tests

### 9. Audio options (low priority)

Separate sliders for SFX and music on the title screen.

**Affected files:** `game.py`, `sounds.py`, `renderer.py`
**Tests:** ~2 tests

### 10. Tutorial / How to Play (low priority)

Controls screen before starting.

**Affected files:** `game.py`, `renderer.py`
**Tests:** none

---

## Decision matrix

| Feature | Effort | Gameplay impact | Technical complexity |
|---------|--------|-----------------|---------------------|
| Enemy variety | High | Very high | Medium |
| Boss phases | Medium | High | Low |
| Achievements | Medium | Medium | Low |
| Animations | High | High | Medium |
| Leaderboard | Medium | Medium | Low |
| Preferences | Low | Low | Low |
| Gamepad | Low | Medium | Low |
| Endless mode | High | High | Medium |
| Audio sliders | Low | Low | Low |
| Tutorial | Low | Low | Low |

---

## Recommendation

**Batch 1** (most impact): Enemy variety + Boss phases
**Batch 2** (polish): Achievements + Leaderboard + Preferences
**Batch 3** (quality of life): Gamepad + Audio sliders
**Batch 4** (extra content): Endless mode + Tutorial
