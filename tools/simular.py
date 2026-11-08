#!/usr/bin/env python3
"""Roda o main.py de verdade, sem tela, som nem controle, com um jogador automático.

Usa a OpenAL em modo nulo (carrega e toca todos os sons de verdade, mas ninguém
ouve), relógio simulado e fala só no registro. Serve para pegar erros de
integração entre o main.py, a biblioteca-ponte e a corrida.

    python3 tools/simular.py [segundos] [--erra]    # --erra: o jogador falha de propósito
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SECONDS = float(next((a for a in sys.argv[1:] if not a.startswith("-")), 120))
SLOPPY = "--erra" in sys.argv
SCREEN = "--tela" in sys.argv    # desenha de verdade pela SDL (driver de vídeo "dummy")
if SCREEN:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

os.environ.setdefault("ALSOFT_DRIVERS", "null")
os.environ["A11Y_SAVE_DIR"] = tempfile.mkdtemp(prefix="role-")
os.environ["A11Y_GAME_DIR"] = os.path.abspath(ROOT)
sys.path.insert(0, os.path.abspath(ROOT))

import time as _time

clock = {"now": 1000.0}
_time.monotonic = lambda: clock["now"]

import r36s_a11y as a11y
from r36s_a11y import game as game_module

spoken = []


def fake_run(self):
    g = sys._getframe(1).f_globals            # os globais do main.py
    pending = []                               # (hora, on_done)

    def say(text, queue=False, on_done=None):
        spoken.append((round(clock["now"] - 1000.0, 1), text))
        if on_done:
            pending.append((clock["now"] + 0.04 * len(text), on_done))
    self.speech.say = say
    self.speech.poll = lambda: [(fn, True) for t, fn in list(pending) if t <= clock["now"] and not pending.remove((t, fn))]
    print("OpenAL disponível:", self.sound.available)
    for fn in self._handlers["start"]:
        fn()
    step = 1 / 60
    seen_run = False

    def press(button):
        self._dispatch_button(button, a11y.DOWN, 0)
        self._dispatch_button(button, a11y.UP, 0)

    for tick in range(int(SECONDS / step)):
        clock["now"] += step
        for fn, done in self.speech.poll():
            fn(done)
        self._tick_timers(clock["now"])
        state = g["state"]
        if self._focus and self._focus[-1] is g["main_menu"] and tick % 30 == 0:
            if g["main_menu"].items[g["main_menu"].index] != "Jogar":
                press("down")
            else:
                press("b")
        for fn in list(self._handlers["update"]):
            fn(step)
        run = state["run"]
        if state["phase"] == "run" and run is not None and not run.stopped and not self._focus:
            if run._hold is None and run._rail is None and run.t >= run._busy_until:
                for b in ("a", "x", "left", "right", "down"):
                    if b in run.held:
                        self._dispatch_button(b, a11y.UP, 0)
            if run.obstacles and run.can_act:
                o = run.obstacles[0]
                if run.t >= o.at + (0.7 if SLOPPY and o.name[0] in "abcdefg" else 0.0):
                    if o.kind == "corrimao":
                        self._dispatch_button("a", a11y.DOWN, 0)
                        press("b")
                    elif o.kind in ("escada", "curva_esq", "curva_dir", "freada"):
                        b = {"escada": "x", "curva_esq": "left", "curva_dir": "right", "freada": "down"}[o.kind]
                        self._dispatch_button(b, a11y.DOWN, 0)
                    else:
                        press({"pular": "b", "rampa": "up"}[o.kind])
            hold = run._hold
            if hold is not None and hold["kind"] == "freada" and not hold["got"] \
                    and run.t >= hold["at"] + 0.2:
                self._dispatch_button(hold["side"], a11y.DOWN, 0)
            if run.airborne and run.t - run._trick_until > 0.02 and run._air_until - run.t > 0.26:
                self._dispatch_button("left", a11y.DOWN, 0)
                press("y")
                self._dispatch_button("left", a11y.UP, 0)
        if SCREEN and tick % 3 == 0:
            gfx = self.gfx
            if gfx.available:
                gfx.begin()
                for fn in self._handlers["draw"]:
                    fn(gfx)
                if tick in (1500, 2400):
                    gfx.screenshot("/tmp/tela-%d.png" % tick)
                gfx.end()
            elif tick == 0:
                print("SDL indisponível: sem desenho")
        if state["run"] is not None:
            seen_run = True
        if seen_run and state["phase"] == "menu" and state["run"] is None and not self._focus:
            break
    run = g["state"]["run"]
    print("fala (%d linhas), primeiras e últimas:" % len(spoken))
    for t, text in spoken[:6] + [(".", "...")] + spoken[-6:]:
        print("  %s %s" % (t, text[:110]))
    if run is not None:
        print("estado final:", run.status_text(), "| obstáculos:", run.cleared, "| tombos:", run.falls,
              "| manobras:", run.tricks, "| t=%.0fs" % run.t)
    print("placar:", g["game"].high_scores.entries(g["BOARD"])[:1])


game_module.Game.run = fake_run
import runpy
runpy.run_path(os.path.join(ROOT, "main.py"), run_name="__main__")
