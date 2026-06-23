from dataclasses import dataclass
from typing import Optional

from classes import PowerUpType


@dataclass
class CollisionEvent:
    points: int = 0
    x: float = 0
    y: float = 0
    color: tuple = (255, 255, 255)
    sound: Optional[str] = None
    explosion_count: int = 0
    player_hit: bool = False
    powerup_name: str = ""
