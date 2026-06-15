import pygame
from settings import (
    PLAYER_W, PLAYER_H, PLAYER_SPEED, PLAYER_LIVES,
    PLAYER_BOTTOM_MARGIN, INVULNERABLE_MS, GAME_WIDTH,
    WINDOW_HEIGHT, GREEN, CYAN, GAME_AREA
)


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((PLAYER_W, PLAYER_H), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self._draw_ship()
        self.reset()

    def _draw_ship(self):
        cx, by = self.rect.width // 2, self.rect.height
        points = [(cx, 0), (2, by), (cx + cx - 2, by)]
        pygame.draw.polygon(self.image, GREEN, points)
        pygame.draw.rect(self.image, CYAN, (cx - 4, by // 2 - 2, 8, by // 2))

    def reset(self, reset_lives=True):
        self.rect.midbottom = (GAME_WIDTH // 2, WINDOW_HEIGHT - PLAYER_BOTTOM_MARGIN)
        if reset_lives:
            self.lives = PLAYER_LIVES
        self.speed = PLAYER_SPEED
        self.invulnerable = False
        self.invuln_start = pygame.time.get_ticks()
        self.image.set_alpha(255)

    def update(self, *args):
        if self.invulnerable:
            now = pygame.time.get_ticks()
            if now - self.invuln_start > INVULNERABLE_MS:
                self.invulnerable = False
                self.image.set_alpha(255)
            elif ((now - self.invuln_start) // 100) % 2 == 0:
                self.image.set_alpha(0)
            else:
                self.image.set_alpha(255)

    def handle_input(self, keys):
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        self.rect.clamp_ip(GAME_AREA)

    def take_hit(self):
        self.lives -= 1
        self.invulnerable = True
        self.invuln_start = pygame.time.get_ticks()
        self.rect.midbottom = (GAME_WIDTH // 2, WINDOW_HEIGHT - PLAYER_BOTTOM_MARGIN)
