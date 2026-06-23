import random

from settings import GAME_WIDTH, UFO_SPAWN_MIN, UFO_SPAWN_MAX
from sprites.ufo import UFO


class UfoManager:
    def __init__(self):
        self.ufo = None
        self.spawn_timer = 0
        self.spawn_delay = random.randint(UFO_SPAWN_MIN, UFO_SPAWN_MAX)

    def update(self, dt: int) -> None:
        if self.ufo is None:
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_delay:
                self.ufo = UFO()
                self.spawn_timer = 0
        else:
            self.ufo.update(dt)
            off_screen = (
                self.ufo.rect.right < 0 or self.ufo.rect.left > GAME_WIDTH
            )
            if off_screen:
                self._despawn()

    def _despawn(self) -> None:
        self.ufo = None
        self.spawn_delay = random.randint(UFO_SPAWN_MIN, UFO_SPAWN_MAX)
        self.spawn_timer = 0

    def despawn(self) -> None:
        self._despawn()

    def reset(self) -> None:
        self.ufo = None
        self.spawn_timer = 0
        self.spawn_delay = random.randint(UFO_SPAWN_MIN, UFO_SPAWN_MAX)
