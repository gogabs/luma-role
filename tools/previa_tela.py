#!/usr/bin/env python3
"""Desenha a tela do jogo em PNGs, sem SDL, com o Pillow, para conferir o visual.

    python3 tools/previa_tela.py [pasta-de-saída]     # padrão: previa-telas/

Uma imagem por situação: cada ação, a queda e os menus. Precisa do Pillow
(pip install pillow); não faz parte do jogo.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

from PIL import Image, ImageDraw, ImageFont

from pista import config as C
from pista import tela
from pista.cenarios import SCENARIOS
from pista.corrida import Obstacle, Run

_IMGS = {}
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def rgba(c):
    if isinstance(c, str):
        c = c.lstrip("#")
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
    return tuple(c) + (255,) * (4 - len(c))


class PilImage:
    def __init__(self, img):
        self.img, self.width, self.height = img, img.width, img.height
        self.texture = True


class PilGfx:
    available = True

    def image(self, path):
        if not hasattr(self, "_imgs"):
            self._imgs = _IMGS
        if path not in self._imgs:
            self._imgs[path] = PilImage(Image.open(path).convert("RGBA"))
        return self._imgs[path]

    def draw(self, image, x, y, src=None, scale=1.0, rotation=0.0, flip_x=False, flip_y=False,
             alpha=255, tint=None):
        sx, sy, sw, sh = src if src else (0, 0, image.width, image.height)
        part = image.img.crop((sx, sy, sx + sw, sy + sh))
        part = part.resize((int(sw * scale), int(sh * scale)), Image.NEAREST)
        if flip_x:
            part = part.transpose(Image.FLIP_LEFT_RIGHT)
        if alpha < 255:
            part.putalpha(part.getchannel("A").point(lambda v: v * alpha // 255))
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        layer.paste(part, (int(x), int(y)))
        self._put(layer)

    def __init__(self):
        self.img = Image.new("RGBA", (640, 480), (0, 0, 0, 255))

    def _d(self, color):
        c = rgba(color)
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        return layer, ImageDraw.Draw(layer), c

    def _put(self, layer):
        self.img = Image.alpha_composite(self.img, layer)

    def font(self, path=None, size=24):
        return ImageFont.truetype(FONT, int(size))

    def clear(self, color):
        self.img = Image.new("RGBA", (640, 480), rgba(color))

    def rect(self, x, y, w, h, color=None, fill=True):
        layer, d, c = self._d(color)
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=c if fill else None, outline=c)
        self._put(layer)

    def line(self, x1, y1, x2, y2, color=None, width=1):
        layer, d, c = self._d(color)
        d.line([x1, y1, x2, y2], fill=c, width=int(width))
        self._put(layer)

    def circle(self, x, y, r, color=None, fill=True):
        layer, d, c = self._d(color)
        d.ellipse([x - r, y - r, x + r, y + r], fill=c if fill else None, outline=c, width=3)
        self._put(layer)

    def polygon(self, pts, color=None, fill=True):
        layer, d, c = self._d(color)
        d.polygon(pts, fill=c if fill else None, outline=c)
        self._put(layer)

    def text(self, s, x, y, font=None, color=None, align="left"):
        layer, d, c = self._d(color)
        w = d.textlength(s, font=font)
        x -= w / 2 if align == "center" else (w if align == "right" else 0)
        d.text((x, y), s, font=font, fill=c)
        self._put(layer)


class FakeMenu:
    def __init__(self, title, items, index=0):
        self.title, self.items, self.index = title, items, index


class Quiet:
    def __getattr__(self, name):
        return lambda *a, **k: None


def scene(name, out, kinds, at, scenario=0, setup=None, caption=""):
    tela._scroll.update(t=0.0, pos=0.0)
    run = Run(Quiet(), seed=1, seen={"pular", "freada", "rampa", "corrimao", "escada", "curva_esq", "curva_dir"},
              scenarios_seen={0, 1, 2, 3})
    run.scenario = scenario
    run.obstacles = [Obstacle(k, SCENARIOS[scenario]["objetos"].get(k, k), a, 0.5) for k, a in kinds]
    run._plan = lambda: None
    for o in run.obstacles:
        o.side = "left"
    t = 0.0
    while t < at - 1e-9:
        run.update(0.02)
        t += 0.02
    run.scenario = scenario
    if setup:
        setup(run)
    g = PilGfx()
    tela.draw(g, run, caption=caption)
    g.img.convert("RGB").save(os.path.join(out, name + ".png"))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "previa-telas")
    os.makedirs(out, exist_ok=True)
    for i, (kind, nm) in enumerate((("pular", "praca"), ("freada", "rua"), ("rampa", "praca"),
                                     ("corrimao", "rua"), ("escada", "estacionamento"), ("curva_esq", "escola"))):
        sc = {"praca": 0, "rua": 1, "estacionamento": 2, "escola": 3}[nm]
        scene("1-aviso-" + kind, out, [(kind, 6.5)], 5.2, sc, caption="Obstáculo chegando")

    def act(kind, button=None, advance=0.5):
        def setup(run):
            if button:
                run.button_down(button)
            run.action(kind)
            for _ in range(int(advance / 0.02)):
                run.update(0.02)
        return setup

    scene("2-rampa-no-ar", out, [("rampa", 5.0), ("pular", 30)], 5.0, 0, act("rampa", None, 0.7))
    scene("2-manobra", out, [("rampa", 5.0), ("pular", 30)], 5.0, 0,
          lambda run: (act("rampa", None, 0.5)(run), run.trick(("left",)), run.update(0.1)))
    scene("2-freada", out, [("freada", 5.0), ("pular", 30)], 5.0, 1, act("freada", "down", 0.8))
    scene("2-escada", out, [("escada", 5.0), ("pular", 30)], 5.0, 2, act("escada", "x", 0.6))
    scene("2-curva", out, [("curva_esq", 5.0), ("pular", 30)], 5.0, 3, act("curva_esq", "left", 0.6))
    scene("2-corrimao", out, [("corrimao", 5.0), ("pular", 30)], 5.0, 1,
          lambda run: (run.button_down("a"), run.action("pular"), [run.update(0.02) for _ in range(30)]))
    scene("3-queda", out, [("pular", 5.0), ("pular", 30)], 5.0, 0, lambda run: (run.action("freada"),
          [run.update(0.02) for _ in range(10)]))
    g = PilGfx()
    tela.draw(g, None, menu=FakeMenu("Rolê", ["Jogar", "Aprender os sons", "Como jogar", "Música: média",
                                              "Recorde", "Sair"], 1), caption="Rolê. Aprender os sons, 2 de 6.")
    g.img.convert("RGB").save(os.path.join(out, "4-menu.png"))
    print("telas em", os.path.normpath(out))


if __name__ == "__main__":
    main()
