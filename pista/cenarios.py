"""Os cenários: música, obstáculos que aparecem e como cada um se chama."""

# O som e o botão de cada obstáculo dependem só da ação (config.KINDS); o cenário
# só dá o nome. Assim, quem aprendeu um som reconhece em qualquer lugar.
SCENARIOS = (
    {"id": "praca", "nome": "Praça",
     "intro": "Praça. Calçada larga, bancos de madeira e árvores. Música tranquila.",
     "objetos": {"pular": "banco", "freada": "pombos na calçada", "rampa": "rampa de concreto"}},
    {"id": "rua", "nome": "Rua",
     "intro": "Rua. Calçada movimentada, faixas de pedestres e rampas de entrega. A música ganha mais batida.",
     "objetos": {"pular": "lixeira caída", "freada": "faixa de pedestres",
                 "rampa": "rampa de entrega", "corrimao": "corrimão da calçada",
                 "curva_esq": "esquina à esquerda", "curva_dir": "esquina à direita"}},
    {"id": "estacionamento", "nome": "Estacionamento",
     "intro": "Estacionamento. Cones, carros saindo das vagas e a escada da garagem. A música tem eco.",
     "objetos": {"pular": "cone", "freada": "carro saindo da vaga", "rampa": "rampa da garagem",
                 "corrimao": "corrimão da rampa de pedestres", "escada": "escada da garagem",
                 "curva_esq": "curva da garagem à esquerda", "curva_dir": "curva da garagem à direita"}},
    {"id": "escola", "nome": "Escola",
     "intro": "Escola. Mochilas no chão, crianças atravessando e a escadaria da entrada. A música é saltitante.",
     "objetos": {"pular": "mochila no chão", "freada": "crianças atravessando",
                 "rampa": "rampa de acessibilidade", "corrimao": "corrimão do pátio",
                 "escada": "escadaria da entrada",
                 "curva_esq": "curva do pátio à esquerda", "curva_dir": "curva do pátio à direita"}},
)

# O que cada ação é, para a ajuda e para a primeira vez que o obstáculo aparece
KIND_INFO = {
    "pular": {"nome": "obstáculo baixo", "verbo": "pular",
              "som": "uma batida seca de madeira, sempre igual",
              "dica": "Aperte B na terceira batida para pular."},
    "freada": {"nome": "freada", "verbo": "frear e derrapar para um lado",
               "som": "um cantar de pneu",
               "dica": ("Na terceira batida, aperte e segure Baixo para frear. No meio da freada, "
                        "uma nota de corneta diz o lado: grave é esquerda, aguda é direita. Aperte esse "
                        "lado sem soltar Baixo e segure os dois até o toque agudo de duas notas.")},
    "rampa": {"nome": "rampa", "verbo": "pegar a rampa",
              "som": "um sopro de vento que sobe",
              "dica": "Aperte para cima na terceira batida para pegar a rampa. O voo é longo: dá tempo de fazer manobras."},
    "corrimao": {"nome": "corrimão", "verbo": "deslizar no corrimão",
                 "som": "um sininho agudo",
                 "dica": "Na terceira batida, aperte B para saltar e segure A para deslizar até o toque agudo de duas notas. Soltar antes é tombo."},
    "curva_esq": {"nome": "curva à esquerda", "verbo": "fazer a curva à esquerda",
                  "som": "uma nota grave de corneta",
                  "dica": "Na terceira batida, aperte esquerda e segure até o toque agudo de duas notas. Soltar antes, ou apertar o outro lado, é tombo."},
    "curva_dir": {"nome": "curva à direita", "verbo": "fazer a curva à direita",
                  "som": "uma nota aguda de corneta",
                  "dica": "Na terceira batida, aperte direita e segure até o toque agudo de duas notas. Soltar antes, ou apertar o outro lado, é tombo."},
    "escada": {"nome": "escada", "verbo": "descer a escada",
               "som": "três notas descendo, como degraus",
               "dica": "Na terceira batida, aperte X e segure até o toque agudo de duas notas. Soltar antes é tombo."},
}

KIND_ORDER = ("pular", "freada", "rampa", "corrimao", "escada", "curva_esq", "curva_dir")
