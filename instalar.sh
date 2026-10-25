#!/bin/bash
# Empacota o jogo com a biblioteca Python do Mage Core e instala no console pelo SSH.
#
#   ./instalar.sh [host-ssh]     (padrão: r36s)
#
# Não reinicia nada: o Luma percebe o jogo novo sozinho. Com o jogo aberto, não
# instala, porque ele carrega os sons da pasta instalada. O recorde fica nos saves.
set -euo pipefail
HOST=${1:-r36s}
HERE=$(cd "$(dirname "$0")" && pwd)
ID=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['id'])" "$HERE/game.json")

if ssh "$HOST" "for p in /proc/[0-9]*; do readlink \"\$p/cwd\"; done 2>/dev/null | grep -Eq '^/(roms|opt)/a11y/games/$ID(/|\$)'"; then
  echo "O jogo está aberto no console. Feche e rode de novo."
  exit 1
fi

PKG=$(mktemp -d)
trap 'rm -rf "$PKG"' EXIT
mkdir -p "$PKG/$ID"
cp -r "$HERE/game.json" "$HERE/main.py" "$HERE/pista" "$HERE/sounds" "$HERE/r36s_a11y" "$PKG/$ID/"
find "$PKG" -name __pycache__ -prune -exec rm -rf {} +

tar -C "$PKG" -czf - "$ID" | ssh "$HOST" "
  set -e; mkdir -p /roms/a11y/games; cd /roms/a11y/games
  rm -rf .$ID.novo && mkdir .$ID.novo
  tar -xzmf - -C .$ID.novo
  rm -rf $ID && mv .$ID.novo/$ID . && rmdir .$ID.novo
  rm -rf /opt/a11y/games/$ID
  echo \"instalado: \$(ls $ID/sounds | wc -l) sons\"; df -h /roms | tail -1"
