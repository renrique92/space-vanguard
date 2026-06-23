import random

import pygame

from settings import BULLET_W, GAME_WIDTH, WINDOW_HEIGHT


class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.w = 80
        self.h = 50
        self.image = pygame.Surface((self.w, self.h))
        self._draw_frame((200, 50, 50))
        self.rect = self.image.get_rect(midtop=(GAME_WIDTH // 2, 30))
        self.hp = 20
        self.max_hp = 20
        self.phase = 1
        self.dx = random.choice([-1, 1]) * random.uniform(0.5, 1.2)
        self.dy = random.choice([-1, 1]) * random.uniform(0.3, 0.8)
        self._change_dir_timer = random.randint(1000, 3000)

    def _draw_frame(self, base_color):
        r, g, b = base_color
        self.image.fill((r, g, b))
        pygame.draw.rect(self.image, (min(255, r+55), min(255, g+50), min(255, b+50)), (10, 10, 20, 15))
        pygame.draw.rect(self.image, (min(255, r+55), min(255, g+50), min(255, b+50)), (self.w - 30, 10, 20, 15))
        pygame.draw.rect(self.image, (255, 200, 50), (self.w // 2 - 5, self.h // 2 - 5, 10, 10))

    def update(self, *args):
        dt = args[0] if args else 16
        hp_ratio = self.hp / self.max_hp
        if hp_ratio <= 0.5 and self.phase == 1:
            self.phase = 2
            self._draw_frame((200, 100, 200))

        speed_mult = 1.5 if self.phase == 2 else 1.0
        self._change_dir_timer -= dt
        if self._change_dir_timer <= 0:
            self.dx = random.choice([-1, 1]) * random.uniform(0.5, 1.2) * speed_mult
            self.dy = random.choice([-1, 1]) * random.uniform(0.3, 0.8) * speed_mult
            self._change_dir_timer = random.randint(800, 2000) if self.phase == 2 else random.randint(1000, 3000)

        self.rect.x += self.dx * (dt / 16)
        self.rect.y += self.dy * (dt / 16)

        if self.rect.left < 0:
            self.rect.left = 0
            self.dx = abs(self.dx)
        elif self.rect.right > GAME_WIDTH:
            self.rect.right = GAME_WIDTH
            self.dx = -abs(self.dx)

        if self.rect.top < 20:
            self.rect.top = 20
            self.dy = abs(self.dy)
        elif self.rect.bottom > WINDOW_HEIGHT - 180:
            self.rect.bottom = WINDOW_HEIGHT - 180
            self.dy = -abs(self.dy)

    def try_shoot(self):
        return (self.rect.centerx - BULLET_W // 2, self.rect.bottom)

    def take_hit(self, color=(200, 50, 50)):
        self.hp -= 1
        r = 200 if self.phase == 1 else 200
        g = 50 if self.phase == 1 else 100
        b = 50 if self.phase == 1 else 200
        shade = min(255, 100 + (self.max_hp - self.hp) * 8)
        self._draw_frame((r, shade // 2 if self.phase == 1 else shade, b))
        if self.hp <= 0:
            self.kill()


class BossMinion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.w = 20
        self.h = 16
        self.image = pygame.Surface((self.w, self.h))
        self.image.fill((255, 150, 50))
        pygame.draw.rect(self.image, (255, 200, 100), (4, 4, 12, 8))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 3

    def update(self, *args):
        dt = args[0] if args else 16
        self.rect.y += self.speed * (dt / 16)
        if self.rect.top > 800:
            self.kill()
