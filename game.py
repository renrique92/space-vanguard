import json
import os
import random

import pygame

from classes import Difficulty, GameState, PowerUpType
from settings import DIFFICULTY_ORDER, DIFFICULTY_PRESETS
from collision import (
    handle_boss_collisions,
    handle_bunker_collisions,
    handle_enemy_collisions,
    handle_game_state_checks,
    handle_player_hit,
    handle_powerup_collection,
    handle_ufo_collision,
)
from levels import (
    advance_level, create_bunkers, handle_transition_end, reset_game,
)
from settings import (
    BULLET_W, ENEMY_BULLET_SPEED, FPS, GAME_WIDTH, LEVELS,
    MAX_LIVES, MAX_PLAYER_BULLETS, PLAYER_BULLET_H,
    PLAYER_BULLET_SPEED, POWERUP_COOLDOWN,
    SCORE_MULT_START, SCORE_MULT_DECAY,
    SCORE_MULT_MIN, SHOT_DELAY, SLOWMO_RATE, TOTAL_LEVELS,
    UFO_SPAWN_MIN, UFO_SPAWN_MAX, WINDOW_HEIGHT, WINDOW_WIDTH,
)
from sounds import SoundManager
from effects import ScreenShake, MuzzleFlash
from sprites.bullet import Bullet
from sprites.enemy import EnemyFormation
from sprites.player import Player
from sprites.ufo import UFO
from ui.info_panel import InfoPanel
from renderer import Renderer

HIGH_SCORE_FILE = os.path.join(os.path.dirname(__file__), "high_score.json")


class Game:
    def __init__(self) -> None:
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Space Vanguard")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.TITLE
        self._prev_state = GameState.TITLE
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
        self.difficulty = Difficulty.NORMAL

        self.player = Player()
        self.player.lives = DIFFICULTY_PRESETS[self.difficulty]["lives"]
        diff = DIFFICULTY_PRESETS[self.difficulty]
        self.formation = EnemyFormation(LEVELS[0], diff)
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

        self.streak = 0
        self.ufo = None
        self.ufo_spawn_timer = 0
        self.ufo_spawn_delay = random.randint(UFO_SPAWN_MIN, UFO_SPAWN_MAX)
        self.boss = None
        self.boss_shoot_timer = 0

        self.bunkers = create_bunkers()

        self.game_surf = pygame.Surface((GAME_WIDTH, WINDOW_HEIGHT))
        self.renderer = Renderer(
            self.screen, self.game_surf, self.screen_shake,
            self.info_panel, self.stars,
        )

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS)
            self._handle_events()

            if self.state in (GameState.TITLE, GameState.INTRO, GameState.PLAYING):
                self._update(dt)

            self._draw()
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif hasattr(pygame, 'WINDOWEVENT') and event.type == pygame.WINDOWEVENT:
                if event.event == pygame.WINDOWEVENT_FOCUS_LOST and self.state == GameState.PLAYING:
                    self._prev_state = self.state
                    self.state = GameState.PAUSED
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_p:
                    if self.state == GameState.PAUSED:
                        self.state = self._prev_state
                    elif self.state in (GameState.TITLE, GameState.INTRO, GameState.PLAYING):
                        self._prev_state = self.state
                        self.state = GameState.PAUSED
                elif event.key == pygame.K_r and self.state in (GameState.GAME_OVER, GameState.WIN):
                    reset_game(self)
                elif event.key == pygame.K_LEFT and self.state == GameState.TITLE:
                    idx = DIFFICULTY_ORDER.index(self.difficulty)
                    self.difficulty = DIFFICULTY_ORDER[(idx - 1) % len(DIFFICULTY_ORDER)]
                elif event.key == pygame.K_RIGHT and self.state == GameState.TITLE:
                    idx = DIFFICULTY_ORDER.index(self.difficulty)
                    self.difficulty = DIFFICULTY_ORDER[(idx + 1) % len(DIFFICULTY_ORDER)]
                elif event.key == pygame.K_SPACE and self.state == GameState.TITLE:
                    self.state = GameState.INTRO
                    self.transition_timer = 2000
                elif event.key == pygame.K_f:
                    pygame.display.toggle_fullscreen()
                elif event.key == pygame.K_m:
                    self.sound.muted = not self.sound.muted
                    if self.sound.muted:
                        self.sound.stop_bgm()

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

    def _update(self, dt: int) -> None:
        self.elapsed_time += dt
        self._update_stars(dt)

        if self.state == GameState.TITLE:
            return

        if self.transition_timer > 0:
            self.transition_timer -= dt
            self.particles.update(dt)
            self.flash_fx.update(dt)
            if self.transition_timer <= 0:
                handle_transition_end(self)
            return

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

        handle_bunker_collisions(self)
        handle_enemy_collisions(self)
        handle_boss_collisions(self)
        handle_powerup_collection(self)

        if self.powerup_msg_timer > 0:
            self.powerup_msg_timer -= dt
            if self.powerup_msg_timer <= 0:
                self.powerup_msg = ""

        self.powerups.update(dt)

        self._resolve_shots()
        self._shot_timer = max(0, self._shot_timer - dt)

        handle_player_hit(self)
        handle_game_state_checks(self)

    def _update_score_popups(self, dt: int) -> None:
        for popup in self.score_popups[:]:
            popup["timer"] -= dt
            popup["y"] -= 0.5 * (dt / 16)
            if popup["timer"] <= 0:
                self.score_popups.remove(popup)

    def _update_stars(self, dt: int) -> None:
        for s in self.stars:
            s[1] += s[4] * (dt / 16)
            if s[1] > WINDOW_HEIGHT:
                s[1] = 0
                s[0] = random.uniform(0, GAME_WIDTH)

    def _create_bullet(self) -> list:
        if len(self.player_bullets) >= MAX_PLAYER_BULLETS:
            return []
        x = self.player.rect.centerx - BULLET_W // 2
        y = self.player.rect.top - PLAYER_BULLET_H
        return [Bullet(x, y, -PLAYER_BULLET_SPEED, is_player=True)]

    def _create_spread(self) -> list:
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

    def _update_ufo(self, dt: int) -> None:
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
                handle_ufo_collision(self)

    def _draw(self) -> None:
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
            self.score_multiplier, self.accuracy, self.streak,
            difficulty=self.difficulty,
            powerup_msg=self.powerup_msg,
            active_pu_type=active_pu_type,
            active_pu_remaining=active_pu_remaining,
            score_popups=self.score_popups,
            boss=self.boss,
        )

    def _load_high_score(self) -> int:
        try:
            with open(HIGH_SCORE_FILE) as f:
                return json.load(f)
        except Exception:
            return 0

    def _save_high_score(self) -> None:
        if self.score > self.high_score:
            self.high_score = self.score
            with open(HIGH_SCORE_FILE, "w") as f:
                json.dump(self.high_score, f)

    def _resolve_shots(self) -> None:
        dead = [s for s in self._pending_shots if not s.alive()]
        for s in dead:
            self.shots_fired += 1
            self._pending_shots.remove(s)


