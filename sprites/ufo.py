import random
import pygame
from settings import UFO_W, UFO_H, UFO_SPEED, UFO_Y, UFO_POINTS, GAME_WIDTH


class UFO(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((UFO_W, UFO_H), pygame.SRCALPHA)
        self._draw_saucer()
        self.direction = random.choice([-1, 1])
        if self.direction == 1:
            self.rect = self.image.get_rect(topleft=(-UFO_W, UFO_Y))
        else:
            self.rect = self.image.get_rect(topright=(GAME_WIDTH + UFO_W, UFO_Y))
        self.points = random.choice(UFO_POINTS)

    def _draw_saucer(self):
        cx, cy = UFO_W // 2, UFO_H // 2
        # body
        pygame.draw.ellipse(self.image, (180, 100, 200), (2, cy - 4, UFO_W - 4, 10))
        # dome
        pygame.draw.ellipse(self.image, (220, 180, 240), (cx - 8, cy - 8, 16, 10))
        # lights
        for lx in (6, UFO_W // 2, UFO_W - 10):
            pygame.draw.circle(self.image, (255, 100, 100), (lx, cy + 2), 2)

    def update(self, *args):
        self.rect.x += UFO_SPEED * self.direction
