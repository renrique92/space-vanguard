import pygame
import pytest

from game import Game
from settings import GameState
from sprites.bullet import Bullet
from sprites.enemy import Enemy, EnemyFormation
from settings import (
    GAME_WIDTH, WINDOW_HEIGHT, PLAYER_LIVES, LEVELS,
    SCORE_MULT_START, SCORE_MULT_DECAY, SCORE_MULT_MIN,
    TOTAL_LEVELS, INVULNERABLE_MS,
)


class TestInit:
    def test_initial_state(self, game):
        assert game.state == GameState.PLAYING
        assert game.level == 1
        assert game.player.lives == PLAYER_LIVES
        assert game.running is True
        assert game.score == 0
        assert game.shots_fired == 0
        assert game.shots_hit == 0

    def test_high_score_loaded(self, game):
        assert isinstance(game.high_score, int)

    def test_enemy_formation_created(self, game):
        assert len(game.formation.enemies) > 0

    def test_game_surf_exists(self, game):
        assert game.game_surf.get_width() == GAME_WIDTH
        assert game.game_surf.get_height() == WINDOW_HEIGHT


class TestLoopSmoke:
    def test_update_no_crash(self, game):
        for _ in range(120):
            game._update(16)

    def test_update_and_draw_no_crash(self, game):
        for _ in range(60):
            game._update(16)
            game._draw()

    def test_events_no_crash(self, game):
        game._handle_events()


class TestLevelTransition:
    def test_transition_timer_counts_down(self, game):
        game.transition_timer = 2000
        game.state = GameState.INTRO
        game._update(16)
        assert game.transition_timer == 2000 - 16

    def test_transition_from_intro_to_playing(self, game):
        game.state = GameState.INTRO
        game.transition_timer = 2000
        for _ in range(130):
            game._update(16)
        assert game.state == GameState.PLAYING
        assert game.transition_timer <= 0

    def test_advance_level_increases_level(self, game):
        lvl = game.level
        game._advance_level()
        assert game.level == lvl + 1

    def test_advance_level_resets_elapsed_time(self, game):
        game.elapsed_time = 5000
        game._advance_level()
        assert game.elapsed_time == 0

    def test_advance_level_new_formation(self, game):
        old_formation = game.formation
        game._advance_level()
        assert game.formation is not old_formation

    def test_advance_level_preserves_lives(self, game):
        game.player.lives = 1
        game._advance_level()
        assert game.player.lives == 1


class TestEnemyFormation:
    def test_initial_enemy_count(self, game):
        expected = sum(sum(row) for row in LEVELS[0]["pattern"])
        assert len(game.formation.enemies) == expected

    def test_enemy_update_moves_enemies(self, game):
        pos_before = [e.rect.x for e in game.formation.enemies]
        game.formation.update()
        pos_after = [e.rect.x for e in game.formation.enemies]
        assert pos_after != pos_before

    def test_enemy_reverse_on_boundary(self, game):
        d_before = game.formation.direction
        for e in game.formation.enemies:
            e.rect.x = GAME_WIDTH - 1
        for _ in range(10):
            game.formation.update()
        assert game.formation.direction == -d_before

    def test_try_shoot_returns_none_or_position(self, game):
        result = game.formation.try_shoot()
        if result is not None:
            x, y = result
            assert isinstance(x, (int, float))
            assert isinstance(y, (int, float))

    def test_reached_game_over_returns_bool(self, game):
        assert game.formation.reached_game_over() is False

    def test_all_formation_configs_load(self):
        for idx, config in enumerate(LEVELS):
            f = EnemyFormation(config)
            expected = sum(sum(row) for row in config["pattern"])
            assert len(f.enemies) == expected, f"Level {idx + 1}: expected {expected}, got {len(f.enemies)}"


class TestPlayer:
    def test_take_hit_loses_life(self, game):
        lives_before = game.player.lives
        game.player.take_hit()
        assert game.player.lives == lives_before - 1

    def test_take_hit_makes_invulnerable(self, game):
        game.player.invulnerable = False
        game.player.take_hit()
        assert game.player.invulnerable is True

    def test_invulnerable_blocks_damage_through_update(self, game):
        game.player.invulnerable = True
        game.player.invuln_timer = 1500
        bullet = Bullet(game.player.rect.centerx, game.player.rect.top, 5, is_player=False)
        game.enemy_bullets.add(bullet)
        game._update(16)
        assert game.player.lives == PLAYER_LIVES

    def test_invulnerability_expires_after_delay(self, game):
        game.player.invulnerable = True
        game.player.invuln_timer = 1500
        for _ in range(100):
            game._update(16)
        assert game.player.invulnerable is False

    def test_take_hit_sets_invuln_timer(self, game):
        game.player.take_hit()
        assert game.player.invulnerable is True
        assert game.player.invuln_timer == 1500

    def test_reset_restores_lives(self, game):
        game.player.lives = 1
        game.player.reset()
        assert game.player.lives == PLAYER_LIVES

    def test_reset_keeps_lives_when_flag_false(self, game):
        game.player.lives = 1
        game.player.reset(reset_lives=False)
        assert game.player.lives == 1

    def test_player_reset_position(self, game):
        game.player.rect.x = 0
        game.player.reset()
        assert game.player.rect.centerx == GAME_WIDTH // 2


class TestBullet:
    def test_player_bullet_moves_up(self, game):
        bullet = Bullet(100, 300, -9, is_player=True)
        y_before = bullet.rect.y
        bullet.update()
        assert bullet.rect.y < y_before

    def test_enemy_bullet_moves_down(self, game):
        bullet = Bullet(100, 100, 5, is_player=False)
        y_before = bullet.rect.y
        bullet.update()
        assert bullet.rect.y > y_before

    def test_bullet_killed_off_screen(self, game):
        bullet = Bullet(100, WINDOW_HEIGHT + 50, 5, is_player=False)
        bullet.update()
        assert not bullet.alive()

    def test_player_bullet_killed_off_top(self, game):
        bullet = Bullet(100, -50, -9, is_player=True)
        bullet.update()
        assert not bullet.alive()


class TestCollision:
    def test_bullet_hits_enemy(self, game):
        game.formation.enemies.empty()
        bullet = Bullet(200, 200, -9, is_player=True)
        game.player_bullets.add(bullet)
        game._pending_shots.add(bullet)

        enemy = Enemy(200, 200, (255, 0, 0), 30)
        game.formation.enemies.add(enemy)

        game._update(16)

        assert not enemy.alive()
        assert game.shots_hit == 1

    def test_bullet_hit_adds_score(self, game):
        score_before = game.score
        bullet = Bullet(200, 200, -9, is_player=True)
        game.player_bullets.add(bullet)
        game._pending_shots.add(bullet)
        enemy = Enemy(200, 200, (255, 0, 0), 30)
        game.formation.enemies.add(enemy)
        game._update(16)
        assert game.score > score_before

    def test_enemy_bullet_hits_player(self, game):
        game.player.invulnerable = False
        game.player.rect.center = (200, 200)
        bullet = Bullet(200, 180, 5, is_player=False)
        game.enemy_bullets.add(bullet)
        lives_before = game.player.lives
        game._update(16)
        assert game.player.lives == lives_before - 1


class TestScore:
    def test_multiplier_starts_high(self, game):
        assert game.score_multiplier == pytest.approx(SCORE_MULT_START)

    def test_multiplier_decays(self, game):
        game.elapsed_time = 5000
        expected = max(SCORE_MULT_MIN, SCORE_MULT_START - 5 / SCORE_MULT_DECAY)
        assert game.score_multiplier == pytest.approx(expected)

    def test_multiplier_floor(self, game):
        game.elapsed_time = 999999
        assert game.score_multiplier == pytest.approx(SCORE_MULT_MIN)

    def test_accuracy_initially_100(self, game):
        assert game.accuracy == pytest.approx(100.0)

    def test_accuracy_after_miss(self, game):
        game.shots_fired = 1
        game.shots_hit = 0
        assert game.accuracy == pytest.approx(0.0)

    def test_accuracy_after_hit(self, game):
        game.shots_fired = 2
        game.shots_hit = 1
        assert game.accuracy == pytest.approx(50.0)

    def test_resolve_shots_counts_bullets(self, game):
        bullet = Bullet(100, 100, -9, is_player=True)
        game._pending_shots.add(bullet)
        bullet.kill()
        game._resolve_shots()
        assert game.shots_fired == 1

    def test_resolve_shots_ignores_alive_bullets(self, game):
        bullet = Bullet(100, 100, -9, is_player=True)
        game.player_bullets.add(bullet)
        game._pending_shots.add(bullet)
        game._resolve_shots()
        assert game.shots_fired == 0


class TestStateMachine:
    def test_game_over_on_zero_lives(self, game):
        game.player.invulnerable = False
        game.player.lives = 1

        bullet = Bullet(game.player.rect.centerx, game.player.rect.top, 5, is_player=False)
        game.enemy_bullets.add(bullet)

        game._update(16)

        assert game.state == GameState.GAME_OVER

    def test_reset_clears_state(self, game):
        game.state = GameState.GAME_OVER
        game._reset()
        assert game.state == GameState.INTRO
        assert game.score == 0
        assert game.level == 1

    def test_win_after_final_level(self, game):
        game.level = TOTAL_LEVELS
        game.formation.enemies.empty()
        game._update(16)
        assert game.state == GameState.WIN

    def test_level_up_on_clear(self, game):
        game.level = 1
        game.formation.enemies.empty()
        game._update(16)
        assert game.transition_timer > 0

    def test_resolve_shots_empty_no_error(self, game):
        game._pending_shots.clear()
        game._resolve_shots()
        assert game.shots_fired == 0

    def test_pause_toggle(self, game):
        assert game.state == GameState.PLAYING
        game._prev_state = game.state
        game.state = GameState.PAUSED
        assert game.state == GameState.PAUSED
        game.state = game._prev_state
        assert game.state == GameState.PLAYING


class TestHighScore:
    def test_save_updates_high_score(self, game, tmp_path):
        game.score = 999
        game.high_score = 100
        game._save_high_score()
        assert game.high_score == 999

    def test_save_does_not_lower(self, game):
        game.score = 50
        game.high_score = 100
        game._save_high_score()
        assert game.high_score == 100

    def test_persistence(self, game):
        game.score = 500
        game._save_high_score()
        hs = game._load_high_score()
        assert hs == 500


class TestParticles:
    def test_spawn_explosion_creates_particles(self, game):
        from effects import spawn_explosion
        group = spawn_explosion(100, 100, (255, 0, 0))
        assert len(group) == 10

    def test_particles_age_and_die(self, game):
        from effects import spawn_explosion
        group = spawn_explosion(100, 100, (255, 0, 0))
        for _ in range(100):
            group.update(16)
        assert len(group) == 0

    def test_muzzle_flash_fades(self, game):
        from effects import MuzzleFlash
        mf = MuzzleFlash(100, 100)
        game.flash_fx.add(mf)
        assert mf.alive()
        for _ in range(10):
            mf.update(16)
        assert not mf.alive()
