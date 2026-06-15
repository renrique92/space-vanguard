import pygame
import random
from settings import (
    ENEMY_W, ENEMY_H, ENEMY_H_GAP, ENEMY_V_GAP,
    ENEMY_TOP, ENEMY_COLS, ENEMY_ROWS,
    ENEMY_BASE_SPEED, ENEMY_STEP_DOWN, ENEMY_AUTO_STEP,
    ENEMY_BOUNDARY, ROW_COLORS, ROW_POINTS, GAME_WIDTH,
    BULLET_W, WHITE, ENEMY_SHOOT_RATE_BASE,
    ENEMY_SHOOT_RATE_PER_ENEMY, GAME_OVER_LINE
)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, color, points):
        super().__init__()
        self.image = pygame.Surface((ENEMY_W, ENEMY_H))
        self.image.fill(color)
        pygame.draw.rect(self.image, WHITE, (8, 4, 6, 7))
        pygame.draw.rect(self.image, WHITE, (ENEMY_W - 14, 4, 6, 7))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.points = points

    def get_shoot_position(self):
        return (self.rect.centerx - BULLET_W // 2, self.rect.bottom)


class EnemyFormation:
    def __init__(self):
        self.direction = 1
        self.speed = ENEMY_BASE_SPEED
        self.initial_count = ENEMY_ROWS * ENEMY_COLS
        self.enemies = pygame.sprite.Group()
        self._create()

    def _create(self):
        for row in range(ENEMY_ROWS):
            for col in range(ENEMY_COLS):
                x = ENEMY_BOUNDARY + col * (ENEMY_W + ENEMY_H_GAP)
                y = ENEMY_TOP + row * (ENEMY_H + ENEMY_V_GAP)
                self.enemies.add(
                    Enemy(x, y, ROW_COLORS[row], ROW_POINTS[row])
                )

    def update(self, *args):
        if not self.enemies:
            return

        for enemy in self.enemies:
            if self.direction == 1 and enemy.rect.right >= GAME_WIDTH - ENEMY_BOUNDARY:
                self._reverse_and_step()
                break
            if self.direction == -1 and enemy.rect.left <= ENEMY_BOUNDARY:
                self._reverse_and_step()
                break

        remaining = len(self.enemies)
        mult = 1 + 2 * (1 - remaining / self.initial_count) if remaining > 0 else 1
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

    def reset(self):
        self.enemies.empty()
        self.direction = 1
        self.speed = ENEMY_BASE_SPEED
        self._create()
