from typing import Optional

import pygame

from events import CollisionEvent


def check_bunker_collisions(player_bullets, enemy_bullets, bunkers) -> None:
    for bunker in bunkers:
        for bullet in player_bullets.sprites():
            if not bullet.alive():
                continue
            bricks = pygame.sprite.spritecollide(bullet, bunker.bricks, False)
            if bricks:
                bullet.kill()
                bricks[0].hit()
        pygame.sprite.groupcollide(
            enemy_bullets, bunker.bricks, True, True,
        )


def check_enemy_collisions(player_bullets, enemies, dokill_player, mult, streak
                           ) -> tuple[list[CollisionEvent], int]:
    events = []
    hits = pygame.sprite.groupcollide(
        player_bullets, enemies, dokill_player, False,
    )
    for bullet, hit_enemies in hits.items():
        bullet.has_hit = True
        for enemy in list(hit_enemies):
            killed = enemy.take_hit()
            color = enemy.image.get_at((0, 0))[:3]
            if killed:
                streak += 1
                streak_bonus = min(streak, 99)
                pts = int(enemy.points * mult) + streak_bonus
                enemy.kill()
                events.append(CollisionEvent(
                    points=pts,
                    x=enemy.rect.centerx,
                    y=enemy.rect.centery,
                    color=color,
                    sound="explosion",
                    explosion_count=10,
                ))
            else:
                if dokill_player:
                    bullet.kill()
                events.append(CollisionEvent(
                    points=0,
                    x=bullet.rect.centerx,
                    y=bullet.rect.centery,
                    color=color,
                    explosion_count=3,
                ))
    return events, streak


def check_boss_collisions(player_bullets, boss) -> list[CollisionEvent]:
    if not boss:
        return []
    events = []
    for bullet in player_bullets.sprites():
        if bullet.has_hit:
            continue
        if bullet.rect.colliderect(boss.rect):
            bullet.kill()
            bullet.has_hit = True
            boss.take_hit()
            events.append(CollisionEvent(
                points=50,
                x=boss.rect.centerx,
                y=boss.rect.top,
                color=(200, 100, 100),
                sound="explosion",
                explosion_count=10,
            ))
    return events


def check_powerup_collection(player, powerups) -> Optional[CollisionEvent]:
    collected = pygame.sprite.spritecollide(player, powerups, True)
    if not collected:
        return None
    pu = collected[0]
    player.activate_powerup(pu.power_type)
    return CollisionEvent(
        sound="powerup",
        powerup_name=pu.power_type.name.title(),
    )


def check_player_hit(player, enemy_bullets, kamikazes, minions) -> Optional[CollisionEvent]:
    if player.invulnerable:
        return None

    hit_by_bullet = pygame.sprite.spritecollide(
        player, enemy_bullets, True,
    )
    hit_by_kamikaze = (
        pygame.sprite.spritecollide(player, kamikazes, True)
        if kamikazes else []
    )
    hit_by_minion = (
        pygame.sprite.spritecollide(player, minions, True)
        if minions else []
    )

    if not (hit_by_bullet or hit_by_kamikaze or hit_by_minion):
        return None

    player.take_hit()
    return CollisionEvent(
        player_hit=True,
        x=player.rect.centerx,
        y=player.rect.centery,
        color=(0, 200, 255),
        explosion_count=10,
    )


def check_ufo_collision(player_bullets, ufo) -> Optional[CollisionEvent]:
    if ufo is None:
        return None
    hits = pygame.sprite.spritecollide(ufo, player_bullets, True)
    if not hits:
        return None
    bullet = hits[0]
    bullet.has_hit = True
    pts = ufo.points
    return CollisionEvent(
        points=pts,
        x=ufo.rect.centerx,
        y=ufo.rect.centery,
        color=(180, 100, 200),
        sound="explosion",
        explosion_count=10,
    )


def check_kamikaze_collisions(player_bullets, kamikazes, mult, streak
                              ) -> tuple[list[CollisionEvent], int]:
    events = []
    hits = pygame.sprite.groupcollide(player_bullets, kamikazes, True, True)
    for bullet, kam_list in hits.items():
        for kam in kam_list:
            streak += 1
            streak_bonus = min(streak, 99)
            pts = int(kam.points * mult) + streak_bonus
            events.append(CollisionEvent(
                points=pts,
                x=kam.rect.centerx,
                y=kam.rect.centery,
                color=(200, 100, 50),
                explosion_count=4,
            ))
    return events, streak


def check_minion_collisions(player_bullets, minions) -> list[CollisionEvent]:
    events = []
    hits = pygame.sprite.groupcollide(player_bullets, minions, True, True)
    for bullet, m_list in hits.items():
        for m in m_list:
            events.append(CollisionEvent(
                points=20,
                x=m.rect.centerx,
                y=m.rect.centery,
                color=(255, 150, 50),
                sound="explosion",
                explosion_count=3,
            ))
    return events
