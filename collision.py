import random

import pygame

from classes import EnemyType, GameState, PowerUpType
from effects import spawn_explosion
from settings import (
    POWERUP_CHANCE, POWERUP_COOLDOWN, UFO_SPAWN_MAX, UFO_SPAWN_MIN,
    BOSS_INTERVAL, MAX_LIVES, SPECIAL_BEAM_TICK, SPECIAL_BEAM_WIDTH,
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
        game.player_bullets, game.formation.enemies, dokill_player, False
    )
    mult = game.score_multiplier
    for bullet, enemies in hits.items():
        bullet.has_hit = True
        for enemy in list(enemies):
            killed = enemy.take_hit()
            color = enemy.image.get_at((0, 0))[:3]
            if killed:
                game.streak += 1
                streak_bonus = min(game.streak, 99)
                pts = int(enemy.points * mult) + streak_bonus
                game.score += pts
                game.score_popups.append({
                    "text": f"+{pts}",
                    "x": enemy.rect.centerx,
                    "y": enemy.rect.centery,
                    "timer": 800,
                    "start_y": enemy.rect.centery,
                })
                game.particles.add(
                    spawn_explosion(enemy.rect.centerx, enemy.rect.centery, color)
                )
                game.sound.play("explosion")
                enemy.kill()
                if (game.powerup_spawn_cooldown >= POWERUP_COOLDOWN
                        and random.random() < POWERUP_CHANCE):
                    ptype = random.choice(list(PowerUpType))
                    game.powerups.add(
                        PowerUp(enemy.rect.centerx, enemy.rect.centery, ptype)
                    )
                    game.powerup_spawn_cooldown = 0
            else:
                if dokill_player:
                    bullet.kill()
                game.particles.add(
                    spawn_explosion(bullet.rect.centerx, bullet.rect.centery, color, count=3)
                )


def handle_boss_collisions(game) -> None:
    if not game.boss:
        return
    for bullet in game.player_bullets.sprites():
        if bullet.has_hit:
            continue
        if bullet.rect.colliderect(game.boss.rect):
            bullet.kill()
            bullet.has_hit = True
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

    hit_by_bullet = pygame.sprite.spritecollide(
        game.player, game.enemy_bullets, True
    )
    hit_by_kamikaze = pygame.sprite.spritecollide(
        game.player, game.kamikazes, True
    ) if game.kamikazes else []
    hit_by_minion = pygame.sprite.spritecollide(
        game.player, game.minions, True
    ) if game.minions else []

    if not (hit_by_bullet or hit_by_kamikaze or hit_by_minion):
        return

    game.player.take_hit()
    game.particles.add(
        spawn_explosion(
            game.player.rect.centerx, game.player.rect.centery,
            (0, 200, 255),
        )
    )
    game.streak = 0
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


def handle_kamikaze_bullet_collisions(game) -> None:
    hits = pygame.sprite.groupcollide(game.player_bullets, game.kamikazes, True, True)
    for bullet, kamikazes in hits.items():
        for kam in kamikazes:
            game.streak += 1
            streak_bonus = min(game.streak, 99)
            pts = int(kam.points * game.score_multiplier) + streak_bonus
            game.score += pts
            game.particles.add(
                spawn_explosion(kam.rect.centerx, kam.rect.centery, (200, 100, 50), count=4)
            )


def handle_minion_collisions(game) -> None:
    hits = pygame.sprite.groupcollide(game.player_bullets, game.minions, True, True)
    for bullet, minions in hits.items():
        for m in minions:
            pts = 20
            game.score += pts
            game.particles.add(
                spawn_explosion(m.rect.centerx, m.rect.centery, (255, 150, 50), count=3)
            )
            game.sound.play("explosion")


def handle_game_state_checks(game) -> None:
    if game.formation.reached_game_over():
        game.state = GameState.GAME_OVER
        game.sound.stop_bgm()
        game._save_high_score()
        game.sound.play("game_over")
        return

    if len(game.formation.enemies) == 0 and game.boss is None:
        if game.level % BOSS_INTERVAL == 0:
            game.boss = Boss()
            game.boss_shoot_timer = 0
        else:
            game.transition_timer = 2000
            if game.player.lives < MAX_LIVES:
                game.player.lives += 1
            game.sound.play("level_up")
            game.player_bullets.empty()
            game.enemy_bullets.empty()

    if game.boss and game.boss.hp <= 0:
        game.transition_timer = 2000
        if game.player.lives < MAX_LIVES:
            game.player.lives += 1
        game.sound.play("level_up")
        game.player_bullets.empty()
        game.enemy_bullets.empty()
        game.boss = None
        game.boss_shoot_timer = 0


def handle_special_beam(game) -> None:
    if not game.player.special_active:
        return
    if game.transition_timer > 0:
        return
    game.player.special_tick_timer += game._last_dt
    if game.player.special_tick_timer < SPECIAL_BEAM_TICK:
        return
    game.player.special_tick_timer = 0

    cx = game.player.rect.centerx
    beam_rect = pygame.Rect(cx - SPECIAL_BEAM_WIDTH // 2, 0, SPECIAL_BEAM_WIDTH, game.player.rect.top)

    for enemy in list(game.formation.enemies):
        if enemy.rect.colliderect(beam_rect):
            mult = game.score_multiplier
            game.streak += 1
            streak_bonus = min(game.streak, 99)
            pts = int(enemy.points * mult) + streak_bonus
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
                spawn_explosion(enemy.rect.centerx, enemy.rect.centery, color, count=6)
            )
            game.sound.play("explosion")
            enemy.kill()

    for bullet in list(game.enemy_bullets):
        if bullet.rect.colliderect(beam_rect):
            bullet.kill()

    if game.ufo and game.ufo.rect.colliderect(beam_rect):
        pts = game.ufo.points
        game.score += pts
        game.score_popups.append({
            "text": f"+{pts}",
            "x": game.ufo.rect.centerx,
            "y": game.ufo.rect.centery,
            "timer": 800,
            "start_y": game.ufo.rect.centery,
        })
        game.particles.add(
            spawn_explosion(game.ufo.rect.centerx, game.ufo.rect.centery, (180, 100, 200))
        )
        game.sound.play("explosion")
        game.ufo = None
        game.ufo_spawn_delay = random.randint(UFO_SPAWN_MIN, UFO_SPAWN_MAX)
        game.ufo_spawn_timer = 0

    for kam in list(game.kamikazes):
        if kam.rect.colliderect(beam_rect):
            game.streak += 1
            pts = int(kam.points * game.score_multiplier) + min(game.streak, 99)
            game.score += pts
            game.particles.add(spawn_explosion(kam.rect.centerx, kam.rect.centery, (200, 100, 50), count=4))
            kam.kill()

    for m in list(game.minions):
        if m.rect.colliderect(beam_rect):
            game.score += 20
            game.particles.add(spawn_explosion(m.rect.centerx, m.rect.centery, (255, 150, 50), count=3))
            m.kill()

    if game.boss and game.boss.rect.colliderect(beam_rect):
        game.boss.take_hit()
        game.particles.add(
            spawn_explosion(game.boss.rect.centerx, game.boss.rect.centery, (200, 100, 100), count=4)
        )
        game.score += 50
        game.sound.play("explosion")
