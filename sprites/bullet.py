import pygame
from settings import (
    BULLET_W, PLAYER_BULLET_H, ENEMY_BULLET_H,
    PLAYER_BULLET_COLOR, ENEMY_BULLET_COLOR, WINDOW_HEIGHT
)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, is_player=True, vx=0):
        super().__init__()
        self.is_player = is_player
        w = BULLET_W
        h = PLAYER_BULLET_H if is_player else ENEMY_BULLET_H
        color = PLAYER_BULLET_COLOR if is_player else ENEMY_BULLET_COLOR
        self.image = pygame.Surface((w, h))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = speed
        self.vx = vx
        self.has_hit = False

    def update(self, *args):
        self.rect.y += self.speed
        self.rect.x += self.vx
        if self.rect.bottom < 0 or self.rect.top > WINDOW_HEIGHT:
            self.kill()
