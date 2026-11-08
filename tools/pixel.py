"""Ferramentas para desenhar pixel art por código (usa o Pillow; só para gerar os sprites)."""
import math

from PIL import Image, ImageDraw

OUTLINE = (26, 20, 35, 255)


def rgba(c, a=255):
    if isinstance(c, str):
        c = c.lstrip("#")
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (a,)
    return tuple(c) + (255,) * (4 - len(c))


class Canvas:
    """Imagem RGBA com operações sem suavização."""

    def __init__(self, w, h, fill=(0, 0, 0, 0)):
        self.img = Image.new("RGBA", (w, h), fill)
        self.d = ImageDraw.Draw(self.img)
        self.w, self.h = w, h

    def rect(self, x, y, w, h, c):
        self.d.rectangle([int(x), int(y), int(x + w - 1), int(y + h - 1)], fill=rgba(c))

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.img.putpixel((int(x), int(y)), rgba(c))

    def line(self, p0, p1, c, width=1):
        self.d.line([p0, p1], fill=rgba(c), width=width)

    def poly(self, pts, c):
        self.d.polygon(pts, fill=rgba(c))

    def ellipse(self, x0, y0, x1, y1, c):
        self.d.ellipse([x0, y0, x1, y1], fill=rgba(c))

    def circle(self, x, y, r, c):
        self.d.ellipse([x - r, y - r, x + r, y + r], fill=rgba(c))

    def paste(self, other, x, y):
        self.img.alpha_composite(other.img if isinstance(other, Canvas) else other, (int(x), int(y)))

    def outline(self, color=OUTLINE):
        """Contorna de 1 px tudo o que está desenhado (pixels vizinhos transparentes)."""
        src = self.img.copy()
        out = self.img
        for y in range(self.h):
            for x in range(self.w):
                if src.getpixel((x, y))[3] == 0:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.w and 0 <= ny < self.h and src.getpixel((nx, ny))[3] > 0:
                            out.putpixel((x, y), rgba(color))
                            break
        self.d = ImageDraw.Draw(self.img)

    def save(self, path):
        self.img.save(path)


def lerp(a, b, t):
    return a + (b - a) * t


def shade(c, f):
    r, g, b, a = rgba(c)
    return (max(0, min(255, int(r * f))), max(0, min(255, int(g * f))), max(0, min(255, int(b * f))), a)


def dither(canvas, x, y, w, h, c1, c2, phase=0):
    """Tabuleiro de dois tons, para degradês de pixel art."""
    for j in range(h):
        for i in range(w):
            canvas.px(x + i, y + j, c1 if (i + j + phase) % 2 == 0 else c2)


def vgradient(canvas, top, bottom, steps=8, y0=0, y1=None):
    """Degradê vertical em faixas, com tabuleiro entre elas (pixel art de céu)."""
    y1 = canvas.h if y1 is None else y1
    band = (y1 - y0) / steps
    for s in range(steps):
        t0 = s / max(1, steps - 1)
        c = tuple(int(lerp(rgba(top)[k], rgba(bottom)[k], t0)) for k in range(3)) + (255,)
        ya = int(y0 + s * band)
        yb = int(y0 + (s + 1) * band) if s < steps - 1 else y1
        canvas.rect(0, ya, canvas.w, yb - ya, c)
        if s < steps - 1:
            t1 = (s + 1) / max(1, steps - 1)
            c2 = tuple(int(lerp(rgba(top)[k], rgba(bottom)[k], t1)) for k in range(3)) + (255,)
            dither(canvas, 0, yb - 2, canvas.w, 2, c, c2)
