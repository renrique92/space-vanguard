import random

from settings import ENEMY_BULLET_SPEED, SLOWMO_RATE
from sprites.bullet import Bullet


def handle_enemy_shooting(formation, player, level, enemy_bullets, sound, last_dt) -> None:
    slowmo_active = player.effects.slowmo > 0 if hasattr(player, 'effects') else False
    if slowmo_active:
        if random.random() >= SLOWMO_RATE:
            result = None
        else:
            result = formation.try_shoot()
    else:
        result = formation.try_shoot()

    if result:
        x, y = result
        r = random.random()
        if level >= 3 and r < 0.25:
            enemy_bullets.add(
                Bullet(x, y, ENEMY_BULLET_SPEED + 3, is_player=False)
            )
        elif level >= 2 and r < 0.35:
            enemy_bullets.add(
                Bullet(x, y, ENEMY_BULLET_SPEED, is_player=False,
                       wiggle_amp=1.5, wiggle_freq=0.08)
            )
        else:
            enemy_bullets.add(
                Bullet(x, y, ENEMY_BULLET_SPEED, is_player=False)
            )
        sound.play("enemy_shoot")

    shooter_shots = formation.get_shooter_shots(last_dt)
    for sx, sy in shooter_shots:
        enemy_bullets.add(
            Bullet(sx, sy, ENEMY_BULLET_SPEED, is_player=False)
        )
