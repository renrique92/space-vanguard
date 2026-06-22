import json
import os
import random

import pygame

from classes import GameState, PowerUpType
from settings import (
    BULLET_W, BUNKER_COUNT,
    ENEMY_BULLET_SPEED, FPS, GAME_WIDTH, LEVELS,
    MAX_LIVES, MAX_PLAYER_BULLETS, PLAYER_BULLET_H,
    PLAYER_BULLET_SPEED, POWERUP_CHANCE, POWERUP_COOLDOWN,
    SCORE_MULT_START, SCORE_MULT_DECAY,
    SCORE_MULT_MIN, SHOT_DELAY, SLOWMO_RATE, TOTAL_LEVELS,
    UFO_SPAWN_MIN, UFO_SPAWN_MAX, WINDOW_HEIGHT, WINDOW_WIDTH,
)
from sounds import SoundManager
from effects import ScreenShake, MuzzleFlash, spawn_explosion
from sprites.boss import Boss
from sprites.bullet import Bullet
from sprites.bunker import Bunker
from sprites.enemy import EnemyFormation
from sprites.player import Player
from sprites.powerup import PowerUp
from sprites.ufo import UFO
from ui.info_panel import InfoPanel
from renderer import Renderer

HIGH_SCORE_FILE = os.path.join(os.path.dirname(__file__), "high_score.json")


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Space Vanguard")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.INTRO
        self._prev_state = GameState.INTRO
        self.score = 0
        self.high_score = self._load_high_score()

        self.stars = []
        layers = [
            (40, 0.2, 80, 1),
            (40, 0.5, 160, 1),
            (40, 1.0, 255, 2),
        ]
        for count, speed, base_brightness, size in layers:
            for _ in range(count):
                self.stars.append([
                    random.uniform(0, GAME_WIDTH),
                    random.uniform(0, WINDOW_HEIGHT),
                    base_brightness,
                    size,
                    speed,
                ])

        self.sound = SoundManager()
        self.screen_shake = ScreenShake()

        self.level = 1
        self.transition_timer = 2000

        self.player = Player()
        self.formation = EnemyFormation(LEVELS[0])
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.flash_fx = pygame.sprite.Group()
        self.info_panel = InfoPanel()
        self.auto_step_timer = 0
        self._shot_timer = 0
        self.elapsed_time = 0
        self.shots_fired = 0
        self.shots_hit = 0
        self._pending_shots = set()
        self.score_popups = []

        self.powerups = pygame.sprite.Group()
        self.powerup_msg = ""
        self.powerup_msg_timer = 0
        self.powerup_spawn_cooldown = POWERUP_COOLDOWN

        self.ufo = None
        self.ufo_spawn_timer = 0
        self.ufo_spawn_delay = random.randint(UFO_SPAWN_MIN, UFO_SPAWN_MAX)
        self.boss = None
        self.boss_shoot_timer = 0

        self.bunkers = self._create_bunkers()

        self.game_surf = pygame.Surface((GAME_WIDTH, WINDOW_HEIGHT))
        self.renderer = Renderer(
            self.screen, self.game_surf, self.screen_shake,
            self.info_panel, self.stars,
        )

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self._handle_events()

            if self.state in (GameState.INTRO, GameState.PLAYING):
                self._update(dt)

            self._draw()
        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_p:
                    if self.state == GameState.PAUSED:
                        self.state = self._prev_state
                    elif self.state in (GameState.INTRO, GameState.PLAYING):
                        self._prev_state = self.state
                        self.state = GameState.PAUSED
                elif event.key == pygame.K_r and self.state in (GameState.GAME_OVER, GameState.WIN):
                    self._reset()

        if self.state == GameState.PLAYING and self.transition_timer <= 0:
            keys = pygame.key.get_pressed()
            self.player.handle_input(keys)
            shot_delay = 80 if self.player.rapid_timer > 0 else SHOT_DELAY
            if (
                keys[pygame.K_SPACE]
                and len(self.player_bullets) < MAX_PLAYER_BULLETS
                and self._shot_timer <= 0
            ):
                if self.player.spread_timer > 0:
                    bullets = self._create_spread()
                else:
                    bullets = self._create_bullet()
                if bullets:
                    self._shot_timer = shot_delay
                    for b in bullets:
                        self.player_bullets.add(b)
                        self._pending_shots.add(b)
                    self.sound.play("shoot")
                    self.flash_fx.add(
                        MuzzleFlash(self.player.rect.centerx, self.player.rect.top)
                    )

    @property
    def score_multiplier(self):
        if self.player.score_timer > 0:
            return 2.0
        sec = self.elapsed_time / 1000
        return max(SCORE_MULT_MIN, SCORE_MULT_START - sec / SCORE_MULT_DECAY)

    @property
    def accuracy(self):
        if self.shots_fired == 0:
            return 100.0
        return self.shots_hit / self.shots_fired * 100

    def _update(self, dt):
        self.elapsed_time += dt

        if self.transition_timer > 0:
            self.transition_timer -= dt
            self.particles.update(dt)
            self.flash_fx.update(dt)
            if self.transition_timer <= 0:
                if self.state == GameState.INTRO:
                    self.state = GameState.PLAYING
                    self.sound.play_bgm()
                else:
                    self._advance_level()
            return

        self._update_stars(dt)
        self.screen_shake.update(dt)
        self.player.update(dt)

        speed_mult = SLOWMO_RATE if self.player.slowmo_timer > 0 else 1.0
        self.formation.update(dt, speed_mult)
        self.auto_step_timer += int(dt * speed_mult)

        if self.auto_step_timer >= self.formation._diff["auto_step_ms"]:
            self.formation.auto_step_down()
            self.auto_step_timer = 0

        if self.player.slowmo_timer > 0:
            if random.random() >= SLOWMO_RATE:
                result = None
            else:
                result = self.formation.try_shoot()
        else:
            result = self.formation.try_shoot()
        if result:
            x, y = result
            r = random.random()
            if self.level >= 3 and r < 0.25:
                self.enemy_bullets.add(
                    Bullet(x, y, ENEMY_BULLET_SPEED + 3, is_player=False)
                )
            elif self.level >= 2 and r < 0.35:
                self.enemy_bullets.add(
                    Bullet(x, y, ENEMY_BULLET_SPEED, is_player=False,
                           wiggle_amp=1.5, wiggle_freq=0.08)
                )
            else:
                self.enemy_bullets.add(
                    Bullet(x, y, ENEMY_BULLET_SPEED, is_player=False)
                )
            self.sound.play("enemy_shoot")

        self.player_bullets.update()
        self.enemy_bullets.update()
        self.particles.update(dt)
        self.flash_fx.update(dt)
        self._update_score_popups(dt)

        self.powerup_spawn_cooldown += dt
        self._update_ufo(dt)

        if self.boss:
            self.boss.update(dt)
            self.boss_shoot_timer += dt
            if self.boss_shoot_timer >= 800:
                self.boss_shoot_timer = 0
                x, y = self.boss.try_shoot()
                self.enemy_bullets.add(
                    Bullet(x, y, ENEMY_BULLET_SPEED + 2, is_player=False)
                )

        for bunker in self.bunkers:
            for bullet in self.player_bullets.sprites():
                if not bullet.alive():
                    continue
                bricks = pygame.sprite.spritecollide(bullet, bunker.bricks, False)
                if bricks:
                    bullet.kill()
                    bricks[0].hit()
            pygame.sprite.groupcollide(
                self.enemy_bullets, bunker.bricks, True, True
            )

        dokill_player = self.player.pierce_timer <= 0
        hits = pygame.sprite.groupcollide(
            self.player_bullets, self.formation.enemies, dokill_player, True
        )
        mult = self.score_multiplier
        for bullet, enemies in hits.items():
            bullet.has_hit = True
            for enemy in enemies:
                self.shots_hit += 1
                pts = int(enemy.points * mult)
                self.score += pts
                self.score_popups.append({
                    "text": f"+{pts}",
                    "x": enemy.rect.centerx,
                    "y": enemy.rect.centery,
                    "timer": 800,
                    "start_y": enemy.rect.centery,
                })
                color = enemy.image.get_at((0, 0))[:3]
                self.particles.add(
                    spawn_explosion(
                        enemy.rect.centerx, enemy.rect.centery, color
                    )
                )
                self.sound.play("explosion")
                if (self.powerup_spawn_cooldown >= POWERUP_COOLDOWN
                        and random.random() < POWERUP_CHANCE):
                    ptype = random.choice(list(PowerUpType))
                    self.powerups.add(
                        PowerUp(enemy.rect.centerx, enemy.rect.centery, ptype)
                    )
                    self.powerup_spawn_cooldown = 0

        if self.boss:
            for bullet in self.player_bullets.sprites():
                if bullet.has_hit:
                    continue
                if bullet.rect.colliderect(self.boss.rect):
                    bullet.kill()
                    self.shots_hit += 1
                    self.boss.take_hit()
                    self.particles.add(
                        spawn_explosion(
                            bullet.rect.centerx, bullet.rect.centery,
                            (200, 100, 100),
                        )
                    )
                    self.score += 50
                    self.score_popups.append({
                        "text": "+50",
                        "x": self.boss.rect.centerx,
                        "y": self.boss.rect.top,
                        "timer": 800,
                        "start_y": self.boss.rect.top,
                    })

        collected = pygame.sprite.spritecollide(
            self.player, self.powerups, True
        )
        for pu in collected:
            self.player.activate_powerup(pu.power_type)
            self.sound.play("powerup")
            self.powerup_msg = pu.power_type.name.title()
            self.powerup_msg_timer = 2000

        if self.powerup_msg_timer > 0:
            self.powerup_msg_timer -= dt
            if self.powerup_msg_timer <= 0:
                self.powerup_msg = ""

        self.powerups.update(dt)

        self._resolve_shots()
        self._shot_timer = max(0, self._shot_timer - dt)

        if not self.player.invulnerable:
            hit = pygame.sprite.spritecollide(
                self.player, self.enemy_bullets, True
            )
            if hit:
                self.player.take_hit()
                self.particles.add(
                    spawn_explosion(
                        self.player.rect.centerx, self.player.rect.centery,
                        (0, 200, 255),
                    )
                )
                self.sound.play("player_hit")
                self.screen_shake.trigger(8, 200)
                if self.player.lives <= 0:
                    self.state = GameState.GAME_OVER
                    self.sound.stop_bgm()
                    self._save_high_score()
                    self.sound.play("game_over")

        if self.formation.reached_game_over():
            self.state = GameState.GAME_OVER
            self.sound.stop_bgm()
            self._save_high_score()
            self.sound.play("game_over")

        if len(self.formation.enemies) == 0 and self.boss is None:
            if self.level < TOTAL_LEVELS:
                self.transition_timer = 2000
                if self.player.lives < MAX_LIVES:
                    self.player.lives += 1
                self.sound.play("level_up")
                self.player_bullets.empty()
                self.enemy_bullets.empty()
            else:
                self.boss = Boss()
                self.boss_shoot_timer = 0

        if self.boss and self.boss.hp <= 0:
            self.state = GameState.WIN
            self.sound.stop_bgm()
            self._save_high_score()
            self.sound.play("win")

    def _update_score_popups(self, dt):
        for popup in self.score_popups[:]:
            popup["timer"] -= dt
            popup["y"] -= 0.5 * (dt / 16)
            if popup["timer"] <= 0:
                self.score_popups.remove(popup)

    def _update_stars(self, dt):
        for s in self.stars:
            s[1] += s[4] * (dt / 16)
            if s[1] > WINDOW_HEIGHT:
                s[1] = 0
                s[0] = random.uniform(0, GAME_WIDTH)

    def _create_bullet(self):
        if len(self.player_bullets) >= MAX_PLAYER_BULLETS:
            return []
        x = self.player.rect.centerx - BULLET_W // 2
        y = self.player.rect.top - PLAYER_BULLET_H
        return [Bullet(x, y, -PLAYER_BULLET_SPEED, is_player=True)]

    def _create_spread(self):
        if len(self.player_bullets) + 3 > MAX_PLAYER_BULLETS:
            return []
        cx = self.player.rect.centerx
        y = self.player.rect.top - PLAYER_BULLET_H
        bullets = []
        for ox, ovx in [(-8, -2), (0, 0), (8, 2)]:
            x = cx - BULLET_W // 2 + ox
            bullets.append(
                Bullet(x, y, -PLAYER_BULLET_SPEED, is_player=True, vx=ovx)
            )
        return bullets

    def _update_ufo(self, dt):
        if self.ufo is None:
            self.ufo_spawn_timer += dt
            if self.ufo_spawn_timer >= self.ufo_spawn_delay:
                self.ufo = UFO()
                self.sound.play("ufo")
                self.ufo_spawn_timer = 0
        else:
            self.ufo.update(dt)
            off_screen = (
                self.ufo.rect.right < 0 or self.ufo.rect.left > GAME_WIDTH
            )
            if off_screen:
                self.ufo = None
                self.ufo_spawn_delay = random.randint(
                    UFO_SPAWN_MIN, UFO_SPAWN_MAX
                )
                self.ufo_spawn_timer = 0
            else:
                hits = pygame.sprite.spritecollide(
                    self.ufo, self.player_bullets, True
                )
                if hits:
                    bullet = hits[0]
                    bullet.has_hit = True
                    pts = self.ufo.points
                    self.score += pts
                    self.shots_hit += 1
                    self.score_popups.append({
                        "text": f"+{pts}",
                        "x": self.ufo.rect.centerx,
                        "y": self.ufo.rect.centery,
                        "timer": 800,
                        "start_y": self.ufo.rect.centery,
                    })
                    self.particles.add(
                        spawn_explosion(
                            self.ufo.rect.centerx, self.ufo.rect.centery,
                            (180, 100, 200),
                        )
                    )
                    self.sound.play("explosion")
                    self.ufo = None
                    self.ufo_spawn_delay = random.randint(
                        UFO_SPAWN_MIN, UFO_SPAWN_MAX
                    )
                    self.ufo_spawn_timer = 0

    def _draw(self):
        active_pu_type = None
        active_pu_remaining = 0
        for pt in PowerUpType:
            timer = getattr(self.player, f"{pt.name.lower()}_timer", 0)
            if timer > 0:
                active_pu_type = pt
                active_pu_remaining = timer
                break

        self.renderer.draw(
            self.state, self.level, self.transition_timer,
            self.player, self.formation,
            self.player_bullets, self.enemy_bullets,
            self.particles, self.flash_fx,
            self.ufo, self.bunkers, self.powerups,
            self.score, self.high_score, self.player.lives,
            self.score_multiplier, self.accuracy,
            powerup_msg=self.powerup_msg,
            active_pu_type=active_pu_type,
            active_pu_remaining=active_pu_remaining,
            score_popups=self.score_popups,
            boss=self.boss,
        )

    @staticmethod
    def _create_bunkers():
        spacing = GAME_WIDTH // (BUNKER_COUNT + 1)
        return [Bunker(spacing * i) for i in range(1, BUNKER_COUNT + 1)]

    def _load_high_score(self):
        try:
            with open(HIGH_SCORE_FILE) as f:
                return json.load(f)
        except Exception:
            return 0

    def _save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            with open(HIGH_SCORE_FILE, "w") as f:
                json.dump(self.high_score, f)

    def _reset(self):
        self.sound.stop_bgm()
        self.score = 0
        self.level = 1
        self.state = GameState.INTRO
        self._prev_state = GameState.INTRO
        self.transition_timer = 2000
        self.auto_step_timer = 0
        self._shot_timer = 0
        self.elapsed_time = 0
        self.shots_fired = 0
        self.shots_hit = 0
        self._pending_shots.clear()
        self.score_popups.clear()
        self.player_bullets.empty()
        self.enemy_bullets.empty()
        self.particles.empty()
        self.flash_fx.empty()
        self.powerups.empty()
        self.powerup_spawn_cooldown = POWERUP_COOLDOWN
        self.ufo = None
        self.ufo_spawn_timer = 0
        self.ufo_spawn_delay = random.randint(UFO_SPAWN_MIN, UFO_SPAWN_MAX)
        self.boss = None
        self.boss_shoot_timer = 0
        self.bunkers = self._create_bunkers()
        self.player.reset()
        self.formation = EnemyFormation(LEVELS[0])

    def _resolve_shots(self):
        dead = [s for s in self._pending_shots if not s.alive()]
        for s in dead:
            self.shots_fired += 1
            self._pending_shots.remove(s)

    def _advance_level(self):
        self.level += 1
        self.transition_timer = 0
        self.elapsed_time = 0
        self.ufo = None
        self.ufo_spawn_timer = 0
        self.ufo_spawn_delay = random.randint(UFO_SPAWN_MIN, UFO_SPAWN_MAX)
        self.bunkers = self._create_bunkers()
        self.powerups.empty()
        self.powerup_spawn_cooldown = POWERUP_COOLDOWN
        self.formation = EnemyFormation(LEVELS[self.level - 1])
        self.player.reset(reset_lives=False)
        self.auto_step_timer = 0


