import pygame

from classes import GameState, PowerUpType
from settings import (
    BLACK, DIVIDER, GAME_WIDTH,
    TEXT_ACCENT, TEXT_MAIN, WINDOW_HEIGHT, WINDOW_WIDTH,
    POWERUP_COLORS, POWERUP_SYMBOLS,
)


class Renderer:
    def __init__(self, screen, game_surf, screen_shake, info_panel, stars):
        self.screen = screen
        self.game_surf = game_surf
        self.screen_shake = screen_shake
        self.info_panel = info_panel
        self.stars = stars
        self.font_level = pygame.font.Font(None, 28)
        self.font_popup = pygame.font.Font(None, 20)

    def draw(self, state, level, transition_timer, player, formation,
             player_bullets, enemy_bullets, particles, flash_fx,
             ufo, bunkers, powerups, score, high_score, lives,
             score_multiplier, accuracy,
             powerup_msg="", active_pu_type=None, active_pu_remaining=0,
             score_popups=None):
        self.game_surf.fill(BLACK)

        for s in self.stars:
            pygame.draw.circle(self.game_surf, (s[2], s[2], s[2]), (int(s[0]), int(s[1])), s[3])

        if ufo and state != GameState.INTRO:
            self.game_surf.blit(ufo.image, ufo.rect)
        for bunker in bunkers:
            bunker.bricks.draw(self.game_surf)
        enemy_bullets.draw(self.game_surf)
        player_bullets.draw(self.game_surf)
        if state != GameState.INTRO:
            formation.enemies.draw(self.game_surf)
        powerups.draw(self.game_surf)
        particles.draw(self.game_surf)
        flash_fx.draw(self.game_surf)

        if score_popups:
            for p in score_popups:
                alpha = max(0, int(255 * p["timer"] / 800))
                text = self.font_popup.render(p["text"], True, (255, 255, 255))
                text.set_alpha(alpha)
                self.game_surf.blit(text, (p["x"] - text.get_width() // 2, p["y"]))
        self.game_surf.blit(player.image, player.rect)

        self._draw_level_indicator(level)
        self._draw_powerup_popup(powerup_msg)
        self._draw_powerup_indicator(active_pu_type, active_pu_remaining)

        if transition_timer > 0:
            self._draw_level_transition(state, level)

        self._present(state, score, high_score, lives,
                      score_multiplier, accuracy)

    def _draw_powerup_popup(self, msg):
        if not msg:
            return
        font = pygame.font.Font(None, 52)
        text = font.render(f"POWER-UP: {msg}", True, TEXT_ACCENT)
        r = text.get_rect(center=(GAME_WIDTH // 2, WINDOW_HEIGHT // 2 - 60))
        self.game_surf.blit(text, r)

    def _draw_powerup_indicator(self, pu_type, remaining_ms):
        if pu_type is None or remaining_ms <= 0:
            return
        sec = max(1, int(remaining_ms / 1000))
        color = POWERUP_COLORS[pu_type]
        sym = POWERUP_SYMBOLS[pu_type]
        font = pygame.font.Font(None, 22)
        badge = font.render(f"[{sym}] {sec}s", True, color)
        bg = pygame.Surface((badge.get_width() + 12, badge.get_height() + 6))
        bg.set_alpha(120)
        bg.fill((0, 0, 0))
        x = GAME_WIDTH - badge.get_width() - 20
        y = 8
        self.game_surf.blit(bg, (x - 8, y - 4))
        self.game_surf.blit(badge, (x, y))

    def _draw_level_indicator(self, level):
        text = self.font_level.render(f"Level {level}", True, TEXT_ACCENT)
        bg = pygame.Surface((text.get_width() + 12, text.get_height() + 6))
        bg.set_alpha(100)
        bg.fill((0, 0, 0))
        self.game_surf.blit(bg, (8, 8))
        self.game_surf.blit(text, (14, 11))

    def _draw_level_transition(self, state, level):
        ft = pygame.font.Font(None, 56)
        fs = pygame.font.Font(None, 28)
        if state == GameState.INTRO:
            t1 = ft.render(f"LEVEL {level}", True, TEXT_ACCENT)
        else:
            t1 = ft.render(f"LEVEL {level} CLEAR", True, TEXT_ACCENT)
        t2 = fs.render("Get ready...", True, TEXT_MAIN)
        r1 = t1.get_rect(center=(GAME_WIDTH // 2, WINDOW_HEIGHT // 2 - 20))
        r2 = t2.get_rect(center=(GAME_WIDTH // 2, WINDOW_HEIGHT // 2 + 30))
        self.game_surf.blit(t1, r1)
        self.game_surf.blit(t2, r2)

    def _present(self, state, score, high_score, lives,
                 score_multiplier, accuracy):
        sx, sy = self.screen_shake.get_offset()
        self.screen.fill(BLACK)
        self.screen.blit(self.game_surf, (sx, sy))

        pygame.draw.line(
            self.screen, DIVIDER,
            (GAME_WIDTH, 0), (GAME_WIDTH, WINDOW_HEIGHT), 3,
        )

        self.info_panel.draw(
            self.screen, score, high_score, lives,
            state, score_multiplier, accuracy,
        )

        if state == GameState.PAUSED:
            self._draw_overlay("PAUSED", "Press P to resume")
        elif state == GameState.GAME_OVER:
            self._draw_overlay("GAME OVER", "Press R to restart")
        elif state == GameState.WIN:
            self._draw_overlay("YOU WIN!", "Press R to restart", score)

        pygame.display.flip()

    def _draw_overlay(self, title, subtitle, score=None):
        overlay = pygame.Surface(
            (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA,
        )
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        ft = pygame.font.Font(None, 72)
        fs = pygame.font.Font(None, 36)
        fv = pygame.font.Font(None, 28)

        img_t = ft.render(title, True, TEXT_ACCENT)
        r_t = img_t.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40)
        )
        self.screen.blit(img_t, r_t)

        img_s = fs.render(subtitle, True, TEXT_MAIN)
        r_s = img_s.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20)
        )
        self.screen.blit(img_s, r_s)

        if score is not None:
            img_score = fv.render(
                f"Final Score: {score}", True, TEXT_ACCENT,
            )
            r_score = img_score.get_rect(
                center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 65)
            )
            self.screen.blit(img_score, r_score)
