import pygame

from classes import Difficulty, GameState
from settings import DIFFICULTY_ORDER, DIFFICULTY_PRESETS
from collision import (
    check_boss_collisions,
    check_bunker_collisions,
    check_enemy_collisions,
    check_kamikaze_collisions,
    check_minion_collisions,
    check_player_hit,
    check_powerup_collection,
    check_ufo_collision,
)
from effects import MuzzleFlash, spawn_explosion, ScreenShake
from shooting import handle_enemy_shooting
from level_generator import generate_level
from levels import create_bunkers, handle_transition_end
from settings import (
    BULLET_W, ENEMY_BULLET_SPEED, FPS, GAME_WIDTH,
    MAX_LIVES, MAX_PLAYER_BULLETS, PLAYER_BULLET_H,
    PLAYER_BULLET_SPEED, POWERUP_COOLDOWN,
    SCORE_MULT_START, SCORE_MULT_DECAY,
    SCORE_MULT_MIN, SHOT_DELAY, SLOWMO_RATE,
    SPECIAL_ACTIVATE_KEY,
    UFO_SPAWN_MIN, UFO_SPAWN_MAX, WINDOW_HEIGHT, WINDOW_WIDTH,
)
from sounds import SoundManager
from sprites.bullet import Bullet
from sprites.enemy import EnemyFormation
from sprites.player import Player, POWERUP_FIELD_MAP
from ui.info_panel import InfoPanel
from renderer import Renderer, SceneState
from score import ScoreKeeper
from starfield import StarField
from powerup_manager import PowerUpManager
from ufo_manager import UfoManager
from boss_manager import BossManager


class Game:
    def __init__(self) -> None:
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Space Vanguard")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.TITLE
        self._prev_state = GameState.TITLE

        self.starfield = StarField()
        self.score_keeper = ScoreKeeper()
        self.sound = SoundManager()
        self.screen_shake = ScreenShake()

        self.level = 1
        self.transition_timer = 2000
        self.difficulty = Difficulty.NORMAL

        self.player = Player()
        self.player.lives = DIFFICULTY_PRESETS[self.difficulty]["lives"]
        diff = DIFFICULTY_PRESETS[self.difficulty]
        self.formation = EnemyFormation(generate_level(1), diff)
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.flash_fx = pygame.sprite.Group()
        self.info_panel = InfoPanel()
        self.auto_step_timer = 0
        self._shot_timer = 0
        self._last_dt = 0
        self._prev_player_bullets = set()

        self.kamikazes = pygame.sprite.Group()
        self.minions = pygame.sprite.Group()

        self.powerup_manager = PowerUpManager()
        self.ufo_manager = UfoManager()
        self.boss_manager = BossManager()

        self.bunkers = create_bunkers()

        self.game_surf = pygame.Surface((GAME_WIDTH, WINDOW_HEIGHT))
        self.renderer = Renderer(
            self.screen, self.game_surf, self.screen_shake,
            self.info_panel, self.starfield,
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
                    self._reset_game()
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
                elif event.key == SPECIAL_ACTIVATE_KEY and self.state == GameState.PLAYING and self.transition_timer <= 0:
                    if self.player.special_active:
                        self.player.special_active = False
                    elif self.player.special_charge >= 1.0:
                        self.player.special_active = True
                        self.player.special_used = True
                        self.player.special_tick_timer = 0
                        self.player.special_charge = 1.0
                        self.sound.play("special")

        if self.state == GameState.PLAYING and self.transition_timer <= 0:
            if not self.player.special_active:
                keys = pygame.key.get_pressed()
                self.player.handle_input(keys)
                shot_delay = 80 if self.player.effects.rapid > 0 else SHOT_DELAY
                if (
                    keys[pygame.K_SPACE]
                    and len(self.player_bullets) < MAX_PLAYER_BULLETS
                    and self._shot_timer <= 0
                ):
                    if self.player.effects.spread > 0:
                        bullets = self._create_spread()
                    else:
                        bullets = self._create_bullet()
                    if bullets:
                        self._shot_timer = shot_delay
                        for b in bullets:
                            self.player_bullets.add(b)
                        self.sound.play("shoot")
                        self.flash_fx.add(
                            MuzzleFlash(self.player.rect.centerx, self.player.rect.top)
                        )

    def _get_multiplier(self) -> float:
        mult = self.score_keeper.multiplier
        if self.player.effects.score > 0:
            mult = 2.0
        return mult

    def _update(self, dt: int) -> None:
        self._last_dt = dt
        self.score_keeper.elapsed_time += dt
        self.starfield.update(dt)

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
        self.player.add_special_charge(dt)
        self.player.drain_special_charge(dt)

        speed_mult = SLOWMO_RATE if self.player.effects.slowmo > 0 else 1.0
        self.formation.update(dt, speed_mult)
        self.auto_step_timer += int(dt * speed_mult)

        if self.auto_step_timer >= self.formation._diff["auto_step_ms"]:
            self.formation.auto_step_down()
            self.auto_step_timer = 0

        handle_enemy_shooting(
            self.formation, self.player, self.level,
            self.enemy_bullets, self.sound, self._last_dt,
        )

        self._prev_player_bullets = set(self.player_bullets.sprites())
        self.player_bullets.update()
        self.enemy_bullets.update()
        self.kamikazes.update(dt)
        self.minions.update(dt)
        self.particles.update(dt)
        self.flash_fx.update(dt)
        self._update_score_popups(dt)

        new_kamikazes = self.formation.detach_kamikazes(self.player)
        for k in new_kamikazes:
            self.kamikazes.add(k)
            self.flash_fx.add(MuzzleFlash(k.rect.centerx, k.rect.top))

        for kam in list(self.kamikazes):
            if kam.rect.top > WINDOW_HEIGHT + 50:
                self.particles.add(
                    spawn_explosion(kam.rect.centerx, WINDOW_HEIGHT, (200, 100, 50), count=8)
                )
                self.sound.play("explosion")
                kam.kill()

        self.powerup_manager.update(dt)
        self.ufo_manager.update(dt)
        self.boss_manager.update(dt, self.player.rect.centerx, self.enemy_bullets, self.minions)

        check_bunker_collisions(self.player_bullets, self.enemy_bullets, self.bunkers)

        mult = self._get_multiplier()

        events = []

        e_events, self.score_keeper.streak = check_enemy_collisions(
            self.player_bullets, self.formation.enemies,
            self.player.effects.pierce <= 0, mult,
            self.score_keeper.streak,
        )
        events.extend(e_events)

        events.extend(check_boss_collisions(self.player_bullets, self.boss_manager.boss))

        k_events, self.score_keeper.streak = check_kamikaze_collisions(
            self.player_bullets, self.kamikazes, mult, self.score_keeper.streak,
        )
        events.extend(k_events)

        events.extend(check_minion_collisions(self.player_bullets, self.minions))

        pu_event = check_powerup_collection(self.player, self.powerup_manager.powerups)
        if pu_event:
            events.append(pu_event)

        ufo_event = check_ufo_collision(self.player_bullets, self.ufo_manager.ufo)
        if ufo_event:
            self.ufo_manager.despawn()
            events.append(ufo_event)

        self._shot_timer = max(0, self._shot_timer - dt)

        hit_event = check_player_hit(self.player, self.enemy_bullets, self.kamikazes, self.minions)

        self._check_game_state()

        beam_events, self.score_keeper.streak, beam_ufo_hit = self._check_special_beam(
            mult, dt,
        )
        events.extend(beam_events)
        if beam_ufo_hit:
            self.ufo_manager.despawn()

        for event in events:
            if event.points:
                self.score_keeper.score += event.points
                self.score_keeper.add_popup(event.points, event.x, event.y)
            if event.sound:
                self.sound.play(event.sound)
            if event.explosion_count:
                self.particles.add(
                    spawn_explosion(event.x, event.y, event.color, event.explosion_count)
                )
            if event.powerup_name:
                self.powerup_manager.show_message(event.powerup_name)

        if hit_event:
            self.score_keeper.streak = 0
            self.sound.play("player_hit")
            self.screen_shake.trigger(8, 200)
            self.particles.add(
                spawn_explosion(hit_event.x, hit_event.y, hit_event.color, hit_event.explosion_count)
            )
            if self.player.lives <= 0:
                self.state = GameState.GAME_OVER
                self.sound.stop_bgm()
                self.score_keeper.save()
                self.sound.play("game_over")

        for b in self._prev_player_bullets:
            if not b.alive() and not b.has_hit:
                self.score_keeper.streak = 0

    def _check_special_beam(self, mult: float, dt: int
                            ) -> tuple[list, int, bool]:
        events = []
        if not self.player.special_active:
            return events, self.score_keeper.streak, False
        if self.transition_timer > 0:
            return events, self.score_keeper.streak, False

        self.player.special_tick_timer += dt
        if self.player.special_tick_timer < 100:
            return events, self.score_keeper.streak, False
        self.player.special_tick_timer = 0

        from settings import SPECIAL_BEAM_WIDTH
        cx = self.player.rect.centerx
        beam_rect = pygame.Rect(
            cx - SPECIAL_BEAM_WIDTH // 2, 0,
            SPECIAL_BEAM_WIDTH, self.player.rect.top,
        )

        ufo_hit = False
        streak = self.score_keeper.streak

        for enemy in list(self.formation.enemies):
            if enemy.rect.colliderect(beam_rect):
                streak += 1
                streak_bonus = min(streak, 99)
                pts = int(enemy.points * mult) + streak_bonus
                color = enemy.image.get_at((0, 0))[:3]
                events.append(self._beam_event(pts, enemy.rect.centerx, enemy.rect.centery, color))
                self.sound.play("explosion")
                enemy.kill()

        for bullet in list(self.enemy_bullets):
            if bullet.rect.colliderect(beam_rect):
                bullet.kill()

        if self.ufo_manager.ufo and self.ufo_manager.ufo.rect.colliderect(beam_rect):
            pts = self.ufo_manager.ufo.points
            events.append(self._beam_event(pts, self.ufo_manager.ufo.rect.centerx,
                                           self.ufo_manager.ufo.rect.centery, (180, 100, 200)))
            self.sound.play("explosion")
            ufo_hit = True

        for kam in list(self.kamikazes):
            if kam.rect.colliderect(beam_rect):
                streak += 1
                pts = int(kam.points * mult) + min(streak, 99)
                events.append(self._beam_event(pts, kam.rect.centerx, kam.rect.centery, (200, 100, 50)))
                kam.kill()

        for m in list(self.minions):
            if m.rect.colliderect(beam_rect):
                events.append(self._beam_event(20, m.rect.centerx, m.rect.centery, (255, 150, 50)))
                m.kill()

        if self.boss_manager.boss and self.boss_manager.boss.rect.colliderect(beam_rect):
            self.boss_manager.boss.take_hit()
            events.append(self._beam_event(50, self.boss_manager.boss.rect.centerx,
                                           self.boss_manager.boss.rect.centery, (200, 100, 100)))
            self.sound.play("explosion")

        return events, streak, ufo_hit

    def _beam_event(self, points: int, x: float, y: float, color: tuple):
        from events import CollisionEvent
        return CollisionEvent(
            points=points, x=x, y=y, color=color,
            explosion_count=6,
        )

    def _update_score_popups(self, dt: int) -> None:
        for popup in self.score_keeper.popups:
            popup["timer"] -= dt
            popup["y"] -= 0.5 * (dt / 16)
        self.score_keeper.popups = [p for p in self.score_keeper.popups if p["timer"] > 0]

    def _check_game_state(self) -> None:
        from settings import BOSS_INTERVAL

        if self.formation.reached_game_over():
            self.state = GameState.GAME_OVER
            self.sound.stop_bgm()
            self.score_keeper.save()
            self.sound.play("game_over")
            return

        if len(self.formation.enemies) == 0 and self.boss_manager.boss is None:
            if self.level % BOSS_INTERVAL == 0:
                self.boss_manager.spawn()
            else:
                self.transition_timer = 2000
                if self.player.lives < MAX_LIVES:
                    self.player.lives += 1
                self.sound.play("level_up")
                self.player_bullets.empty()
                self.enemy_bullets.empty()

        if self.boss_manager.boss and self.boss_manager.boss.hp <= 0:
            self.transition_timer = 2000
            if self.player.lives < MAX_LIVES:
                self.player.lives += 1
            self.sound.play("level_up")
            self.player_bullets.empty()
            self.enemy_bullets.empty()
            self.boss_manager.reset()

    def _advance_level(self) -> None:
        self.level += 1
        self.transition_timer = 0
        self.score_keeper.elapsed_time = 0
        self.ufo_manager.reset()
        self.boss_manager.reset()
        self.bunkers = create_bunkers()
        self.powerup_manager.reset()
        diff = DIFFICULTY_PRESETS[self.difficulty]
        self.formation = EnemyFormation(generate_level(self.level), diff)
        self.kamikazes.empty()
        self.minions.empty()
        self.player.reset(reset_lives=False)
        if self.player.special_charge >= 1.0 and not self.player.special_used:
            self.player.special_charge = 1.0
        else:
            self.player.special_charge = 0.0
        self.player.special_used = False
        self.player.special_active = False
        self.boss_manager.reset()
        self.auto_step_timer = 0

    def _reset_game(self) -> None:
        self.sound.stop_bgm()
        self.score_keeper = ScoreKeeper()
        self.level = 1
        self.state = GameState.INTRO
        self._prev_state = GameState.INTRO
        self.transition_timer = 2000
        self.auto_step_timer = 0
        self._shot_timer = 0
        self.player_bullets.empty()
        self.enemy_bullets.empty()
        self.particles.empty()
        self.flash_fx.empty()
        self.kamikazes.empty()
        self.minions.empty()
        self.powerup_manager.reset()
        self.ufo_manager.reset()
        self.boss_manager.reset()
        self.bunkers = create_bunkers()
        diff = DIFFICULTY_PRESETS[self.difficulty]
        self.player.reset()
        self.player.lives = diff["lives"]
        self.formation = EnemyFormation(generate_level(1), diff)

    def _build_scene(self) -> SceneState:
        active_pu_type = None
        active_pu_remaining = 0
        for pt, field_name in POWERUP_FIELD_MAP.items():
            timer = getattr(self.player.effects, field_name, 0)
            if timer > 0:
                active_pu_type = pt
                active_pu_remaining = timer
                break

        return SceneState(
            state=self.state,
            level=self.level,
            transition_timer=self.transition_timer,
            player=self.player,
            formation=self.formation,
            player_bullets=self.player_bullets,
            enemy_bullets=self.enemy_bullets,
            particles=self.particles,
            flash_fx=self.flash_fx,
            ufo=self.ufo_manager.ufo,
            bunkers=self.bunkers,
            powerups=self.powerup_manager.powerups,
            score=self.score_keeper.score,
            high_score=self.score_keeper.high_score,
            lives=self.player.lives,
            score_multiplier=self._get_multiplier(),
            streak=self.score_keeper.streak,
            popups=self.score_keeper.popups,
            boss=self.boss_manager.boss,
            kamikazes=self.kamikazes,
            minions=self.minions,
            difficulty=self.difficulty,
            powerup_msg=self.powerup_manager.msg,
            active_pu_type=active_pu_type,
            active_pu_remaining=active_pu_remaining,
            special_charge=self.player.special_charge,
            special_active=self.player.special_active,
        )

    def _draw(self) -> None:
        self.renderer.draw(self._build_scene())

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
