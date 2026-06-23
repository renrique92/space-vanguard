import random

import pygame

from settings import GAME_WIDTH, WINDOW_HEIGHT


class StarField:
    def __init__(self):
        self.stars = []
        layers = [
            (40, 0.2, 80, 1),
            (40, 0.5, 160, 1),
            (40, 1.0, 255, 2),
        ]
        for count, speed, base_brightness, size in layers:
            for _ in range(count):
                self.stars.append([
                    random.uniform(0, GAME_WIDTH),
                    random.uniform(0, WINDOW_HEIGHT),
                    base_brightness,
                    size,
                    speed,
                ])

    def update(self, dt: int) -> None:
        for s in self.stars:
            s[1] += s[4] * (dt / 16)
            if s[1] > WINDOW_HEIGHT:
                s[1] = 0
                s[0] = random.uniform(0, GAME_WIDTH)

    def draw_on(self, surface: pygame.Surface, scale_x: float = 1.0, scale_y: float = 1.0) -> None:
        for s in self.stars:
            x = int(s[0] * scale_x)
            y = int(s[1] * scale_y)
            pygame.draw.circle(surface, (s[2], s[2], s[2]), (x, y), s[3])
