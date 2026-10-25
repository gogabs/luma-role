#!/usr/bin/env python3
"""Rolê: patinação urbana só com som. Quatro batidas avisam; aperte na quarta."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# Durante o desenvolvimento, usa a biblioteca do repositório vizinho se não houver cópia aqui.
if not os.path.isdir(os.path.join(HERE, "r36s_a11y")):
    sys.path.insert(1, os.path.join(HERE, "..", "r36s-a11y-sdk", "python"))

import r36s_a11y as a11y

from pista import config as C
from pista import textos as T
from pista.cenarios import KIND_INFO, KIND_ORDER, SCENARIOS
from pista.corrida import Run

game = a11y.Game(repeat=False)
SETTINGS_FILE = os.path.join(game.save_dir, "config.json")
BOARD = "pontos"
DIRS = ("up", "down", "left", "right")
SURFACE_GAIN = {"rodas": 0.5, "degraus": 0.7, "grind": 0.7}
MUSIC_LEVELS = (("alta", 1.0), ("média", 0.6), ("baixa", 0.3), ("desligada", 0.0))


# --- ajustes e o que já foi explicado --------------------------------------------
def load_settings():
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    level = data.get("musica")
    return {"musica": level if level in range(len(MUSIC_LEVELS)) else 1,
            "seen": [k for k in data.get("seen", []) if k in KIND_ORDER],
            "scenarios_seen": [i for i in data.get("scenarios_seen", [])
                               if isinstance(i, int) and 0 <= i < len(SCENARIOS)]}


def save_settings():
    run = state["run"]
    if run is not None:
        settings["seen"] = sorted(run.seen)
        settings["scenarios_seen"] = sorted(run.scenarios_seen)
    tmp = SETTINGS_FILE + ".novo"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(settings, f)
    os.replace(tmp, SETTINGS_FILE)


settings = load_settings()
state = {"phase": "menu", "run": None, "rolling": {}, "demo": 0}

sounds = {}
for f in sorted(os.listdir(os.path.join(game.dir, "sounds"))):
    base, ext = os.path.splitext(f)
    if ext.lower() in (".wav", ".ogg"):
        sounds[base] = game.sound.load(base, os.path.join("sounds", f))
menu_sounds = {"move": sounds["menu_mover"], "select": sounds["menu_confirmar"]}


# --- música: 5 camadas por cenário tocam juntas; o combo abre o volume ----------------
class Music:
    LAYERS = 5

    def __init__(self):
        self.voices = []
        self.layers = 1
        self.level = MUSIC_LEVELS[settings["musica"]][1]

    def start(self, scenario):
        self.stop(fade=1.0)
        name = SCENARIOS[scenario]["id"]
        self.voices = [sounds["musica_%s_%d" % (name, i)].play(loop=True, volume=self._volume(i))
                       for i in range(self.LAYERS)]

    def _volume(self, i):
        return self.level if i < self.layers else 0.0

    def set_layers(self, n, fade=0.5):
        self.layers = n
        for i, voice in enumerate(self.voices):
            voice.set_volume(self._volume(i), fade=fade)

    def set_level(self, level):
        self.level = level
        for i, voice in enumerate(self.voices):
            voice.set_volume(self._volume(i), fade=0.2)

    def stop(self, fade=0.0):
        for voice in self.voices:
            voice.stop(fade=fade)
        self.voices = []


music = Music()


# --- o que a corrida pede ao jogo ----------------------------------------------------
class UI:
    def cue(self, name, volume=1.0, pitch=1.0, pan=None):
        sound = sounds.get(name)
        if sound is not None:
            sound.play(volume=volume, pitch=pitch, pan=pan)

    def say(self, text):
        game.say(text)

    def brief(self, text, kind, resume):
        def after(done):
            if kind is not None and state["phase"] == "run":
                demo(kind, resume)
            else:
                resume()
        game.say(text, on_done=after)

    def scenario(self, index):
        music.start(index)

    def layers(self, n):
        music.set_layers(n, fade=0.4 if n > music.layers else 0.3)

    def rolling(self, volume, pitch, surface="rodas"):
        for name, voice in state["rolling"].items():
            on = name == surface
            voice.set_volume(SURFACE_GAIN[name] * volume if on else 0.0, fade=0.05)
            if on:
                voice.set_pitch(pitch)

    def remember(self):
        save_settings()

    def over(self, run):
        finish(run)


ui = UI()


def demo(kind, then=None):
    """Toca as quatro batidas do obstáculo, como na corrida, e chama then()."""
    state["demo"] += 1
    token = state["demo"]
    for i in range(C.WARN_BEATS + 1):
        name = kind + ("_agora" if i == C.WARN_BEATS else "")
        game.after(0.3 + i * C.BEAT, lambda name=name, v=C.CUE_VOLUMES[i]:
                   ui.cue(name, v) if state["demo"] == token else None)
    game.after(0.3 + (C.WARN_BEATS + 1) * C.BEAT + 0.3,
               lambda: then() if then is not None and state["demo"] == token else None)


# --- corrida -----------------------------------------------------------------------------
def new_game():
    main_menu.close()
    run = Run(ui, seen=set(settings["seen"]), scenarios_seen=set(settings["scenarios_seen"]))
    state.update(phase="run", run=run)
    state["rolling"] = {n: sounds[n + "_loop"].play(loop=True, volume=0.0) for n in SURFACE_GAIN}
    music.layers = 1


def stop_surfaces():
    for voice in state["rolling"].values():
        voice.stop(fade=0.3)
    state["rolling"] = {}


def end_run():
    state["phase"] = "menu"
    state["run"] = None
    music.stop(fade=1.0)
    stop_surfaces()


def finish(run):
    state["phase"] = "fim"
    music.stop(fade=1.5)
    stop_surfaces()
    save_settings()

    def result():
        ui.cue("fim", 0.8)
        previous = game.high_scores.best(BOARD)
        position = (game.high_scores.add(BOARD, run.score, board_name="Rolê")
                    if run.score > 0 else None)
        text = T.final(run, position, previous["score"] if previous else None)
        game.after(1.4, lambda: game.say(text, on_done=lambda done: back_to_menu()))
    game.after(1.4, result)


def back_to_menu():
    end_run()
    open_main()


@game.on_update
def update(dt):
    run = state["run"]
    if state["phase"] == "run" and run is not None:
        run.update(dt)


# --- menus -------------------------------------------------------------------------------
def music_item():
    return "Música: " + MUSIC_LEVELS[settings["musica"]][0]


def main_items():
    return ["Jogar", T.SOUNDS_MENU, "Como jogar", music_item(), "Recorde", "Sair"]


def open_main(index=0, announce_help=False):
    main_menu.items = main_items()
    main_menu.open(index=index, announce_help=announce_help)


def cycle_music(menu, index):
    settings["musica"] = (settings["musica"] + 1) % len(MUSIC_LEVELS)
    music.set_level(MUSIC_LEVELS[settings["musica"]][1])
    save_settings()
    menu.items[index] = music_item()
    game.say(menu.items[index])


def on_main(index, item):
    if item == "Jogar":
        new_game()
    elif item == T.SOUNDS_MENU:
        main_menu.close()
        learn_menu.open()
    elif item == "Como jogar":
        main_menu.close()
        help_menu.open()
    elif item.startswith("Música"):
        cycle_music(main_menu, index)
    elif item == "Recorde":
        best = game.high_scores.best(BOARD)
        game.say("Recorde: %d pontos." % best["score"] if best
                 else "Ainda não há recorde. Vá patinar!")
    else:
        game.quit()


main_menu = a11y.Menu(game, "Rolê", main_items(), on_select=on_main, on_back=game.quit,
                      sounds=menu_sounds)


def close_help():
    help_menu.close()
    open_main(2)


help_menu = a11y.Menu(
    game, "Como jogar", [t for t, _ in T.HELP] + ["Voltar"],
    on_select=lambda i, item: close_help() if item == "Voltar" else game.say(T.HELP[i][1]),
    on_back=close_help, sounds=menu_sounds)


LEARN_BUTTONS = {"pular": "b", "agachar": "down", "rampa": "up", "corrimao": "b e a", "escada": "x"}


def learn_item(kind):
    label = " e ".join(game.button_label(b) for b in LEARN_BUTTONS[kind].split(" e "))
    return "%s, %s" % (KIND_INFO[kind]["nome"].capitalize(), label)


def close_learn():
    state["demo"] += 1
    learn_menu.close()
    open_main(1)


def on_learn(index, item):
    if index >= len(KIND_ORDER):
        close_learn()
        return
    kind = KIND_ORDER[index]
    game.say(T.learn_text(kind), on_done=lambda done: demo(kind))


learn_menu = a11y.Menu(game, "Aprender os sons", [learn_item(k) for k in KIND_ORDER] + ["Voltar"],
                       on_select=on_learn, on_back=close_learn, sounds=menu_sounds)


def pause():
    run = state["run"]
    run.halted = True
    game.sound.pause_all()
    pause_menu.items = ["Continuar", music_item(), "Sair para o menu"]
    pause_menu.open()


def resume():
    pause_menu.close()
    run = state["run"]
    game.sound.resume_all()
    game.say("Continuando.", on_done=lambda done: run.resume())


def on_pause(index, item):
    if item == "Continuar":
        resume()
    elif item.startswith("Música"):
        cycle_music(pause_menu, index)
    else:
        pause_menu.close()
        game.sound.resume_all()
        run = state["run"]
        run.halted = True
        back_to_menu()


pause_menu = a11y.Menu(game, "Pausa", ["Continuar", music_item(), "Sair para o menu"],
                       on_select=on_pause, on_back=resume, sounds=menu_sounds)


# --- controles -------------------------------------------------------------------------
@game.on_button
def button(b, st, ms):
    run = state["run"]
    if state["phase"] != "run" or run is None:
        return
    if st == a11y.UP:
        run.button_up(b)
        return
    if st != a11y.DOWN:
        return
    if run.paused:      # uma explicação está sendo falada
        return
    run.button_down(b)
    if b in DIRS:
        run.direction(b)
    kind = C.BUTTON_KIND.get(b)
    if kind is not None:
        run.action(kind)
    elif b == "y":
        run.trick()
    elif b == "select":
        game.say(run.status_text())
    elif b == "start":
        pause()


@game.on_start
def start():
    game.say(T.INTRO, on_done=lambda done: open_main(announce_help=True))


@game.on_quit
def quit_():
    save_settings()


game.run()
