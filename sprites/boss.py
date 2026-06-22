import pygame
from settings import GAME_WIDTH, WINDOW_HEIGHT, ENEMY_BOUNDARY, ENEMY_BULLET_SPEED, BULLET_W
from sprites.bullet import Bullet


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
        self.direction = 1
        self.speed = 0.8
        self._anim_timer = 0
        self._anim_frame = 0

    def update(self, *args):
        self.rect.x += self.speed * self.direction
        if self.rect.right >= GAME_WIDTH - ENEMY_BOUNDARY:
            self.direction = -1
        elif self.rect.left <= ENEMY_BOUNDARY:
            self.direction = 1

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
