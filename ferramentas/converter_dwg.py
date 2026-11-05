"""Converte os desenhos gerados (DXF 2D e STEP 3D) em DWG usando o AutoCAD instalado.

Para cada pasta saida/ do projeto:
  <nome>.dxf   -> <nome>.dwg     (desenho técnico 2D com cotas)
  <nome>.step  -> <nome>_3d.dwg  (sólido 3D)

Uso:  python ferramentas\\converter_dwg.py [pasta_saida ...]
Sem argumentos, converte bandeja-800ml/saida e bandeja-redonda/saida.
"""

import glob
import os
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # console do Windows (cp1252) não tem ✓/✗


def acad():
    c = sorted(glob.glob(r"C:\Program Files\Autodesk\AutoCAD 20*\accoreconsole.exe"), reverse=True)
    if not c:
        sys.exit("AutoCAD não encontrado.")
    return c[0]


def rodar(entrada, linhas):
    """Abre `entrada` no AutoCAD sem janela e executa as linhas de script."""
    with tempfile.TemporaryDirectory() as tmp:
        scr = os.path.join(tmp, "s.scr")
        with open(scr, "w", encoding="ascii") as f:
            f.write("_.FILEDIA 0\n_.CMDECHO 0\n" + "\n".join(linhas) + "\n_.QUIT _Y\n")
        r = subprocess.run([acad(), "/i", entrada, "/s", scr, "/l", "pt-BR"], capture_output=True, timeout=600)
        return r.stdout.decode("utf-16-le", errors="ignore")


def caminho(p):
    return p.replace("\\", "/")


def converter(pasta):
    for dxf in glob.glob(os.path.join(pasta, "*.dxf")):
        dwg = dxf[:-4] + ".dwg"
        if os.path.exists(dwg):
            os.remove(dwg)
        rodar(dxf, ["_.ZOOM _E", f'_.SAVEAS 2018 "{caminho(dwg)}"'])
        print(("✓ " if os.path.exists(dwg) else "✗ ") + os.path.relpath(dwg, RAIZ))

    for step in glob.glob(os.path.join(pasta, "*.step")):
        dwg = step[:-5] + "_3d.dwg"
        if os.path.exists(dwg):
            os.remove(dwg)
        base = glob.glob(os.path.join(pasta, "*.dxf"))[0]  # qualquer desenho serve de ponto de partida
        log = rodar(base, [
            "_.ERASE _ALL ",  # o espaço final encerra a seleção (linha vazia repetiria o comando)
            f'_.IMPORT "{caminho(step)}"',
            "_.VSCURRENT _C", "_.-VIEW _SWISO", "_.ZOOM _E",
            f'_.SAVEAS 2018 "{caminho(dwg)}"',
        ])
        ok = os.path.exists(dwg)
        print(("✓ " if ok else "✗ ") + os.path.relpath(dwg, RAIZ))
        if not ok:
            print("   " + " | ".join(l.strip() for l in log.splitlines() if l.strip())[-600:])


if __name__ == "__main__":
    pastas = sys.argv[1:] or [os.path.join(RAIZ, "bandeja-800ml", "saida"), os.path.join(RAIZ, "bandeja-redonda", "saida")]
    for p in pastas:
        converter(p)
