from dataclasses import dataclass
from typing import Optional

import pygame

from classes import Difficulty, GameState, PowerUpType
from settings import BOSS_INTERVAL, DIFFICULTY_NAMES
from settings import (
    BLACK, DIVIDER, GAME_WIDTH,
    TEXT_ACCENT, TEXT_MAIN, WINDOW_HEIGHT, WINDOW_WIDTH,
    POWERUP_COLORS, POWERUP_SYMBOLS,
)


@dataclass
class SceneState:
    state: GameState
    level: int
    transition_timer: int
    player: 'Player'
    formation: 'EnemyFormation'
    player_bullets: pygame.sprite.Group
    enemy_bullets: pygame.sprite.Group
    particles: pygame.sprite.Group
    flash_fx: pygame.sprite.Group
    ufo: Optional['UFO']
    bunkers: list
    powerups: pygame.sprite.Group
    score: int
    high_score: int
    lives: int
    score_multiplier: float
    streak: int
    popups: list[dict]
    boss: Optional['Boss']
    kamikazes: pygame.sprite.Group
    minions: pygame.sprite.Group
    difficulty: Difficulty
    powerup_msg: str
    active_pu_type: Optional[PowerUpType]
    active_pu_remaining: int
    special_charge: float
    special_active: bool


class Renderer:
    def __init__(self, screen, game_surf, screen_shake, info_panel, starfield):
        self.screen = screen
        self.game_surf = game_surf
        self.screen_shake = screen_shake
        self.info_panel = info_panel
        self.starfield = starfield
        self.font_tiny = pygame.font.Font(None, 16)
        self.font_popup = pygame.font.Font(None, 20)
        self.font_small = pygame.font.Font(None, 22)
        self.font_med = pygame.font.Font(None, 28)
        self.font_large = pygame.font.Font(None, 36)
        self.font_xl = pygame.font.Font(None, 52)
        self.font_xxl = pygame.font.Font(None, 56)
        self.font_huge = pygame.font.Font(None, 72)
        self.workspace = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))

    def draw(self, scene: SceneState) -> None:
        if scene.state == GameState.TITLE:
            self._draw_title_screen(scene)
            return

        self.game_surf.fill(BLACK)
        self.starfield.draw_on(self.game_surf)

        if scene.ufo and scene.state != GameState.INTRO:
            self.game_surf.blit(scene.ufo.image, scene.ufo.rect)
        for bunker in scene.bunkers:
            bunker.bricks.draw(self.game_surf)
        scene.enemy_bullets.draw(self.game_surf)
        scene.player_bullets.draw(self.game_surf)
        if scene.kamikazes:
            scene.kamikazes.draw(self.game_surf)
        if scene.minions:
            scene.minions.draw(self.game_surf)
        if scene.state != GameState.INTRO:
            scene.formation.enemies.draw(self.game_surf)
        if scene.boss:
            self.game_surf.blit(scene.boss.image, scene.boss.rect)
        scene.powerups.draw(self.game_surf)
        scene.particles.draw(self.game_surf)
        scene.flash_fx.draw(self.game_surf)

        if scene.popups:
            for p in scene.popups:
                alpha = max(0, int(255 * p["timer"] / 800))
                text = self.font_popup.render(p["text"], True, (255, 255, 255))
                text.set_alpha(alpha)
                self.game_surf.blit(text, (p["x"] - text.get_width() // 2, p["y"]))
        self.game_surf.blit(scene.player.image, scene.player.rect)
        self._draw_special_bar(scene.player, scene.special_charge, scene.special_active)

        if scene.special_active:
            self._draw_beam(scene.player)

        self._draw_level_indicator(scene.level)
        self._draw_powerup_popup(scene.powerup_msg)
        self._draw_powerup_indicator(scene.active_pu_type, scene.active_pu_remaining)
        self._draw_boss_hp(scene.boss)

        if scene.transition_timer > 0:
            self._draw_level_transition(scene.state, scene.level)

        self._present(scene)

    def _draw_title_screen(self, scene: SceneState) -> None:
        self.screen.fill(BLACK)
        sw, sh = self.screen.get_size()
        self.starfield.draw_on(self.screen, sw / GAME_WIDTH, sh / WINDOW_HEIGHT)
        self._draw_title(scene.difficulty)
        pygame.display.flip()

    def _draw_powerup_popup(self, msg):
        if not msg:
            return
        text = self.font_xl.render(f"POWER-UP: {msg}", True, TEXT_ACCENT)
        r = text.get_rect(center=(GAME_WIDTH // 2, WINDOW_HEIGHT // 2 - 60))
        self.game_surf.blit(text, r)

    def _draw_powerup_indicator(self, pu_type, remaining_ms):
        if pu_type is None or remaining_ms <= 0:
            return
        sec = max(1, int(remaining_ms / 1000))
        color = POWERUP_COLORS[pu_type]
        sym = POWERUP_SYMBOLS[pu_type]
        badge = self.font_small.render(f"[{sym}] {sec}s", True, color)
        bg = pygame.Surface((badge.get_width() + 12, badge.get_height() + 6))
        bg.set_alpha(120)
        bg.fill((0, 0, 0))
        x = GAME_WIDTH - badge.get_width() - 20
        y = 8
        self.game_surf.blit(bg, (x - 8, y - 4))
        self.game_surf.blit(badge, (x, y))

    def _draw_level_indicator(self, level):
        is_boss = level % BOSS_INTERVAL == 0
        label = f"LEVEL {level}" if not is_boss else f"BOSS LEVEL {level}"
        color = (255, 100, 50) if is_boss else TEXT_ACCENT
        text = self.font_med.render(label, True, color)
        bg = pygame.Surface((text.get_width() + 12, text.get_height() + 6))
        bg.set_alpha(100)
        bg.fill((0, 0, 0))
        self.game_surf.blit(bg, (8, 8))
        self.game_surf.blit(text, (14, 11))

    def _draw_boss_hp(self, boss):
        if not boss:
            return
        bw = boss.w
        bh = 8
        bx = boss.rect.centerx - bw // 2
        by = boss.rect.top - 14
        pygame.draw.rect(self.game_surf, (60, 60, 60), (bx, by, bw, bh))
        ratio = max(0, boss.hp / boss.max_hp)
        pygame.draw.rect(self.game_surf, (255, 80, 80), (bx, by, int(bw * ratio), bh))

    def _draw_special_bar(self, player, charge, active):
        from settings import SPECIAL_BEAM_COLOR, GAME_WIDTH, WHITE, DIVIDER

        bar_w = 80
        bar_h = 6
        bx = player.rect.centerx - bar_w // 2
        by = player.rect.bottom + 4

        if not active:
            if charge < 1.0:
                label = f"Z {int(charge * 100)}%"
            else:
                label = "Z READY"
        else:
            label = "Z BEAM"

        pygame.draw.rect(self.game_surf, (40, 40, 50), (bx, by, bar_w, bar_h))
        fill_w = int(bar_w * charge)
        if fill_w > 0:
            bar_color = WHITE if active else SPECIAL_BEAM_COLOR
            pygame.draw.rect(self.game_surf, bar_color, (bx, by, fill_w, bar_h))
        pygame.draw.rect(self.game_surf, DIVIDER, (bx, by, bar_w, bar_h), 1)

        fs = self.font_tiny
        text = fs.render(label, True, SPECIAL_BEAM_COLOR if not active else WHITE)
        tr = text.get_rect(center=(player.rect.centerx, by + bar_h + 10))
        self.game_surf.blit(text, tr)

    def _draw_beam(self, player):
        from settings import SPECIAL_BEAM_COLOR, SPECIAL_BEAM_CORE, SPECIAL_BEAM_WIDTH

        cx = player.rect.centerx
        bw = SPECIAL_BEAM_WIDTH
        bh = player.rect.top

        glow = pygame.Surface((bw + 16, bh), pygame.SRCALPHA)
        glow.fill((*SPECIAL_BEAM_COLOR, 20))
        self.game_surf.blit(glow, (cx - bw // 2 - 8, 0))

        for i in range(3):
            alpha = 60 - i * 15
            w = bw + 10 - i * 4
            s = pygame.Surface((w, bh), pygame.SRCALPHA)
            s.fill((*SPECIAL_BEAM_COLOR, max(0, alpha)))
            self.game_surf.blit(s, (cx - w // 2, 0))

        core = pygame.Surface((bw, bh), pygame.SRCALPHA)
        core.fill((*SPECIAL_BEAM_CORE, 40))
        self.game_surf.blit(core, (cx - bw // 2, 0))

    def _draw_level_transition(self, state, level):
        is_boss_clear = level > 0 and level % BOSS_INTERVAL == 0

        ft = self.font_xxl
        fs = self.font_med
        if state == GameState.INTRO:
            t1 = ft.render(f"LEVEL {level}", True, TEXT_ACCENT)
            t2 = fs.render("Get ready...", True, TEXT_MAIN)
        elif is_boss_clear:
            t1 = ft.render(f"BOSS DEFEATED", True, (255, 100, 50))
            t2 = fs.render(f"Advancing to level {level + 1}", True, TEXT_MAIN)
        else:
            t1 = ft.render(f"LEVEL {level} CLEAR", True, TEXT_ACCENT)
            t2 = fs.render("Get ready...", True, TEXT_MAIN)
        r1 = t1.get_rect(center=(GAME_WIDTH // 2, WINDOW_HEIGHT // 2 - 20))
        r2 = t2.get_rect(center=(GAME_WIDTH // 2, WINDOW_HEIGHT // 2 + 30))
        self.game_surf.blit(t1, r1)
        self.game_surf.blit(t2, r2)

    def _draw_title(self, difficulty=Difficulty.NORMAL):
        ft = self.font_huge
        fs = self.font_med
        fd = self.font_large
        title = ft.render("SPACE VANGUARD", True, TEXT_ACCENT)
        sub = fs.render("Press SPACE to start", True, TEXT_MAIN)
        diff_label = DIFFICULTY_NAMES[difficulty]
        diff_color = {Difficulty.EASY: (100, 255, 100), Difficulty.NORMAL: TEXT_ACCENT, Difficulty.HARD: (255, 80, 80)}[difficulty]
        diff_text = fd.render(f"< {diff_label} >", True, diff_color)
        diff_hint = fs.render("LEFT / RIGHT to change", True, (140, 140, 140))
        ctrl = fs.render("Arrows: Move   SPACE: Shoot   P: Pause   F: Fullscreen   M: Mute   ESC: Quit", True, (140, 140, 140))
        sw, sh = self.screen.get_size()
        r1 = title.get_rect(center=(sw // 2, sh // 2 - 55))
        r2 = diff_text.get_rect(center=(sw // 2, sh // 2))
        r3 = diff_hint.get_rect(center=(sw // 2, sh // 2 + 30))
        r4 = sub.get_rect(center=(sw // 2, sh // 2 + 70))
        r5 = ctrl.get_rect(center=(sw // 2, sh // 2 + 110))
        self.screen.blit(title, r1)
        self.screen.blit(diff_text, r2)
        self.screen.blit(diff_hint, r3)
        self.screen.blit(sub, r4)
        self.screen.blit(ctrl, r5)

    def _present(self, scene: SceneState) -> None:
        sx, sy = self.screen_shake.get_offset()
        sw, sh = self.screen.get_size()
        use_scale = sw != WINDOW_WIDTH or sh != WINDOW_HEIGHT

        if use_scale:
            target = self.workspace
        else:
            target = self.screen

        target.fill(BLACK)
        target.blit(self.game_surf, (sx, sy))

        pygame.draw.line(
            target, DIVIDER,
            (GAME_WIDTH, 0), (GAME_WIDTH, WINDOW_HEIGHT), 3,
        )

        self.info_panel.draw(
            target, scene.score, scene.high_score, scene.lives,
            scene.state, scene.score_multiplier, scene.streak,
        )

        if use_scale:
            scaled = pygame.transform.scale(self.workspace, (sw, sh))
            self.screen.blit(scaled, (0, 0))

        if scene.state == GameState.PAUSED:
            self._draw_overlay("PAUSED", "Press P to resume")
        elif scene.state == GameState.GAME_OVER:
            self._draw_overlay("GAME OVER", "Press R to restart", scene.score)

        pygame.display.flip()

    def _draw_overlay(self, title, subtitle, score=None):
        sw, sh = self.screen.get_size()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        ft = self.font_huge
        fs = self.font_large
        fv = self.font_med

        img_t = ft.render(title, True, TEXT_ACCENT)
        r_t = img_t.get_rect(center=(sw // 2, sh // 2 - 40))
        self.screen.blit(img_t, r_t)

        img_s = fs.render(subtitle, True, TEXT_MAIN)
        r_s = img_s.get_rect(center=(sw // 2, sh // 2 + 20))
        self.screen.blit(img_s, r_s)

        if score is not None:
            img_score = fv.render(
                f"Final Score: {score}", True, TEXT_ACCENT,
            )
            r_score = img_score.get_rect(
                center=(sw // 2, sh // 2 + 65)
            )
            self.screen.blit(img_score, r_score)
