import random

from settings import (
    BOSS_INTERVAL, CYAN, ENEMY_TYPE_CHANCES, LIME, ORANGE, RED, YELLOW,
)

COLOR_PALETTE = [RED, ORANGE, YELLOW, LIME, CYAN]
TYPE_KEYS = ["shooter", "kamikaze", "shield", "zigzag", "fast"]


def generate_level(level_num: int) -> dict:
    rng = random.Random()
    is_boss = level_num % BOSS_INTERVAL == 0

    if is_boss:
        rows = rng.randint(2, 3)
        cols = rng.randint(6, 8)
    else:
        rows = rng.randint(4, 6)
        cols = rng.randint(8, 12)

    pattern = _generate_pattern(rng, rows, cols, is_boss)
    colors = _generate_colors(rows)
    points = _generate_points(rows, level_num)
    diff = _generate_difficulty(level_num, is_boss)
    types = _generate_types(rng, rows, cols, pattern, level_num)

    return {
        "pattern": pattern,
        "colors": colors,
        "points": points,
        "difficulty": diff,
        "types": types,
    }


def _generate_pattern(rng: random.Random, rows: int, cols: int, is_boss: bool) -> list:
    pattern = []
    for r in range(rows):
        density = 0.9 - 0.1 * r
        if is_boss:
            density *= 0.7
        row_data = [1 if rng.random() < density else 0 for _ in range(cols)]
        if sum(row_data) == 0:
            row_data[rng.randint(0, cols - 1)] = 1
        pattern.append(row_data)
    return pattern


def _generate_colors(rows: int) -> list:
    return [COLOR_PALETTE[i % len(COLOR_PALETTE)] for i in range(rows)]


def _generate_points(rows: int, level_num: int) -> list:
    base = 10 + level_num // 2
    return [max(5, base + (rows - 1 - i) * 5) for i in range(rows)]


def _generate_difficulty(level_num: int, is_boss: bool) -> dict:
    cycle = (level_num - 1) // BOSS_INTERVAL
    pos = (level_num - 1) % BOSS_INTERVAL

    speed = 0.8 + 0.1 * pos + 0.1 * cycle
    shoot = 0.8 + 0.15 * pos + 0.15 * cycle
    auto_step = max(1500, 4000 - 300 * pos - 300 * cycle)

    if is_boss:
        speed *= 0.7
        shoot *= 0.5

    return {
        "speed": speed,
        "shoot": shoot,
        "auto_step_ms": int(auto_step),
    }


def _generate_types(rng, rows, cols, pattern, level_num):
    scale = 1.0 + (level_num - 1) * 0.03
    type_grid = []
    for r in range(rows):
        row_types = []
        for c in range(cols):
            if not pattern[r][c]:
                row_types.append("normal")
                continue
            chosen = "normal"
            for key in TYPE_KEYS:
                chance = ENEMY_TYPE_CHANCES[key] * scale
                if rng.random() < chance:
                    chosen = key
                    break
            row_types.append(chosen)
        type_grid.append(row_types)
    return type_grid
