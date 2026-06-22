from enum import Enum, auto


class GameState(Enum):
    TITLE = auto()
    INTRO = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    WIN = auto()
