from enum import Enum, auto

import pygame

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
FPS = 60

GAME_WIDTH = 700
PANEL_WIDTH = 300

GAME_AREA = pygame.Rect(0, 0, GAME_WIDTH, WINDOW_HEIGHT)
PANEL_AREA = pygame.Rect(GAME_WIDTH, 0, PANEL_WIDTH, WINDOW_HEIGHT)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (57, 255, 20)
RED = (255, 50, 50)
ORANGE = (255, 140, 0)
YELLOW = (255, 230, 50)
LIME = (80, 220, 80)
CYAN = (0, 255, 255)
DARK_BG = (15, 15, 30)
DIVIDER = (60, 60, 80)
TEXT_MAIN = (200, 200, 210)
TEXT_ACCENT = (255, 200, 50)
TITLE_COLOR = (80, 200, 255)
PLAYER_BULLET_COLOR = CYAN
ENEMY_BULLET_COLOR = (255, 100, 50)

PLAYER_W = 40
PLAYER_H = 30
PLAYER_SPEED = 5
PLAYER_LIVES = 3
PLAYER_BOTTOM_MARGIN = 30
INVULNERABLE_MS = 1500
MAX_PLAYER_BULLETS = 3
SHOT_DELAY = 250

ENEMY_W = 36
ENEMY_H = 22
ENEMY_H_GAP = 10
ENEMY_V_GAP = 10
ENEMY_TOP = 60
ENEMY_BASE_SPEED = 1.5
ENEMY_STEP_DOWN = 20
ENEMY_AUTO_STEP_INTERVAL = 4000
ENEMY_AUTO_STEP = 3
ENEMY_ANIM_INTERVAL = 500
ENEMY_BOUNDARY = 10

ROW_COLORS = [RED, ORANGE, YELLOW, LIME, CYAN]
ROW_POINTS = [30, 25, 20, 15, 10]

TOTAL_LEVELS = 5
MAX_LIVES = 5

LEVELS = [
    {
        "pattern": [
            [1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1],
        ],
        "colors": [RED, ORANGE, YELLOW, LIME, CYAN],
        "points": [30, 25, 20, 15, 10],
    },
    {
        "pattern": [
            [0,0,0,1,1,0,0,0],
            [0,0,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,0],
            [0,0,1,1,1,1,0,0],
            [0,0,0,1,1,0,0,0],
        ],
        "colors": [RED, ORANGE, YELLOW, LIME, CYAN],
        "points": [30, 25, 20, 15, 10],
    },
    {
        "pattern": [
            [0,0,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,0],
            [1,1,1,1,1,1,1,1],
            [0,1,1,0,0,1,1,0],
            [0,0,1,0,0,1,0,0],
        ],
        "colors": [RED, ORANGE, YELLOW, LIME, CYAN],
        "points": [30, 25, 20, 15, 10],
    },
    {
        "pattern": [
            [1,0,1,0,1,0,1,0,1,0],
            [1,0,1,0,1,0,1,0,1,0],
            [1,0,1,0,1,0,1,0,1,0],
            [1,0,1,0,1,0,1,0,1,0],
        ],
        "colors": [RED, ORANGE, YELLOW, LIME],
        "points": [30, 25, 20, 15],
    },
    {
        "pattern": [
            [1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1],
        ],
        "colors": [RED, ORANGE],
        "points": [35, 30],
    },
]

BULLET_W = 4
PLAYER_BULLET_H = 14
ENEMY_BULLET_H = 10
PLAYER_BULLET_SPEED = 9
ENEMY_BULLET_SPEED = 5

ENEMY_SHOOT_RATE_BASE = 0.015
ENEMY_SHOOT_RATE_PER_ENEMY = 0.00025

UFO_W = 44
UFO_H = 20
UFO_SPEED = 3
UFO_Y = 40
UFO_SPAWN_MIN = 8000
UFO_SPAWN_MAX = 15000
UFO_POINTS = [50, 100, 150, 200, 300]

BUNKER_COUNT = 3
BUNKER_COLS = 9
BUNKER_ROWS = 6
BUNKER_BRICK_W = 8
BUNKER_BRICK_H = 6
BUNKER_BRICK_GAP = 1
BUNKER_Y = WINDOW_HEIGHT - 140
BUNKER_COLOR = (0, 180, 0)
BUNKER_HIT_COLOR = (100, 220, 100)

GAME_OVER_LINE = WINDOW_HEIGHT - 80

SCORE_MULT_START = 3.0
SCORE_MULT_DECAY = 10
SCORE_MULT_MIN = 0.3


class GameState(Enum):
    INTRO = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    WIN = auto()
