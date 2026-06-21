import json
import os
import random

import pygame

from settings import (
    BULLET_W, ENEMY_AUTO_STEP_INTERVAL, ENEMY_BULLET_SPEED,
    FPS, GAME_WIDTH, GameState, LEVELS, MAX_LIVES,
    MAX_PLAYER_BULLETS, PLAYER_BULLET_H, PLAYER_BULLET_SPEED,
    SCORE_MULT_START, SCORE_MULT_DECAY, SCORE_MULT_MIN,
    SHOT_DELAY, TOTAL_LEVELS, WINDOW_HEIGHT, WINDOW_WIDTH,
)
from sounds import SoundManager
from effects import ScreenShake, MuzzleFlash, spawn_explosion
from sprites.bullet import Bullet
from sprites.enemy import EnemyFormation
from sprites.player import Player
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

        self.stars = [
            (
                random.randint(0, GAME_WIDTH),
                random.randint(0, WINDOW_HEIGHT),
                random.randint(80, 255),
            )
            for _ in range(120)
        ]

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
        self.last_shot_time = 0
        self.elapsed_time = 0
        self.shots_fired = 0
        self.shots_hit = 0
        self._pending_shots = set()

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
            now = pygame.time.get_ticks()
            if (
                keys[pygame.K_SPACE]
                and len(self.player_bullets) < MAX_PLAYER_BULLETS
                and now - self.last_shot_time >= SHOT_DELAY
            ):
                self.last_shot_time = now
                x = self.player.rect.centerx - BULLET_W // 2
                y = self.player.rect.top - PLAYER_BULLET_H
                bullet = Bullet(x, y, -PLAYER_BULLET_SPEED, is_player=True)
                self.player_bullets.add(bullet)
                self._pending_shots.add(bullet)
                self.sound.play("shoot")
                self.flash_fx.add(
                    MuzzleFlash(self.player.rect.centerx, self.player.rect.top)
                )

    @property
    def score_multiplier(self):
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
                else:
                    self._advance_level()
            return

        self.screen_shake.update(dt)
        self.player.update(dt)
        self.formation.update()

        self.auto_step_timer += dt
        if self.auto_step_timer >= ENEMY_AUTO_STEP_INTERVAL:
            self.formation.auto_step_down()
            self.auto_step_timer = 0

        result = self.formation.try_shoot()
        if result:
            x, y = result
            self.enemy_bullets.add(
                Bullet(x, y, ENEMY_BULLET_SPEED, is_player=False)
            )
            self.sound.play("enemy_shoot")

        self.player_bullets.update()
        self.enemy_bullets.update()
        self.particles.update(dt)
        self.flash_fx.update(dt)

        hits = pygame.sprite.groupcollide(
            self.player_bullets, self.formation.enemies, True, True
        )
        mult = self.score_multiplier
        for bullet, enemies in hits.items():
            bullet.has_hit = True
            for enemy in enemies:
                self.shots_hit += 1
                self.score += int(enemy.points * mult)
                color = enemy.image.get_at((0, 0))[:3]
                self.particles.add(
                    spawn_explosion(
                        enemy.rect.centerx, enemy.rect.centery, color
                    )
                )
                self.sound.play("explosion")

        self._resolve_shots()

        if not self.player.invulnerable:
            hit = pygame.sprite.spritecollide(
                self.player, self.enemy_bullets, True
            )
            if hit:
                self.player.take_hit()
                self.sound.play("player_hit")
                self.screen_shake.trigger(8, 200)
                if self.player.lives <= 0:
                    self.state = GameState.GAME_OVER
                    self._save_high_score()
                    self.sound.play("game_over")

        if self.formation.reached_game_over():
            self.state = GameState.GAME_OVER
            self._save_high_score()
            self.sound.play("game_over")

        if len(self.formation.enemies) == 0:
            if self.level < TOTAL_LEVELS:
                self.transition_timer = 2000
                if self.player.lives < MAX_LIVES:
                    self.player.lives += 1
                self.sound.play("level_up")
                self.player_bullets.empty()
                self.enemy_bullets.empty()
            else:
                self.state = GameState.WIN
                self._save_high_score()
                self.sound.play("win")

    def _draw(self):
        self.renderer.draw(
            self.state, self.level, self.transition_timer,
            self.player, self.formation,
            self.player_bullets, self.enemy_bullets,
            self.particles, self.flash_fx,
            self.score, self.high_score, self.player.lives,
            self.score_multiplier, self.accuracy,
        )

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
        self.score = 0
        self.level = 1
        self.state = GameState.INTRO
        self._prev_state = GameState.INTRO
        self.transition_timer = 2000
        self.auto_step_timer = 0
        self.last_shot_time = 0
        self.elapsed_time = 0
        self.shots_fired = 0
        self.shots_hit = 0
        self._pending_shots.clear()
        self.player_bullets.empty()
        self.enemy_bullets.empty()
        self.particles.empty()
        self.flash_fx.empty()
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
        self.formation = EnemyFormation(LEVELS[self.level - 1])
        self.player.reset(reset_lives=False)
        self.auto_step_timer = 0


