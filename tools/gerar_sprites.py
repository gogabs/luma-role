#!/usr/bin/env python3
"""Gera os sprites do jogo (pixel art) em sprites/, por código, com o Pillow.

Nada aqui é desenhado à mão nem baixado: o patinador é um esqueleto de ossos que
vira quadros diferentes (rolando, salto, giro, freada, grind, degraus, curva, queda),
e os obstáculos e cenários saem de formas simples com paleta por fase. O jogo
amplia tudo por 3 e a SDL usa o vizinho mais próximo, então os pixels ficam nítidos.

    python3 tools/gerar_sprites.py             # sprites/*.png
    python3 tools/gerar_sprites.py --previa    # também previa-sprites/ ampliado
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PIL import Image

from pixel import OUTLINE, Canvas, lerp, rgba, shade, vgradient

OUT = os.path.join(HERE, "..", "sprites")
CELL = 48                      # o quadro do patinador, em pixels nativos
SKIN, SHIRT, SHORTS = "#f0b58a", "#27a9e1", "#34388f"
HELMET, BOOT, WHEEL = "#ff8a3d", "#f4f1ea", "#e8453c"


def pt(x, y):
    return (round(x), round(y))


def limb(c, a, b, color, width=3):
    c.line(pt(*a), pt(*b), OUTLINE, width + 2)
    c.line(pt(*a), pt(*b), color, width)


def skater(pose):
    """Um quadro do patinador. pose é um dicionário de ângulos e posições (em px nativos),
    com origem no chão sob os pés, centro horizontal da célula."""
    c = Canvas(CELL, CELL)
    ox, oy = CELL // 2, CELL - 6                 # o chão
    hip = (ox + pose.get("hx", 0), oy - pose.get("hy", 17))
    lean = math.radians(pose.get("lean", 0))
    torso_len, thigh, shin = 12, 8, 8
    shoulder = (hip[0] + math.sin(lean) * torso_len, hip[1] - math.cos(lean) * torso_len)
    head = (shoulder[0] + math.sin(lean) * 5, shoulder[1] - math.cos(lean) * 5)

    def leg(spec):
        knee_a, foot_a = math.radians(spec[0]), math.radians(spec[1])
        knee = (hip[0] + math.sin(knee_a) * thigh, hip[1] + math.cos(knee_a) * thigh)
        foot = (knee[0] + math.sin(foot_a) * shin, knee[1] + math.cos(foot_a) * shin)
        return knee, foot

    def arm(spec):
        elbow_a, hand_a = math.radians(spec[0]), math.radians(spec[1])
        elbow = (shoulder[0] + math.sin(elbow_a) * 6, shoulder[1] + math.cos(elbow_a) * 6)
        hand = (elbow[0] + math.sin(hand_a) * 6, elbow[1] + math.cos(hand_a) * 6)
        return elbow, hand

    back_leg, front_leg = pose.get("legs", ((-10, -6), (12, 8)))
    back_arm, front_arm = pose.get("arms", ((-50, -70), (50, 70)))
    # trás: perna e braço do fundo, em tom mais escuro
    for spec, tone in ((back_leg, 0.75),):
        knee, foot = leg(spec)
        limb(c, hip, knee, shade(SHORTS, tone), 4)
        limb(c, knee, foot, shade(SKIN, tone), 3)
        skate(c, foot, tone)
    elbow, hand = arm(back_arm)
    limb(c, shoulder, elbow, shade(SHIRT, 0.75), 3)
    limb(c, elbow, hand, shade(SKIN, 0.75), 2)
    # tronco
    c.line(pt(*hip), pt(*shoulder), OUTLINE, 8)
    c.line(pt(*hip), pt(*shoulder), SHIRT, 6)
    c.line(pt(hip[0], hip[1]), pt(hip[0] + math.sin(lean) * 3, hip[1] - math.cos(lean) * 3), SHORTS, 6)
    # frente
    knee, foot = leg(front_leg)
    limb(c, hip, knee, SHORTS, 4)
    limb(c, knee, foot, SKIN, 3)
    skate(c, foot, 1.0)
    elbow, hand = arm(front_arm)
    limb(c, shoulder, elbow, SHIRT, 3)
    limb(c, elbow, hand, SKIN, 2)
    # cabeça com capacete e rosto
    hx, hy = head
    c.circle(round(hx), round(hy), 5, OUTLINE)
    c.circle(round(hx), round(hy), 4, SKIN)
    c.rect(round(hx) - 4, round(hy) - 5, 9, 4, HELMET)
    c.rect(round(hx) - 5, round(hy) - 3, 3, 3, HELMET)
    c.px(round(hx) + 2, round(hy), OUTLINE)
    c.px(round(hx) + 2, round(hy) + 2, shade(SKIN, 0.7))
    return c


def skate(c, foot, tone):
    x, y = round(foot[0]), round(foot[1])
    c.rect(x - 4, y - 3, 9, 4, OUTLINE)
    c.rect(x - 3, y - 3, 7, 3, shade(BOOT, tone))
    c.rect(x - 4, y + 1, 9, 2, OUTLINE)
    for wx in (x - 3, x + 2):
        c.rect(wx - 1, y + 1, 3, 3, OUTLINE)
        c.rect(wx, y + 1, 1, 2, shade(WHEEL, tone))


def roll_frames():
    out = []
    for i in range(4):
        a = i / 4 * 2 * math.pi
        s = math.sin(a)
        out.append(skater({"hy": 16 + (1 if i % 2 else 0), "lean": 8,
                           "legs": ((-14 * s - 4, -6 * s - 4), (14 * s + 4, 6 * s + 4)),
                           "arms": ((-40 * s - 20, -60 * s - 40), (40 * s + 20, 60 * s + 40))}))
    return out


def air_frames():
    """0 agachar para saltar, 1 subindo, 2 no ponto mais alto, 3 descendo, 4 amortecendo."""
    return [
        skater({"hy": 12, "lean": 20, "legs": ((-35, -5), (30, 10)), "arms": ((-60, -80), (60, 90))}),
        skater({"hy": 16, "lean": 8, "legs": ((-8, -2), (14, 8)), "arms": ((-80, -100), (80, 100))}),
        skater({"hy": 15, "lean": 0, "legs": ((-14, 4), (14, -4)), "arms": ((-100, -120), (100, 120))}),
        skater({"hy": 17, "lean": -6, "legs": ((-6, 0), (6, 0)), "arms": ((-70, -90), (70, 90))}),
        skater({"hy": 13, "lean": 14, "legs": ((-30, 0), (30, 0)), "arms": ((-50, -70), (50, 70))}),
    ]


def spin_frames(base):
    out = []
    for k in range(8):
        im = base.img.rotate(-45 * k, resample=Image.NEAREST, center=(CELL // 2, CELL - 20))
        c = Canvas(CELL, CELL)
        c.img = im
        out.append(c)
    return out


def special_frames():
    brake = [skater({"hy": 14, "lean": -20, "legs": ((-25, -8), (45, 30)), "arms": ((-60, -80), (30, 50))}),
             skater({"hy": 14, "lean": -24, "legs": ((-28, -10), (50, 34)), "arms": ((-70, -90), (40, 60))})]
    grind = [skater({"hy": 11, "lean": 12, "legs": ((-30, -4), (36, 4)), "arms": ((-80, -95), (70, 90))}),
             skater({"hy": 12, "lean": 14, "legs": ((-32, -6), (34, 6)), "arms": ((-85, -100), (75, 95))})]
    stairs = [skater({"hy": 15, "lean": 22, "legs": ((-10, -4), (16, 10)), "arms": ((-60, -80), (60, 80))}),
              skater({"hy": 13, "lean": 26, "legs": ((-14, -6), (20, 12)), "arms": ((-70, -90), (70, 90))})]
    lean_l = skater({"hy": 15, "lean": -22, "legs": ((-14, -6), (10, 4)), "arms": ((-90, -100), (30, 60))})
    lean_r = skater({"hy": 15, "lean": 24, "legs": ((-8, -2), (16, 8)), "arms": ((-30, -60), (90, 100))})
    fall = []
    for k, ang in enumerate((40, 80)):
        base = skater({"hy": 14, "lean": 30, "legs": ((-40, -30), (50, 40)), "arms": ((-100, -120), (110, 130))})
        im = base.img.rotate(-ang, resample=Image.NEAREST, center=(CELL // 2, CELL - 20))
        c = Canvas(CELL, CELL)
        c.img = im
        fall.append(c)
    lying = Canvas(CELL, CELL)
    lying.paste(skater({"hy": 14, "lean": 30, "legs": ((-40, -30), (50, 40)),
                        "arms": ((-100, -120), (110, 130))}).img.rotate(-88, resample=Image.NEAREST,
                                                                          center=(CELL // 2, CELL - 14)), 0, 4)
    fall.append(lying)
    return brake, grind, stairs, lean_l, lean_r, fall


def build_skater_sheet():
    rolls = roll_frames()
    air = air_frames()
    spins = spin_frames(air[2])
    brake, grind, stairs, lean_l, lean_r, fall = special_frames()
    frames = rolls + air + spins + brake + grind + stairs + [lean_l, lean_r] + fall
    cols = 8
    rows = (len(frames) + cols - 1) // cols
    sheet = Canvas(cols * CELL, rows * CELL)
    for i, f in enumerate(frames):
        sheet.paste(f, (i % cols) * CELL, (i // cols) * CELL)
    index = {"roll": 0, "air": 4, "spin": 9, "brake": 17, "grind": 19, "stairs": 21,
             "lean_l": 23, "lean_r": 24, "fall": 25}
    return sheet, cols, index


# --- obstáculos ------------------------------------------------------------------
def bench(pal):
    c = Canvas(48, 22)
    wood, dark = pal.get("wood", "#c8803c"), pal.get("dark", "#7a4a22")
    for lx in (5, 38):
        c.rect(lx, 12, 4, 9, "#3a3a46")
    c.rect(1, 9, 46, 4, dark)
    c.rect(1, 6, 46, 3, wood)
    c.rect(1, 2, 46, 3, wood)
    c.rect(1, 2, 46, 1, shade(wood, 1.25))
    c.outline()
    return c


def bin_fallen(pal):
    c = Canvas(34, 20)
    c.rect(4, 4, 24, 14, "#4a9c5e")
    c.rect(4, 4, 24, 3, "#6bc27f")
    c.ellipse(26, 4, 32, 17, "#2f6e41")
    c.rect(8, 8, 16, 2, "#2f6e41")
    c.rect(0, 14, 5, 3, "#6bc27f")
    c.outline()
    return c


def cone(pal):
    c = Canvas(18, 24)
    c.poly([(9, 1), (15, 18), (3, 18)], "#ff7a1a")
    c.poly([(9, 1), (11, 7), (7, 7)], "#ff7a1a")
    c.poly([(7, 8), (11, 8), (12, 12), (6, 12)], "#ffffff")
    c.rect(1, 18, 16, 4, "#3a3a46")
    c.outline()
    return c


def backpack(pal):
    c = Canvas(26, 22)
    c.rect(3, 4, 20, 16, "#e0457b")
    c.rect(3, 4, 20, 4, "#ff7aa8")
    c.rect(7, 12, 12, 6, "#a02a58")
    c.rect(9, 1, 8, 4, "#a02a58")
    c.rect(11, 13, 4, 2, "#ffd23f")
    c.outline()
    return c


def pigeons(pal):
    c = Canvas(44, 18)
    for x, h in ((3, 0), (17, 1), (31, 0)):
        c.ellipse(x, 6 + h, x + 11, 15 + h, "#a8adb8")
        c.ellipse(x + 7, 3 + h, x + 13, 9 + h, "#c9cedb")
        c.px(x + 11, 5 + h, "#1a1423")
        c.px(x + 13, 6 + h, "#ffb347")
        c.rect(x + 2, 12 + h, 5, 3, "#7d8290")
        c.px(x + 4, 16 + h, "#ff9aa2")
        c.px(x + 7, 16 + h, "#ff9aa2")
    c.outline()
    return c


def pedestrian(pal):
    c = Canvas(30, 44)
    c.rect(2, 41, 26, 3, "#ffffff")
    c.circle(15, 7, 5, "#f0b58a")
    c.rect(10, 1, 11, 4, "#5a3a22")
    c.rect(9, 13, 13, 15, pal.get("shirt", "#e8453c"))
    c.rect(9, 28, 5, 13, "#34388f")
    c.rect(16, 28, 5, 13, "#34388f")
    c.rect(5, 14, 4, 11, "#f0b58a")
    c.rect(22, 14, 4, 11, "#f0b58a")
    c.outline()
    return c


def car(pal):
    c = Canvas(66, 30)
    c.rect(2, 12, 62, 12, pal.get("body", "#d9334a"))
    c.poly([(14, 12), (22, 3), (44, 3), (54, 12)], pal.get("body", "#d9334a"))
    c.poly([(18, 11), (24, 5), (32, 5), (32, 11)], "#bfe7ff")
    c.poly([(35, 11), (35, 5), (43, 5), (50, 11)], "#bfe7ff")
    c.rect(60, 15, 4, 4, "#fff2a0")
    c.rect(2, 15, 3, 4, "#ff6a5a")
    for wx in (14, 48):
        c.circle(wx, 24, 6, "#1a1423")
        c.circle(wx, 24, 3, "#c9cedb")
    c.outline()
    return c


def kids(pal):
    c = Canvas(40, 36)
    for x, shirt in ((3, "#ffd23f"), (22, "#5dd6a0")):
        c.circle(x + 7, 6, 4, "#f0b58a")
        c.rect(x + 3, 1, 9, 3, "#2a1e17")
        c.rect(x + 3, 11, 9, 12, shirt)
        c.rect(x + 3, 23, 4, 11, "#34388f")
        c.rect(x + 8, 23, 4, 11, "#34388f")
        c.rect(x, 12, 3, 9, "#f0b58a")
        c.rect(x + 12, 12, 3, 9, "#f0b58a")
    c.outline()
    return c


def ramp(pal):
    c = Canvas(60, 34)
    top, side = pal.get("top", "#b9bfca"), pal.get("side", "#7d8493")
    c.poly([(1, 32), (58, 32), (58, 3)], top)
    c.poly([(1, 32), (58, 32), (58, 24)], side)
    c.line((1, 32), (58, 3), shade(top, 1.2), 1)
    for i in range(1, 6):
        c.line((i * 9, 32), (i * 9, 31 - i * 4), side, 1)
    c.rect(56, 3, 3, 29, side)
    if pal.get("stripe"):
        c.poly([(40, 32), (47, 32), (58, 16), (58, 9)], pal["stripe"])
    c.outline()
    return c


def rail(pal):
    c = Canvas(70, 30)
    metal, shine = pal.get("metal", "#c9cedb"), "#ffffff"
    for px in (6, 63):
        c.rect(px, 8, 3, 21, shade(metal, 0.7))
    c.rect(1, 6, 68, 4, metal)
    c.rect(1, 6, 68, 1, shine)
    c.rect(1, 14, 68, 2, shade(metal, 0.8))
    for px in range(10, 62, 8):
        c.rect(px, 16, 2, 13, shade(metal, 0.75))
    c.outline()
    return c


def stairs(pal):
    c = Canvas(66, 44)
    top, front = pal.get("top", "#c9cedb"), pal.get("front", "#8c93a3")
    for i in range(5):
        x, y = 1 + i * 12, 4 + i * 8
        c.rect(x, y, 12, 3, top)
        c.rect(x, y + 3, 12, 40 - y - 3, front)
    c.outline()
    return c


def sign(pal):
    """Placa de curva à esquerda; a da direita é a mesma espelhada."""
    c = Canvas(34, 52)
    c.rect(15, 22, 4, 29, "#6a7080")
    c.rect(1, 2, 32, 21, "#1d6fd8")
    c.rect(2, 3, 30, 19, "#2d86f0")
    c.poly([(5, 12), (13, 5), (13, 19)], "#ffffff")
    c.rect(13, 9, 15, 7, "#ffffff")
    c.outline()
    return c


SCENE_PALS = {
    "praca": {"bench": {"wood": "#c8803c"}, "ramp": {"top": "#b9bfca", "side": "#7d8493"},
              "rail": {"metal": "#c9cedb"}, "stairs": {"top": "#cfc7b4", "front": "#9a9179"}, "ped": {"shirt": "#e8453c"}},
    "rua": {"ramp": {"top": "#d8a24a", "side": "#9a6d2a", "stripe": "#2b2b33"}, "rail": {"metal": "#e0b34a"},
            "stairs": {"top": "#d2b48a", "front": "#9a7c55"}, "ped": {"shirt": "#2f7be0"}},
    "estacionamento": {"ramp": {"top": "#9aa0ad", "side": "#6a7080", "stripe": "#ffd23f"},
                       "rail": {"metal": "#ffd23f"}, "stairs": {"top": "#a9b0bd", "front": "#6a7080"},
                       "car": {"body": "#d9334a"}},
    "escola": {"ramp": {"top": "#7fb6e8", "side": "#4f85b8"}, "rail": {"metal": "#5dd6a0"},
               "stairs": {"top": "#e6cfa4", "front": "#b89e6c"}},
}


def build_obstacles():
    """Cada obstáculo é um quadro; o índice diz onde cada um está na folha."""
    items = []   # (nome, canvas)
    items += [("pular_praca", bench(SCENE_PALS["praca"].get("bench", {}))),
              ("pular_rua", bin_fallen({})), ("pular_estacionamento", cone({})),
              ("pular_escola", backpack({})),
              ("freada_praca", pigeons({})), ("freada_rua", pedestrian({"shirt": "#e8453c"})),
              ("freada_estacionamento", car({"body": "#d9334a"})), ("freada_escola", kids({}))]
    for sc in ("praca", "rua", "estacionamento", "escola"):
        pal = SCENE_PALS[sc]
        items.append(("rampa_" + sc, ramp(pal["ramp"])))
        items.append(("escada_" + sc, stairs(pal["stairs"])))
        items.append(("corrimao_" + sc, rail(pal["rail"])))
    items.append(("curva", sign({})))
    cw = max(c.w for _, c in items) + 2
    ch = max(c.h for _, c in items) + 2
    cols = 6
    rows = (len(items) + cols - 1) // cols
    sheet = Canvas(cols * cw, rows * ch)
    index = {}
    for i, (name, c) in enumerate(items):
        x, y = (i % cols) * cw + 1, (i // cols) * ch + 1
        sheet.paste(c, x, y)
        index[name] = (x, y, c.w, c.h)
    return sheet, index


# --- cenários em camadas (216 px nativos de largura, que repetem sem emenda) ---------
TILE = 216              # 216 x 3 = 648 px: um pouco mais que a tela de 640
SKY_H, GROUND_Y, SCREEN_H = 124, 124, 160


def wrap_do(draw, x, w):
    """Chama draw(x) e as cópias deslocadas por TILE, para o que passa da borda voltar pelo outro lado."""
    for dx in (-TILE, 0, TILE):
        if -w < x + dx < TILE:
            draw(x + dx)


def sky(top, bottom, sun=None):
    c = Canvas(TILE, SKY_H)
    vgradient(c, top, bottom, 9)
    if sun:
        c.circle(sun[0], sun[1], sun[2], sun[3])
        c.circle(sun[0], sun[1], sun[2] - 3, shade(sun[3], 1.12))
    return c


def clouds(seed, tone="#ffffff"):
    import random
    r = random.Random(seed)
    c = Canvas(TILE, 50)
    for i in range(4):
        x, y = i * 54 + r.randint(0, 20), r.randint(6, 28)
        w = r.randint(22, 34)

        def draw(px, y=y, w=w):
            c.ellipse(px, y + 4, px + w, y + 12, tone)
            c.ellipse(px + 5, y, px + w - 8, y + 10, tone)
            c.ellipse(px + 12, y - 2, px + w - 2, y + 8, tone)
        wrap_do(draw, x, w)
    return c


def hills(seed, base, light, height=60, trees=None):
    import random
    r = random.Random(seed)
    c = Canvas(TILE, height + 10)
    ph1, ph2 = r.random() * 6, r.random() * 6
    for x in range(TILE):
        t = x / TILE * 2 * math.pi
        top = height - 20 - 10 * math.sin(t + ph1) - 6 * math.sin(2 * t + ph2) - 4 * math.sin(3 * t)
        c.rect(x, int(top), 1, c.h - int(top), base)
        c.px(x, int(top), light)
        c.px(x, int(top) + 1, light)
    if trees:
        for i in range(10):
            x = i * 22 + r.randint(0, 10)
            y = height - 2 - r.randint(0, 6)

            def draw(px, y=y):
                c.rect(px + 2, y - 5, 2, 5, trees[1])
                c.circle(px + 3, y - 8, 5, trees[0])
            wrap_do(draw, x, 8)
    return c


def skyline(seed, body, window, floor=70, lit=0.35):
    import random
    r = random.Random(seed)
    c = Canvas(TILE, floor)
    x = 0
    while x < TILE:
        w = min(r.randint(16, 30), TILE - x)
        h = r.randint(28, floor - 6)
        c.rect(x, floor - h, w, h, body)
        c.rect(x, floor - h, w, 2, shade(body, 1.25))
        for wy in range(floor - h + 5, floor - 4, 6):
            for wx in range(x + 3, x + w - 3, 5):
                if r.random() < lit:
                    c.rect(wx, wy, 2, 3, window)
        x += w + r.randint(0, 3)
    return c


def trees_row(seed, canopy, trunk, floor=56):
    import random
    r = random.Random(seed)
    c = Canvas(TILE, floor)
    for i in range(5):
        x = 4 + i * 43 + r.randint(-4, 4)
        tall = r.randint(24, 36)

        def draw(px, tall=tall):
            c.rect(px + 9, floor - tall // 2, 4, tall // 2, trunk)
            c.circle(px + 11, floor - tall + 2, 11, shade(canopy, 0.85))
            c.circle(px + 7, floor - tall + 5, 8, canopy)
            c.circle(px + 15, floor - tall + 5, 8, canopy)
            c.circle(px + 10, floor - tall - 2, 6, shade(canopy, 1.15))
        wrap_do(draw, x, 24)
    for i in range(4):                                       # postes de luz
        x = 20 + i * 54

        def lamp(px):
            c.rect(px, floor - 34, 2, 34, "#3a3a46")
            c.rect(px - 3, floor - 36, 8, 3, "#ffe9a8")
        wrap_do(lamp, x, 6)
    for i in range(6):                                       # arbustos
        x = 8 + i * 36

        def bush(px):
            c.ellipse(px, floor - 9, px + 14, floor, "#3f9a56")
            c.ellipse(px + 6, floor - 11, px + 20, floor, "#59b868")
        wrap_do(bush, x, 22)
    return c


def shops(seed, floor=56):
    import random
    r = random.Random(seed)
    c = Canvas(TILE, floor)
    palette = ["#e8453c", "#2d86f0", "#ffd23f", "#5dd6a0", "#c06bd6", "#ff8a3d"]
    x = 0
    while x < TILE:
        w = 36 if x + 36 <= TILE else TILE - x
        wall = r.choice(["#d9c3a5", "#b8c4e0", "#e6b8a8", "#c4d9b8"])
        c.rect(x, 4, w, floor - 4, wall)
        c.rect(x, 4, w, 3, shade(wall, 0.8))
        awn = r.choice(palette)
        for i in range(0, w, 4):
            c.rect(x + i, 24, 4, 7, awn if (i // 4) % 2 == 0 else "#ffffff")
        c.rect(x, 31, w, 1, shade(awn, 0.7))
        c.rect(x + 4, 10, 11, 10, "#bfe7ff")
        c.rect(x + 4, 10, 11, 2, "#ffffff")
        c.rect(x + w - 14, 34, 9, 22, shade(wall, 0.65))
        c.rect(x + 4, 36, 14, 14, "#fff2a0")
        c.rect(x + 8, 32, 6, 1, "#1a1423")
        c.rect(x + w - 1, 4, 1, floor - 4, shade(wall, 0.7))
        x += w
    return c


def parking(seed, floor=56):
    import random
    r = random.Random(seed)
    c = Canvas(TILE, floor)
    for x in (10, 82, 154):                                   # pilares com faixa de aviso
        c.rect(x, 0, 10, floor, "#6f6a85")
        c.rect(x, 0, 10, 2, "#8e89a8")
        for y in range(34, floor - 4, 8):
            c.poly([(x, y), (x + 5, y), (x + 10, y + 5), (x + 10, y + 8), (x + 5, y + 8), (x, y + 3)], "#ffd23f")
        c.rect(x + 9, 0, 1, floor, "#4d4963")
    for x, col in ((32, "#4fa6e0"), (104, "#e0a64f"), (176, "#9a6be0")):   # carros ao fundo
        c.rect(x, floor - 14, 34, 10, col)
        c.rect(x + 6, floor - 22, 20, 9, col)
        c.rect(x + 8, floor - 21, 7, 6, "#cdeaff")
        c.rect(x + 17, floor - 21, 7, 6, "#cdeaff")
        c.circle(x + 7, floor - 4, 4, "#1a1423")
        c.circle(x + 27, floor - 4, 4, "#1a1423")
    for x in (58, 130, 202):                                  # luminárias
        c.rect(x, 4, 2, 8, "#3a3a46")
        c.rect(x - 4, 12, 10, 3, "#ffe9a8")
    return c


def school(seed, floor=56):
    c = Canvas(TILE, floor)
    c.rect(0, 10, 150, floor - 10, "#c4653f")
    c.rect(0, 10, 150, 4, "#8e3f26")
    for row in range(2):
        for i in range(6):
            x = 8 + i * 24
            c.rect(x, 18 + row * 18, 12, 11, "#bfe7ff")
            c.rect(x, 18 + row * 18, 12, 2, "#ffffff")
            c.rect(x, 29 + row * 18, 12, 2, "#8e3f26")
    c.rect(60, 38, 22, 18, "#6a3a22")
    c.rect(64, 42, 6, 14, "#9a5a32")
    c.rect(72, 42, 6, 14, "#9a5a32")
    c.rect(56, 34, 30, 4, "#8e3f26")
    c.rect(116, 0, 2, 24, "#3a3a46")                          # mastro com bandeira
    c.poly([(118, 1), (132, 4), (118, 9)], "#ffd23f")
    for x in range(156, TILE, 6):                              # grade
        c.rect(x, floor - 22, 2, 22, "#3a3a46")
    c.rect(150, floor - 20, TILE - 150, 2, "#3a3a46")
    c.rect(150, floor - 8, TILE - 150, 2, "#3a3a46")
    c.rect(TILE - 2, floor - 22, 2, 22, "#3a3a46")
    return c


def ground(kind, seed):
    import random
    r = random.Random(seed)
    h = SCREEN_H - GROUND_Y
    c = Canvas(TILE, h)
    if kind == "praca":
        c.rect(0, 0, TILE, 6, "#59b868")
        c.rect(0, 5, TILE, 1, "#3f9a56")
        for x in range(0, TILE, 3):
            c.px(x, 1 + (x * 7) % 3, "#7fd68a")
        c.rect(0, 6, TILE, h - 6, "#cdbfa6")
        for y in range(8, h, 9):
            c.rect(0, y, TILE, 1, "#a99c84")
            off = 0 if (y // 9) % 2 else 12
            for x in range(off, TILE, 24):
                c.rect(x, y, 1, 9, "#a99c84")
    elif kind == "rua":
        c.rect(0, 0, TILE, 10, "#d7d0e0")
        c.rect(0, 9, TILE, 2, "#8e87a3")
        c.rect(0, 11, TILE, h - 11, "#3b3b48")
        for x in range(0, TILE, 36):
            c.rect(x + 4, 24, 18, 2, "#ffd23f")
        for _ in range(26):
            c.px(r.randint(0, TILE - 1), r.randint(12, h - 1), "#4a4a5a")
    elif kind == "estacionamento":
        c.rect(0, 0, TILE, h, "#827e9a")
        c.rect(0, 0, TILE, 2, "#a09cb8")
        for x in range(0, TILE, 54):
            c.line((x + 20, 6), (x + 8, h - 1), "#ffd23f", 2)
        for _ in range(30):
            c.px(r.randint(0, TILE - 1), r.randint(3, h - 1), "#6f6b88")
    else:
        c.rect(0, 0, TILE, h, "#d9c9a3")
        c.rect(0, 0, TILE, 3, "#f2e6c8")
        for y in range(3, h, 9):
            c.rect(0, y, TILE, 1, "#b8a67c")
            off = 0 if (y // 9) % 2 else 9
            for x in range(off, TILE, 18):
                c.rect(x, y, 1, 9, "#b8a67c")
        for x in (40, 130):                                   # amarelinha pintada
            for i in range(3):
                c.rect(x + i * 10, 12, 8, 8, "#e0457b")
    return c


BACKGROUNDS = {
    "praca": lambda: dict(
        ceu=sky("#5fb8ea", "#d9f4ff"), nuvens=clouds(1), longe=hills(2, "#7fc18a", "#a8e0a0", 66, ("#4a9c5e", "#6a4a2a")),
        perto=trees_row(3, "#4fb060", "#6a4a2a"), chao=ground("praca", 4)),
    "rua": lambda: dict(
        ceu=sky("#ff8e6e", "#ffe0a8", (150, 70, 14, "#fff2a0")), nuvens=clouds(5, "#ffd8c4"),
        longe=skyline(6, "#8e7aa8", "#ffe9a8"), perto=shops(7), chao=ground("rua", 8)),
    "estacionamento": lambda: dict(
        ceu=sky("#2d1f5e", "#e8728f"), nuvens=clouds(9, "#a06ab8"),
        longe=skyline(10, "#3d2a6e", "#ffd86a", 74, 0.45), perto=parking(11), chao=ground("estacionamento", 12)),
    "escola": lambda: dict(
        ceu=sky("#6cc0ff", "#eaf8ff"), nuvens=clouds(13), longe=hills(14, "#8ccf7a", "#b4eaa0", 62, ("#5cb060", "#6a4a2a")),
        perto=school(15), chao=ground("escola", 16)),
}


def build_hud():
    """Corações, pontos das batidas e efeitos em uma folha só: (nome, x, y, w, h) em INDEX."""
    c = Canvas(160, 48)
    index = {}

    def put(name, x, y, w, h):
        index[name] = (x, y, w, h)
    # coração cheio e vazio
    for k, (fill, name) in enumerate((("#ff4057", "coracao"), ("#4a4458", "coracao_vazio"))):
        x = k * 14
        for (dx, dy, w) in ((1, 1, 3), (7, 1, 3), (0, 2, 5), (6, 2, 5), (0, 3, 11), (1, 4, 9), (2, 5, 7), (3, 6, 5), (4, 7, 3), (5, 8, 1)):
            c.rect(x + dx, dy, w, 1, fill)
        if k == 0:
            c.rect(x + 2, 2, 2, 2, "#ff9aa8")
        put(name, x, 0, 11, 10)
    # pontos das batidas: aceso/apagado, e o grande da hora
    for k, (col, name, r) in enumerate((("#ffd23f", "ponto", 4), ("#4a4458", "ponto_apagado", 4),
                                          ("#ffd23f", "ponto_hora", 6), ("#4a4458", "ponto_hora_apagado", 6))):
        x, y = 30 + k * 16, 0
        c.circle(x + 6, y + 6, r + 1, OUTLINE)
        c.circle(x + 6, y + 6, r, col)
        if "apagado" not in name:
            c.circle(x + 5, y + 5, max(1, r // 3), "#fff6c4")
        if "hora" in name:
            c.circle(x + 6, y + 6, r + 1, "#ffffff")
            c.circle(x + 6, y + 6, r, col)
        put(name, x, y, 13, 13)
    # faíscas do grind (4 quadros), poeira da freada (4 quadros) e estrelas da queda (3 quadros)
    for f in range(4):
        x, y = f * 14, 16
        import random
        rr = random.Random(f)
        for _ in range(7):
            c.px(x + rr.randint(0, 10), y + rr.randint(0, 10), rr.choice(["#ffd23f", "#ffffff", "#ff8a3d"]))
        put("faisca%d" % f, x, y, 12, 12)
    for f in range(4):
        x, y = f * 18, 30
        r = 3 + f
        c.circle(x + 8, y + 8 - f // 2, r, (232, 228, 240, 255))
        c.circle(x + 6, y + 9 - f // 2, max(2, r - 2), (200, 196, 214, 255))
        put("poeira%d" % f, x, y, 16, 16)
    for f in range(3):
        x, y = 90 + f * 12, 16
        pts = [(x + 5, y), (x + 6, y + 4), (x + 10, y + 5), (x + 6, y + 6), (x + 5, y + 10), (x + 4, y + 6), (x, y + 5), (x + 4, y + 4)]
        c.poly(pts, "#ffd23f" if f % 2 == 0 else "#ffffff")
        put("estrela%d" % f, x, y, 11, 11)
    return c, index


def main():
    os.makedirs(OUT, exist_ok=True)
    sheet, cols, index = build_skater_sheet()
    sheet.save(os.path.join(OUT, "patinador.png"))
    obs, oindex = build_obstacles()
    obs.save(os.path.join(OUT, "obstaculos.png"))
    for name, make in BACKGROUNDS.items():
        for layer, cv in make().items():
            cv.save(os.path.join(OUT, "fundo_%s_%s.png" % (name, layer)))
    hud, hindex = build_hud()
    hud.save(os.path.join(OUT, "interface.png"))
    import json
    quadros = {"roll": 4, "air": 5, "spin": 8, "brake": 2, "grind": 2, "stairs": 2, "lean_l": 1, "lean_r": 1, "fall": 3}
    with open(os.path.join(OUT, "indice.json"), "w", encoding="utf-8") as f:
        json.dump({"celula": CELL, "colunas": cols, "patinador": index, "quadros": quadros,
                   "obstaculos": oindex, "interface": hindex}, f, indent=1, sort_keys=True)
    print("patinador:", sheet.w, "x", sheet.h, "colunas", cols, index)
    print("interface:", hindex)
    print("obstaculos:", obs.w, "x", obs.h)
    if "--previa" in sys.argv:
        prev = os.path.join(HERE, "..", "previa-sprites")
        os.makedirs(prev, exist_ok=True)
        for name, cv in (("patinador", sheet), ("obstaculos", obs)):
            big = cv.img.resize((cv.w * 3, cv.h * 3), Image.NEAREST)
            bg = Image.new("RGBA", big.size, (110, 150, 180, 255))
            bg.alpha_composite(big)
            bg.convert("RGB").save(os.path.join(prev, name + ".png"))


if __name__ == "__main__":
    main()
