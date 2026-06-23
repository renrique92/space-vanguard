from dataclasses import dataclass

import pygame

from classes import PowerUpType
from settings import (
    PLAYER_W, PLAYER_H, PLAYER_SPEED, PLAYER_LIVES,
    PLAYER_BOTTOM_MARGIN, INVULNERABLE_MS, GAME_WIDTH,
    POWERUP_DURATIONS, POWERUP_SHIP_COLORS,
    WINDOW_HEIGHT, GREEN, CYAN, GAME_AREA,
    SPECIAL_CHARGE_TIME, SPECIAL_DURATION,
)

TIMED_TYPES = [
    PowerUpType.SPREAD, PowerUpType.SHIELD, PowerUpType.SPEED,
    PowerUpType.RAPID, PowerUpType.PIERCE, PowerUpType.SCORE, PowerUpType.SLOWMO,
]


@dataclass
class TimedEffects:
    spread: int = 0
    shield: int = 0
    speed: int = 0
    rapid: int = 0
    pierce: int = 0
    score: int = 0
    slowmo: int = 0


POWERUP_FIELD_MAP = {
    PowerUpType.SPREAD: "spread",
    PowerUpType.SHIELD: "shield",
    PowerUpType.SPEED: "speed",
    PowerUpType.RAPID: "rapid",
    PowerUpType.PIERCE: "pierce",
    PowerUpType.SCORE: "score",
    PowerUpType.SLOWMO: "slowmo",
}
FIELD_TO_TYPE = {v: k for k, v in POWERUP_FIELD_MAP.items()}


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((PLAYER_W, PLAYER_H), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.reset()

    def _draw_ship(self, body_color=GREEN, accent_color=CYAN):
        self.image.fill((0, 0, 0, 0))
        cx, by = self.rect.width // 2, self.rect.height
        points = [(cx, 0), (2, by), (cx + cx - 2, by)]
        pygame.draw.polygon(self.image, body_color, points)
        pygame.draw.rect(self.image, accent_color, (cx - 4, by // 2 - 2, 8, by // 2))

    def reset(self, reset_lives=True):
        self.rect.midbottom = (GAME_WIDTH // 2, WINDOW_HEIGHT - PLAYER_BOTTOM_MARGIN)
        if reset_lives:
            self.lives = PLAYER_LIVES
            self.special_charge = 0.0
        self.speed = PLAYER_SPEED
        self.invulnerable = False
        self.invuln_timer = 0
        self.special_active = False
        self.special_used = False
        self.special_tick_timer = 0
        self.effects = TimedEffects()
        self._draw_ship()
        self.image.set_alpha(255)

    def update(self, *args):
        dt = args[0] if args else 16
        if self.invulnerable:
            self.invuln_timer -= dt
            if self.invuln_timer <= 0:
                self.invulnerable = False
                self.image.set_alpha(255)
            elif (int(self.invuln_timer / 100)) % 2 == 0:
                self.image.set_alpha(0)
            else:
                self.image.set_alpha(255)

        self.effects.spread = max(0, self.effects.spread - dt)
        self.effects.shield = max(0, self.effects.shield - dt)
        self.effects.speed = max(0, self.effects.speed - dt)
        self.effects.rapid = max(0, self.effects.rapid - dt)
        self.effects.pierce = max(0, self.effects.pierce - dt)
        self.effects.score = max(0, self.effects.score - dt)
        self.effects.slowmo = max(0, self.effects.slowmo - dt)

        if self.effects.speed > 0:
            self.speed = PLAYER_SPEED * 2
        else:
            self.speed = PLAYER_SPEED

        for field_name in POWERUP_FIELD_MAP.values():
            timer = getattr(self.effects, field_name, 0)
            if timer > 0:
                pt = FIELD_TO_TYPE[field_name]
                if pt in POWERUP_SHIP_COLORS:
                    self._draw_ship(*POWERUP_SHIP_COLORS[pt])
                    break
        else:
            if not self.invulnerable:
                self._draw_ship()

    def handle_input(self, keys):
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        self.rect.clamp_ip(GAME_AREA)

    def take_hit(self):
        if self.effects.shield > 0:
            self.effects.shield = 0
            return
        self.lives -= 1
        self.special_charge = 0.0
        self.special_active = False
        self.invulnerable = True
        self.invuln_timer = INVULNERABLE_MS
        self.rect.midbottom = (GAME_WIDTH // 2, WINDOW_HEIGHT - PLAYER_BOTTOM_MARGIN)

    def activate_powerup(self, power_type):
        self.effects = TimedEffects()
        dur = POWERUP_DURATIONS.get(power_type, 0)
        if dur > 0:
            field = POWERUP_FIELD_MAP.get(power_type)
            if field:
                setattr(self.effects, field, dur)
        if power_type in POWERUP_SHIP_COLORS:
            self._draw_ship(*POWERUP_SHIP_COLORS[power_type])

    def add_special_charge(self, dt):
        if not self.special_active and self.special_charge < 1.0:
            self.special_charge = min(1.0, self.special_charge + dt / SPECIAL_CHARGE_TIME)

    def drain_special_charge(self, dt):
        if self.special_active:
            self.special_charge = max(0.0, self.special_charge - dt / SPECIAL_DURATION)
            if self.special_charge <= 0.0:
                self.special_active = False
