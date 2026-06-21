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
        self._bgm_channel = None
        self._generate_all()

    def _generate_all(self):
        self.sounds["shoot"] = self._tone(880, 0.08, 0.12, "square")
        self.sounds["enemy_shoot"] = self._tone(440, 0.10, 0.08, "square")
        self.sounds["explosion"] = self._noise(0.20, 0.15)
        self.sounds["player_hit"] = self._tone(150, 0.30, 0.20, "sine")
        self.sounds["game_over"] = self._sweep(440, 110, 0.60, 0.15, "sine")
        self.sounds["win"] = self._sweep(330, 880, 0.60, 0.15, "sine")
        self.sounds["ufo"] = self._sweep(200, 600, 0.40, 0.08, "square")
        self.sounds["level_up"] = self._sweep(660, 1320, 0.30, 0.12, "square")
        self.sounds["bgm"] = self._generate_bgm()

    def play(self, name):
        if self.available and name in self.sounds:
            self.sounds[name].play()

    def play_bgm(self):
        if self.available and "bgm" in self.sounds:
            self._bgm_channel = self.sounds["bgm"].play(loops=-1)

    def stop_bgm(self):
        if self._bgm_channel:
            self._bgm_channel.stop()
            self._bgm_channel = None

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

    def _generate_bgm(self):
        sr = 22050
        bpm = 140
        beat_s = 60.0 / bpm
        pattern = [110, 130, 165, 130, 110, 165, 130, 110]
        loop_beats = len(pattern)
        duration = beat_s * loop_beats
        n = int(sr * duration)
        buf = array.array("h", [0]) * n
        for i in range(n):
            t = i / sr
            beat = int(t / beat_s) % loop_beats
            freq = pattern[beat]
            v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
            v2 = math.sin(2 * math.pi * freq * 2 * t) * 0.3
            env = max(0, 1 - (t % beat_s) / beat_s * 0.6)
            buf[i] = int(32767 * 0.08 * (v + v2) * env)
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
