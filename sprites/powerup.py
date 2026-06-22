import pygame

from settings import (
    POWERUP_COLORS, POWERUP_H, POWERUP_SPEED,
    POWERUP_SYMBOLS, POWERUP_W, WINDOW_HEIGHT,
)


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, power_type):
        super().__init__()
        self.power_type = power_type
        self.image = pygame.Surface((POWERUP_W, POWERUP_H), pygame.SRCALPHA)
        color = POWERUP_COLORS[power_type]
        symbol = POWERUP_SYMBOLS[power_type]
        pygame.draw.rect(self.image, color, (0, 0, POWERUP_W, POWERUP_H), border_radius=3)
        font = pygame.font.Font(None, 16)
        glyph = font.render(symbol, True, (0, 0, 0))
        gr = glyph.get_rect(center=(POWERUP_W // 2, POWERUP_H // 2))
        self.image.blit(glyph, gr)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, *args):
        self.rect.y += POWERUP_SPEED
        if self.rect.top > WINDOW_HEIGHT:
            self.kill()
