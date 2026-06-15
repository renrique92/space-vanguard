import pygame
from settings import (
    GAME_WIDTH, PANEL_WIDTH, DARK_BG, DIVIDER,
    TEXT_MAIN, TEXT_ACCENT, TITLE_COLOR, WHITE,
    GREEN, PANEL_AREA, RED,
)


class InfoPanel:
    def __init__(self):
        pygame.font.init()
        self.font_title = pygame.font.Font(None, 44)
        self.font_score = pygame.font.Font(None, 32)
        self.font_value = pygame.font.Font(None, 40)
        self.font_small = pygame.font.Font(None, 22)
        self.font_control = pygame.font.Font(None, 20)

        cx = GAME_WIDTH + PANEL_WIDTH // 2
        left_margin = GAME_WIDTH + 30

        self.title_y = 45
        self.score_label_y = 120
        self.score_value_y = 155
        self.div1_y = 195

        self.high_label_y = 225
        self.high_value_y = 260
        self.div2_y = 300

        self.lives_label_y = 330
        self.lives_y = 370
        self.lives_start_x = left_margin
        self.div3_y = 410

        self.mult_label_y = 440
        self.mult_value_y = 470
        self.div4_y = 510

        self.acc_label_y = 535
        self.acc_value_y = 565
        self.div5_y = 595

        self.controls_y = 610
        self.cx = cx

    def draw(self, screen, score, high_score, lives, state, multiplier, accuracy):
        screen.fill(DARK_BG, PANEL_AREA)

        t1 = self.font_title.render("SPACE", True, TITLE_COLOR)
        r1 = t1.get_rect(center=(self.cx, self.title_y - 10))
        screen.blit(t1, r1)

        t2 = self.font_title.render("VANGUARD", True, TEXT_ACCENT)
        r2 = t2.get_rect(center=(self.cx, self.title_y + 22))
        screen.blit(t2, r2)

        self._divider(screen, self.div1_y)
        self._divider(screen, self.div2_y)
        self._divider(screen, self.div3_y)
        self._divider(screen, self.div4_y)
        self._divider(screen, self.div5_y)

        self._label(screen, "SCORE", self.font_score, self.cx, self.score_label_y)
        sv = self.font_value.render(f"{score:07d}", True, TEXT_ACCENT)
        sr = sv.get_rect(center=(self.cx, self.score_value_y))
        screen.blit(sv, sr)

        self._label(screen, "HIGH SCORE", self.font_small, self.cx, self.high_label_y)
        hv = self.font_value.render(f"{high_score:07d}", True, WHITE)
        hr = hv.get_rect(center=(self.cx, self.high_value_y))
        screen.blit(hv, hr)

        self._label(screen, "LIVES", self.font_score, self.cx, self.lives_label_y)
        for i in range(min(lives, 5)):
            self._life_icon(screen, self.lives_start_x + i * 30, self.lives_y)

        self._label(screen, "MULTIPLIER", self.font_score, self.cx, self.mult_label_y)
        mult_color = TEXT_ACCENT if multiplier >= 1.0 else RED
        mult_text = self.font_value.render(f"× {multiplier:.1f}", True, mult_color)
        mult_rect = mult_text.get_rect(center=(self.cx, self.mult_value_y))
        screen.blit(mult_text, mult_rect)

        self._label(screen, "ACCURACY", self.font_score, self.cx, self.acc_label_y)
        acc_color = TEXT_ACCENT if accuracy >= 50.0 else RED
        acc_text = self.font_value.render(f"{accuracy:.0f}%", True, acc_color)
        acc_rect = acc_text.get_rect(center=(self.cx, self.acc_value_y))
        screen.blit(acc_text, acc_rect)

        controls = [
            ("LEFT RIGHT", "MOVE"),
            ("SPACE", "SHOOT"),
            ("P", "PAUSE"),
            ("R", "RESTART"),
        ]
        y = self.controls_y
        for key, action in controls:
            k = self.font_control.render(key, True, TEXT_ACCENT)
            a = self.font_control.render(action, True, TEXT_MAIN)
            k_r = k.get_rect(midright=(self.cx - 20, y))
            a_r = a.get_rect(midleft=(self.cx - 10, y))
            screen.blit(k, k_r)
            screen.blit(a, a_r)
            y += 22

    def _divider(self, screen, y):
        x1 = GAME_WIDTH + 20
        x2 = GAME_WIDTH + PANEL_WIDTH - 20
        pygame.draw.line(screen, DIVIDER, (x1, y), (x2, y), 1)
        pygame.draw.line(screen, DIVIDER, (x1, y + 2), (x2, y + 2), 1)

    def _label(self, screen, text, font, x, y):
        img = font.render(text, True, TEXT_MAIN)
        r = img.get_rect(center=(x, y))
        screen.blit(img, r)

    def _life_icon(self, screen, x, y):
        w, h = 20, 14
        cx = w // 2
        pts = [(cx + x, y), (x + 1, y + h), (x + w - 1, y + h)]
        pygame.draw.polygon(screen, GREEN, pts)
