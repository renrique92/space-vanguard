import random

from settings import ENEMY_BULLET_SPEED, SLOWMO_RATE
from sprites.bullet import Bullet


def handle_enemy_shooting(game) -> None:
    if game.player.slowmo_timer > 0:
        if random.random() >= SLOWMO_RATE:
            result = None
        else:
            result = game.formation.try_shoot()
    else:
        result = game.formation.try_shoot()

    if not result:
        return

    x, y = result
    r = random.random()
    if game.level >= 3 and r < 0.25:
        game.enemy_bullets.add(
            Bullet(x, y, ENEMY_BULLET_SPEED + 3, is_player=False)
        )
    elif game.level >= 2 and r < 0.35:
        game.enemy_bullets.add(
            Bullet(x, y, ENEMY_BULLET_SPEED, is_player=False,
                   wiggle_amp=1.5, wiggle_freq=0.08)
        )
    else:
        game.enemy_bullets.add(
            Bullet(x, y, ENEMY_BULLET_SPEED, is_player=False)
        )
    game.sound.play("enemy_shoot")
