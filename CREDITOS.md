# Créditos dos sons

Os sons e a música são **sintetizados** por [tools/gerar_sons.py](tools/gerar_sons.py), só
com a biblioteca padrão do Python, e têm a licença do jogo. A única exceção é o
raspado de metal do grind, uma gravação em **CC0 1.0** (não exige crédito, mas fica aqui):

| No jogo | Original | Autor | Fonte | O que mudou |
|---|---|---|---|---|
| `grind_loop` | Grinding metal barrier opening 3 (#2357), de 0,55 s a 1,5 s | Joseph Sardin | [BigSoundBank](https://bigsoundbank.com/grinding-metal-barrier-opening-3-s2357.html) | mono, 44,1 kHz, costurado em laço e misturado a um raspado sintético; o recorte está em `sons-originais/` |

Os demais sons: Para trocar um som, ponha
um arquivo com o mesmo nome em `sounds/` (WAV ou OGG); se ele vier de terceiros,
registre aqui autor, licença (CC0 ou CC-BY) e fonte.

| Grupo | Arquivos | Como é feito |
|---|---|---|
| Avisos dos obstáculos | `pular`, `agachar`, `rampa`, `corrimao`, `escada` e as versões `_agora` | madeira (seno com clique), assobios que descem e sobem, sino com parciais inarmônicos, marimba |
| Patinador | `pulo`, `agacha`, `grind_entra`, `rampa_sobe`, `degraus_entra`, `pouso`, `pouso_limpo`, `tombo` | ruído filtrado, estalos e golpes graves |
| Pisos em laço | `rodas_loop` (chiado e juntas da calçada), `degraus_loop` | ruído filtrado e pancadas |
| Retorno | `acerto`, `perfeito`, `trick` (corda dedilhada, Karplus-Strong), `trick_tarde`, `fim`, `cenario`, menus | senos curtos |
| Música | `musica_<cenário>_0` a `_4` | 5 camadas por cenário: bumbo e baixo, chimbal e palma, acordes, melodia, arpejo |
