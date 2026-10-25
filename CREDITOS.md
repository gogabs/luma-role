# Créditos dos sons

Todos os sons e a música do jogo são **sintetizados** por
[tools/gerar_sons.py](tools/gerar_sons.py), só com a biblioteca padrão do Python.
Nada é gravado nem baixado de terceiros, então não há autores a creditar e os
arquivos de `sounds/` têm a mesma licença do jogo. Para trocar um som, ponha
um arquivo com o mesmo nome em `sounds/` (WAV ou OGG); se ele vier de terceiros,
registre aqui autor, licença (CC0 ou CC-BY) e fonte.

| Grupo | Arquivos | Como é feito |
|---|---|---|
| Avisos dos obstáculos | `pular`, `agachar`, `rampa`, `corrimao`, `escada` e as versões `_agora` | madeira (seno com clique), assobios que descem e sobem, sino com parciais inarmônicos, marimba |
| Patinador | `pulo`, `agacha`, `grind`, `rampa_sobe`, `escada_desce`, `pouso`, `pouso_limpo`, `tombo`, `rodas` | ruído filtrado e golpes graves |
| Retorno | `acerto`, `perfeito`, `trick` (corda dedilhada, Karplus-Strong), `trick_tarde`, `fim`, `cenario`, menus | senos curtos |
| Música | `musica_<cenário>_0` a `_4` | 5 camadas por cenário: bumbo e baixo, chimbal e palma, acordes, melodia, arpejo |
