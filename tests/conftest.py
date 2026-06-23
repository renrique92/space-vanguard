import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import json
import tempfile

import pytest
import pygame

import score as score_module
from game import Game
from classes import GameState


@pytest.fixture(scope="session", autouse=True)
def _pygame_init():
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture(autouse=True)
def _isolate_high_score(monkeypatch, tmp_path):
    f = tmp_path / "high_score.json"
    f.write_text("0")
    monkeypatch.setattr(score_module, "HIGH_SCORE_FILE", str(f))
    yield


@pytest.fixture
def game():
    g = Game()
    if g.state in (GameState.TITLE, GameState.INTRO):
        g.state = GameState.PLAYING
        g.transition_timer = 0
    yield g
