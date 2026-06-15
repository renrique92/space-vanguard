import math
import random

import pygame


class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color, speed, angle, life_ms, size=3):
        super().__init__()
        self.size = size
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.age = 0
        self.life_ms = life_ms

    def update(self, *args):
        dt = args[0] if args else 16
        self.age += dt
        if self.age > self.life_ms:
            self.kill()
            return
        ratio = self.age / self.life_ms
        self.rect.x += self.vx
        self.rect.y += self.vy
        self.image.set_alpha(int(255 * (1 - ratio)))


def spawn_explosion(x, y, color, count=10):
    group = pygame.sprite.Group()
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 4.5)
        life = random.randint(200, 400)
        size = random.randint(2, 4)
        group.add(Particle(x, y, color, speed, angle, life, size))
    return group


class MuzzleFlash(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((14, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (255, 255, 200, 220), (0, 0, 14, 8))
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.age = 0

    def update(self, *args):
        dt = args[0] if args else 16
        self.age += dt
        if self.age > 80:
            self.kill()
        elif self.age > 40:
            ratio = (self.age - 40) / 40
            self.image.set_alpha(max(0, 220 - int(220 * ratio)))


class ScreenShake:
    def __init__(self):
        self.offset_x = 0.0
        self.offset_y = 0.0
        self._intensity = 0.0
        self._duration = 0
        self._age = 0
        self._active = False

    def trigger(self, intensity, duration_ms):
        self._intensity = intensity
        self._duration = duration_ms
        self._age = 0
        self._active = True

    def update(self, dt=None):
        if not self._active:
            self.offset_x = 0.0
            self.offset_y = 0.0
            return
        self._age += dt if dt else 16
        if self._age > self._duration:
            self._active = False
            self.offset_x = 0.0
            self.offset_y = 0.0
            return
        decay = 1 - self._age / self._duration
        strength = self._intensity * decay
        self.offset_x = random.uniform(-strength, strength)
        self.offset_y = random.uniform(-strength, strength)

    def get_offset(self):
        return (int(self.offset_x), int(self.offset_y))
