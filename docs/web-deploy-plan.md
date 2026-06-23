# Space Vanguard — Web Deploy Plan (Pygbag)

> Fecha: 23 Jun 2026
> Target: juego jugable en navegador, hosting gratuito

---

## 1. Overview

Pygbag empaqueta el juego Python+Pygame a WebAssembly vía Emscripten.
Genera una carpeta `build/web/` con HTML+JS+WASM.
Se hostea como sitio estático: GitHub Pages, Netlify, Vercel, Itch.io.

---

## 2. Prerrequisitos

| Requisito | Versión | Nota |
|-----------|---------|------|
| Python | 3.9+ | igual que local |
| pip | última | — |
| pygbag | ≥0.8.0 | `pip install pygbag` |
| git | — | para deploy a gh-pages |
| navegador | moderno | Chrome/Firefox/Safari/Edge |

---

## 3. Cambios al código

### 3.1 `main.py` — loop asíncrono

```python
import asyncio
import pygame
from game import Game

async def main():
    pygame.init()
    game = Game()
    await game.run()
    pygame.quit()

asyncio.run(main())
```

### 3.2 `game.py` — `run()` async, `clock.tick()` → `await asyncio.sleep(0)`

```python
async def run(self):
    self.running = True
    while self.running:
        dt = self.clock.get_time()
        self._handle_events()
        self._update(dt)
        self._render()
        self.clock.tick(self.settings.FPS)
        await asyncio.sleep(0)  # cedé control al browser
```

Agregar `import asyncio`.

### 3.3 `sounds.py` — fallback mixer para WASM

`pygame.mixer` no siempre init en WebAssembly. Envolver todo:

```python
import pygame
import os

_mixer_available = True

try:
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=22050, size=-16, channels=1)
except pygame.error:
    _mixer_available = False

class Sound:
    def __init__(self, sound_data):
        self.sound_data = sound_data
        self._sound = None
        if _mixer_available:
            try:
                self._sound = pygame.mixer.Sound(sound_data)
            except Exception:
                pass

    def play(self):
        if _mixer_available and self._sound:
            self._sound.play()
```

### 3.4 `settings.py` — ajustes para web

```python
# Pygbag: window size fijo, FPS sincronizado con browser vsync
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60  # ideal para web (requestAnimationFrame sync)
```

### 3.5 Persistencia — high_score

Pygame no tiene filesystem real en WASM. Usar `localStorage` vía JavaScript bridge.

```python
# persistence.py (nuevo)
import json
import platform
from pathlib import Path

_HIGH_SCORE_FILE = Path("high_score.json")

def is_web():
    return platform.system() == "Emscripten"

def load_high_score():
    if is_web():
        import js
        val = js.localStorage.getItem("space_vanguard_high_score")
        return int(val) if val else 0
    else:
        if _HIGH_SCORE_FILE.exists():
            return json.loads(_HIGH_SCORE_FILE.read_text()).get("high_score", 0)
        return 0

def save_high_score(score):
    if is_web():
        import js
        js.localStorage.setItem("space_vanguard_high_score", str(score))
    else:
        _HIGH_SCORE_FILE.write_text(json.dumps({"high_score": score}))
```

### 3.6 `game.py` — integrar nuevo persistence

Reemplazar `json.load`/`json.dump` directo por `load_high_score()`/`save_high_score()`.

### 3.7 Pantalla de carga (loading screen)

Pygbag muestra pantalla de carga default. Se puede customizar con `index.html`:

```html
<!-- static/index.html (pygbag lo genera, se puede sobrescribir) -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Space Vanguard</title>
  <style>
    body { margin: 0; background: #000; color: #0f0;
           font-family: monospace; display: flex;
           justify-content: center; align-items: center;
           height: 100vh; }
    #loading { font-size: 24px; text-align: center; }
  </style>
</head>
<body>
  <div id="loading">🚀 Space Vanguard<br><small>cargando...</small></div>
  <script src="pygbag.js" async></script>
</body>
</html>
```

---

## 4. Pygbag configuration

Crear `pygbag.toml` (opcional, controla build):

```toml
[pygbag]
build = "build/web/"
package = "."
main = "main.py"
title = "Space Vanguard"
version = "1.0.0"
author = "Rafael Sendrea"
window_width = 800
window_height = 600
orientation = "landscape"
```

---

## 5. Build

```bash
# 1. Instalar
pip install pygbag

# 2. Build (desde raíz del proyecto)
python -m pygbag --build .

# 3. Output: build/web/
#    - index.html
#    - pygbag.js
#    - space_vanguard.data (WASM binary, ~15-30 MB)
#    - space_vanguard.wasm
#    - space_vanguard.js
```

**Flags útiles:**

| Flag | Uso |
|------|-----|
| `--build` | Build producción (minificado) |
| `--bind 0.0.0.0` | Servir en red local para test |
| `--template static/index.html` | Custom loading screen |
| `--ume_block 0` | No bloquear en load |
| `--can_close 1` | Permitir cerrar |

**Test local:**

```bash
python -m pygbag --bind 0.0.0.0 .
# Abrir http://localhost:8000
```

---

## 6. Hosting

### 6.1 GitHub Pages (recomendado)

```bash
# Desde la raíz del proyecto
git checkout -b gh-pages
cp -r build/web/* .
git add . && git commit -m "deploy to gh-pages"
git push origin gh-pages

# Activar en Settings > Pages > Source: gh-pages (root)
# URL: https://<usuario>.github.io/space-invaders/
```

**Alternativa con GitHub Actions (automático):**

```yaml
# .github/workflows/deploy.yml
name: Deploy to GitHub Pages
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install pygbag
      - run: python -m pygbag --build .
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./build/web
```

### 6.2 Netlify

- Build command: `pip install pygbag && python -m pygbag --build .`
- Publish directory: `build/web/`
- O drag & drop `build/web/` en Netlify Drop

### 6.3 Vercel

- Framework: `Static`
- Output: `build/web/`
- O instalar `vercel` CLI: `vercel --prod build/web/`

### 6.4 Itch.io

1. Zip `build/web/` → `space-vanguard-web.zip`
2. Subir a Itch.io > Upload > "HTML game"
3. Viewport: 800x600, auto-fit

---

## 7. Problemas conocidos y mitigaciones (GOTCHAS)

| # | Problema | Causa | Mitigación |
|---|----------|-------|------------|
| 1 | `pygame.mixer.get_init()` → False | WASM no soporta audio nativo | Fallback a mute + botón M para habilitar (AudioContext) |
| 2 | Sonidos sintetizados (22050 Hz) crash | Mixer no init previo | Sound class con try/except (3.3) |
| 3 | `high_score.json` no persiste | No hay filesystem real | localStorage bridge (3.5) |
| 4 | WASM 15-30 MB lento en cargar | Tamaño del runtime | Pantalla de carga + compresión gzip (automática en Netlify/GH Pages) |
| 5 | Input lag vs desktop | Browser event loop | `await asyncio.sleep(0)` + `clock.tick(60)` |
| 6 | Fullscreen (F key) no funciona igual | Browser fullscreen API | Dejar default, no forzar |
| 7 | `pygame.display.toggle_fullscreen()` crash | No soportado en WASM | Sacar o try/except |
| 8 | Auto-pause al perder foco | Browser visibility API | Funciona out-of-the-box con Pygbag |
| 9 | Teclas fantasma (ghosting) | Browser keyboard repeat | `key.set_repeat()` config en `game.py` |
| 10 | Archivos locales no existen | CWD distinto en WASM | Usar `importlib.resources` o `pathlib` con fallback |

---

## 8. Testing post-deploy

| Test | Qué verificar |
|------|---------------|
| Carga | Pantalla de carga aparece, WASM descarga |
| Menú title | Dificultad cicla con LEFT/RIGHT |
| Juego | Movimiento, disparo, colisiones, power-ups |
| Sonido | Mute toggle (M) funciona sin crash |
| Boss nivel 5 | Spawnea, fases, drops |
| UFO | Spawnea, se mueve, da puntos |
| Game Over / Win | Transiciones, score final |
| Streak | Contador aumenta/resetea |
| Special attack | Carga, Z dispara, no se mueve |
| Persistencia | High score sobrevive a refresh |
| Responsive | Escala en ventanas chicas |

---

## 9. Mantenimiento

| Tarea | Frecuencia | Cómo |
|-------|------------|------|
| Rebuild | Cada cambio de código | `python -m pygbag --build .` |
| Update pygbag | Mensual | `pip install --upgrade pygbag` |
| Monitorear WASM size | Cada build | Ver `build/web/*.data` size |
| Test cross-browser | Cada release | Chrome, Firefox, Safari, Edge |
| GitHub Actions | Automático | Push a main → build + deploy |

---

## 10. Resumen de archivos a modificar/crear

| Archivo | Acción | Cambio |
|---------|--------|--------|
| `main.py` | Modificar | Loop async |
| `game.py` | Modificar | `run()` async, `await asyncio.sleep(0)` |
| `sounds.py` | Modificar | Fallback mixer para WASM |
| `settings.py` | Modificar | `FPS = 60` |
| `persistence.py` | **Crear** | localStorage bridge para web |
| `game.py` (persistence) | Modificar | Usar `persistence.py` en vez de JSON directo |
| `pygbag.toml` | **Crear** | Config build |
| `.github/workflows/deploy.yml` | **Crear** | CI/CD auto |
| `requirements.txt` | Modificar | Agregar `pygbag` (opcional, es build dep) |

---

## 11. Esfuerzo estimado

| Fase | Tiempo | Dependencias |
|------|--------|-------------|
| Modificaciones código | 1-2 hrs | Ninguna |
| Build + test local | 30 min | Código modificado |
| Deploy a hosting | 30 min | Build exitoso |
| CI/CD (opcional) | 30 min | Repo en GitHub |
| **Total** | **~3 hrs** | — |
