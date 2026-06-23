import random

from classes import GameState
from settings import (
    BUNKER_BRICK_GAP, BUNKER_BRICK_W, BUNKER_COLS,
    BUNKER_COUNT, DIFFICULTY_PRESETS, GAME_WIDTH, LEVELS, POWERUP_COOLDOWN,
    UFO_SPAWN_MAX, UFO_SPAWN_MIN,
)
from sprites.bunker import Bunker
from sprites.enemy import EnemyFormation


def create_bunkers() -> list:
    spacing = GAME_WIDTH // (BUNKER_COUNT + 1)
    bunker_w = BUNKER_COLS * (BUNKER_BRICK_W + BUNKER_BRICK_GAP) - BUNKER_BRICK_GAP
    return [Bunker(spacing * i - bunker_w // 2) for i in range(1, BUNKER_COUNT + 1)]


def advance_level(game) -> None:
    game.level += 1
    game.transition_timer = 0
    game.elapsed_time = 0
    game.ufo = None
    game.ufo_spawn_timer = 0
    game.ufo_spawn_delay = random.randint(UFO_SPAWN_MIN, UFO_SPAWN_MAX)
    game.bunkers = create_bunkers()
    game.powerups.empty()
    game.powerup_spawn_cooldown = POWERUP_COOLDOWN
    diff = DIFFICULTY_PRESETS[game.difficulty]
    game.formation = EnemyFormation(LEVELS[game.level - 1], diff)
    game.player.reset(reset_lives=False)
    game.auto_step_timer = 0


def reset_game(game) -> None:
    game.sound.stop_bgm()
    game.score = 0
    game.level = 1
    game.state = GameState.INTRO
    game._prev_state = GameState.INTRO
    game.transition_timer = 2000
    game.auto_step_timer = 0
    game._shot_timer = 0
    game.elapsed_time = 0
    game.score_popups.clear()
    game.player_bullets.empty()
    game.enemy_bullets.empty()
    game.particles.empty()
    game.flash_fx.empty()
    game.powerups.empty()
    game.powerup_spawn_cooldown = POWERUP_COOLDOWN
    game.streak = 0
    game.ufo = None
    game.ufo_spawn_timer = 0
    game.ufo_spawn_delay = random.randint(UFO_SPAWN_MIN, UFO_SPAWN_MAX)
    game.boss = None
    game.boss_shoot_timer = 0
    game.bunkers = create_bunkers()
    diff = DIFFICULTY_PRESETS[game.difficulty]
    game.player.reset()
    game.player.lives = diff["lives"]
    game.formation = EnemyFormation(LEVELS[0], diff)


def handle_transition_end(game) -> None:
    if game.state == GameState.INTRO:
        game.state = GameState.PLAYING
        game.sound.play_bgm()
    else:
        advance_level(game)
