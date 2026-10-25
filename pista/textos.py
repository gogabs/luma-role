"""Falas mais longas: ajuda, menus e fim de corrida."""
from .cenarios import KIND_INFO, KIND_ORDER, SCENARIOS

INTRO = ("Rolê. Você patina sozinho pela cidade e escuta os obstáculos chegando. "
         "Três batidas avisam; aperte na terceira.")

HELP = (
    ("Como funciona",
     "Você patina sozinho e cada vez mais rápido. Cada obstáculo avisa com três batidas "
     "do mesmo som, cada uma mais forte que a anterior. Aperte o botão certo na terceira, "
     "a mais forte. Acertar sobe o combo; errar é um tombo, que zera o combo e custa uma "
     "vida. São três vidas. Não precisa de estéreo: cada obstáculo tem um som só dele."),
    ("Os obstáculos",
     " ".join("%s: %s. %s" % (KIND_INFO[k]["nome"].capitalize(), KIND_INFO[k]["som"],
                              KIND_INFO[k]["dica"]) for k in KIND_ORDER)),
    ("Segurar botão",
     "A escada e o corrimão pedem que você segure o botão. Na escada, aperte X na terceira "
     "batida e segure enquanto ouvir os degraus. No corrimão, aperte B na terceira batida para "
     "saltar e segure A: o grind soa como metal raspando. Quando ouvir um toque agudo de duas notas subindo, solte. "
     "Soltar antes do fim, ou não estar segurando A ao pousar, é tombo."),
    ("Curvas",
     "A curva avisa com uma nota de corneta: grave é para a esquerda, aguda é para a direita. "
     "Na terceira batida, aperte esquerda ou direita e segure enquanto a corneta zumbir, até o toque agudo de duas notas. "
     "Soltar antes, ou apertar o lado errado, é tombo."),
    ("Manobras",
     "No ar, depois de pular ou pegar a rampa, aperte Y para fazer uma "
     "manobra. Y com um direcional faz outra manobra, e cada uma toca uma nota diferente. "
     "Cada manobra dura um quarto de segundo e precisa caber no voo. Se for tarde demais, "
     "você ouve um toque seco e nada acontece. Repetir a mesma manobra no mesmo voo vale menos."),
    ("Combo e música",
     "Cada obstáculo vencido ou manobra sobe o combo, e a cada quatro de combo o "
     "multiplicador de pontos sobe, até cinco vezes. A música ganha uma camada nova com "
     "o combo: bateria e baixo, depois chimbal, acordes, melodia e arpejo. Um tombo tira "
     "as camadas de novo."),
    ("Cenários",
     "A corrida passa por quatro cenários, cada um com uma música: " +
     ", ".join(sc["nome"] for sc in SCENARIOS) + ". Depois da escola, volta à praça, mais rápido."),
    ("Botões",
     "B pula. Para baixo se abaixa. Para cima pega a rampa. No corrimão, B salta e A fica "
     "segurado durante o grind. Na escada, X fica segurado até o fim. Esquerda e direita fazem as curvas. Y faz manobra no ar. "
     "Select diz pontos, combo e vidas. Start pausa."),
)

SOUNDS_MENU = "Aprender os sons"


def learn_text(kind):
    info = KIND_INFO[kind]
    return ("%s, para %s. Avisa com %s, em três batidas. %s"
            % (info["nome"].capitalize(), info["verbo"], info["som"], info["dica"]))


def final(run, position, best):
    text = "Fim da corrida. " + run.summary_text()
    if position == 1:
        text += " Recorde novo!" if best else " Primeiro recorde."
    elif best:
        text += " O recorde é %d." % best
    return text
