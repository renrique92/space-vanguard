import pygame
from settings import (
    BUNKER_COUNT, BUNKER_COLS, BUNKER_ROWS,
    BUNKER_BRICK_W, BUNKER_BRICK_H, BUNKER_BRICK_GAP,
    BUNKER_Y, BUNKER_COLOR, BUNKER_HIT_COLOR,
    GAME_WIDTH,
)


BUNKER_PATTERN = [
    [0, 0, 1, 1, 1, 1, 1, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 0, 0, 0, 1, 1, 1],
]


class Brick(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface(
            (BUNKER_BRICK_W, BUNKER_BRICK_H)
        )
        self.image.fill(BUNKER_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hp = 2

    def hit(self):
        self.hp -= 1
        if self.hp > 0:
            self.image.fill(BUNKER_HIT_COLOR)
        else:
            self.kill()


class Bunker:
    def __init__(self, x):
        self.bricks = pygame.sprite.Group()
        for row_idx, row_data in enumerate(BUNKER_PATTERN):
            for col_idx, cell in enumerate(row_data):
                if cell:
                    bx = x + col_idx * (BUNKER_BRICK_W + BUNKER_BRICK_GAP)
                    by = BUNKER_Y + row_idx * (BUNKER_BRICK_H + BUNKER_BRICK_GAP)
                    self.bricks.add(Brick(bx, by))
