# 3dtools

Ferramentas para modelagem 3D, arquivos STL e impressão 3D.

## App Ferramentas 3D (`app/`)

Um único app web com página inicial e duas ferramentas:

- [`app/index.html`](app/index.html) — Página inicial
- [`app/stl/`](app/stl/index.html) — Reparador de STL
- [`app/gcode/`](app/gcode/index.html) — Reparador de G-code

Publicado em https://ferramentas-3d.vercel.app

## Scripts Python

- [`bandeja-800ml/`](bandeja-800ml/gerar_bandeja.py) — Gerador paramétrico da bandeja de 800 mL (STL, STEP, DXF)
- [`bandeja-redonda/`](bandeja-redonda/gerar_bandeja_redonda.py) — Gerador paramétrico da bandeja redonda (STL, STEP, DXF)
- [`ferramentas/converter_dwg.py`](ferramentas/converter_dwg.py) — Converte DXF/STEP gerados em DWG usando o AutoCAD

```
pip install -r requirements.txt
```

Os arquivos gerados ficam em `<projeto>/saida/` (não versionados).
