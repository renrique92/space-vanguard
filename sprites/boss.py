import random

import pygame

from settings import BULLET_W, GAME_WIDTH, WINDOW_HEIGHT


class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.w = 80
        self.h = 50
        self.image = pygame.Surface((self.w, self.h))
        self.image.fill((200, 50, 50))
        pygame.draw.rect(self.image, (255, 100, 100), (10, 10, 20, 15))
        pygame.draw.rect(self.image, (255, 100, 100), (self.w - 30, 10, 20, 15))
        pygame.draw.rect(self.image, (255, 200, 50), (self.w // 2 - 5, self.h // 2 - 5, 10, 10))
        self.rect = self.image.get_rect(midtop=(GAME_WIDTH // 2, 30))
        self.hp = 20
        self.max_hp = 20
        self.dx = random.choice([-1, 1]) * random.uniform(0.5, 1.2)
        self.dy = random.choice([-1, 1]) * random.uniform(0.3, 0.8)
        self._change_dir_timer = random.randint(1000, 3000)

    def update(self, *args):
        dt = args[0] if args else 16
        self._change_dir_timer -= dt
        if self._change_dir_timer <= 0:
            self.dx = random.choice([-1, 1]) * random.uniform(0.5, 1.2)
            self.dy = random.choice([-1, 1]) * random.uniform(0.3, 0.8)
            self._change_dir_timer = random.randint(1000, 3000)

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
        shade = min(255, 100 + (self.max_hp - self.hp) * 8)
        self.image.fill((200, shade // 2, shade // 2))
        pygame.draw.rect(self.image, (255, 100, 100), (10, 10, 20, 15))
        pygame.draw.rect(self.image, (255, 100, 100), (self.w - 30, 10, 20, 15))
        pygame.draw.rect(self.image, (255, 200, 50), (self.w // 2 - 5, self.h // 2 - 5, 10, 10))
        if self.hp <= 0:
            self.kill()
