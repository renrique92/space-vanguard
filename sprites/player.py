import pygame
from classes import PowerUpType
from settings import (
    PLAYER_W, PLAYER_H, PLAYER_SPEED, PLAYER_LIVES,
    PLAYER_BOTTOM_MARGIN, INVULNERABLE_MS, GAME_WIDTH,
    POWERUP_DURATIONS, POWERUP_SHIP_COLORS,
    WINDOW_HEIGHT, GREEN, CYAN, GAME_AREA,
)

TIMED_TYPES = [
    PowerUpType.SPREAD, PowerUpType.SHIELD, PowerUpType.SPEED,
    PowerUpType.RAPID, PowerUpType.PIERCE, PowerUpType.SCORE, PowerUpType.SLOWMO,
]


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
        self.speed = PLAYER_SPEED
        self.invulnerable = False
        self.invuln_timer = 0
        self._clear_timers()
        self._draw_ship()
        self.image.set_alpha(255)

    def _clear_timers(self):
        for pt in TIMED_TYPES:
            setattr(self, f"{pt.name.lower()}_timer", 0)

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

        for pt in TIMED_TYPES:
            timer = getattr(self, f"{pt.name.lower()}_timer", 0)
            if timer > 0:
                setattr(self, f"{pt.name.lower()}_timer", timer - dt)

        if self.speed_timer > 0:
            self.speed = PLAYER_SPEED * 2
        else:
            self.speed = PLAYER_SPEED

        for pt in TIMED_TYPES:
            timer = getattr(self, f"{pt.name.lower()}_timer", 0)
            if timer > 0 and pt in POWERUP_SHIP_COLORS:
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
        if self.shield_timer > 0:
            self.shield_timer = 0
            return
        self.lives -= 1
        self.invulnerable = True
        self.invuln_timer = INVULNERABLE_MS
        self.rect.midbottom = (GAME_WIDTH // 2, WINDOW_HEIGHT - PLAYER_BOTTOM_MARGIN)

    def activate_powerup(self, power_type):
        self._clear_timers()
        dur = POWERUP_DURATIONS.get(power_type, 0)
        if dur > 0:
            setattr(self, f"{power_type.name.lower()}_timer", dur)
        if power_type in POWERUP_SHIP_COLORS:
            self._draw_ship(*POWERUP_SHIP_COLORS[power_type])
