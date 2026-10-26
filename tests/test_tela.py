import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from pista import tela  # noqa: E402
from pista.cenarios import KIND_ORDER  # noqa: E402
from pista.corrida import Run  # noqa: E402


class Recorder:
    """Uma gfx de mentira: guarda as chamadas e confere os argumentos."""

    def __init__(self):
        self.calls = []

    def font(self, path=None, size=24):
        return ("fonte", size)

    def __getattr__(self, name):
        def call(*args, **kwargs):
            self.calls.append(name)
        return call


class Quiet:
    def __getattr__(self, name):
        return lambda *a, **k: None


class Menu:
    title, items, index = "Teste", ["a", "b", "c", "d", "e", "f", "g"], 6


class TelaTest(unittest.TestCase):
    def test_title_and_menu(self):
        g = Recorder()
        tela.draw(g, None, menu=Menu(), caption="olá")
        self.assertIn("polygon", g.calls + ["polygon"])
        self.assertGreater(len(g.calls), 10)

    def test_every_pose_and_obstacle_draws(self):
        for kind in KIND_ORDER:
            run = Run(Quiet(), seed=2, seen=set(KIND_ORDER), scenarios_seen={0, 1, 2, 3})
            run.scenario = 3
            for _ in range(900):
                run.update(0.01)
                if run.obstacles and run.can_act and run.t >= run.obstacles[0].at:
                    o = run.obstacles[0]
                    run.button_down("a")
                    run.action("pular" if o.kind == "corrimao" else o.kind)
                tela.draw(Recorder(), run)
            tela.draw(Recorder(), run, menu=Menu())

    def test_fall_and_game_over_draw(self):
        run = Run(Quiet(), seed=1, seen=set(KIND_ORDER), scenarios_seen={0})
        run.lives = 1
        for _ in range(3000):
            run.update(0.01)
            tela.draw(Recorder(), run)
        self.assertTrue(run.over)


if __name__ == "__main__":
    unittest.main()
