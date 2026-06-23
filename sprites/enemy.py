import math
import random

import pygame

from classes import EnemyType
from settings import (
    ENEMY_ANIM_INTERVAL, ENEMY_AUTO_STEP, ENEMY_BASE_SPEED,
    ENEMY_BOUNDARY, ENEMY_FAST_MULT, ENEMY_H, ENEMY_H_GAP,
    ENEMY_KAMIKAZE_BASE_SPEED, ENEMY_KAMIKAZE_MAX_SPEED,
    ENEMY_KAMIKAZE_ACCEL, ENEMY_KAMIKAZE_STEER,
    ENEMY_SHOOTER_INTERVAL, ENEMY_STEP_DOWN,
    ENEMY_TOP, ENEMY_V_GAP, ENEMY_W, ENEMY_ZIGZAG_AMP,
    ENEMY_ZIGZAG_FREQ, GAME_OVER_LINE, GAME_WIDTH, WHITE,
)


_COLORKEY = (1, 0, 1)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, color, points, enemy_type=EnemyType.NORMAL):
        super().__init__()
        w, h = ENEMY_W, ENEMY_H
        self.enemy_type = enemy_type
        self.base_color = color
        self.points = points
        self._anim_timer = 0

        self.frame_a = pygame.Surface((w, h))
        self.frame_a.set_colorkey(_COLORKEY)
        self.frame_b = pygame.Surface((w, h))
        self.frame_b.set_colorkey(_COLORKEY)
        self._redraw_frames(color)

        self.image = self.frame_a
        self.rect = self.image.get_rect(topleft=(x, y))

        self.base_x = float(x)
        self.base_y = float(y)
        self.hp = 2 if enemy_type == EnemyType.SHIELD else 1
        self._shoot_timer = random.randint(1000, ENEMY_SHOOTER_INTERVAL)
        self._kamikaze_active = False
        self._zig_time = 0.0

    def _redraw_frames(self, color):
        w, h = ENEMY_W, ENEMY_H
        eye = WHITE

        def _eyes(surf, off=0):
            pygame.draw.rect(surf, eye, (12 + off, 6, 5, 5))
            pygame.draw.rect(surf, eye, (23 - off, 6, 5, 5))

        def _bumps(surf, col):
            pygame.draw.rect(surf, col, (14, 0, 4, 6))
            pygame.draw.rect(surf, col, (22, 0, 4, 6))

        def _body_base(surf, col, leg_h):
            pygame.draw.polygon(surf, col, [(12, 5), (24, 5), (30, 16), (6, 16)])
            _bumps(surf, col)
            pygame.draw.rect(surf, col, (8, 16, 5, leg_h))
            pygame.draw.rect(surf, col, (23, 16, 5, leg_h))

        self.frame_a.fill(_COLORKEY)
        self.frame_b.fill(_COLORKEY)

        if self.enemy_type in (EnemyType.NORMAL, EnemyType.SHOOTER):
            _body_base(self.frame_a, color, 5)
            _eyes(self.frame_a)
            _body_base(self.frame_b, color, 3)
            _eyes(self.frame_b, off=1)
            if self.enemy_type == EnemyType.SHOOTER:
                pygame.draw.rect(self.frame_a, color, (14, 18, 8, 3))
                pygame.draw.rect(self.frame_b, color, (14, 18, 8, 3))

        elif self.enemy_type == EnemyType.KAMIKAZE:
            pygame.draw.polygon(self.frame_a, color, [(18, 0), (6, 10), (18, 21), (30, 10)])
            pygame.draw.polygon(self.frame_b, color, [(18, 0), (8, 10), (18, 19), (28, 10)])
            pygame.draw.rect(self.frame_a, eye, (15, 6, 4, 4))
            pygame.draw.rect(self.frame_a, eye, (19, 6, 4, 4))
            pygame.draw.rect(self.frame_b, eye, (16, 6, 3, 4))
            pygame.draw.rect(self.frame_b, eye, (19, 6, 3, 4))

        elif self.enemy_type == EnemyType.SHIELD:
            pts = [(2, 13), (2, 7), (6, 3), (30, 3), (34, 7), (34, 13), (18, 20)]
            pygame.draw.polygon(self.frame_a, color, pts)
            pygame.draw.polygon(self.frame_b, color, pts)
            pygame.draw.rect(self.frame_a, eye, (12, 5, 5, 5))
            pygame.draw.rect(self.frame_a, eye, (23, 5, 5, 5))
            pygame.draw.rect(self.frame_b, eye, (13, 5, 4, 5))
            pygame.draw.rect(self.frame_b, eye, (23, 5, 4, 5))

        elif self.enemy_type == EnemyType.ZIGZAG:
            pygame.draw.rect(self.frame_a, color, (6, 3, 24, 7))
            pygame.draw.rect(self.frame_a, color, (10, 10, 16, 7))
            pygame.draw.rect(self.frame_a, color, (14, 17, 8, 4))
            _eyes(self.frame_a, off=1)
            pygame.draw.rect(self.frame_b, color, (4, 3, 28, 7))
            pygame.draw.rect(self.frame_b, color, (8, 10, 20, 7))
            pygame.draw.rect(self.frame_b, color, (12, 17, 12, 4))
            _eyes(self.frame_b, off=0)

        elif self.enemy_type == EnemyType.FAST:
            pts = [(18, 0), (2, 10), (10, 16), (18, 22), (26, 16), (34, 10)]
            pygame.draw.polygon(self.frame_a, color, pts)
            pygame.draw.polygon(self.frame_b, color, [(18, 0), (2, 10), (12, 16), (20, 22), (28, 16), (34, 10)])
            pygame.draw.rect(self.frame_a, eye, (16, 6, 4, 6))
            pygame.draw.rect(self.frame_b, eye, (17, 6, 2, 6))

    def update(self, *args):
        dt = args[0] if args else 16

        if self.enemy_type == EnemyType.ZIGZAG:
            self._zig_time += dt
            offset = math.sin(self._zig_time * ENEMY_ZIGZAG_FREQ) * ENEMY_ZIGZAG_AMP
            self.rect.x = int(self.base_x + offset)

        self._anim_timer += dt
        if self._anim_timer >= ENEMY_ANIM_INTERVAL:
            self._anim_timer -= ENEMY_ANIM_INTERVAL
            self.image = self.frame_b if self.image is self.frame_a else self.frame_a

    def get_shoot_position(self):
        return (self.rect.centerx - 2, self.rect.bottom)

    def take_hit(self):
        if self.enemy_type == EnemyType.SHIELD:
            self.hp -= 1
            if self.hp <= 0:
                return True
            self._dim()
            return False
        self.hp -= 1
        return True

    def _dim(self):
        dimmed = tuple(max(0, v - 80) for v in self.base_color)
        self._redraw_frames(dimmed)

    def is_shooter(self):
        return self.enemy_type == EnemyType.SHOOTER

    def should_shoot(self, dt):
        if self.enemy_type != EnemyType.SHOOTER:
            return None
        self._shoot_timer -= dt
        if self._shoot_timer <= 0:
            self._shoot_timer = ENEMY_SHOOTER_INTERVAL
            return self.get_shoot_position()
        return None


class KamikazeEnemy(pygame.sprite.Sprite):
    def __init__(self, enemy, player):
        super().__init__()
        self.image = enemy.image.copy()
        self.rect = enemy.rect.copy()
        self.points = enemy.points
        self.player = player
        self._elapsed = 0.0
        self._speed = ENEMY_KAMIKAZE_BASE_SPEED

    def update(self, *args):
        dt = args[0] if args else 16
        self._elapsed += dt
        self._speed = min(ENEMY_KAMIKAZE_MAX_SPEED,
                          ENEMY_KAMIKAZE_BASE_SPEED + self._elapsed * ENEMY_KAMIKAZE_ACCEL * 0.001)
        if self.player and self.player.alive():
            dx = self.player.rect.centerx - self.rect.centerx
            steer = max(-ENEMY_KAMIKAZE_STEER, min(ENEMY_KAMIKAZE_STEER, dx * 0.08))
            self.rect.x += steer * (dt / 16)
        self.rect.y += self._speed * (dt / 16)


class EnemyFormation:
    def __init__(self, config, diff_mult=None):
        self.direction = 1
        self.speed = ENEMY_BASE_SPEED
        self.config = config
        self.enemies = pygame.sprite.Group()
        self.initial_count = sum(sum(row) for row in config["pattern"])
        self._frac_x = 0.0
        self._elapsed = 0.0
        self._diff = config.get("difficulty", {"speed": 1.0, "shoot": 1.0, "auto_step_ms": 4000}).copy()
        if diff_mult:
            self._diff["speed"] *= diff_mult.get("speed", 1.0)
            self._diff["shoot"] *= diff_mult.get("shoot", 1.0)
            self._diff["auto_step_ms"] = int(self._diff["auto_step_ms"] * diff_mult.get("auto_step_ms", 1.0))
        self._create()

    def _create(self):
        pattern = self.config["pattern"]
        colors = self.config["colors"]
        points = self.config["points"]
        types = self.config.get("types", None)
        for row_idx, row_data in enumerate(pattern):
            for col_idx, cell in enumerate(row_data):
                if cell:
                    x = ENEMY_BOUNDARY + col_idx * (ENEMY_W + ENEMY_H_GAP)
                    y = ENEMY_TOP + row_idx * (ENEMY_H + ENEMY_V_GAP)
                    etype = EnemyType.NORMAL
                    if types and row_idx < len(types) and col_idx < len(types[row_idx]):
                        tname = types[row_idx][col_idx]
                        etype = getattr(EnemyType, tname.upper(), EnemyType.NORMAL)
                    self.enemies.add(
                        Enemy(x, y, colors[row_idx], points[row_idx], etype)
                    )

    def update(self, *args):
        if not self.enemies:
            return

        dt = args[0] if args else 16
        speed_mult = args[1] if len(args) > 1 else 1.0
        self._elapsed += dt

        self.enemies.update(dt)

        for enemy in self.enemies:
            if self.direction == 1 and enemy.rect.right >= GAME_WIDTH - ENEMY_BOUNDARY:
                self._reverse_and_step()
                break
            if self.direction == -1 and enemy.rect.left <= ENEMY_BOUNDARY:
                self._reverse_and_step()
                break

        remaining = len(self.enemies)
        mult = 1 + 0.7 * (1 - remaining / self.initial_count) if remaining > 0 else 1
        self.speed = ENEMY_BASE_SPEED * mult

        step_total = self.speed * self.direction * speed_mult * self._diff["speed"]
        self._frac_x += step_total
        if abs(self._frac_x) >= 1:
            step = int(self._frac_x)
            for enemy in self.enemies:
                fast = enemy.enemy_type == EnemyType.FAST
                extra = int(step * (ENEMY_FAST_MULT - 1)) if fast else 0
                enemy.rect.x += step + extra
                if enemy.enemy_type != EnemyType.ZIGZAG:
                    enemy.base_x = float(enemy.rect.x)
                else:
                    enemy.base_x += step
            self._frac_x -= step

    def _reverse_and_step(self):
        self.direction *= -1
        for enemy in self.enemies:
            enemy.rect.y += ENEMY_STEP_DOWN
            enemy.base_y += ENEMY_STEP_DOWN

    def auto_step_down(self):
        for enemy in self.enemies:
            enemy.rect.y += ENEMY_AUTO_STEP
            enemy.base_y += ENEMY_AUTO_STEP

    def try_shoot(self):
        if not self.enemies:
            return None
        rate = 0.015 + 0.00025 * len(self.enemies) * self._diff["shoot"]
        if random.random() < rate:
            shooter = random.choice(self.enemies.sprites())
            return shooter.get_shoot_position()
        return None

    def get_shooter_shots(self, dt):
        shots = []
        for enemy in self.enemies.sprites():
            pos = enemy.should_shoot(dt)
            if pos:
                shots.append(pos)
        return shots

    def detach_kamikazes(self, player):
        detached = []
        for enemy in list(self.enemies):
            if enemy.enemy_type == EnemyType.KAMIKAZE and not enemy._kamikaze_active:
                if player and enemy.rect.bottom > player.rect.top - 100:
                    if random.random() < 0.02:
                        enemy._kamikaze_active = True
                        self.enemies.remove(enemy)
                        detached.append(KamikazeEnemy(enemy, player))
        return detached

    def reached_game_over(self):
        for enemy in self.enemies:
            if enemy.rect.bottom >= GAME_OVER_LINE:
                return True
        return False
