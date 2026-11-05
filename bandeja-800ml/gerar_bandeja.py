"""Bandeja de alumínio 800 ml — modelo paramétrico.

Gera, na pasta saida/:
  bandeja_800ml.step  sólido 3D (abre em AutoCAD, SolidWorks, Fusion, FreeCAD)
  bandeja_800ml.stl   malha para visualização/impressão
  bandeja_800ml.dxf   desenho técnico 2D (vista superior + corte) com cotas

Uso:  .venv\\Scripts\\python.exe bandeja-800ml\\gerar_bandeja.py
"""

import math
from pathlib import Path

import cadquery as cq
import ezdxf

# ---------------------------------------------------------------------------
# Parâmetros (mm) — medidas da foto de referência
# ---------------------------------------------------------------------------
FUNDO = 70.0          # base interna, lado do quadrado
BOCA = 115.5          # topo interno, lado do quadrado
ALTURA = 91.2         # altura vertical interna
RAIO_QUINA = 6.0      # raio das quinas verticais
RAIO_FUNDO = 4.0      # raio de concordância fundo/parede
ESPESSURA = 0.05      # espessura da folha
ABA = 8.0             # largura da aba no topo (ESTIMADA — não consta na foto)

ANGULO = math.degrees(math.atan((BOCA - FUNDO) / 2 / ALTURA))

SAIDA = Path(__file__).parent / "saida"
SAIDA.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Modelo 3D
# ---------------------------------------------------------------------------
def quadrado(lado, raio, z=0.0):
    return cq.Sketch().rect(lado, lado).vertices().fillet(raio).moved(cq.Location((0, 0, z)))


def cavidade(folga=0.0):
    """Volume interno da bandeja (o 'ar' que ela contém), deslocado de `folga` para fora."""
    t = math.tan(math.radians(ANGULO))
    dx = folga / math.cos(math.radians(ANGULO)) - folga * t  # deslocamento horizontal no plano z=-folga
    return (
        cq.Workplane("XY")
        .placeSketch(
            quadrado(FUNDO + 2 * dx, RAIO_QUINA + folga, -folga),
            quadrado(BOCA + 2 * (dx + (ALTURA + folga) * t) - (BOCA - FUNDO), RAIO_QUINA + folga, ALTURA),
        )
        .loft(ruled=True)
        .edges("<Z").fillet(RAIO_FUNDO + folga)
    )


def bandeja():
    # Casca de 0,05 mm: sólido externo deslocado menos a cavidade
    corpo = cavidade(ESPESSURA).cut(cavidade())

    # Aba plana no topo, sobreposta à boca para a união ficar robusta
    externo = BOCA + 2 * ESPESSURA + 2 * ABA
    base = cq.Workplane("XY").workplane(offset=ALTURA - ESPESSURA)
    aba = base.placeSketch(quadrado(externo, RAIO_QUINA + ABA)).extrude(ESPESSURA)
    furo = base.placeSketch(quadrado(BOCA, RAIO_QUINA)).extrude(ESPESSURA)
    return corpo.union(aba.cut(furo))


# ---------------------------------------------------------------------------
# Desenho técnico 2D
# ---------------------------------------------------------------------------
B90 = math.tan(math.radians(90) / 4)  # bulge de um arco de 90°


def quadrado_arredondado(msp, cx, cy, lado, raio, layer):
    h, r = lado / 2, raio
    pts = [
        (cx + h - r, cy - h, B90), (cx + h, cy - h + r, 0),
        (cx + h, cy + h - r, B90), (cx + h - r, cy + h, 0),
        (cx - h + r, cy + h, B90), (cx - h, cy + h - r, 0),
        (cx - h, cy - h + r, B90), (cx - h + r, cy - h, 0),
    ]
    msp.add_lwpolyline(pts, format="xyb", close=True, dxfattribs={"layer": layer})


def desenho():
    doc = ezdxf.new("R2018", setup=True, units=ezdxf.units.MM)
    for nome, cor, tipo in [
        ("CONTORNO", 7, "CONTINUOUS"), ("OCULTA", 8, "DASHED"),
        ("CENTRO", 1, "CENTER"), ("COTAS", 3, "CONTINUOUS"), ("TEXTO", 7, "CONTINUOUS"),
    ]:
        doc.layers.add(nome, color=cor, linetype=tipo)

    estilo = doc.dimstyles.duplicate_entry("EZDXF", "BANDEJA")
    estilo.dxf.dimtxt = 3.0
    estilo.dxf.dimasz = 2.5
    estilo.dxf.dimexo = 1.5
    estilo.dxf.dimexe = 1.5
    estilo.dxf.dimlfac = 1         # o estilo base EZDXF vem com fator 100
    estilo.dxf.dimdec = 1
    estilo.dxf.dimadec = 0
    estilo.dxf.dimzin = 0
    estilo.dxf.dimdsep = ord(",")   # separador decimal brasileiro
    msp = doc.modelspace()
    # ezdxf não herda esses valores do estilo ao gerar o texto da cota — repetir no override
    cota = {
        "dimstyle": "BANDEJA",
        "dxfattribs": {"layer": "COTAS"},
        "override": {"dimlfac": 1, "dimdec": 1, "dimzin": 0, "dimdsep": ord(","), "dimadec": 0},
    }
    externo = BOCA + 2 * ESPESSURA + 2 * ABA

    # --- Vista superior (centro em 0,0) ------------------------------------
    quadrado_arredondado(msp, 0, 0, externo, RAIO_QUINA + ABA, "CONTORNO")
    quadrado_arredondado(msp, 0, 0, BOCA, RAIO_QUINA, "CONTORNO")
    quadrado_arredondado(msp, 0, 0, FUNDO, RAIO_QUINA, "CONTORNO")
    for p1, p2 in [((-80, 0), (80, 0)), ((0, -80), (0, 80))]:
        msp.add_line(p1, p2, dxfattribs={"layer": "CENTRO"})
    h = BOCA / 2
    msp.add_linear_dim(base=(0, -externo / 2 - 12), p1=(-h, -h), p2=(h, -h), **cota).render()
    msp.add_linear_dim(base=(0, -externo / 2 - 22), p1=(-externo / 2, 0), p2=(externo / 2, 0), **cota).render()
    msp.add_linear_dim(base=(0, FUNDO / 2 + 8), p1=(-FUNDO / 2, FUNDO / 2), p2=(FUNDO / 2, FUNDO / 2), **cota).render()
    msp.add_linear_dim(base=(externo / 2 + 12, 0), p1=(h, -h), p2=(h, h), angle=90, **cota).render()
    msp.add_radius_dim(center=(FUNDO / 2 - RAIO_QUINA, FUNDO / 2 - RAIO_QUINA),
                       radius=RAIO_QUINA, angle=45, location=(FUNDO / 2 + 12, FUNDO / 2 + 18), **cota).render()
    msp.add_text("VISTA SUPERIOR", height=4, dxfattribs={"layer": "TEXTO"}).set_placement(
        (0, externo / 2 + 10), align=ezdxf.enums.TextEntityAlignment.BOTTOM_CENTER)

    # --- Corte A-A (fundo interno no ponto ox, oy) -------------------------
    ox, oy = 190.0, -ALTURA / 2

    def P(x, z):
        return (ox + x, oy + z)

    t = math.tan(math.radians(ANGULO))
    c = math.cos(math.radians(ANGULO))
    s = math.sin(math.radians(ANGULO))
    xc = FUNDO / 2 + RAIO_FUNDO * t - RAIO_FUNDO / c       # centro do raio de fundo
    xt, zt = xc + RAIO_FUNDO * c, RAIO_FUNDO - RAIO_FUNDO * s  # tangência com a parede
    barco = math.tan(math.radians(90 - ANGULO) / 4)
    xa = externo / 2
    perfil = [
        (*P(-xa, ALTURA), 0), (*P(-h, ALTURA), 0), (*P(-xt, zt), barco),
        (*P(-xc, 0), 0), (*P(xc, 0), barco), (*P(xt, zt), 0),
        (*P(h, ALTURA), 0), (*P(xa, ALTURA), 0),
    ]
    msp.add_lwpolyline(perfil, format="xyb", dxfattribs={"layer": "CONTORNO"})
    msp.add_line(P(0, -8), P(0, ALTURA + 8), dxfattribs={"layer": "CENTRO"})

    msp.add_linear_dim(base=P(0, ALTURA + 10), p1=P(-h, ALTURA), p2=P(h, ALTURA), **cota).render()
    msp.add_linear_dim(base=P(0, -10), p1=P(-FUNDO / 2, 0), p2=P(FUNDO / 2, 0), **cota).render()
    msp.add_linear_dim(base=P(xa + 12, 0), p1=P(xc, 0), p2=P(h, ALTURA), angle=90, **cota).render()
    msp.add_linear_dim(base=P(0, ALTURA + 18), p1=P(xa - ABA, ALTURA), p2=P(xa, ALTURA), **cota).render()
    # ângulo da parede em relação à vertical
    msp.add_line(P(FUNDO / 2, 0), P(FUNDO / 2, 60), dxfattribs={"layer": "CENTRO"})
    msp.add_angular_dim_3p(base=P(FUNDO / 2 + 6, 50), center=P(FUNDO / 2, 0),
                           p1=P(FUNDO / 2 + 60 * t, 60), p2=P(FUNDO / 2, 60), **cota).render()
    msp.add_radius_dim(center=P(xc, RAIO_FUNDO), radius=RAIO_FUNDO, angle=-60,
                       location=P(xc + 14, -16), **cota).render()
    msp.add_text("CORTE A-A", height=4, dxfattribs={"layer": "TEXTO"}).set_placement(
        P(0, ALTURA + 26), align=ezdxf.enums.TextEntityAlignment.BOTTOM_CENTER)

    # --- Notas --------------------------------------------------------------
    notas = [
        "BANDEJA DE ALUMINIO 800 ml",
        f"Volume interno calculado: {VOLUME_ML:.0f} ml",
        f"Espessura da folha: {ESPESSURA:.2f} mm".replace(".", ","),
        f"Angulo das paredes: {ANGULO:.1f} graus".replace(".", ","),
        "Medidas internas em mm",
        f"Aba de {ABA:.0f} mm ESTIMADA (nao consta na referencia)",
    ]
    for i, linha in enumerate(notas):
        msp.add_text(linha, height=3.5 if i else 5, dxfattribs={"layer": "TEXTO"}).set_placement((-70, -120 - i * 7))

    doc.saveas(SAIDA / "bandeja_800ml.dxf")


if __name__ == "__main__":
    VOLUME_ML = cavidade().val().Volume() / 1000
    peca = bandeja()
    cq.exporters.export(peca, str(SAIDA / "bandeja_800ml.step"))
    cq.exporters.export(peca, str(SAIDA / "bandeja_800ml.stl"), tolerance=0.02, angularTolerance=0.1)
    desenho()
    print(f"Angulo das paredes: {ANGULO:.2f} graus")
    print(f"Volume interno:     {VOLUME_ML:.1f} ml")
    print(f"Solido valido:      {peca.val().isValid()}")
    print(f"Arquivos em:        {SAIDA}")
