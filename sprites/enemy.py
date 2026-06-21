import pygame
import random
from settings import (
    ENEMY_W, ENEMY_H, ENEMY_H_GAP, ENEMY_V_GAP,
    ENEMY_TOP, ENEMY_BASE_SPEED, ENEMY_STEP_DOWN,
    ENEMY_AUTO_STEP, ENEMY_ANIM_INTERVAL, ENEMY_BOUNDARY,
    GAME_WIDTH, BULLET_W, WHITE, ENEMY_SHOOT_RATE_BASE,
    ENEMY_SHOOT_RATE_PER_ENEMY, GAME_OVER_LINE
)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, color, points):
        super().__init__()
        w, h = ENEMY_W, ENEMY_H
        self.frame_a = pygame.Surface((w, h))
        self.frame_a.fill(color)
        pygame.draw.rect(self.frame_a, WHITE, (8, 4, 6, 7))
        pygame.draw.rect(self.frame_a, WHITE, (w - 14, 4, 6, 7))
        self.frame_b = pygame.Surface((w, h))
        self.frame_b.fill(color)
        pygame.draw.rect(self.frame_b, WHITE, (6, 6, 6, 7))
        pygame.draw.rect(self.frame_b, WHITE, (w - 12, 6, 6, 7))
        self.image = self.frame_a
        self.rect = self.image.get_rect(topleft=(x, y))
        self.points = points
        self._anim_timer = 0

    def update(self, *args):
        dt = args[0] if args else 16
        self._anim_timer += dt
        if self._anim_timer >= ENEMY_ANIM_INTERVAL:
            self._anim_timer = 0
            self.image = self.frame_b if self.image is self.frame_a else self.frame_a

    def get_shoot_position(self):
        return (self.rect.centerx - BULLET_W // 2, self.rect.bottom)


class EnemyFormation:
    def __init__(self, config):
        self.direction = 1
        self.speed = ENEMY_BASE_SPEED
        self.config = config
        self.enemies = pygame.sprite.Group()
        self.initial_count = sum(sum(row) for row in config["pattern"])
        self._create()

    def _create(self):
        pattern = self.config["pattern"]
        colors = self.config["colors"]
        points = self.config["points"]
        for row_idx, row_data in enumerate(pattern):
            for col_idx, cell in enumerate(row_data):
                if cell:
                    x = ENEMY_BOUNDARY + col_idx * (ENEMY_W + ENEMY_H_GAP)
                    y = ENEMY_TOP + row_idx * (ENEMY_H + ENEMY_V_GAP)
                    self.enemies.add(
                        Enemy(x, y, colors[row_idx], points[row_idx])
                    )

    def update(self, *args):
        if not self.enemies:
            return

        dt = args[0] if args else 16
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

        for enemy in self.enemies:
            enemy.rect.x += self.speed * self.direction

    def _reverse_and_step(self):
        self.direction *= -1
        for enemy in self.enemies:
            enemy.rect.y += ENEMY_STEP_DOWN

    def auto_step_down(self):
        for enemy in self.enemies:
            enemy.rect.y += ENEMY_AUTO_STEP

    def try_shoot(self):
        if not self.enemies:
            return None
        rate = ENEMY_SHOOT_RATE_BASE + ENEMY_SHOOT_RATE_PER_ENEMY * len(self.enemies)
        if random.random() < rate:
            shooter = random.choice(self.enemies.sprites())
            return shooter.get_shoot_position()
        return None

    def reached_game_over(self):
        for enemy in self.enemies:
            if enemy.rect.bottom >= GAME_OVER_LINE:
                return True
        return False

    def reset(self, config=None):
        self.enemies.empty()
        self.direction = 1
        self.speed = ENEMY_BASE_SPEED
        if config is not None:
            self.config = config
            self.initial_count = sum(sum(row) for row in config["pattern"])
        self._create()
