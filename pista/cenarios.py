"""Os cenários: música, obstáculos que aparecem e como cada um se chama."""

# O som e o botão de cada obstáculo dependem só da ação (config.KINDS); o cenário
# só dá o nome. Assim, quem aprendeu um som reconhece em qualquer lugar.
SCENARIOS = (
    {"id": "praca", "nome": "Praça",
     "intro": "Praça. Calçada larga, bancos de madeira e árvores. Música tranquila.",
     "objetos": {"pular": "banco", "agachar": "galho baixo", "rampa": "rampa de concreto"}},
    {"id": "rua", "nome": "Rua",
     "intro": "Rua. Calçada movimentada, toldos e rampas de entrega. A música ganha mais batida.",
     "objetos": {"pular": "lixeira caída", "agachar": "toldo baixo",
                 "rampa": "rampa de entrega", "corrimao": "corrimão da calçada"}},
    {"id": "estacionamento", "nome": "Estacionamento",
     "intro": "Estacionamento. Cones, cancelas e a escada da garagem. A música tem eco.",
     "objetos": {"pular": "cone", "agachar": "cancela", "rampa": "rampa da garagem",
                 "corrimao": "corrimão da rampa de pedestres", "escada": "escada da garagem"}},
    {"id": "escola", "nome": "Escola",
     "intro": "Escola. Mochilas no chão, bandeirinhas e a escadaria da entrada. A música é saltitante.",
     "objetos": {"pular": "mochila no chão", "agachar": "varal de bandeirinhas",
                 "rampa": "rampa de acessibilidade", "corrimao": "corrimão do pátio",
                 "escada": "escadaria da entrada"}},
)

# O que cada ação é, para a ajuda e para a primeira vez que o obstáculo aparece
KIND_INFO = {
    "pular": {"nome": "obstáculo baixo", "verbo": "pular",
              "som": "uma batida seca de madeira, sempre igual",
              "dica": "Aperte B na quarta batida para pular."},
    "agachar": {"nome": "obstáculo alto", "verbo": "passar rente",
                "som": "um assobio que desce",
                "dica": "Aperte para baixo na quarta batida para se abaixar e passar rente."},
    "rampa": {"nome": "rampa", "verbo": "pegar a rampa",
              "som": "um assobio que sobe",
              "dica": "Aperte para cima na quarta batida para pegar a rampa. O voo é longo: dá tempo de fazer manobras."},
    "corrimao": {"nome": "corrimão", "verbo": "entrar no corrimão",
                 "som": "um sininho agudo",
                 "dica": "Aperte A na quarta batida para deslizar no corrimão."},
    "escada": {"nome": "escada", "verbo": "descer a escada",
               "som": "três notas descendo, como degraus",
               "dica": "Aperte X na quarta batida para descer a escada, e faça manobras no voo."},
}

KIND_ORDER = ("pular", "agachar", "rampa", "corrimao", "escada")
