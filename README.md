# 3dtools

Ferramentas para modelagem 3D, arquivos STL e impressão 3D.

## Ferramentas

- [`stl-solido/`](stl-solido/index.html) — Reparador de STL (página web, abrir no navegador)
- [`reparador-gcode/`](reparador-gcode/index.html) — Reparador de G-code (página web)
- [`bandeja-800ml/`](bandeja-800ml/gerar_bandeja.py) — Gerador paramétrico da bandeja de 800 mL (STL, STEP, DXF)
- [`bandeja-redonda/`](bandeja-redonda/gerar_bandeja_redonda.py) — Gerador paramétrico da bandeja redonda (STL, STEP, DXF)
- [`ferramentas/converter_dwg.py`](ferramentas/converter_dwg.py) — Converte DXF/STEP gerados em DWG usando o AutoCAD

## Requisitos (scripts Python)

```
pip install -r requirements.txt
```

Os arquivos gerados ficam em `<projeto>/saida/` (não versionados).
