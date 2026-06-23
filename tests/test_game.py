import pygame
import pytest

from game import Game
from levels import advance_level, reset_game
from classes import Difficulty, EnemyType, GameState, PowerUpType
from sprites.bullet import Bullet
from sprites.boss import Boss, BossMinion
from settings import ENEMY_KAMIKAZE_BASE_SPEED
from sprites.enemy import Enemy, EnemyFormation, KamikazeEnemy
from level_generator import generate_level
from settings import (
    BUNKER_COUNT, ENEMY_ANIM_INTERVAL, GAME_WIDTH,
    WINDOW_HEIGHT, PLAYER_LIVES, SCORE_MULT_START,
    SCORE_MULT_DECAY, SCORE_MULT_MIN, BOSS_INTERVAL,
    INVULNERABLE_MS, UFO_W, UFO_SPEED, UFO_Y,
    UFO_SPAWN_MIN, UFO_SPAWN_MAX,
    PLAYER_BULLET_SPEED, PLAYER_BULLET_H, BULLET_W,
    POWERUP_CHANCE, POWERUP_COOLDOWN, POWERUP_SPEED,
    POWERUP_DURATIONS, POWERUP_W, POWERUP_H,
    GAME_OVER_LINE, MAX_PLAYER_BULLETS, DIFFICULTY_PRESETS,
    ENEMY_BULLET_SPEED, SLOWMO_RATE,
)
from sprites.powerup import PowerUp


class TestInit:
    def test_initial_state(self, game):
        assert game.state == GameState.PLAYING
        assert game.level == 1
        assert game.player.lives == PLAYER_LIVES
        assert game.running is True
        assert game.score_keeper.score == 0

    def test_high_score_loaded(self, game):
        assert isinstance(game.score_keeper.high_score, int)

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
        advance_level(game)
        assert game.level == lvl + 1

    def test_advance_level_resets_elapsed_time(self, game):
        game.score_keeper.elapsed_time = 5000
        advance_level(game)
        assert game.score_keeper.elapsed_time == 0

    def test_advance_level_new_formation(self, game):
        old_formation = game.formation
        advance_level(game)
        assert game.formation is not old_formation

    def test_advance_level_preserves_lives(self, game):
        game.player.lives = 1
        advance_level(game)
        assert game.player.lives == 1


class TestEnemyFormation:
    def test_initial_enemy_count(self, game):
        assert len(game.formation.enemies) > 0

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

    def test_generated_levels_load(self):
        for n in [1, 2, 3, 5, 6, 10, 11]:
            cfg = generate_level(n)
            f = EnemyFormation(cfg)
            expected = sum(sum(row) for row in cfg["pattern"])
            assert len(f.enemies) == expected, f"Level {n}: expected {expected}, got {len(f.enemies)}"
            assert len(cfg["colors"]) == len(cfg["pattern"])
            assert len(cfg["points"]) == len(cfg["pattern"])

    def test_boss_level_has_smaller_formation(self):
        cfg = generate_level(5)
        rows = len(cfg["pattern"])
        assert rows <= 3

    def test_animation_frames_alternate(self, game):
        before = [e.image for e in game.formation.enemies]
        game._update(ENEMY_ANIM_INTERVAL)
        after = [e.image for e in game.formation.enemies]
        changed = sum(
            1 for b, a in zip(before, after) if b is not a
        )
        assert changed > 0

    def test_animation_does_not_switch_too_early(self, game):
        before = [e.image for e in game.formation.enemies]
        game._update(ENEMY_ANIM_INTERVAL - 1)
        after = [e.image for e in game.formation.enemies]
        assert all(b is a for b, a in zip(before, after))


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

        enemy = Enemy(200, 200, (255, 0, 0), 30)
        game.formation.enemies.add(enemy)

        game._update(16)

        assert not enemy.alive()

    def test_bullet_hit_adds_score(self, game):
        score_before = game.score_keeper.score
        bullet = Bullet(200, 200, -9, is_player=True)
        game.player_bullets.add(bullet)
        enemy = Enemy(200, 200, (255, 0, 0), 30)
        game.formation.enemies.add(enemy)
        game._update(16)
        assert game.score_keeper.score > score_before

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
        assert game._get_multiplier() == pytest.approx(SCORE_MULT_START)

    def test_multiplier_decays(self, game):
        game.score_keeper.elapsed_time = 5000
        expected = max(SCORE_MULT_MIN, SCORE_MULT_START - 5 / SCORE_MULT_DECAY)
        assert game._get_multiplier() == pytest.approx(expected)

    def test_multiplier_floor(self, game):
        game.score_keeper.elapsed_time = 999999
        assert game._get_multiplier() == pytest.approx(SCORE_MULT_MIN)

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
        reset_game(game)
        assert game.state == GameState.INTRO
        assert game.score_keeper.score == 0
        assert game.level == 1

    def test_boss_at_interval_spawns_on_clear(self, game):
        game.level = BOSS_INTERVAL
        game.formation.enemies.empty()
        game._update(16)
        assert game.boss_manager.boss is not None
        assert game.state == GameState.PLAYING

    def test_boss_defeated_transitions(self, game):
        game.level = BOSS_INTERVAL
        game.formation.enemies.empty()
        game._update(16)
        assert game.boss_manager.boss is not None
        for _ in range(game.boss_manager.boss.max_hp):
            game.boss_manager.boss.take_hit()
        assert game.boss_manager.boss.hp <= 0
        game._update(16)
        assert game.transition_timer > 0
        assert game.state == GameState.PLAYING
        assert game.boss_manager.boss is None

    def test_level_up_on_clear(self, game):
        game.level = 1
        game.formation.enemies.empty()
        game._update(16)
        assert game.transition_timer > 0

    def test_pause_toggle(self, game):
        assert game.state == GameState.PLAYING
        game._prev_state = game.state
        game.state = GameState.PAUSED
        assert game.state == GameState.PAUSED
        game.state = game._prev_state
        assert game.state == GameState.PLAYING


class TestHighScore:
    def test_save_updates_high_score(self, game, tmp_path):
        game.score_keeper.score = 999
        game.score_keeper.high_score = 100
        game.score_keeper.save()
        assert game.score_keeper.high_score == 999

    def test_save_does_not_lower(self, game):
        game.score_keeper.score = 50
        game.score_keeper.high_score = 100
        game.score_keeper.save()
        assert game.score_keeper.high_score == 100

    def test_persistence(self, game):
        game.score_keeper.score = 500
        game.score_keeper.save()
        hs = game.score_keeper._load()
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


class TestUFO:
    def test_ufo_starts_none(self, game):
        assert game.ufo_manager.ufo is None
        assert game.ufo_manager.spawn_timer == 0

    def test_ufo_spawns_after_delay(self, game):
        game.ufo_manager.spawn_delay = 100
        game.ufo_manager.spawn_timer = 100
        game.ufo_manager.update(16)
        assert game.ufo_manager.ufo is not None

    def test_ufo_moves_across_screen(self, game):
        from sprites.ufo import UFO
        u = UFO()
        x_before = u.rect.x
        u.update(16)
        assert u.rect.x != x_before

    def test_ufo_offscreen_detected(self, game):
        from sprites.ufo import UFO
        u = UFO()
        u.rect.x = GAME_WIDTH + 10
        u.update(16)
        assert u.rect.left > GAME_WIDTH
        u.rect.x = -UFO_W - 10
        u.update(16)
        assert u.rect.right < 0

    def test_ufo_hit_adds_score(self, game):
        from sprites.ufo import UFO
        from sprites.bullet import Bullet
        from collision import check_ufo_collision
        u = UFO()
        game.ufo_manager.ufo = u
        score_before = game.score_keeper.score
        bullet = Bullet(u.rect.centerx, u.rect.top, -9, is_player=True)
        game.player_bullets.add(bullet)
        ufo_event = check_ufo_collision(game.player_bullets, game.ufo_manager.ufo)
        if ufo_event:
            game.score_keeper.score += ufo_event.points
            game.score_keeper.add_popup(ufo_event.points, ufo_event.x, ufo_event.y)
            game.ufo_manager.despawn()
        assert game.score_keeper.score > score_before
        assert game.ufo_manager.ufo is None

    def test_ufo_reset_on_level_advance(self, game):
        from sprites.ufo import UFO
        game.ufo_manager.ufo = UFO()
        advance_level(game)
        assert game.ufo_manager.ufo is None
        assert game.ufo_manager.spawn_timer == 0

    def test_ufo_reset_on_game_reset(self, game):
        from sprites.ufo import UFO
        game.ufo_manager.ufo = UFO()
        game.state = GameState.GAME_OVER
        reset_game(game)
        assert game.ufo_manager.ufo is None
        assert game.ufo_manager.spawn_timer == 0

    def test_ufo_spawns_in_random_direction(self, game):
        from sprites.ufo import UFO
        dirs = set()
        for _ in range(50):
            u = UFO()
            dirs.add(u.direction)
        assert -1 in dirs
        assert 1 in dirs


class TestBunker:
    def test_bunkers_created(self, game):
        assert len(game.bunkers) == BUNKER_COUNT

    def test_bunker_has_bricks(self, game):
        for b in game.bunkers:
            assert len(b.bricks) > 0

    def test_bunker_bullet_destroyed(self, game):
        from sprites.bullet import Bullet
        bunker = game.bunkers[0]
        brick_count_before = len(bunker.bricks)
        target = list(bunker.bricks)[0]
        assert target.hp == 2
        bullet1 = Bullet(target.rect.centerx, target.rect.centery, -9, is_player=True)
        game.player_bullets.add(bullet1)
        game._update(16)
        assert len(bunker.bricks) == brick_count_before
        assert not bullet1.alive()
        assert target.hp == 1
        bullet2 = Bullet(target.rect.centerx, target.rect.centery, -9, is_player=True)
        game.player_bullets.add(bullet2)
        game._update(16)
        assert len(bunker.bricks) == brick_count_before - 1
        assert not bullet2.alive()

    def test_bunker_blocks_enemy_bullet(self, game):
        from sprites.bullet import Bullet
        bunker = game.bunkers[0]
        target = list(bunker.bricks)[0]
        bullet = Bullet(target.rect.centerx, target.rect.centery, 5, is_player=False)
        game.enemy_bullets.add(bullet)
        game.player.invulnerable = False
        game._update(16)
        assert not bullet.alive()

    def test_bunker_reset_on_level_advance(self, game):
        old = game.bunkers
        advance_level(game)
        assert game.bunkers is not old
        assert len(game.bunkers) == BUNKER_COUNT

    def test_bunker_reset_on_game_reset(self, game):
        game.bunkers = []
        reset_game(game)
        assert len(game.bunkers) == BUNKER_COUNT

    def test_bunker_bricks_positioned_correctly(self, game):
        for bunker in game.bunkers:
            for brick in bunker.bricks:
                assert brick.rect.y > 0
                assert brick.rect.x < GAME_WIDTH


class TestBGM:
    def test_play_bgm_does_not_crash(self, game):
        game.sound.play_bgm()
        game.sound.stop_bgm()

    def test_bgm_stops_on_game_over(self, game):
        game.sound.play_bgm()
        game.player.invulnerable = False
        game.player.lives = 1
        bullet = __import__('sprites.bullet', fromlist=['Bullet']).Bullet(
            game.player.rect.centerx, game.player.rect.top, 5, is_player=False
        )
        game.enemy_bullets.add(bullet)
        game._update(16)
        assert game.state == GameState.GAME_OVER

    def test_bgm_stops_on_reset(self, game):
        game.sound.play_bgm()
        reset_game(game)
        # no crash

    def test_bgm_starts_on_intro_end(self, game):
        g = Game()
        assert g.state == GameState.TITLE
        g.state = GameState.INTRO
        g.sound.play_bgm()
        g.sound.stop_bgm()


class TestPowerUp:
    def test_powerup_starts_empty(self, game):
        assert len(game.powerup_manager.powerups) == 0

    def test_powerup_falls_and_dies_offscreen(self, game):
        pu = PowerUp(100, WINDOW_HEIGHT + 10, PowerUpType.SPEED)
        pu.update(16)
        assert not pu.alive()

    def test_powerup_spawns_on_enemy_kill(self, game):
        from sprites.enemy import Enemy
        game.formation.enemies.empty()
        enemy = Enemy(200, 210, (255, 0, 0), 30)
        game.formation.enemies.add(enemy)
        bullet = __import__('sprites.bullet', fromlist=['Bullet']).Bullet(
            200, 220, -PLAYER_BULLET_SPEED, is_player=True
        )
        game.player_bullets.add(bullet)
        game._update(16)
        assert len(game.formation.enemies) == 0

    def test_powerup_collect_activates_spread(self, game):
        pu = PowerUp(200, 200, PowerUpType.SPREAD)
        game.powerup_manager.powerups.add(pu)
        game.player.rect.center = (200, 200)
        game._update(16)
        assert game.player.effects.spread > 0

    def test_powerup_collect_activates_shield(self, game):
        pu = PowerUp(200, 200, PowerUpType.SHIELD)
        game.powerup_manager.powerups.add(pu)
        game.player.rect.center = (200, 200)
        game._update(16)
        assert game.player.effects.shield > 0

    def test_powerup_collect_activates_speed(self, game):
        pu = PowerUp(200, 200, PowerUpType.SPEED)
        game.powerup_manager.powerups.add(pu)
        game.player.rect.center = (200, 200)
        game._update(16)
        assert game.player.effects.speed > 0
        game._update(16)
        assert game.player.speed == 10

    def test_spread_creates_multiple_bullets(self, game):
        bullets = game._create_spread()
        assert len(bullets) == 3
        assert bullets[0].vx == -2
        assert bullets[1].vx == 0
        assert bullets[2].vx == 2

    def test_spread_returns_empty_when_no_room(self, game):
        for _ in range(3):
            b = __import__('sprites.bullet', fromlist=['Bullet']).Bullet(
                100, 100, -9, is_player=True
            )
            game.player_bullets.add(b)
        bullets = game._create_spread()
        assert len(bullets) == 0

    def test_powerup_cleared_on_reset(self, game):
        game.powerup_manager.powerups.add(PowerUp(200, 200, PowerUpType.SPEED))
        reset_game(game)
        assert len(game.powerup_manager.powerups) == 0

    def test_powerup_cleared_on_advance_level(self, game):
        game.powerup_manager.powerups.add(PowerUp(200, 200, PowerUpType.SPEED))
        advance_level(game)
        assert len(game.powerup_manager.powerups) == 0

    def test_shield_absorbs_one_hit(self, game):
        game.player.effects.shield = 8000
        lives_before = game.player.lives
        game.player.take_hit()
        assert game.player.lives == lives_before
        assert game.player.effects.shield == 0

    def test_powerup_draw_no_crash(self, game):
        pu = PowerUp(200, 200, PowerUpType.SPREAD)
        game.powerup_manager.powerups.add(pu)
        game._draw()

    def test_powerup_timers_expire(self, game):
        game.player.effects.spread = 100
        game.player.effects.shield = 100
        game.player.effects.speed = 100
        for _ in range(10):
            game._update(16)
        assert game.player.effects.spread <= 0
        assert game.player.effects.shield <= 0
        assert game.player.effects.speed <= 0

    def test_powerup_replaces_active(self, game):
        pu1 = PowerUp(200, 200, PowerUpType.SHIELD)
        pu2 = PowerUp(200, 200, PowerUpType.RAPID)
        game.powerup_manager.powerups.add(pu1)
        game.player.rect.center = (200, 200)
        game._update(16)
        assert game.player.effects.shield > 0
        assert game.player.effects.rapid == 0
        game.powerup_manager.powerups.add(pu2)
        game._update(16)
        assert game.player.effects.shield == 0
        assert game.player.effects.rapid > 0

    def test_powerup_msg_shown(self, game):
        game.powerup_manager.msg = ""
        game.powerup_manager.msg_timer = 0
        pu = PowerUp(200, 200, PowerUpType.SPREAD)
        game.powerup_manager.powerups.add(pu)
        game.player.rect.center = (200, 200)
        game._update(16)
        assert game.powerup_manager.msg == "Spread"
        assert game.powerup_manager.msg_timer > 0

    def test_powerup_msg_expires(self, game):
        game.powerup_manager.msg = "Test"
        game.powerup_manager.msg_timer = 100
        game._update(200)
        assert game.powerup_manager.msg == ""

    def test_ship_color_changes_on_powerup(self, game):
        from sprites.player import POWERUP_SHIP_COLORS
        pu = PowerUp(200, 200, PowerUpType.SPREAD)
        game.powerup_manager.powerups.add(pu)
        game.player.rect.center = (200, 200)
        game._update(16)
        color = game.player.image.get_at((game.player.rect.width // 2, 0))[:3]
        assert color == POWERUP_SHIP_COLORS[PowerUpType.SPREAD][0]

    def test_ship_restores_default_when_powerup_expires(self, game):
        game.player.effects.spread = 50
        game._update(16)
        for _ in range(5):
            game._update(16)
        color = game.player.image.get_at((game.player.rect.width // 2, 0))[:3]
        from settings import GREEN
        assert color == GREEN

    def test_powerup_spawn_cooldown_blocks(self, game):
        game.powerup_manager.spawn_cooldown = 0
        assert game.powerup_manager.spawn_cooldown < POWERUP_COOLDOWN

    def test_powerup_spawn_cooldown_allows_after_wait(self, game):
        game.powerup_manager.spawn_cooldown = POWERUP_COOLDOWN
        assert game.powerup_manager.spawn_cooldown >= POWERUP_COOLDOWN

    def test_rapid_fire_custom_shot_delay(self, game):
        game.player.effects.rapid = 1000
        assert game._shot_timer == 0
        shot_delay = 80
        game._shot_timer = shot_delay
        assert game._shot_timer > 0
        assert game.player.effects.rapid > 0

    def test_score_powerup_overrides_multiplier(self, game):
        game.player.effects.score = 1000
        assert game._get_multiplier() == 2.0

    def test_score_multiplier_normal_when_not_active(self, game):
        game.player.effects.score = 0
        game.score_keeper.elapsed_time = 0
        from settings import SCORE_MULT_START
        assert game._get_multiplier() == SCORE_MULT_START

    def test_slowmo_slows_enemies(self, game):
        from settings import SLOWMO_RATE
        enemy = list(game.formation.enemies)[0]
        x0 = enemy.rect.x
        for _ in range(10):
            game.formation.update(16, SLOWMO_RATE)
        dx = abs(enemy.rect.x - x0)
        assert 0 < dx < 10 * 2  # slowmo moves but less than 10 frames full speed

    def test_pierce_bullet_survives_enemy_collision(self, game):
        from sprites.enemy import Enemy
        game.formation.enemies.empty()
        enemy1 = Enemy(200, 210, (255, 0, 0), 30)
        enemy2 = Enemy(300, 210, (255, 0, 0), 30)
        game.formation.enemies.add(enemy1, enemy2)
        bullet = __import__('sprites.bullet', fromlist=['Bullet']).Bullet(
            200, 220, -PLAYER_BULLET_SPEED, is_player=True
        )
        game.player_bullets.add(bullet)
        game.player.effects.pierce = 1000
        game._update(16)
        assert bullet.alive()
        assert not enemy1.alive()
        assert enemy2.alive()

    def test_pierce_bullet_dies_normally_without_powerup(self, game):
        from sprites.enemy import Enemy
        game.formation.enemies.empty()
        enemy = Enemy(200, 210, (255, 0, 0), 30)
        game.formation.enemies.add(enemy)
        bullet = __import__('sprites.bullet', fromlist=['Bullet']).Bullet(
            200, 220, -PLAYER_BULLET_SPEED, is_player=True
        )
        game.player_bullets.add(bullet)
        game.player.effects.pierce = 0
        game._update(16)
        assert not bullet.alive()
        assert len(game.formation.enemies) == 0

    def test_activate_clears_previous(self, game):
        game.player.activate_powerup(PowerUpType.SPREAD)
        assert game.player.effects.spread > 0
        game.player.activate_powerup(PowerUpType.SLOWMO)
        assert game.player.effects.spread == 0
        assert game.player.effects.slowmo > 0

    def test_all_powerup_types_have_duration(self, game):
        for pt in PowerUpType:
            assert POWERUP_DURATIONS[pt] > 0
            assert POWERUP_DURATIONS[pt] % 1000 == 0


class TestEdgeCase:
    def test_title_update_returns_early(self, game):
        game.state = GameState.TITLE
        score_before = game.score_keeper.score
        game._update(16)
        assert game.state == GameState.TITLE
        assert game.score_keeper.score == score_before

    def test_empty_formation_try_shoot_returns_none(self, game):
        game.formation.enemies.empty()
        assert game.formation.try_shoot() is None

    def test_enemies_reach_game_over_line(self, game):
        for e in game.formation.enemies:
            e.rect.bottom = GAME_OVER_LINE + 10
        game._update(16)
        assert game.state == GameState.GAME_OVER

    def test_create_bullet_at_max_returns_empty(self, game):
        for _ in range(MAX_PLAYER_BULLETS):
            b = Bullet(100, 100, -9, is_player=True)
            game.player_bullets.add(b)
        assert game._create_bullet() == []

    def test_score_popup_removed_after_expiry(self, game):
        game.score_keeper.popups.append({
            "text": "+100", "x": 100, "y": 100, "timer": 50, "start_y": 100,
        })
        game._update_score_popups(100)
        assert len(game.score_keeper.popups) == 0

    def test_empty_bunkers_no_crash(self, game):
        game.bunkers = []
        game._update(16)

    def test_stars_wrap_around(self, game):
        s = game.starfield.stars[0]
        s[1] = WINDOW_HEIGHT + 10
        game.starfield.update(16)
        assert 0 <= s[1] < WINDOW_HEIGHT

    def test_formation_update_empty_no_crash(self, game):
        game.formation.enemies.empty()
        game.formation.update(16)

    def test_auto_step_down_empty_no_crash(self, game):
        game.formation.enemies.empty()
        game.formation.auto_step_down()


class TestDifficulty:
    def test_default_normal_lives(self, game):
        assert game.player.lives == PLAYER_LIVES

    def test_easy_reset_lives(self):
        g = Game()
        g.difficulty = Difficulty.EASY
        reset_game(g)
        assert g.player.lives == DIFFICULTY_PRESETS[Difficulty.EASY]["lives"]

    def test_hard_reset_lives(self):
        g = Game()
        g.difficulty = Difficulty.HARD
        reset_game(g)
        assert g.player.lives == DIFFICULTY_PRESETS[Difficulty.HARD]["lives"]

    def test_easy_advance_preserves_lives(self, game):
        game.difficulty = Difficulty.EASY
        game.player.lives = 2
        advance_level(game)
        assert game.player.lives == 2


class TestStreak:
    def test_streak_increments_on_kill(self, game):
        game.score_keeper.streak = 5
        game.formation.enemies.empty()
        bullet = Bullet(200, 200, -9, is_player=True)
        game.player_bullets.add(bullet)
        enemy = Enemy(200, 200, (255, 0, 0), 30)
        game.formation.enemies.add(enemy)
        game._update(16)
        assert game.score_keeper.streak == 6

    def test_streak_resets_on_hit(self, game):
        game.score_keeper.streak = 10
        game.player.invulnerable = False
        bullet = Bullet(
            game.player.rect.centerx, game.player.rect.top, 5, is_player=False
        )
        game.enemy_bullets.add(bullet)
        game._update(16)
        assert game.score_keeper.streak == 0

    def test_streak_persists_on_level_advance(self, game):
        game.score_keeper.streak = 15
        advance_level(game)
        assert game.score_keeper.streak == 15

    def test_streak_resets_on_game_reset(self, game):
        game.score_keeper.streak = 20
        reset_game(game)
        assert game.score_keeper.streak == 0

    def test_streak_bonus_added_to_score(self, game):
        game.score_keeper.streak = 50
        game.score_keeper.elapsed_time = 0
        game.formation.enemies.empty()
        bullet = Bullet(200, 200, -9, is_player=True)
        game.player_bullets.add(bullet)
        enemy = Enemy(200, 200, (255, 0, 0), 30)
        game.formation.enemies.add(enemy)
        score_before = game.score_keeper.score
        game._update(16)
        delta = game.score_keeper.score - score_before
        assert delta >= 50

    def test_streak_bonus_caps_at_99(self, game):
        game.score_keeper.streak = 200
        game.score_keeper.elapsed_time = 0
        game.formation.enemies.empty()
        bullet = Bullet(200, 200, -9, is_player=True)
        game.player_bullets.add(bullet)
        enemy = Enemy(200, 200, (255, 0, 0), 30)
        game.formation.enemies.add(enemy)
        score_before = game.score_keeper.score
        game._update(16)
        delta = game.score_keeper.score - score_before
        assert delta >= 99
        assert delta < 200

    def test_miss_resets_streak(self, game):
        game.score_keeper.streak = 10
        bullet = Bullet(100, -30, -9, is_player=True)
        game.player_bullets.add(bullet)
        game._update(16)
        assert game.score_keeper.streak == 0

    def test_hit_preserves_streak(self, game):
        game.score_keeper.streak = 10
        game.formation.enemies.empty()
        bullet = Bullet(200, 200, -9, is_player=True)
        game.player_bullets.add(bullet)
        enemy = Enemy(200, 200, (255, 0, 0), 30)
        game.formation.enemies.add(enemy)
        game._update(16)
        assert game.score_keeper.streak == 11


class TestBoss:
    def test_try_shoot_returns_position(self, game):
        boss = Boss()
        pos = boss.try_shoot()
        assert len(pos) == 2
        assert isinstance(pos[0], (int, float))
        assert isinstance(pos[1], (int, float))

    def test_take_hit_reduces_hp(self, game):
        boss = Boss()
        hp_before = boss.hp
        boss.take_hit()
        assert boss.hp == hp_before - 1

    def test_boss_killed_when_hp_zero(self, game):
        boss = Boss()
        for _ in range(boss.max_hp):
            boss.take_hit()
        assert not boss.alive()

    def test_boss_shoots_after_timer(self, game):
        game.boss_manager.boss = Boss()
        game.boss_manager.shoot_timer = 800
        n_before = len(game.enemy_bullets)
        game._update(16)
        assert len(game.enemy_bullets) == n_before + 1
        assert game.boss_manager.shoot_timer == 0

    def test_boss_phase_2_after_half_hp(self, game):
        boss = Boss()
        boss.hp = boss.max_hp // 2
        boss.update(16)
        assert boss.phase == 2

    def test_boss_minion_creation_and_movement(self):
        m = BossMinion(100, 50)
        assert m.rect.centery == 50
        m.update(16)
        assert m.rect.centery > 50

    def test_boss_phase_2_shoots_spread(self, game):
        game.boss_manager.boss = Boss()
        game.boss_manager.boss.hp = 5
        game.boss_manager.boss.update(16)
        assert game.boss_manager.boss.phase == 2
        game.boss_manager.shoot_timer = 600
        n_before = len(game.enemy_bullets)
        game._update(16)
        assert len(game.enemy_bullets) >= n_before + 2


class TestEnemyTypes:
    def test_enemy_type_assignment(self):
        cfg = generate_level(1)
        assert "types" in cfg
        types = cfg["types"]
        assert len(types) == len(cfg["pattern"])

    def test_enemy_types_have_valid_names(self):
        cfg = generate_level(1)
        valid = {t.name.lower() for t in EnemyType}
        for row in cfg["types"]:
            for tname in row:
                assert tname in valid, f"Invalid type {tname}"

    def test_shield_enemy_survives_one_hit(self, game):
        game.state = GameState.PLAYING
        game.transition_timer = 0
        for e in list(game.formation.enemies):
            if e.enemy_type == EnemyType.SHIELD:
                alive_before = e.alive()
                e.take_hit()
                assert e.alive(), "Shield died in one hit"
                assert e.hp >= 1
                return
        assert True

    def test_kamikaze_enemy_moves_down(self):
        e = Enemy(100, 100, (255, 0, 0), 10, EnemyType.KAMIKAZE)
        class FakePlayer:
            def alive(self): return True
            rect = pygame.Rect(0, 0, 20, 20)
        k = KamikazeEnemy(e, FakePlayer())
        y_before = k.rect.y
        k.update(16)
        assert k.rect.y > y_before

    def test_kamikaze_steers_toward_player(self):
        e = Enemy(0, 100, (255, 0, 0), 10, EnemyType.KAMIKAZE)
        class FarPlayer:
            def alive(self): return True
            rect = pygame.Rect(500, 0, 20, 20)
        k = KamikazeEnemy(e, FarPlayer())
        k.update(16)
        assert k.rect.x > 0, "Should steer right toward player at x=500"

    def test_kamikaze_accelerates(self):
        e = Enemy(0, 0, (255, 0, 0), 10, EnemyType.KAMIKAZE)
        class FakePlayer:
            def alive(self): return True
            rect = pygame.Rect(0, 0, 20, 20)
        k = KamikazeEnemy(e, FakePlayer())
        k.update(16)
        first_dy = k.rect.y
        for _ in range(100):
            k.update(16)
        assert k._speed > ENEMY_KAMIKAZE_BASE_SPEED, "Speed should increase over time"

    def test_formation_creates_enemies_with_types(self):
        cfg = generate_level(1)
        form = EnemyFormation(cfg)
        types_seen = set()
        for e in form.enemies:
            types_seen.add(e.enemy_type)
        assert len(types_seen) >= 1
        assert EnemyType.NORMAL in types_seen

    def test_each_type_has_unique_sprite(self):
        colors = [(255, 0, 0)] * 6
        pixels = {}
        for i, t in enumerate(EnemyType):
            e = Enemy(0, 0, colors[i], 10, t)
            surf = e.frame_a
            ck = surf.get_colorkey()
            px_ct = sum(
                1 for y in range(surf.get_height())
                for x in range(surf.get_width())
                if surf.get_at((x, y))[:3] != ck[:3]
            )
            pixels[t.name] = px_ct
        unique = set(pixels.values())
        assert len(unique) >= 4, f"Too many types share same pixel count: {pixels}"

    def test_shield_dim_after_hit(self):
        e = Enemy(0, 0, (200, 100, 50), 10, EnemyType.SHIELD)
        ck = e.frame_a.get_colorkey()
        px_after = sum(
            1 for y in range(e.frame_b.get_height())
            for x in range(e.frame_b.get_width())
            if e.frame_b.get_at((x, y))[:3] != ck[:3]
        )
        e.take_hit()
        px_dim = sum(
            1 for y in range(e.frame_b.get_height())
            for x in range(e.frame_b.get_width())
            if e.frame_b.get_at((x, y))[:3] != ck[:3]
        )
        assert e.hp == 1
        assert px_dim > 0, "Dimmed shield has no visible pixels"


class TestRender:
    def test_draw_playing_no_crash(self, game):
        game._draw()

    def test_draw_intro_no_crash(self, game):
        game.state = GameState.INTRO
        game.transition_timer = 2000
        game._draw()

    def test_draw_paused_no_crash(self, game):
        game._prev_state = game.state
        game.state = GameState.PAUSED
        game._draw()

    def test_draw_game_over_no_crash(self, game):
        game.state = GameState.GAME_OVER
        game._draw()

    def test_draw_win_no_crash(self, game):
        game.state = GameState.WIN
        game._draw()

    def test_draw_title_no_crash(self):
        g = Game()
        assert g.state == GameState.TITLE
        g._draw()

    def test_draw_transition_with_boss_powerups(self, game):
        game.state = GameState.INTRO
        game.transition_timer = 2000
        game.boss_manager.boss = Boss()
        from sprites.powerup import PowerUp
        game.powerup_manager.powerups.add(PowerUp(200, 200, PowerUpType.SPREAD))
        game.player.activate_powerup(PowerUpType.SHIELD)
        game._draw()

    def test_draw_score_popups(self, game):
        game.score_keeper.popups.append({
            "text": "+100", "x": 100, "y": 100, "timer": 500, "start_y": 100,
        })
        game._draw()


class TestPerformance:
    def test_100_frames_under_2s(self, game):
        import time
        start = time.perf_counter()
        for _ in range(100):
            game._update(16)
            game._draw()
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0

    def test_stress_many_bullets(self, game):
        for _ in range(50):
            b = Bullet(100, 100, 5, is_player=False)
            game.enemy_bullets.add(b)
            b = Bullet(100, 300, -9, is_player=True)
            game.player_bullets.add(b)
        for _ in range(200):
            game._update(16)
        assert len(game.player_bullets) == 0
        assert len(game.enemy_bullets) < 20

    def test_stress_many_particles(self, game):
        from effects import spawn_explosion
        for _ in range(20):
            game.particles.add(spawn_explosion(100, 100, (255, 0, 0)))
        for _ in range(60):
            game._update(16)
        assert len(game.particles) == 0
