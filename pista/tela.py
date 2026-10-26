"""A tela: vetores de alto contraste que acompanham o som. Nada aqui é só visual;
tudo o que aparece também é dito ou tocado.

Desenha em 640x480. O patinador fica à esquerda e os obstáculos chegam da direita.
"""
import math

from . import config as C
from . import sprites
from .cenarios import KIND_INFO, SCENARIOS
from .corrida import multiplier

W, H = 640, 480
GROUND = 372
FEET = sprites.FEET
SKATER_X = 150
PX_PER_SEC = 150          # a 3 s de distância o obstáculo entra pela borda direita
SHOW_SECONDS = 3.0
PLATE = (0, 0, 0, 120)     # fundo translúcido atrás dos textos, para o contraste não depender do cenário

_scroll = {"t": 0.0, "pos": 0.0}

WHITE, BLACK = "#ffffff", "#000000"
YELLOW, ORANGE, RED, CYAN, GREEN = "#ffd23f", "#ff8a00", "#ff3b3b", "#35e0ff", "#5dff7e"

# cor do céu, do chão, da faixa de fundo e dos detalhes de cada cenário
PALETTES = {
    "praca": {"sky": "#0f3d2e", "ground": "#1c1c1c", "far": "#1f6b4a", "mark": "#d9f2c4"},
    "rua": {"sky": "#1a2340", "ground": "#222222", "far": "#33406e", "mark": "#ffd23f"},
    "estacionamento": {"sky": "#2a1a3d", "ground": "#1b1b1b", "far": "#4c3270", "mark": "#ffffff"},
    "escola": {"sky": "#3d2a0f", "ground": "#1f1a14", "far": "#7a5424", "mark": "#fff1b0"},
}
BUTTON_HINT = {"pular": "B", "freada": "BAIXO", "rampa": "CIMA", "corrimao": "B e segure A",
               "escada": "X (segure)", "curva_esq": "ESQUERDA (segure)", "curva_dir": "DIREITA (segure)"}
ACTION_WORD = {"pular": "PULE", "freada": "FREIE", "rampa": "RAMPA", "corrimao": "CORRIMÃO",
               "escada": "ESCADA", "curva_esq": "CURVA", "curva_dir": "CURVA"}

_fonts = {}


def font(gfx, size):
    if size not in _fonts:
        _fonts[size] = gfx.font(None, size)
    return _fonts[size]


def text(gfx, s, x, y, size=24, color=WHITE, align="left", shadow=True):
    f = font(gfx, size)
    if shadow:
        gfx.text(s, x + 2, y + 2, font=f, color=BLACK, align=align)
    gfx.text(s, x, y, font=f, color=color, align=align)


def draw(gfx, run, menu=None, caption="", scenario=0, now=0.0):
    """run: a corrida em andamento ou None; menu: o menu aberto ou None."""
    sid = SCENARIOS[(run.scenario if run else scenario) % len(SCENARIOS)]["id"]
    pal = PALETTES[sid]
    t = run.t if run else now
    speed = run.speed if run else 1.0
    art = sprites.load(gfx)
    dt = t - _scroll["t"]
    _scroll["t"] = t
    if 0 < dt < 1.0:
        _scroll["pos"] += dt * PX_PER_SEC * speed
    if art:
        art.background(gfx, sid, _scroll["pos"])
    else:
        background(gfx, pal, t, speed)
    if run is not None:
        world(gfx, run, pal, art, sid)
        hud(gfx, run, art)
    else:
        if art:
            gfx.rect(0, 8, W, 84, color=PLATE)
        text(gfx, "ROLÊ", W // 2, 14, 72, YELLOW, "center")
        if art:
            art.skater_draw(gfx, SKATER_X + 60, 0, "roll", int(t * 9) % 4, False)
        else:
            skater(gfx, SKATER_X + 60, GROUND, "rodas", t, speed)
    if menu is not None:
        menu_box(gfx, menu)
    if caption:
        gfx.rect(0, H - 26, W, 26, color=(0, 0, 0, 170))
        text(gfx, caption[:78], W // 2, H - 24, 18, WHITE, "center", shadow=False)


# --- cenário -----------------------------------------------------------------
def background(gfx, pal, t, speed):
    gfx.clear(pal["sky"])
    # prédios ou árvores ao fundo, rolando devagar
    shift = (t * 25 * speed) % 160
    for i in range(-1, 6):
        x = i * 160 - shift
        h = 90 + (i * 37) % 70
        gfx.rect(x, GROUND - h - 30, 110, h + 30, color=pal["far"])
    gfx.rect(0, GROUND, W, H - GROUND, color=pal["ground"])
    gfx.line(0, GROUND, W, GROUND, color=pal["mark"], width=4)
    # marcas no chão dão a sensação de velocidade
    shift = (t * 220 * speed) % 90
    for i in range(-1, 9):
        gfx.rect(i * 90 - shift, GROUND + 38, 46, 6, color=pal["mark"])


def world(gfx, run, pal, art=None, sid="praca"):
    for o in reversed(run.obstacles):
        x = SKATER_X + (o.at - run.t) * PX_PER_SEC * run.speed
        if x > W + 80:
            continue
        if art:
            top = art.obstacle(gfx, o.kind, sid, x)
            art.beat_dots(gfx, x, 172, o.cues)
            gfx.rect(x - 90, FEET + 22, 180, 26, color=PLATE)
            text(gfx, o.name, x, FEET + 24, 20, WHITE, "center")
        else:
            obstacle(gfx, o, x, pal)
    pose = run.pose
    lift = 0.0
    spin = 0.0
    if pose in ("ar", "rampa"):
        p = run.air_progress
        lift = 4 * p * (1 - p) * (150 if pose == "rampa" else 80)
    name, at = run.last_trick
    if run.t - at < C.TRICK_TIME and pose in ("ar", "rampa"):
        spin = (run.t - at) / C.TRICK_TIME * 360 * (-1 if name == "left" else 1)
    if pose == "salto_corrimao":
        lift = 60
    if art and pose == "corrimao":
        lift = 74
        art.obstacle(gfx, "corrimao", sid, SKATER_X)
    elif art and pose == "escada":
        left = run.hold_left or 0.0
        lift = 120 * left
        art.obstacle(gfx, "escada", sid, SKATER_X + 40)
    if art:
        sname, n, flip = art.skater_frame(run, run.t)
        art.skater_draw(gfx, SKATER_X, lift, sname, n, flip)
        art.effects(gfx, run, SKATER_X, lift, run.t)
    else:
        skater(gfx, SKATER_X, GROUND - lift, pose, run.t, run.speed, spin, getattr(run, "_hold", None))
        if pose == "queda":
            for i in range(4):
                a = run.t * 6 + i * 1.57
                gfx.circle(SKATER_X + 28 * math.cos(a), GROUND - 80 + 12 * math.sin(a), 6, color=YELLOW)
    if name is not None or at > 0:
        if 0 <= run.t - at < 1.0 and run.last_trick[1] > 0:
            text(gfx, C.TRICK_NAMES[name], SKATER_X + 40, max(190, GROUND - lift - 150), 30, CYAN, "left")


def obstacle(gfx, o, x, pal):
    kind = o.kind
    g = GROUND
    if kind == "pular":
        gfx.rect(x - 40, g - 46, 80, 14, color=ORANGE)
        for dx in (-32, 26):
            gfx.rect(x + dx, g - 32, 8, 32, color=ORANGE)
    elif kind == "freada":
        gfx.polygon([(x - 26, g - 80), (x + 26, g - 80), (x + 40, g - 108), (x + 40, g - 134),
                     (x + 26, g - 160), (x - 26, g - 160), (x - 40, g - 134), (x - 40, g - 108)],
                    color=RED)
        text(gfx, "!", x, g - 160, 64, WHITE, "center")
        gfx.rect(x - 4, g - 80, 8, 80, color=WHITE)
    elif kind == "rampa":
        gfx.polygon([(x - 50, g), (x + 50, g), (x + 50, g - 90)], color=CYAN)
    elif kind == "corrimao":
        gfx.line(x - 60, g - 62, x + 60, g - 62, color=YELLOW, width=8)
        for dx in (-54, 54):
            gfx.line(x + dx, g - 62, x + dx, g, color=YELLOW, width=6)
    elif kind == "escada":
        for i in range(5):
            gfx.rect(x - 60 + i * 24, g - 100 + i * 20, 24, 100 - i * 20, color=GREEN)
    else:  # curva_esq, curva_dir
        left = kind == "curva_esq"
        d = -1 if left else 1
        gfx.line(x - 40 * d, g - 40, x + 40 * d, g - 40, color=ORANGE, width=12)
        gfx.polygon([(x + 40 * d, g - 72), (x + 80 * d, g - 40), (x + 40 * d, g - 8)], color=ORANGE)
    # os pontos das batidas: acendem a cada aviso; a terceira é a hora e é maior
    for i in range(C.WARN_BEATS + 1):
        cx = x + (i - C.WARN_BEATS / 2) * 38
        last = i == C.WARN_BEATS
        r = 17 if last else 11
        gfx.circle(cx, g - 200, r, color=YELLOW if i < o.cues else "#444444", fill=True)
        if last:
            gfx.circle(cx, g - 200, r + 4, color=WHITE, fill=False)
    text(gfx, o.name, x, g + 56, 20, WHITE, "center")


# --- patinador ------------------------------------------------------------------
def rot(points, angle, cx, cy):
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (px - cx) * ca - (py - cy) * sa, cy + (px - cx) * sa + (py - cy) * ca)
            for px, py in points]


def skater(gfx, x, y, pose, t, speed, spin=0.0, hold=None):
    """Figura de palitos grossos. (x, y) é o ponto do chão sob os pés."""
    stride = math.sin(t * 9 * speed)
    lean = 0.0
    legs = [((-10, 0), (-14 + 14 * stride, -40), (-8, -62)), ((10, 0), (14 - 14 * stride, -40), (8, -62))]
    torso = ((0, -62), (0, -112))
    head = (0, -128)
    arms = [((0, -104), (-26, -86 - 8 * stride)), ((0, -104), (26, -86 + 8 * stride))]
    tilt = 0.0
    if pose == "queda":
        tilt = 90
        arms = [((0, -104), (-30, -120)), ((0, -104), (30, -120))]
        legs = [((-10, 0), (-20, -40), (-8, -62)), ((10, 0), (20, -40), (8, -62))]
        y += 6
    elif pose in ("ar", "rampa", "salto_corrimao"):
        legs = [((-10, -4), (-18, -34), (-8, -62)), ((10, -4), (18, -34), (8, -62))]
        arms = [((0, -104), (-36, -110)), ((0, -104), (36, -110))]
    elif pose == "freada":
        tilt = -18
        legs = [((-16, 0), (-20, -34), (-8, -62)), ((26, 0), (22, -36), (8, -62))]
        arms = [((0, -104), (-34, -96)), ((0, -104), (34, -100))]
        for i in range(4):
            gfx.line(x - 20 - i * 26, y - 4 - i, x - 60 - i * 26, y - 4 - i, color=WHITE, width=3)
    elif pose == "corrimao":
        legs = [((-14, -6), (-16, -38), (-8, -60)), ((14, -6), (16, -38), (8, -60))]
        for i in range(6):
            a = t * 40 + i * 1.3
            gfx.line(x + 10, y - 4, x + 10 + 18 * math.cos(a) - 6, y - 4 - 12 * abs(math.sin(a)) - 2,
                     color=YELLOW, width=2)
        gfx.line(x - 70, y + 2, x + 70, y + 2, color=YELLOW, width=6)
    elif pose == "escada":
        tilt = 16
        legs = [((-12, 0), (-16, -34), (-8, -60)), ((12, 0), (16, -34), (8, -60))]
    elif pose in ("curva_esq", "curva_dir"):
        tilt = -22 if pose == "curva_esq" else 22
        legs = [((-12, 0), (-16, -36), (-8, -62)), ((12, 0), (16, -36), (8, -62))]
    body = [legs[0], legs[1], torso, arms[0], arms[1]]
    ang = tilt + spin
    pivot = (0, -60)
    parts = []
    for seg in body:
        pts = rot([(px, py) for px, py in seg], ang, *pivot)
        parts.append([(x + px, y + py) for px, py in pts])
    hx, hy = rot([head], ang, *pivot)[0]
    for pts in parts:
        gfx.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1], color=WHITE, width=9)
        if len(pts) > 2:
            gfx.line(pts[1][0], pts[1][1], pts[2][0], pts[2][1], color=WHITE, width=9)
    gfx.circle(x + hx, y + hy, 17, color=YELLOW, fill=True)       # capacete
    gfx.circle(x + hx + 6, y + hy + 2, 5, color=BLACK, fill=True)  # óculos
    # patins: um bloco e duas rodas
    for sx in (-10, 10):
        fx, fy = rot([(sx, 0)], ang, *pivot)[0]
        gfx.rect(x + fx - 12, y + fy - 7, 24, 7, color=RED)
        gfx.circle(x + fx - 7, y + fy + 3, 4, color=BLACK, fill=True)
        gfx.circle(x + fx + 7, y + fy + 3, 4, color=BLACK, fill=True)


# --- painel -------------------------------------------------------------------------
def hud(gfx, run, art=None):
    if art:
        gfx.rect(0, 0, W, 86, color=PLATE)
    text(gfx, "%d" % run.score, 16, 8, 48, WHITE)
    mult = multiplier(run.combo)
    text(gfx, "COMBO %d   x%d" % (run.combo, mult), 16, 62, 28, YELLOW if run.combo else "#c8c8c8")
    for i in range(C.LIVES):
        if art:
            art.ui_piece(gfx, "coracao" if i < run.lives else "coracao_vazio", W - 48 - i * 44, 12)
        else:
            gfx.circle(W - 28 - i * 40, 32, 15, color=RED if i < run.lives else "#444444", fill=True)
    from .corrida import layers_for
    layers = layers_for(run.combo)
    for i in range(5):
        gfx.rect(W - 28 - 4 * 38 + i * 38 - 15, 62, 30, 12, color=CYAN if i < layers else "#444444")
    # o que fazer agora: o próximo obstáculo e o botão
    nxt = run.obstacles[0] if run.obstacles else None
    left = run.hold_left
    if left is not None:
        hold = run._hold
        prompt = "SEGURE " + {"corrimao": "A", "escada": "X", "freada": "BAIXO",
                              "curva_esq": "ESQUERDA", "curva_dir": "DIREITA"}[hold["kind"]]
        if hold["kind"] == "freada":
            if hold.get("got"):
                prompt = "SEGURE BAIXO E " + ("ESQUERDA" if hold["side"] == "left" else "DIREITA")
            elif run.t >= hold["at"]:
                prompt = "ESCOLHA O LADO: " + ("ESQUERDA" if hold["side"] == "left" else "DIREITA")
        if art:
            gfx.rect(20, 100, W - 40, 46, color=PLATE)
        text(gfx, prompt, W // 2, 108, 40, GREEN, "center")
        gfx.rect(120, 156, 400, 18, color="#333333")
        gfx.rect(120, 156, 400 * left, 18, color=GREEN)
    elif nxt is not None and nxt.at - run.t < SHOW_SECONDS:
        if art:
            gfx.rect(120, 102, W - 240, 40, color=PLATE)
        text(gfx, "%s: %s" % (ACTION_WORD[nxt.kind], BUTTON_HINT[nxt.kind]), W // 2, 108, 34, ORANGE, "center")
    if run.over:
        gfx.rect(0, 0, W, H, color=(0, 0, 0, 150))
        text(gfx, "FIM DA CORRIDA", W // 2, 170, 56, RED, "center")
        text(gfx, "%d pontos" % run.score, W // 2, 250, 44, WHITE, "center")
    elif run.t < run._fall_until:
        gfx.rect(0, 0, W, H, color=(255, 0, 0, 40))
        text(gfx, "TOMBO", W // 2, 200, 72, RED, "center")


def menu_box(gfx, menu):
    gfx.rect(60, 110, W - 120, 300, color=(0, 0, 0, 215))
    text(gfx, menu.title, W // 2, 118, 40, YELLOW, "center")
    items = menu.items
    first = max(0, min(menu.index - 2, len(items) - 5))
    for row, i in enumerate(range(first, min(len(items), first + 5))):
        y = 170 + row * 46
        if i == menu.index:
            gfx.rect(80, y - 4, W - 160, 44, color="#2d5bff")
        text(gfx, items[i], W // 2, y, 32, WHITE if i == menu.index else "#b0b0b0", "center", shadow=False)
