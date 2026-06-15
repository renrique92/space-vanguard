import array
import math
import random

import pygame


class SoundManager:
    def __init__(self):
        self.available = True
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        except Exception:
            self.available = False
            return

        self.sounds = {}
        self._generate_all()

    def _generate_all(self):
        self.sounds["shoot"] = self._tone(880, 0.08, 0.12, "square")
        self.sounds["enemy_shoot"] = self._tone(440, 0.10, 0.08, "square")
        self.sounds["explosion"] = self._noise(0.20, 0.15)
        self.sounds["player_hit"] = self._tone(150, 0.30, 0.20, "sine")
        self.sounds["game_over"] = self._sweep(440, 110, 0.60, 0.15, "sine")
        self.sounds["win"] = self._sweep(330, 880, 0.60, 0.15, "sine")

    def play(self, name):
        if self.available and name in self.sounds:
            self.sounds[name].play()

    def _to_sound(self, buf):
        return pygame.mixer.Sound(buffer=bytes(buf))

    def _tone(self, freq, duration, volume, wave):
        sr = 22050
        n = int(sr * duration)
        buf = array.array("h", [0]) * n
        for i in range(n):
            t = i / sr
            if wave == "square":
                v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
            else:
                v = math.sin(2 * math.pi * freq * t)
            buf[i] = int(32767 * volume * v)
        return self._to_sound(buf)

    def _noise(self, duration, volume):
        sr = 22050
        n = int(sr * duration)
        buf = array.array("h", [0]) * n
        for i in range(n):
            t = i / sr
            v = random.uniform(-1, 1) * (1 - t / duration)
            buf[i] = int(32767 * volume * v)
        return self._to_sound(buf)

    def _sweep(self, f_start, f_end, duration, volume, wave):
        sr = 22050
        n = int(sr * duration)
        buf = array.array("h", [0]) * n
        for i in range(n):
            t = i / sr
            freq = f_start + (f_end - f_start) * (t / duration)
            if wave == "square":
                v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
            else:
                v = math.sin(2 * math.pi * freq * t)
            fade = 1 - t / duration * 0.7
            buf[i] = int(32767 * volume * v * fade)
        return self._to_sound(buf)
