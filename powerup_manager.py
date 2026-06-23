import random

import pygame

from classes import PowerUpType
from settings import POWERUP_CHANCE, POWERUP_COOLDOWN
from sprites.powerup import PowerUp


class PowerUpManager:
    def __init__(self):
        self.powerups = pygame.sprite.Group()
        self.spawn_cooldown = POWERUP_COOLDOWN
        self.msg = ""
        self.msg_timer = 0

    def try_spawn(self, x: int, y: int) -> bool:
        if self.spawn_cooldown >= POWERUP_COOLDOWN and random.random() < POWERUP_CHANCE:
            ptype = random.choice(list(PowerUpType))
            self.powerups.add(PowerUp(x, y, ptype))
            self.spawn_cooldown = 0
            return True
        return False

    def update(self, dt: int) -> None:
        self.powerups.update(dt)
        self.spawn_cooldown += dt
        if self.msg_timer > 0:
            self.msg_timer -= dt
            if self.msg_timer <= 0:
                self.msg = ""

    def show_message(self, text: str, duration: int = 2000) -> None:
        self.msg = text
        self.msg_timer = duration

    def reset(self) -> None:
        self.powerups.empty()
        self.spawn_cooldown = POWERUP_COOLDOWN
        self.msg = ""
        self.msg_timer = 0
