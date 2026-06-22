import random

import pygame

from classes import GameState, PowerUpType
from effects import spawn_explosion
from settings import (
    POWERUP_CHANCE, POWERUP_COOLDOWN, UFO_SPAWN_MAX, UFO_SPAWN_MIN,
    MAX_LIVES, TOTAL_LEVELS,
)
from sprites.boss import Boss
from sprites.powerup import PowerUp


def handle_bunker_collisions(game) -> None:
    for bunker in game.bunkers:
        for bullet in game.player_bullets.sprites():
            if not bullet.alive():
                continue
            bricks = pygame.sprite.spritecollide(bullet, bunker.bricks, False)
            if bricks:
                bullet.kill()
                bricks[0].hit()
        pygame.sprite.groupcollide(
            game.enemy_bullets, bunker.bricks, True, True
        )


def handle_enemy_collisions(game) -> None:
    dokill_player = game.player.pierce_timer <= 0
    hits = pygame.sprite.groupcollide(
        game.player_bullets, game.formation.enemies, dokill_player, True
    )
    mult = game.score_multiplier
    for bullet, enemies in hits.items():
        bullet.has_hit = True
        for enemy in enemies:
            game.shots_hit += 1
            pts = int(enemy.points * mult)
            game.score += pts
            game.score_popups.append({
                "text": f"+{pts}",
                "x": enemy.rect.centerx,
                "y": enemy.rect.centery,
                "timer": 800,
                "start_y": enemy.rect.centery,
            })
            color = enemy.image.get_at((0, 0))[:3]
            game.particles.add(
                spawn_explosion(
                    enemy.rect.centerx, enemy.rect.centery, color
                )
            )
            game.sound.play("explosion")
            if (game.powerup_spawn_cooldown >= POWERUP_COOLDOWN
                    and random.random() < POWERUP_CHANCE):
                ptype = random.choice(list(PowerUpType))
                game.powerups.add(
                    PowerUp(enemy.rect.centerx, enemy.rect.centery, ptype)
                )
                game.powerup_spawn_cooldown = 0


def handle_boss_collisions(game) -> None:
    if not game.boss:
        return
    for bullet in game.player_bullets.sprites():
        if bullet.has_hit:
            continue
        if bullet.rect.colliderect(game.boss.rect):
            bullet.kill()
            game.shots_hit += 1
            game.boss.take_hit()
            game.particles.add(
                spawn_explosion(
                    bullet.rect.centerx, bullet.rect.centery,
                    (200, 100, 100),
                )
            )
            game.score += 50
            game.score_popups.append({
                "text": "+50",
                "x": game.boss.rect.centerx,
                "y": game.boss.rect.top,
                "timer": 800,
                "start_y": game.boss.rect.top,
            })


def handle_powerup_collection(game) -> None:
    collected = pygame.sprite.spritecollide(
        game.player, game.powerups, True
    )
    for pu in collected:
        game.player.activate_powerup(pu.power_type)
        game.sound.play("powerup")
        game.powerup_msg = pu.power_type.name.title()
        game.powerup_msg_timer = 2000


def handle_player_hit(game) -> None:
    if game.player.invulnerable:
        return
    hit = pygame.sprite.spritecollide(
        game.player, game.enemy_bullets, True
    )
    if not hit:
        return
    game.player.take_hit()
    game.particles.add(
        spawn_explosion(
            game.player.rect.centerx, game.player.rect.centery,
            (0, 200, 255),
        )
    )
    game.sound.play("player_hit")
    game.screen_shake.trigger(8, 200)
    if game.player.lives <= 0:
        game.state = GameState.GAME_OVER
        game.sound.stop_bgm()
        game._save_high_score()
        game.sound.play("game_over")


def handle_ufo_collision(game) -> bool:
    if game.ufo is None:
        return False
    hits = pygame.sprite.spritecollide(game.ufo, game.player_bullets, True)
    if not hits:
        return False
    bullet = hits[0]
    bullet.has_hit = True
    pts = game.ufo.points
    game.score += pts
    game.shots_hit += 1
    game.score_popups.append({
        "text": f"+{pts}",
        "x": game.ufo.rect.centerx,
        "y": game.ufo.rect.centery,
        "timer": 800,
        "start_y": game.ufo.rect.centery,
    })
    game.particles.add(
        spawn_explosion(
            game.ufo.rect.centerx, game.ufo.rect.centery,
            (180, 100, 200),
        )
    )
    game.sound.play("explosion")
    game.ufo = None
    game.ufo_spawn_delay = random.randint(UFO_SPAWN_MIN, UFO_SPAWN_MAX)
    game.ufo_spawn_timer = 0
    return True


def handle_game_state_checks(game) -> None:
    if game.formation.reached_game_over():
        game.state = GameState.GAME_OVER
        game.sound.stop_bgm()
        game._save_high_score()
        game.sound.play("game_over")
        return

    if len(game.formation.enemies) == 0 and game.boss is None:
        if game.level < TOTAL_LEVELS:
            game.transition_timer = 2000
            if game.player.lives < MAX_LIVES:
                game.player.lives += 1
            game.sound.play("level_up")
            game.player_bullets.empty()
            game.enemy_bullets.empty()
        else:
            game.boss = Boss()
            game.boss_shoot_timer = 0

    if game.boss and game.boss.hp <= 0:
        game.state = GameState.WIN
        game.sound.stop_bgm()
        game._save_high_score()
        game.sound.play("win")
