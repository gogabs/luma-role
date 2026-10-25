# Rolê

Patinação urbana só com som, para o R36S acessível. Você patina sozinho, cada
vez mais rápido, e escuta os obstáculos chegando: **três batidas** do mesmo
som avisam, cada uma mais forte, e é na **terceira** que se aperta.

Não precisa de estéreo nem de fone: cada obstáculo tem um som só dele, e o que
muda de um para outro é o timbre e a altura, como no Rio Abaixo. O estéreo só
complementa (as manobras soam à esquerda ou à direita conforme o direcional).

| Som do aviso | Obstáculo | Botão |
|---|---|---|
| Batida seca de madeira, grave | Obstáculo baixo (banco, cone): **pular** | B |
| Assobio que **desce** | Obstáculo alto (galho, cancela): **passar rente** | Baixo |
| Assobio que **sobe** | **Rampa** | Cima |
| Sininho metálico agudo | **Corrimão**: salte com B e **segure A** durante o grind | B, depois A |
| Três notas descendo, como degraus | **Escada**: **segure X** por todo o percurso | X |

Escada e corrimão pedem segurar o botão até o som acabar (degraus ou metal raspando); um toque agudo de duas notas subindo avisa a hora de soltar; soltar antes, ou pousar no corrimão sem A, é tombo.

No ar (depois de pular ou da rampa), **Y** faz uma manobra; Y com um
direcional faz outra. Cada uma toca uma nota diferente e o jogo fala o nome (giro de 180, 360 para a esquerda, 360 para a direita, mute grab, fishbrain). Uma manobra dura um
quarto de segundo e precisa caber no voo. Se for tarde, um toque seco avisa e
nada acontece. Cada vitória ou manobra sobe o **combo**; a cada quatro, o
multiplicador de pontos sobe (até 5×). A música ganha uma camada nova com o
combo: bateria e baixo, chimbal, acordes, melodia e arpejo. Errar é um **tombo**:
zera o combo, tira as camadas e custa uma de três vidas.

A corrida passa por quatro cenários, cada um com música e obstáculos próprios:
**praça** (banco, galho, rampa), **rua** (+ corrimão), **estacionamento** (+ escada)
e **escola** (tudo). Depois volta à praça, mais rápido. Na primeira vez que um
cenário ou um obstáculo aparece, o jogo para, explica e toca as três batidas
de exemplo. O menu "Aprender os sons" repete isso quando quiser.

## Controles

| Botão | O quê |
|---|---|
| B / Baixo / Cima | Pular / passar rente / rampa (na terceira batida) |
| B e segurar A | Corrimão: salto na terceira batida, A segurado no grind |
| Segurar X | Escada: apertar na terceira batida e segurar até o fim |
| Y (com ou sem direcional) | Manobra no ar |
| Select | Pontos, combo, multiplicador e vidas |
| Start | Pausa (dá para mudar o volume da música) |

No PC: setas, Enter ou Z (B), Backspace ou X (A), S (X), A (Y), Tab (Select),
Esc (Start).

## Rodar

No PC (Windows), com o Mage Core clonado ao lado ou a cópia em `r36s_a11y/`:

```bat
python main.py
```

No console, com o console ligado em rede (SSH `r36s`):

```bash
./instalar.sh
```

Ou copie a pasta do zip (`python3 tools/empacotar.py` gera `dist/`) para `a11y/games`
no cartão.

## Desenvolvimento

```bash
python3 -m unittest discover -s tests   # regras, textos e conferência dos sons
python3 tools/gerar_sons.py             # sons e música por síntese, em sounds/
python3 tools/simular.py 120            # roda o main.py de verdade, sem tela, com jogador automático
python3 tools/sync_sdk.py               # atualiza a cópia do Mage Core em r36s_a11y/
python3 tools/empacotar.py              # dist/<id>-<versão>-r36s.zip
```

Os números da corrida (ritmo, janelas de acerto, pontos, camadas) estão em
[pista/config.py](pista/config.py); os cenários, em [pista/cenarios.py](pista/cenarios.py).
Autores e licenças dos sons em [CREDITOS.md](CREDITOS.md).
