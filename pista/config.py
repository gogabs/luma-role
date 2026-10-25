"""Números da corrida. Tempos em segundos."""

# Ritmo: cada obstáculo avisa com 3 batidas do mesmo som; a terceira, mais forte, é a hora de agir.
BEAT = 0.5                # intervalo entre as batidas no começo
MIN_BEAT = 0.3            # e o mais curto que chega, na velocidade máxima
SPEED_GAIN = 0.7          # a velocidade vai de 1.0 até 1.0 + isto
SPEED_TAU = 100.0         # constante de tempo (s) da subida
WARN_BEATS = 2            # batidas de aviso antes da hora de agir (a terceira é a hora)
CUE_VOLUMES = (0.6, 0.8, 1.0)   # as 2 de aviso e a da hora

# Janela de acerto, em fração da batida (com um mínimo, para a velocidade máxima)
EARLY = 0.7
LATE = 0.4
EARLY_MIN = 0.2
LATE_MIN = 0.12
PERFECT = 0.1             # |erro| até aqui é "perfeito"

# Cada ação: botão, tempo no ar (quando sobe), tempo ocupado e pontos extras
KINDS = {
    "pular":    {"button": "b",    "air": 0.55, "busy": 0.55, "extra": 0},
    "agachar":  {"button": "down", "air": 0.0,  "busy": 0.5,  "extra": 0},
    "corrimao": {"button": "a",    "air": 0.0,  "busy": 1.7,  "extra": 80},
    "rampa":    {"button": "up",   "air": 1.35, "busy": 1.35, "extra": 120},
    "escada":   {"button": "x",    "air": 0.0,  "busy": 1.4,  "extra": 60, "hold": 1.4},
    "curva_esq": {"button": "left", "air": 0.0, "busy": 1.4,  "extra": 40, "hold": 1.4},
    "curva_dir": {"button": "right", "air": 0.0, "busy": 1.4, "extra": 40, "hold": 1.4},
}
# Quem começa cada ação. O corrimão começa com B (o salto) e o A é só segurado; a
# escada começa com X, que fica segurado até o fim.
BUTTON_KIND = {"b": "pular", "down": "agachar", "up": "rampa", "x": "escada",
               "left": "curva_esq", "right": "curva_dir"}
HOLD_KINDS = tuple(k for k, v in KINDS.items() if v.get("hold"))   # segurados até o fim

# Escada e corrimão pedem segurar o botão até o fim; soltar antes é tombo.
RAIL_JUMP = 0.3           # do salto (B) até pousar no corrimão; o A precisa estar segurado aí
RAIL_TIME = 1.4           # o grind, com A segurado
RELEASE_GRACE = 0.08      # soltar no fim, com esta folga, ainda vale
POINTS_HOLD = 60          # bônus por completar o percurso

# Manobras: Y no ar, com o direcional (ou sem). Nota na escala pentatônica.
TRICK_TIME = 0.25         # quanto dura uma manobra; precisa caber no que falta do voo
TRICKS = {None: 1.0, "left": 1.122, "up": 1.26, "right": 1.498, "down": 1.682}
TRICK_NAMES = {None: "giro de 180", "left": "360 para a esquerda", "right": "360 para a direita",
               "up": "mute grab", "down": "fishbrain"}
TRICK_PAN = {"left": -0.6, "right": 0.6}
TRICK_GRACE = 0.15        # o direcional apertado até isto antes do Y ainda vale

POINTS_OBSTACLE = 100
POINTS_PERFECT = 50
POINTS_TRICK = 60
POINTS_LAND = 20          # por manobra, no pouso
REPEAT_FACTOR = 0.5       # a mesma manobra de novo no mesmo voo vale menos
MULTIPLIER_EVERY = 4      # +1 no multiplicador a cada tantos de combo
MULTIPLIER_MAX = 5

# Camadas da música: combo mínimo para cada uma entrar
COMBO_LAYERS = (0, 2, 5, 9, 14)

LIVES = 3
FALL_TIME = 1.3           # sem controle depois de um tombo
FIRST_OBSTACLE = 4.0
EXTRA_GAP = (0.5, 1.3)    # folga aleatória entre o fim de um obstáculo e o aviso do próximo
PER_SCENARIO = 10
TRANSITION_GAP = 3.0
