# Créditos dos sons

Os sons e a música são **sintetizados** por [tools/gerar_sons.py](tools/gerar_sons.py), só
com a biblioteca padrão do Python, e têm a licença do jogo. A única exceção é o
raspado de metal do grind, uma gravação em **CC0 1.0** (não exige crédito, mas fica aqui):

| No jogo | Original | Autor | Fonte | O que mudou |
|---|---|---|---|---|
| `freada`, `freada_agora`, `freada_loop` | Screeching tires 1 (#2368), de 0,05 s a 1,95 s | Joseph Sardin | [BigSoundBank](https://bigsoundbank.com/screeching-tires-1-s2368.html) | mono, 44,1 kHz; recortes, e a da hora soma uma cópia mais grave; o laço é costurado |
| `rampa` | Whoosh 9 (#1802) | Joseph Sardin | [BigSoundBank](https://bigsoundbank.com/whoosh-9-s1802.html) | mono; acelerado para subir de altura |
| `rampa_agora` | Whoosh 10 (#1798) e a anterior | Joseph Sardin | [BigSoundBank](https://bigsoundbank.com/whoosh-10-s1798.html) | mono; acelerado |
| `grind_loop` | Grinding metal barrier opening 3 (#2357), de 0,55 s a 1,5 s | Joseph Sardin | [BigSoundBank](https://bigsoundbank.com/grinding-metal-barrier-opening-3-s2357.html) | mono, 44,1 kHz, costurado em laço e misturado a um raspado sintético; o recorte está em `sons-originais/` |

Dois sons vêm da biblioteca de sons do Gabs (pasta `sbyw`); a origem e a licença deles ainda
precisam ser confirmadas. Os recortes mono estão em `sons-originais/`:

| No jogo | Original | O que mudou |
|---|---|---|
| `corrimao`, `corrimao_agora` | `wallpole.ogg` (barra de metal) | mono; a da hora soma cópias uma quinta acima e uma oitava abaixo |
| `escada`, `escada_agora` | `wallwood.ogg` (impacto de madeira), primeiros 0,17 s | mono; três pancadas descendo (1,3×, 1×, 0,77×) |

Os demais sons: Para trocar um som, ponha
um arquivo com o mesmo nome em `sounds/` (WAV ou OGG); se ele vier de terceiros,
registre aqui autor, licença (CC0 ou CC-BY) e fonte.

| Grupo | Arquivos | Como é feito |
|---|---|---|
| Avisos dos obstáculos | `pular`, `curva_esq`, `curva_dir` e as versões `_agora` | madeira (seno com clique), corneta (serra filtrada) |
| Patinador | `pulo`, `grind_entra`, `rampa_sobe`, `degraus_entra`, `pouso`, `pouso_limpo`, `tombo` | ruído filtrado, estalos e golpes graves |
| Pisos em laço | `rodas_loop` (chiado e juntas da calçada), `degraus_loop`, `curva_esq_loop`, `curva_dir_loop` | ruído filtrado, pancadas e zumbido de corneta |
| Retorno | `acerto`, `perfeito`, `trick` (corda dedilhada, Karplus-Strong), `trick_tarde`, `fim`, `cenario`, menus | senos curtos |
| Música | `musica_<cenário>_0` a `_4` | 5 camadas por cenário: bumbo e baixo, chimbal e palma, acordes, melodia, arpejo |
