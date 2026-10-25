#!/usr/bin/env python3
"""Gera os sons e a música do jogo por síntese, só com a biblioteca padrão.

Nada é gravado nem baixado: cada som sai das fórmulas abaixo, então os
arquivos têm a mesma licença do jogo e não pedem crédito a ninguém.

Quem joga sem estéreo precisa distinguir os obstáculos só pelo som, então
cada ação tem um desenho próprio de timbre, altura e contorno:

  pular     batida seca de madeira, grave, sempre a mesma nota
  agachar   assobio que desce
  rampa     assobio que sobe
  corrimão  sininho metálico agudo
  escada    três notas descendo, como degraus

O aviso toca em quatro batidas; a quarta (nome_agora) é a mesma figura com
corpo a mais. A música tem 5 camadas de mesmo tamanho por cenário: o jogo
toca todas juntas e só abre o volume das que o combo já liberou.

    python3 tools/gerar_sons.py            # tudo em sounds/
    python3 tools/gerar_sons.py --so-efeitos
    python3 tools/gerar_sons.py --so-musica
"""
import math
import os
import random
import struct
import sys
import wave

RATE = 44100
MUSIC_RATE = 22050
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "sounds")
rng = random.Random(36)
TAU = 2 * math.pi


# --- básico -------------------------------------------------------------------
def n(sec, rate=RATE):
    return int(rate * sec)


def white(sec, rate=RATE):
    return [rng.uniform(-1, 1) for _ in range(n(sec, rate))]


def mul(x, y):
    return [a * b for a, b in zip(x, y)]


def add(*tracks):
    size = max(len(t) for t in tracks)
    out = [0.0] * size
    for t in tracks:
        for i, v in enumerate(t):
            out[i] += v
    return out


def gain(x, g):
    return [v * g for v in x]


def delay(x, sec, rate=RATE):
    return [0.0] * n(sec, rate) + x


def decay(size, tau, attack=0.002, rate=RATE):
    a = max(1, n(attack, rate))
    return [min(1.0, k / a) * math.exp(-k / (rate * tau)) for k in range(size)]


def fade(x, attack, release, rate=RATE):
    a, r = max(1, n(attack, rate)), max(1, n(release, rate))
    size = len(x)
    return [v * max(0.0, min(1.0, k / a, (size - k) / r)) for k, v in enumerate(x)]


def sine(freq, sec, phase=0.0, rate=RATE):
    return [math.sin(phase + TAU * freq * k / rate) for k in range(n(sec, rate))]


def glide(f0, f1, sec, shape=math.sin, rate=RATE):
    """Frequência que anda de f0 a f1 em escala exponencial."""
    out, ph = [], 0.0
    size = n(sec, rate)
    for k in range(size):
        f = f0 * (f1 / f0) ** (k / max(1, size - 1))
        ph += TAU * f / rate
        out.append(shape(ph))
    return out


def tri(ph):
    return 2 / math.pi * math.asin(math.sin(ph))


def square(ph):
    return 1.0 if math.sin(ph) >= 0 else -1.0


def saw(ph):
    return 2 * ((ph / TAU) % 1.0) - 1


def osc(shape, freq, sec, rate=RATE, vibrato=0.0, vib_rate=5.5):
    out, ph = [], 0.0
    for k in range(n(sec, rate)):
        f = freq * (1 + vibrato * math.sin(TAU * vib_rate * k / rate))
        ph += TAU * f / rate
        out.append(shape(ph))
    return out


def biquad(x, kind, freq, q=0.707, rate=RATE):
    w = TAU * freq / rate
    alpha = math.sin(w) / (2 * q)
    c = math.cos(w)
    if kind == "low":
        b = ((1 - c) / 2, 1 - c, (1 - c) / 2)
    elif kind == "high":
        b = ((1 + c) / 2, -(1 + c), (1 + c) / 2)
    else:
        b = (alpha, 0.0, -alpha)
    a0, a1, a2 = 1 + alpha, -2 * c, 1 - alpha
    b0, b1, b2 = (v / a0 for v in b)
    a1, a2 = a1 / a0, a2 / a0
    out, x1, x2, y1, y2 = [], 0.0, 0.0, 0.0, 0.0
    for s in x:
        y = b0 * s + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, s, y1, y
        out.append(y)
    return out


def normalize(x, peak=0.8):
    top = max((abs(v) for v in x), default=0.0)
    return x if top == 0 else [v * peak / top for v in x]


def write(name, x, rate=RATE):
    path = os.path.join(OUT, name + ".wav")
    os.makedirs(OUT, exist_ok=True)
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b"".join(struct.pack("<h", max(-32767, min(32767, int(v * 32767)))) for v in x))


def loop_seamless(x, overlap):
    """Costura o fim no começo com um crossfade, para o som poder repetir sem estalo."""
    o = n(overlap)
    body = x[:-o]
    head, tail = x[:o], x[-o:]
    for k in range(o):
        w = k / o
        body[k] = head[k] * w + tail[k] * (1 - w)
    return body


# --- os cinco avisos -------------------------------------------------------------
def knock(f, sec, heavy=False):
    """Toc de madeira: corpo senoidal curto e um clique."""
    size = n(sec)
    body = mul(sine(f, sec), decay(size, 0.045))
    over = mul(sine(f * 2.03, sec), decay(size, 0.025))
    click = mul(biquad(white(sec), "low", 2500), decay(size, 0.004, 0.0005))
    parts = [body, gain(over, 0.45), gain(click, 0.5)]
    if heavy:
        parts.append(gain(mul(sine(f / 2, sec), decay(size, 0.08)), 0.35))
        parts.append(gain(mul(sine(f * 3.1, sec), decay(size, 0.02)), 0.3))
    return normalize(add(*parts), 0.85)


def whistle(f0, f1, sec, heavy=False):
    x = glide(f0, f1, sec)
    h = glide(f0 * 2, f1 * 2, sec)
    air = biquad(white(sec), "band", (f0 + f1) / 2, 2.0)
    parts = [x, gain(h, 0.2), gain(air, 0.25)]
    if heavy:
        parts.append(gain(glide(f0 * 1.5, f1 * 1.5, sec, tri), 0.5))
    env = fade([1.0] * n(sec), 0.012, sec * 0.45)
    return normalize(mul(add(*parts), env), 0.85)


def bell(f0, sec, heavy=False):
    size = n(sec)
    parts = []
    for ratio, tau, amp in ((1, 0.30, 1.0), (2.76, 0.18, 0.5), (5.4, 0.1, 0.3), (8.93, 0.05, 0.15)):
        parts.append(gain(mul(sine(f0 * ratio, sec), decay(size, tau, 0.001)), amp))
    if heavy:
        parts.append(gain(mul(sine(f0 * 1.26, sec), decay(size, 0.28, 0.001)), 0.7))
        parts.append(gain(mul(sine(f0 * 0.5, sec), decay(size, 0.12, 0.001)), 0.6))
    return normalize(add(*parts), 0.8)


def steps(notes, gap, heavy=False):
    """Notas curtas de marimba, uma após a outra, descendo."""
    parts = []
    for i, f in enumerate(notes):
        size = n(0.16)
        note = add(mul(sine(f, 0.16), decay(size, 0.05, 0.001)),
                   gain(mul(sine(f * 4, 0.16), decay(size, 0.015, 0.001)), 0.4))
        if heavy and i == len(notes) - 1:
            note = add(note, gain(mul(sine(f / 2, 0.16), decay(size, 0.09, 0.001)), 0.9))
        parts.append(delay(note, i * gap))
    return normalize(add(*parts), 0.85)


def alerts():
    write("pular", knock(310, 0.16))
    write("pular_agora", knock(310, 0.26, heavy=True))
    write("agachar", whistle(1250, 520, 0.26))
    write("agachar_agora", whistle(1250, 420, 0.32, heavy=True))
    write("rampa", whistle(380, 1150, 0.26))
    write("rampa_agora", whistle(380, 1300, 0.32, heavy=True))
    write("corrimao", bell(1760, 0.45))
    write("corrimao_agora", bell(1760, 0.6, heavy=True))
    write("escada", steps((784, 659, 523), 0.07))
    write("escada_agora", steps((784, 659, 523, 392), 0.07, heavy=True))


# --- o que o patinador faz e sente ----------------------------------------------
def thud(f, sec, tau=0.07):
    size = n(sec)
    return add(mul(glide(f * 1.6, f, sec), decay(size, tau, 0.001)),
               gain(mul(biquad(white(sec), "low", 900), decay(size, 0.015, 0.0005)), 0.8))


def read_wav(path):
    with wave.open(path) as w:
        raw = w.readframes(w.getnframes())
    return [v / 32768 for v in struct.unpack("<%dh" % (len(raw) // 2), raw)]


def clack(f, sec=0.2):
    """Patim batendo em metal: estalo agudo e um toque que soa."""
    size = n(sec)
    snap = mul(biquad(white(sec), "high", 2800), decay(size, 0.006, 0.0003))
    ring = add(mul(sine(f, sec), decay(size, 0.05, 0.001)),
               gain(mul(sine(f * 1.62, sec), decay(size, 0.035, 0.001)), 0.6))
    return normalize(add(snap, gain(ring, 0.7)), 0.8)


def place_loop(track, at, sound):
    """Soma sound em track a partir de at, dando a volta no fim (para laços)."""
    for k, v in enumerate(sound):
        track[(at + k) % len(track)] += v


def skating():
    # salto de patins: o impulso das rodas (pancada surda) e o zumbido delas subindo ao deixar o chão
    size = n(0.2)
    whirr = mul(biquad(white(0.2), "band", 1500, 2.0), fade([1.0] * size, 0.12, 0.08))
    pop = add(gain(mul(glide(190, 120, 0.2), decay(size, 0.05, 0.001)), 1.0),
              gain(mul(biquad(white(0.2), "low", 1800), decay(size, 0.012, 0.0005)), 0.7),
              gain(whirr, 0.45))
    write("pulo", normalize(pop, 0.8))
    # pouso: as rodas tocam o chão, com o chocalho dos eixos
    land = add(thud(125, 0.22, 0.05),
               delay(gain(thud(110, 0.2, 0.04), 0.6), 0.035),
               gain(mul(biquad(white(0.25), "band", 3200, 1.5),
                        [decay(n(0.25), 0.07, 0.001)[k] * (0.6 + 0.4 * math.sin(TAU * 60 * k / RATE))
                         for k in range(n(0.25))]), 0.35))
    write("pouso", normalize(land, 0.8))
    # tombo: queda com três quiques e um "uuuu" que desce
    fall = add(thud(110, 0.3, 0.09),
               delay(gain(thud(95, 0.25, 0.08), 0.8), 0.22),
               delay(gain(thud(80, 0.2, 0.06), 0.6), 0.42),
               gain(mul(glide(520, 140, 0.7), fade([1.0] * n(0.7), 0.01, 0.5)), 0.35),
               gain(mul(biquad(white(0.8), "band", 700, 0.8), decay(n(0.8), 0.18)), 0.5))
    write("tombo", normalize(fall, 0.9))
    chime = add(mul(sine(1568, 0.3), decay(n(0.3), 0.07, 0.001)),
                delay(mul(sine(2093, 0.3), decay(n(0.3), 0.09, 0.001)), 0.06))
    write("pouso_limpo", normalize(chime, 0.6))
    tuck = mul(biquad(white(0.22), "band", 900, 1.0), fade([1.0] * n(0.22), 0.05, 0.12))
    write("agacha", normalize(tuck, 0.5))
    swoosh = mul(biquad(white(0.45), "band", 600, 1.0), fade([1.0] * n(0.45), 0.35, 0.1))
    write("rampa_sobe", normalize(add(swoosh, gain(thud(150, 0.2, 0.05), 0.4)), 0.6))

    # grind: gravação CC0 de metal raspando (sons-originais/), costurada em laço e com um
    # pouco de raspado sintético por baixo para não repetir de forma óbvia
    src = os.path.join(HERE, "..", "sons-originais", "grind_1_bigsoundbank.wav")
    rec = read_wav(src)
    loop = loop_seamless(rec, 0.15)
    rough = biquad(white(len(loop) / RATE), "band", 2600, 0.9)
    rough = mul(rough, [0.6 + 0.4 * math.sin(TAU * 70 * k / RATE) for k in range(len(rough))])
    write("grind_loop", normalize(add(normalize(loop, 0.8), gain(normalize(rough, 0.5), 0.3)), 0.7))
    write("grind_entra", clack(1450))

    # rodas no asfalto: chiado grave de poliuretano, e a cada junta da calçada duas pancadas
    # (rodas da frente e de trás) ; o laço tem 4 juntas
    sec, joint = 1.68, 0.42
    size = n(sec)
    bed = add(biquad(white(sec + 0.2), "low", 650),
              gain(biquad(white(sec + 0.2), "band", 2300, 0.8), 0.18))
    track = loop_seamless(bed, 0.2) if len(bed) > size else bed
    track = track[:size]
    for j in range(4):
        at = n(j * joint)
        place_loop(track, at, gain(thud(95, 0.12, 0.025), 1.4))
        place_loop(track, at + n(0.075), gain(thud(105, 0.12, 0.025), 1.0))
    write("rodas_loop", normalize(track, 0.55))

    # escada: degraus em sequência rápida, cada um um pouco diferente, com o chacoalhar dos patins
    sec = 1.1
    size = n(sec)
    track = [v * 0.6 for v in loop_seamless(biquad(white(sec + 0.15), "band", 1500, 0.6), 0.15)][:size]
    r2 = random.Random(5)
    for i in range(10):
        place_loop(track, n(i * 0.11), gain(thud(r2.uniform(95, 150), 0.12, 0.03), r2.uniform(0.9, 1.3)))
    write("degraus_loop", normalize(track, 0.6))
    write("degraus_entra", normalize(add(thud(130, 0.25, 0.06),
                                         gain(mul(biquad(white(0.3), "band", 1200, 0.8),
                                                  fade([1.0] * n(0.3), 0.02, 0.2)), 0.5)), 0.75))


def feedback():
    write("acerto", normalize(mul(sine(880, 0.12), decay(n(0.12), 0.04, 0.001)), 0.5))
    spark = add(mul(sine(1175, 0.3), decay(n(0.3), 0.07, 0.001)),
                delay(mul(sine(1760, 0.3), decay(n(0.3), 0.09, 0.001)), 0.05),
                delay(mul(sine(2349, 0.3), decay(n(0.3), 0.1, 0.001)), 0.1))
    write("perfeito", normalize(spark, 0.55))
    # manobra: uma corda dedilhada (Karplus-Strong) em dó; o jogo muda a altura pela direção
    f = 523.25
    period = int(RATE / f)
    buf = [rng.uniform(-1, 1) for _ in range(period)]
    out = []
    for k in range(n(0.35)):
        v = buf[k % period]
        buf[k % period] = 0.5 * (v + buf[(k + 1) % period]) * 0.996
        out.append(v)
    write("trick", normalize(fade(out, 0.001, 0.08), 0.7))
    write("trick_tarde", normalize(thud(150, 0.12, 0.03), 0.4))
    # menus
    write("menu_mover", normalize(mul(sine(660, 0.06), decay(n(0.06), 0.02, 0.001)), 0.4))
    write("menu_confirmar", normalize(add(mul(sine(660, 0.16), decay(n(0.16), 0.05, 0.001)),
                                           delay(mul(sine(990, 0.16), decay(n(0.16), 0.06, 0.001)), 0.07)), 0.5))
    # fim da corrida: três notas caindo
    end = add(*[delay(mul(sine(f, 0.5), decay(n(0.5), 0.15, 0.002)), i * 0.22)
                for i, f in enumerate((659, 523, 392, 262))])
    write("fim", normalize(end, 0.6))
    write("cenario", normalize(mul(biquad(white(0.8), "band", 1200, 0.7),
                                   fade([1.0] * n(0.8), 0.4, 0.4)), 0.4))


# --- música ----------------------------------------------------------------------
def midi(note):
    return 440.0 * 2 ** ((note - 69) / 12)


def kick(rate):
    size = n(0.28, rate)
    return mul(glide(130, 42, 0.28, rate=rate), decay(size, 0.1, 0.001, rate))


def hat(rate, open_=False):
    sec = 0.22 if open_ else 0.05
    return mul(biquad(white(sec, rate), "high", 7000, rate=rate), decay(n(sec, rate), 0.09 if open_ else 0.015, 0.0005, rate))


def clap(rate):
    sec = 0.18
    return mul(biquad(white(sec, rate), "band", 1700, 0.9, rate), decay(n(sec, rate), 0.05, 0.001, rate))


def bass_note(note, sec, rate):
    x = osc(saw, midi(note), sec, rate)
    return mul(biquad(x, "low", 420, 0.9, rate), decay(n(sec, rate), sec * 0.7, 0.004, rate))


def stab(notes, sec, rate):
    voices = [osc(square, midi(m), sec, rate) for m in notes]
    mix = gain(add(*voices), 1.0 / len(voices))
    return mul(biquad(mix, "low", 1800, 0.7, rate), decay(n(sec, rate), sec * 0.5, 0.003, rate))


def lead_note(note, sec, rate):
    x = osc(tri, midi(note), sec, rate, vibrato=0.004)
    return mul(x, fade(decay(n(sec, rate), sec * 1.3, 0.01, rate), 0.01, 0.05, rate))


def pluck(note, sec, rate):
    f = midi(note)
    period = max(2, int(rate / f))
    buf = [rng.uniform(-1, 1) for _ in range(period)]
    out = []
    for k in range(n(sec, rate)):
        v = buf[k % period]
        buf[k % period] = 0.5 * (v + buf[(k + 1) % period]) * 0.994
        out.append(v)
    return out


def place(track, start, sound):
    """Soma sound em track a partir de start, dando a volta no fim (a música repete)."""
    size = len(track)
    for k, v in enumerate(sound):
        track[(start + k) % size] += v


# Cada cenário: andamento, tom, acordes (grau a partir da tônica, tipo), escala e tempero
STYLES = {
    "praca": {"bpm": 104, "root": 48, "scale": (0, 2, 4, 7, 9), "swing": 0.12,
              "chords": ((0, "maj"), (9, "min"), (5, "maj"), (7, "maj")), "echo": 0.0},
    "rua": {"bpm": 120, "root": 45, "scale": (0, 3, 5, 7, 10), "swing": 0.0,
            "chords": ((0, "min"), (0, "min"), (8, "maj"), (7, "maj")), "echo": 0.0},
    "estacionamento": {"bpm": 98, "root": 50, "scale": (0, 2, 3, 7, 9), "swing": 0.05,
                       "chords": ((0, "min"), (5, "maj"), (0, "min"), (10, "maj")), "echo": 0.28},
    "escola": {"bpm": 128, "root": 55, "scale": (0, 2, 4, 7, 9), "swing": 0.0,
               "chords": ((0, "maj"), (7, "maj"), (9, "min"), (5, "maj")), "echo": 0.0},
}
TRIADS = {"maj": (0, 4, 7), "min": (0, 3, 7)}


def echo(x, sec, fb, rate):
    d = n(sec, rate)
    out = list(x)
    for k in range(d, len(out)):
        out[k] += out[k - d] * fb
    return out


def song(name, style):
    r = MUSIC_RATE
    rg = random.Random(name)
    beat = 60.0 / style["bpm"]
    step = beat / 4
    bars = 4
    size = n(beat * 4 * bars, r)
    at = lambda s: int(s * step * r + (style["swing"] * step * r if s % 2 else 0))   # noqa: E731
    root = style["root"]
    scale = style["scale"]
    layers = [[0.0] * size for _ in range(5)]
    base, hats, chords, lead, arp = layers
    melody = []
    for b in range(bars):
        degree, quality = style["chords"][b]
        tones = [root + degree + t for t in TRIADS[quality]]
        s0 = b * 16
        # camada 0: bumbo e baixo
        for s in (0, 6, 8, 14) if name != "rua" else (0, 4, 8, 12):
            place(base, at(s0 + s), gain(kick(r), 0.9))
        pattern = (0, 3, 6, 8, 10, 12, 14) if name != "escola" else (0, 2, 4, 6, 8, 10, 12, 14)
        for i, s in enumerate(pattern):
            note = root + degree - 12 + (7 if i % 3 == 2 else 0)
            place(base, at(s0 + s), gain(bass_note(note, step * 1.8, r), 0.55))
        # camada 1: chimbal e palma
        for s in range(0, 16, 2):
            place(hats, at(s0 + s), gain(hat(r, open_=(s % 4 == 2)), 0.28 if s % 4 == 2 else 0.2))
        for s in (4, 12):
            place(hats, at(s0 + s), gain(clap(r), 0.5))
        # camada 2: acordes
        for s in (2, 6, 10, 14) if name != "escola" else (0, 3, 6, 8, 11, 14):
            place(chords, at(s0 + s), gain(stab([t + 12 for t in tones], step * 1.6, r), 0.3))
        # camada 3: melodia em frases de 4 tempos que respondem uma à outra
        if b % 2 == 0:
            melody = []
            pos = 0
            while pos < 16:
                length = rg.choice((2, 2, 3, 4))
                degree_idx = rg.choice(range(len(scale)))
                if pos == 0:
                    degree_idx = rg.choice((0, 2, 3))
                melody.append((pos, scale[degree_idx] + 12 * rg.choice((0, 0, 1)), length))
                pos += length + rg.choice((0, 0, 2))
        for pos, interval, length in melody:
            if pos < 16:
                place(lead, at(s0 + pos), gain(lead_note(root + 12 + interval, step * length * 0.95, r), 0.5))
        # camada 4: arpejo agudo em semicolcheias
        for s in range(16):
            place(arp, at(s0 + s), gain(pluck(tones[s % 3] + 36, step * 1.8, r), 0.28 if s % 4 else 0.38))
    if style["echo"]:
        layers = [echo(x, beat * 0.75, style["echo"], r) if i in (2, 3, 4) else x
                  for i, x in enumerate(layers)]
    # cada camada chega a um volume próprio, para todas serem ouvidas quando entram;
    # juntas não passam de 0,85
    targets = (0.10, 0.05, 0.05, 0.065, 0.045)
    for i, x in enumerate(layers):
        rms = math.sqrt(sum(v * v for v in x) / len(x))
        k = targets[i] / rms if rms else 1.0
        layers[i] = [v * k for v in x]
    total = [sum(col) for col in zip(*layers)]
    scale_down = min(1.0, 0.85 / max(abs(v) for v in total))
    for i, x in enumerate(layers):
        write("musica_%s_%d" % (name, i), [v * scale_down for v in x], r)


def music():
    for name, style in STYLES.items():
        song(name, style)


def main():
    only_fx = "--so-efeitos" in sys.argv
    only_music = "--so-musica" in sys.argv
    if not only_music:
        alerts()
        skating()
        feedback()
    if not only_fx:
        music()
    print("sons gerados em", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
