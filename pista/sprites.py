"""Os sprites em pixel art (sprites/*.png, gerados por tools/gerar_sprites.py).

Tudo é desenhado ampliado por SCALE com a SDL em vizinho mais próximo. Se as imagens
não carregarem (sem SDL2_image, arquivos faltando), load() devolve None e a tela cai
de volta nos vetores: o jogo continua jogável.
"""
import json
import math
import os

from . import config as C

SCALE = 3
CELL = 48
TILE = 216 * SCALE          # largura de uma camada de cenário já ampliada
GROUND = 372                # onde começa a faixa do chão (124 px nativos)
FEET = 392                  # a linha onde rodas e obstáculos pousam, dentro da faixa do chão
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sprites")

# camada: (y nativo do alto, fator de rolagem em relação ao chão)
LAYERS = (("ceu", 0, 0.0), ("nuvens", 10, 0.04), ("longe", 124 - 76, 0.15),
          ("perto", 124 - 56, 0.4), ("chao", 124, 1.0))
LAYER_H = {"ceu": 124, "nuvens": 50, "longe": 76, "perto": 56, "chao": 36}

_cache = {}


class Art:
    def __init__(self, gfx, index):
        self.index = index
        self.cell = index["celula"]
        self.cols = index["colunas"]
        self.skater = gfx.image(os.path.join(DIR, "patinador.png"))
        self.obstacles = gfx.image(os.path.join(DIR, "obstaculos.png"))
        self.ui = gfx.image(os.path.join(DIR, "interface.png"))
        self.layers = {}
        for sc in ("praca", "rua", "estacionamento", "escola"):
            self.layers[sc] = {name: gfx.image(os.path.join(DIR, "fundo_%s_%s.png" % (sc, name)))
                               for name, _, _ in LAYERS}
        for img in (self.skater, self.obstacles, self.ui):
            if not img.width:
                raise IOError("sprite vazio")

    # --- peças soltas ----------------------------------------------------------------
    def piece(self, gfx, sheet, rect, x, y, **kw):
        gfx.draw(sheet, x, y, src=tuple(rect), scale=SCALE, **kw)

    def ui_piece(self, gfx, name, x, y, scale=SCALE, **kw):
        gfx.draw(self.ui, x, y, src=tuple(self.index["interface"][name]), scale=scale, **kw)

    def frame(self, gfx, name, n, x, y, flip=False, rotation=0.0):
        """Um quadro do patinador; (x, y) é o meio dos pés."""
        i = self.index["patinador"][name] + n
        sx, sy = (i % self.cols) * self.cell, (i // self.cols) * self.cell
        size = self.cell * SCALE
        gfx.draw(self.skater, x - size // 2, y - size + 4, src=(sx, sy, self.cell, self.cell),
                 scale=SCALE, flip_x=flip, rotation=rotation)

    # --- cenário ---------------------------------------------------------------------
    def background(self, gfx, scenario_id, scroll):
        for name, top, factor in LAYERS:
            img = self.layers[scenario_id][name]
            x = -((scroll * factor) % TILE)
            y = top * SCALE
            for k in range(2):
                gfx.draw(img, x + k * TILE, y, scale=SCALE)

    # --- obstáculos ------------------------------------------------------------------
    def obstacle(self, gfx, kind, scenario_id, x):
        name = "curva" if kind.startswith("curva") else "%s_%s" % (kind, scenario_id)
        ox, oy, w, h = self.index["obstaculos"][name]
        flip = kind == "curva_dir"          # a placa desenhada aponta para a esquerda
        top = FEET - h * SCALE
        gfx.draw(self.obstacles, x - w * SCALE / 2, top, src=(ox, oy, w, h), scale=SCALE, flip_x=flip)
        return top

    def beat_dots(self, gfx, x, y, cues):
        n = C.WARN_BEATS + 1
        for i in range(n):
            last = i == C.WARN_BEATS
            name = ("ponto_hora" if last else "ponto") + ("" if i < cues else "_apagado")
            size = 13 * SCALE
            self.ui_piece(gfx, name, x + (i - (n - 1) / 2) * 42 - size / 2, y - size / 2)

    # --- patinador -------------------------------------------------------------------
    def skater_frame(self, run, t):
        """(nome, quadro, espelhar) para a pose atual."""
        pose = run.pose
        speed = run.speed
        name, at = run.last_trick
        spinning = pose in ("ar", "rampa") and 0 <= t - at < C.TRICK_TIME
        if spinning:
            n = min(7, int((t - at) / C.TRICK_TIME * 8))
            return "spin", n, name == "left"
        if pose in ("ar", "rampa"):
            p = run.air_progress
            n = 0 if p < 0.1 else 1 if p < 0.4 else 2 if p < 0.6 else 3 if p < 0.92 else 4
            return "air", n, False
        if pose == "salto_corrimao":
            return "air", 1, False
        if pose == "queda":
            return "fall", min(2, int((t - run.fell_at) / 0.14)), False
        if pose == "freada":
            return "brake", int(t * 8) % 2, False
        if pose == "corrimao":
            return "grind", int(t * 12) % 2, False
        if pose == "escada":
            return "stairs", int(t * 9) % 2, False
        if pose == "curva_esq":
            return "lean_l", 0, False
        if pose == "curva_dir":
            return "lean_r", 0, False
        return "roll", int(t * 9 * speed) % 4, False

    def skater_draw(self, gfx, x, lift, name, n, flip):
        # sombra no chão: encolhe com a altura
        w = max(30, 90 - lift * 0.35)
        gfx.rect(x - w / 2, FEET + 2, w, 6, color=(0, 0, 0, 90))
        self.frame(gfx, name, n, x, FEET - lift, flip)

    def effects(self, gfx, run, x, lift, t):
        pose = run.pose
        if pose == "corrimao":
            for k in range(3):
                f = int(t * 20 + k * 2) % 4
                self.ui_piece(gfx, "faisca%d" % f, x + 6 + k * 18, FEET - 18 - (k % 2) * 14)
        elif pose == "freada":
            for k in range(3):
                f = (int(t * 10) + k) % 4
                self.ui_piece(gfx, "poeira%d" % f, x - 60 - k * 30, FEET - 36 - (k % 2) * 10,
                              alpha=210 - k * 50)
        elif pose == "queda":
            for k in range(3):
                a = t * 6 + k * 2.1
                self.ui_piece(gfx, "estrela%d" % ((int(t * 8) + k) % 3),
                              x + 36 * math.cos(a) - 17, FEET - 140 + 14 * math.sin(a) - 17)


def load(gfx):
    """As imagens carregadas para esta gfx, ou None se não der (aí a tela usa vetores)."""
    if _cache.get("gfx") is not gfx:
        art = None
        try:
            if getattr(gfx, "available", True) is not False:
                with open(os.path.join(DIR, "indice.json"), encoding="utf-8") as f:
                    art = Art(gfx, json.load(f))
        except (IOError, OSError, ValueError, KeyError, AttributeError):
            art = None
        _cache.update(gfx=gfx, art=art)
    return _cache["art"]
