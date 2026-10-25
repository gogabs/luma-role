import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from pista import config as C  # noqa: E402
from pista.cenarios import KIND_ORDER, SCENARIOS  # noqa: E402
from pista.corrida import Obstacle, Run, beat_at, layers_for, multiplier  # noqa: E402


class FakeUI:
    def __init__(self, auto_resume=True):
        self.cues, self.said, self.briefs, self.layer, self.scenarios = [], [], [], 1, []
        self.rolls, self.finished, self.auto_resume = [], None, auto_resume
        self.resume = None

    def cue(self, name, volume=1.0, pitch=1.0, pan=None):
        self.cues.append((name, volume, pitch, pan))

    def say(self, text):
        self.said.append(text)

    def brief(self, text, kind, resume):
        self.briefs.append((text, kind))
        self.resume = resume
        if self.auto_resume:
            resume()

    def scenario(self, index):
        self.scenarios.append(index)

    def layers(self, n):
        self.layer = n

    def rolling(self, volume, pitch):
        self.rolls.append((volume, pitch))

    def remember(self):
        pass

    def over(self, run):
        self.finished = run

    def names(self):
        return [c[0] for c in self.cues]


ALL_SEEN = set(KIND_ORDER)


def fresh(ui=None, kinds=(), seen=ALL_SEEN):
    """Corrida sem os obstáculos sorteados, só os dados (kind, instante)."""
    ui = ui or FakeUI()
    r = Run(ui, seed=1, seen=set(seen), scenarios_seen={0, 1, 2, 3})
    r.obstacles = [Obstacle(k, k, at, 0.5) for k, at in kinds]
    r._plan = lambda: None
    return r


def run(r, seconds, dt=0.01, every=None):
    for i in range(int(seconds / dt)):
        if every:
            every(r, i)
        r.update(dt)


def advance_to(r, t, dt=0.01):
    while r.t < t - 1e-9:
        r.update(min(dt, t - r.t))


class CorridaTest(unittest.TestCase):
    def test_speed_and_beat_get_faster_down_to_the_limit(self):
        self.assertAlmostEqual(beat_at(0), C.BEAT)
        self.assertLess(beat_at(120), beat_at(10))
        self.assertGreaterEqual(beat_at(10_000), C.MIN_BEAT)

    def test_four_beats_the_last_one_is_the_action(self):
        ui = FakeUI()
        r = fresh(ui, [("pular", 5.0)])
        advance_to(r, 5.01)
        self.assertEqual(ui.names()[:4], ["pular", "pular", "pular", "pular_agora"])
        self.assertEqual([c[1] for c in ui.cues[:4]], list(C.CUE_VOLUMES))

    def test_matching_action_in_the_beat_clears(self):
        ui = FakeUI()
        r = fresh(ui, [("pular", 5.0)])
        advance_to(r, 5.0)
        self.assertEqual(r.action("pular"), "perfeito")
        self.assertEqual(r.combo, 1)
        self.assertIn("perfeito", ui.names())
        self.assertEqual(r.lives, C.LIVES)
        self.assertEqual(r.score, (C.POINTS_OBSTACLE + C.POINTS_PERFECT) * 1)

    def test_a_bit_off_is_ok_but_still_clears(self):
        r = fresh(None, [("agachar", 5.0)])
        advance_to(r, 5.0 - 0.2)
        self.assertEqual(r.action("agachar"), "ok")

    def test_wrong_action_in_window_falls(self):
        ui = FakeUI()
        r = fresh(ui, [("pular", 5.0)])
        advance_to(r, 5.0)
        self.assertEqual(r.action("agachar"), "tombo")
        self.assertEqual((r.lives, r.combo), (C.LIVES - 1, 0))
        self.assertIn("tombo", ui.names())

    def test_doing_nothing_falls_after_the_window(self):
        r = fresh(None, [("rampa", 5.0)])
        advance_to(r, 5.0 + 0.5)
        self.assertEqual(r.lives, C.LIVES - 1)

    def test_too_early_is_a_free_move_and_the_obstacle_still_hits(self):
        r = fresh(None, [("pular", 5.0)])
        advance_to(r, 3.0)
        self.assertEqual(r.action("pular"), "livre")
        advance_to(r, 5.5)
        self.assertEqual(r.lives, C.LIVES - 1)

    def test_cannot_act_while_busy(self):
        r = fresh(None, [("pular", 9.0)])
        advance_to(r, 2.0)
        r.action("pular")
        self.assertIsNone(r.action("pular"))
        advance_to(r, 2.0 + C.KINDS["pular"]["busy"] + 0.01)
        self.assertEqual(r.action("pular"), "livre")

    def test_tricks_only_in_the_air(self):
        ui = FakeUI()
        r = fresh(ui, [("rampa", 3.0), ("pular", 20.0)])
        self.assertIsNone(r.trick())
        self.assertIn("trick_tarde", ui.names())
        advance_to(r, 3.0)
        r.action("rampa")
        advance_to(r, 3.1)
        self.assertTrue(r.airborne)
        self.assertEqual(r.trick(), "neutro")   # sem direcional
        self.assertEqual(r.tricks, 1)

    def test_trick_scores_and_pitch_follows_the_direction(self):
        ui = FakeUI()
        r = fresh(ui, [("rampa", 3.0), ("pular", 20.0)])
        advance_to(r, 3.0)
        r.action("rampa")
        advance_to(r, 3.2)
        self.assertEqual(r.trick(("left",)), "left")
        cue = [c for c in ui.cues if c[0] == "trick"][-1]
        self.assertAlmostEqual(cue[2], C.TRICKS["left"])
        self.assertEqual(cue[3], C.TRICK_PAN["left"])        # o estéreo só complementa
        self.assertIsNone(r.trick())                         # ainda fazendo a anterior
        advance_to(r, 3.2 + C.TRICK_TIME + 0.01)
        self.assertEqual(r.trick(("left",)), "left")         # repetida vale menos
        self.assertGreater(r.combo, 2)
        pts = r.score
        advance_to(r, 3.0 + C.KINDS["rampa"]["air"] + 0.05)
        self.assertGreater(r.score, pts)                     # bônus de pouso
        self.assertIn("pouso", ui.names())

    def test_trick_too_late_in_the_flight_is_refused_without_falling(self):
        ui = FakeUI()
        r = fresh(ui, [("pular", 3.0), ("pular", 20.0)])
        advance_to(r, 3.0)
        r.action("pular")
        advance_to(r, 3.0 + C.KINDS["pular"]["air"] - 0.1)
        self.assertIsNone(r.trick())
        self.assertEqual(r.lives, C.LIVES)
        self.assertIn("trick_tarde", ui.names())

    def test_direction_pressed_just_before_y_counts(self):
        r = fresh(None, [("rampa", 3.0), ("pular", 20.0)])
        advance_to(r, 3.0)
        r.action("rampa")
        advance_to(r, 3.3)
        r.direction("up")
        advance_to(r, 3.35)
        self.assertEqual(r.trick(()), "up")

    def test_fall_clears_combo_drops_near_obstacles_and_ends_at_zero_lives(self):
        ui = FakeUI()
        r = fresh(ui, [("pular", 5.0), ("pular", 6.0), ("pular", 30.0)])
        r.combo = 12
        advance_to(r, 5.6)
        self.assertEqual(r.combo, 0)
        self.assertEqual([o.at for o in r.obstacles], [30.0])
        self.assertEqual(ui.layer, 1)
        r.lives = 1
        r.obstacles = [Obstacle("pular", "x", r.t + 0.1, 0.5)]
        run(r, 1.0)
        self.assertTrue(r.over)
        self.assertIs(ui.finished, r)

    def test_layers_follow_the_combo(self):
        self.assertEqual([layers_for(c) for c in (0, 1, 2, 5, 9, 14, 40)], [1, 1, 2, 3, 4, 5, 5])
        self.assertEqual([multiplier(c) for c in (0, 3, 4, 8, 100)], [1, 1, 2, 3, 5])
        ui = FakeUI()
        r = fresh(ui, [("pular", 5.0)])
        r.combo = 1
        advance_to(r, 5.0)
        r.action("pular")
        self.assertEqual(ui.layer, 2)

    def test_no_stereo_needed_every_kind_has_its_own_cue_name(self):
        ui = FakeUI()
        r = fresh(ui, [(k, 5.0 + 5 * i) for i, k in enumerate(KIND_ORDER)])
        self._autopilot(r, 5 * len(KIND_ORDER) + 2, tricks=False)
        self.assertEqual(r.falls, 0)
        heard = {c[0] for c in ui.cues if c[0] in KIND_ORDER or c[0].endswith("_agora")}
        self.assertEqual(len(heard), 2 * len(KIND_ORDER))
        self.assertTrue(all(c[3] is None for c in ui.cues if c[0] in heard))   # nenhum depende de lado

    def test_new_obstacle_is_explained_once_and_pauses(self):
        ui = FakeUI(auto_resume=False)
        r = Run(ui, seed=3, seen=set(), scenarios_seen={0, 1, 2, 3})
        run(r, 3.0)
        self.assertFalse(r.paused)
        # a primeira explicação vem antes do primeiro obstáculo
        t0 = r.t
        run(r, 3.0)
        self.assertTrue(r.paused)
        self.assertEqual(len(ui.briefs), 1)
        text, kind = ui.briefs[0]
        self.assertIn("Novo obstáculo", text)
        self.assertIn(kind, r.seen)
        stuck = r.t
        run(r, 1.0)
        self.assertEqual(r.t, stuck)            # pausada, o tempo não anda
        ui.resume()
        run(r, 0.5)
        self.assertGreater(r.t, stuck)

    def test_scenarios_rotate_with_spoken_name(self):
        ui = FakeUI()
        r = Run(ui, seed=5, seen=set(ALL_SEEN), scenarios_seen={0, 1, 2, 3})
        self._autopilot(r, 400)
        self.assertEqual(ui.scenarios[:5], [0, 1, 2, 3, 0])
        self.assertIn("Rua", ui.said)

    def _autopilot(self, r, seconds, dt=0.01, jitter=0.0, tricks=True):
        def play(r, i):
            if r.over:
                return
            if r.obstacles and r.can_act:
                o = r.obstacles[0]
                if r.t >= o.at + jitter:
                    r.action(o.kind)
            if tricks and r.airborne and r.t - r._trick_until > 0.02:
                r.trick(("left",))
        run(r, seconds, dt, every=play)

    def test_perfect_player_never_falls_and_builds_the_whole_music(self):
        ui = FakeUI()
        r = Run(ui, seed=11, seen=set(ALL_SEEN), scenarios_seen={0, 1, 2, 3})
        self._autopilot(r, 300)
        self.assertEqual(r.falls, 0)
        self.assertGreater(r.cleared, 60)
        self.assertEqual(ui.layer, 5)
        self.assertGreater(r.speed, 1.5)

    def test_slow_player_falls_until_game_over(self):
        ui = FakeUI()
        r = Run(ui, seed=11, seen=set(ALL_SEEN), scenarios_seen={0, 1, 2, 3})
        self._autopilot(r, 200, jitter=0.6, tricks=False)
        self.assertTrue(r.over)
        self.assertEqual(r.lives, 0)

    def test_obstacles_never_overlap_windows(self):
        r = Run(FakeUI(), seed=2, seen=set(ALL_SEEN), scenarios_seen={0, 1, 2, 3})
        for _ in range(200):
            r._plan_one()
        for a, b in zip(r.obstacles, r.obstacles[1:]):
            self.assertGreater(b.at - b.early, a.at + a.late + C.KINDS[a.kind]["busy"] - 0.01)

    def test_only_the_scenario_objects_appear(self):
        r = Run(FakeUI(), seed=4, seen=set(ALL_SEEN), scenarios_seen={0, 1, 2, 3})
        r.obstacles = []
        kinds = []
        for i in range(C.PER_SCENARIO):
            r._plan_one()
        kinds = {o.kind for o in r.obstacles}
        self.assertTrue(kinds <= set(SCENARIOS[0]["objetos"]))

    def test_status_text(self):
        r = Run(FakeUI(), seed=1, seen=set(ALL_SEEN), scenarios_seen={0})
        self.assertIn("Praça", r.status_text())
        self.assertIn("3 vidas", r.status_text())


class SonsTest(unittest.TestCase):
    """Todo som que o jogo toca existe em sounds/."""

    def test_every_sound_the_game_asks_for_exists(self):
        from pista.corrida import START_SOUND
        wanted = set(KIND_ORDER) | {k + "_agora" for k in KIND_ORDER} | set(START_SOUND.values())
        wanted |= {"acerto", "perfeito", "trick", "trick_tarde", "pouso", "pouso_limpo", "tombo",
                   "rodas", "fim", "menu_mover", "menu_confirmar"}
        wanted |= {"musica_%s_%d" % (sc["id"], i) for sc in SCENARIOS for i in range(5)}
        folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sounds")
        have = {os.path.splitext(f)[0] for f in os.listdir(folder)}
        self.assertEqual(wanted - have, set())

    def test_music_layers_of_a_scenario_have_the_same_length(self):
        import wave
        folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sounds")
        for sc in SCENARIOS:
            sizes = set()
            for i in range(5):
                with wave.open(os.path.join(folder, "musica_%s_%d.wav" % (sc["id"], i))) as w:
                    sizes.add(w.getnframes())
            self.assertEqual(len(sizes), 1, sc["id"])

    def test_every_scenario_object_has_a_known_action(self):
        for sc in SCENARIOS:
            self.assertTrue(set(sc["objetos"]) <= set(C.KINDS), sc["id"])


if __name__ == "__main__":
    unittest.main()
