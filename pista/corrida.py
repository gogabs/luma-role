"""A pista e o patinador. Sem áudio nem fala: tudo passa pela ui.

A ui recebe:
  ui.cue(nome, volume, pitch, pan)  um som curto (pan é opcional e só complementa)
  ui.say(texto)                     fala curta, sem pausar a corrida
  ui.brief(texto, tipo, retomar)    fala mais longa; a corrida espera retomar()
  ui.scenario(índice)               trocou o cenário (música e trilha)
  ui.layers(n)                      quantas camadas da música tocam (1 a 5)
  ui.rolling(volume, pitch)         o som das rodas no chão
  ui.remember()                     o que já foi explicado mudou: grave
  ui.over(corrida)                  acabaram as vidas
"""
import math
import random

from . import config as C
from .cenarios import KIND_INFO, SCENARIOS


class Obstacle:
    def __init__(self, kind, name, at, beat):
        self.kind = kind
        self.name = name
        self.at = at            # hora de agir, em segundos de corrida
        self.beat = beat
        self.cues = 0           # quantas batidas já tocaram

    @property
    def early(self):
        return max(C.EARLY_MIN, C.EARLY * self.beat)

    @property
    def late(self):
        return max(C.LATE_MIN, C.LATE * self.beat)


def speed_at(t):
    return 1.0 + C.SPEED_GAIN * (1.0 - math.exp(-t / C.SPEED_TAU))


def beat_at(t):
    return max(C.MIN_BEAT, C.BEAT / speed_at(t))


def multiplier(combo):
    return min(C.MULTIPLIER_MAX, 1 + combo // C.MULTIPLIER_EVERY)


def layers_for(combo):
    return sum(1 for need in C.COMBO_LAYERS if combo >= need)


class Run:
    def __init__(self, ui, seed=None, seen=None, scenarios_seen=None):
        self.ui = ui
        self.rng = random.Random(seed)
        self.seen = seen if seen is not None else set()
        self.scenarios_seen = scenarios_seen if scenarios_seen is not None else set()
        self.t = 0.0
        self.paused = False        # fala longa em andamento
        self.halted = False        # o jogador abriu a pausa
        self.over = False
        self.score = 0
        self.combo = 0
        self.best_combo = 0
        self.lives = C.LIVES
        self.cleared = 0
        self.perfects = 0
        self.tricks = 0
        self.falls = 0
        self.scenario = 0           # o cenário em que o patinador está
        self.obstacles = []         # os que ainda vão chegar, em ordem
        self.events = []            # (hora, tipo, valor): falas e trocas de cenário
        self._plan_scenario = 0
        self._in_scenario = 0
        self._cursor = C.FIRST_OBSTACLE   # o aviso do próximo só começa depois daqui
        self._floor = 0.0
        self._last_end = 0.0
        self._last_kind = None
        self._briefed = set()
        self._busy_until = 0.0
        self._air_until = 0.0
        self._crouch_until = 0.0
        self._grind_until = 0.0
        self._fall_until = 0.0
        self._trick_until = 0.0
        self._flight = []           # manobras do voo atual
        self._in_air = False
        self._layers = 1
        self._dirs = {}             # direcional -> hora do último aperto
        self._event(0.0, "scenario", 0)
        self._plan()

    # --- o que o jogador faz ----------------------------------------------
    @property
    def speed(self):
        return speed_at(self.t)

    @property
    def airborne(self):
        return self.t < self._air_until

    @property
    def stopped(self):
        return self.over or self.paused or self.halted

    @property
    def can_act(self):
        return not self.stopped and self.t >= self._busy_until

    def action(self, kind):
        """pular, agachar, corrimao, rampa ou escada. Devolve "perfeito", "ok", "tombo",
        "livre" (sem obstáculo à vista) ou None (ignorado)."""
        if not self.can_act:
            return None
        target = self._window()
        self._start(kind)
        if target is None:
            return "livre"
        if target.kind != kind:
            self.obstacles.remove(target)
            self._fall()
            return "tombo"
        error = abs(self.t - target.at)
        self.obstacles.remove(target)
        perfect = error <= C.PERFECT
        self.cleared += 1
        self.combo += 1
        self.best_combo = max(self.best_combo, self.combo)
        points = C.POINTS_OBSTACLE + C.KINDS[kind]["extra"]
        if perfect:
            points += C.POINTS_PERFECT
            self.perfects += 1
        self.score += points * multiplier(self.combo)
        self.ui.cue("perfeito" if perfect else "acerto", 1.0, min(1.9, 1.0 + 0.04 * self.combo))
        self._sync_layers()
        return "perfeito" if perfect else "ok"

    def direction(self, name):
        """Registra um direcional apertado, para valer como parte da manobra."""
        self._dirs[name] = self.t

    def trick(self, held=()):
        """Y no ar, com o direcional que estiver apertado (held) ou recém-apertado."""
        if self.stopped or self.t < self._fall_until:
            return None
        if not self.airborne or self.t < self._trick_until:
            self.ui.cue("trick_tarde", 0.8, 1.0, None)
            return None
        if self._air_until - self.t < C.TRICK_TIME:
            self.ui.cue("trick_tarde", 0.8, 1.0, None)
            return None
        name = None
        for d in ("up", "down", "left", "right"):
            if d in held or self.t - self._dirs.get(d, -9.0) <= C.TRICK_GRACE:
                name = d
                break
        points = C.POINTS_TRICK
        if name in self._flight:
            points *= C.REPEAT_FACTOR
        self._flight.append(name)
        self._trick_until = self.t + C.TRICK_TIME
        self.tricks += 1
        self.combo += 1
        self.best_combo = max(self.best_combo, self.combo)
        self.score += int(points * multiplier(self.combo))
        self.ui.cue("trick", 1.0, C.TRICKS[name], C.TRICK_PAN.get(name))
        self._sync_layers()
        return name or "neutro"

    # --- tempo ---------------------------------------------------------------
    def update(self, dt):
        if self.stopped:
            return
        self.t += dt
        self._run_events()
        if self.paused:
            return
        self._landing()
        self._cues()
        self._expire()
        self._plan()
        self._rolling()

    def _run_events(self):
        while self.events and self.events[0][0] <= self.t and not self.paused:
            _, kind, value = self.events.pop(0)
            if kind == "scenario":
                self.scenario = value
                self.ui.scenario(value)
                sc = SCENARIOS[value]
                if value not in self.scenarios_seen:
                    self.scenarios_seen.add(value)
                    self._pause(sc["intro"], None)
                    self.ui.remember()
                else:
                    self.ui.say(sc["nome"])
            elif kind == "brief":
                self._pause(self._brief_text(value), value)
                self.seen.add(value)
                self.ui.remember()

    def _pause(self, text, kind):
        self.paused = True
        self.ui.brief(text, kind, self._resume)

    def _resume(self):
        self.paused = False

    def _brief_text(self, kind):
        info = KIND_INFO[kind]
        name = SCENARIOS[self.scenario]["objetos"].get(kind, info["nome"])
        return ("Novo obstáculo: %s, para %s. Avisa com %s, em quatro batidas. %s"
                % (name, info["verbo"], info["som"], info["dica"]))

    def _landing(self):
        if self._in_air and self.t >= self._air_until:
            self._in_air = False
            self.ui.cue("pouso", 1.0, 1.0, None)
            if self._flight:
                n = len(self._flight)
                self.score += C.POINTS_LAND * n * multiplier(self.combo)
                self.ui.cue("pouso_limpo", 0.8, 1.0, None)
            self._flight = []

    def _cues(self):
        for o in self.obstacles:
            while o.cues <= C.WARN_BEATS:
                when = o.at - (C.WARN_BEATS - o.cues) * o.beat
                if self.t < when:
                    break
                last = o.cues == C.WARN_BEATS
                self.ui.cue(o.kind + ("_agora" if last else ""), C.CUE_VOLUMES[o.cues], 1.0, None)
                o.cues += 1

    def _expire(self):
        for o in self.obstacles:
            if self.t > o.at + o.late:
                self.obstacles.remove(o)
                self._fall()
                return

    def _window(self):
        for o in self.obstacles:
            if o.at - o.early <= self.t <= o.at + o.late:
                return o
        return None

    def _start(self, kind):
        info = C.KINDS[kind]
        self._busy_until = self.t + info["busy"]
        self._crouch_until = self.t + info["busy"] if kind == "agachar" else 0.0
        self._grind_until = self.t + info["busy"] if kind == "corrimao" else 0.0
        if info["air"]:
            self._air_until = self.t + info["air"]
            self._in_air = True
            self._flight = []
        self.ui.cue(START_SOUND[kind], 1.0, 1.0, None)

    def _fall(self):
        self.combo = 0
        self.lives -= 1
        self.falls += 1
        self._air_until = self._busy_until = self._crouch_until = self._grind_until = 0.0
        self._in_air = False
        self._flight = []
        self._fall_until = self._busy_until = self.t + C.FALL_TIME
        self.ui.cue("tombo", 1.0, 1.0, None)
        self._sync_layers()
        if self.lives <= 0:
            self.over = True
            self.ui.rolling(0.0, 1.0)
            self.ui.over(self)
            return
        self.ui.say("Tombo. %s." % lives_text(self.lives))
        # o que ia chegar durante a queda e a recuperação some
        cutoff = self.t + C.FALL_TIME + 0.4 + C.WARN_BEATS * beat_at(self.t)
        self.obstacles = [o for o in self.obstacles if o.at > cutoff]
        cursor = self.t + C.FALL_TIME + 0.4
        if self.obstacles:
            last = self.obstacles[-1]
            cursor = max(cursor, last.at + C.KINDS[last.kind]["busy"] + 0.3)
        self._cursor = max(cursor, self._floor)

    def _sync_layers(self):
        n = layers_for(self.combo)
        if n != self._layers:
            self._layers = n
            self.ui.layers(n)

    def _rolling(self):
        if self.t < self._fall_until or self._grind_until > self.t or self.airborne:
            volume = 0.0
        elif self._crouch_until > self.t:
            volume = 0.4
        else:
            volume = 1.0
        self.ui.rolling(volume, 0.8 + 0.4 * (self.speed - 1.0) / C.SPEED_GAIN)

    # --- o que vem pela frente -------------------------------------------------
    def _event(self, at, kind, value):
        self.events.append((at, kind, value))
        self.events.sort(key=lambda e: e[0])

    def _plan(self):
        while len(self.obstacles) < 3:
            self._plan_one()

    def _plan_one(self):
        if self._in_scenario >= C.PER_SCENARIO:
            self._plan_scenario += 1
            self._in_scenario = 0
            at = self._last_end + 1.0
            self._event(at, "scenario", self._plan_scenario % len(SCENARIOS))
            self._cursor = max(self._cursor, at) + C.TRANSITION_GAP
            self._floor = self._cursor
        sc = SCENARIOS[self._plan_scenario % len(SCENARIOS)]
        kinds = [k for k in sc["objetos"]]
        fresh = [k for k in kinds if k not in self.seen and k not in self._briefed]
        if fresh:
            kind = fresh[0]
        else:
            choices = [k for k in kinds if k != self._last_kind] or kinds
            kind = self.rng.choice(choices)
        if kind not in self.seen and kind not in self._briefed:
            self._briefed.add(kind)
            self._event(self._cursor, "brief", kind)
        beat = beat_at(self._cursor)
        extra = self.rng.uniform(*C.EXTRA_GAP) / speed_at(self._cursor)
        at = self._cursor + C.WARN_BEATS * beat + extra
        o = Obstacle(kind, sc["objetos"][kind], at, beat)
        self.obstacles.append(o)
        self._cursor = at + C.KINDS[kind]["busy"] + 0.3
        self._last_end = at + o.late
        self._last_kind = kind
        self._in_scenario += 1

    # --- falas -----------------------------------------------------------------
    def status_text(self):
        return ("%s. %d pontos. Combo %d, multiplicador %d. %s."
                % (SCENARIOS[self.scenario]["nome"], self.score, self.combo,
                   multiplier(self.combo), lives_text(self.lives)))

    def summary_text(self):
        return ("%d pontos. %s, %s, %s, melhor combo %d."
                % (self.score, plural(self.cleared, "obstáculo vencido", "obstáculos vencidos"),
                   plural(self.tricks, "manobra", "manobras"),
                   plural(self.falls, "tombo", "tombos"), self.best_combo))


START_SOUND = {"pular": "pulo", "agachar": "agacha", "corrimao": "grind",
               "rampa": "rampa_sobe", "escada": "escada_desce"}


def lives_text(n):
    return {0: "Sem vidas", 1: "Última vida"}.get(n, "%d vidas" % n)


def plural(n, one, many):
    return "%d %s" % (n, one if n == 1 else many)
