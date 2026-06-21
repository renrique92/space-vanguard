import pygame

from settings import (
    BLACK, DIVIDER, GAME_WIDTH, GameState,
    TEXT_ACCENT, TEXT_MAIN, WINDOW_HEIGHT, WINDOW_WIDTH,
)


class Renderer:
    def __init__(self, screen, game_surf, screen_shake, info_panel, stars):
        self.screen = screen
        self.game_surf = game_surf
        self.screen_shake = screen_shake
        self.info_panel = info_panel
        self.stars = stars
        self.font_level = pygame.font.Font(None, 28)

    def draw(self, state, level, transition_timer, player, formation,
             player_bullets, enemy_bullets, particles, flash_fx,
             score, high_score, lives, score_multiplier, accuracy):
        self.game_surf.fill(BLACK)

        for sx, sy, sb in self.stars:
            pygame.draw.circle(self.game_surf, (sb, sb, sb), (sx, sy), 1)

        enemy_bullets.draw(self.game_surf)
        player_bullets.draw(self.game_surf)
        if state != GameState.INTRO:
            formation.enemies.draw(self.game_surf)
        particles.draw(self.game_surf)
        flash_fx.draw(self.game_surf)
        self.game_surf.blit(player.image, player.rect)

        self._draw_level_indicator(level)

        if transition_timer > 0:
            self._draw_level_transition(state, level)

        self._present(state, score, high_score, lives,
                      score_multiplier, accuracy)

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
            self._draw_overlay("YOU WIN!", "Press R to restart")

        pygame.display.flip()

    def _draw_overlay(self, title, subtitle):
        overlay = pygame.Surface(
            (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA,
        )
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        ft = pygame.font.Font(None, 72)
        fs = pygame.font.Font(None, 36)

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
