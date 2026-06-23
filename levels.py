import random

from classes import GameState
from level_generator import generate_level
from settings import (
    BUNKER_BRICK_GAP, BUNKER_BRICK_W, BUNKER_COLS,
    BUNKER_COUNT, DIFFICULTY_PRESETS, GAME_WIDTH, POWERUP_COOLDOWN,
    UFO_SPAWN_MAX, UFO_SPAWN_MIN,
)
from sprites.bunker import Bunker
from sprites.enemy import EnemyFormation


def create_bunkers() -> list:
    spacing = GAME_WIDTH // (BUNKER_COUNT + 1)
    bunker_w = BUNKER_COLS * (BUNKER_BRICK_W + BUNKER_BRICK_GAP) - BUNKER_BRICK_GAP
    return [Bunker(spacing * i - bunker_w // 2) for i in range(1, BUNKER_COUNT + 1)]


def advance_level(game) -> None:
    game._advance_level()


def reset_game(game) -> None:
    game._reset_game()


def handle_transition_end(game) -> None:
    if game.state == GameState.INTRO:
        game.state = GameState.PLAYING
        game.sound.play_bgm()
    else:
        advance_level(game)
