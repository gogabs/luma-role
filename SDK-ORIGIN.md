# Origem e atualização do Mage Core

A cópia de reserva em `r36s_a11y/` vem de
[gogabs/r36s-a11y-sdk](https://github.com/gogabs/r36s-a11y-sdk), no commit
registrado em `sdk-origin.json`, junto com os hashes dos arquivos. Para atualizar:

```sh
python3 tools/sync_sdk.py --sdk ../r36s-a11y-sdk
python3 -m unittest discover -s tests
git diff -- r36s_a11y sdk-origin.json
```
