#!/usr/bin/env python3
"""Monta o zip para o cartão do R36S: dist/<id>-<versão>-r36s.zip.

Dentro vai uma pasta <id>/ com o jogo, o Mage Core (r36s_a11y/) e os sons. É só
copiar a pasta para a/games no cartão (EASYROMS), ou rodar ./instalar.sh pelo SSH.
"""
import json
import os
import sys
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
INCLUDE = ("game.json", "main.py", "README.md", "CREDITOS.md", "pista", "sounds", "r36s_a11y")


def main():
    with open(os.path.join(ROOT, "game.json"), encoding="utf-8") as f:
        meta = json.load(f)
    game_id = meta["id"]
    out_dir = os.path.join(ROOT, "dist")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "%s-%s-r36s.zip" % (game_id, meta["version"]))
    if len(sys.argv) > 1:
        out = sys.argv[1]
    names = set()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for item in INCLUDE:
            path = os.path.join(ROOT, item)
            if os.path.isfile(path):
                files = [path]
            else:
                files = [os.path.join(d, f) for d, dirs, fs in os.walk(path)
                         if "__pycache__" not in d for f in fs if not f.endswith(".pyc")]
            for full in sorted(files):
                arc = game_id + "/" + os.path.relpath(full, ROOT).replace(os.sep, "/")
                # a EASYROMS é exFAT: nada de nomes que só diferem em maiúsculas
                if arc.lower() in names:
                    raise SystemExit("nome repetido sem diferença de maiúsculas: " + arc)
                names.add(arc.lower())
                z.write(full, arc)
    print("%s (%.1f MB, %d arquivos)" % (out, os.path.getsize(out) / 1e6, len(names)))


if __name__ == "__main__":
    main()
