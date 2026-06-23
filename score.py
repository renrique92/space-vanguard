import json
import os

from settings import SCORE_MULT_START, SCORE_MULT_DECAY, SCORE_MULT_MIN

HIGH_SCORE_FILE = os.path.join(os.path.dirname(__file__), "high_score.json")


class ScoreKeeper:
    def __init__(self):
        self.score = 0
        self.high_score = self._load()
        self.streak = 0
        self.popups: list[dict] = []
        self.elapsed_time = 0

    def _load(self) -> int:
        try:
            with open(HIGH_SCORE_FILE) as f:
                return json.load(f)
        except Exception:
            return 0

    def save(self) -> None:
        if self.score > self.high_score:
            self.high_score = self.score
            with open(HIGH_SCORE_FILE, "w") as f:
                json.dump(self.high_score, f)

    def add_popup(self, points: int, x: float, y: float) -> None:
        self.popups.append({
            "text": f"+{points}",
            "x": x,
            "y": y,
            "timer": 800,
            "start_y": y,
        })

    @property
    def multiplier(self) -> float:
        sec = self.elapsed_time / 1000
        return max(SCORE_MULT_MIN, SCORE_MULT_START - sec / SCORE_MULT_DECAY)
