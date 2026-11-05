"""Bandeja redonda de alumínio com divisórias — modelo paramétrico.

Bandeja Ø215 mm (fundo) com parede a 15°, anel central Ø90 mm e 3 nervuras radiais.
O anel e as nervuras são frisos estampados na folha: ocos por baixo, seção trapezoidal
5 mm no topo / 11 mm na base.

Gera, na pasta saida/:
  bandeja_redonda.step  sólido 3D
  bandeja_redonda.stl   malha (abre no visualizador 3D da Prancheta CAD)
  bandeja_redonda.dxf   desenho técnico: vista superior + corte A-A, com cotas

Uso:  .venv\\Scripts\\python.exe bandeja-redonda\\gerar_bandeja_redonda.py
"""

import math
from pathlib import Path

import cadquery as cq
import ezdxf

# ---------------------------------------------------------------------------
# Parâmetros (mm) — medidos nas fotos
# ---------------------------------------------------------------------------
D_FUNDO = 215.0       # diâmetro interno do fundo
ALTURA = 55.0         # altura interna
ANGULO = 15.0         # inclinação da parede em relação à vertical (graus)
D_ANEL = 90.0         # diâmetro interno do anel central (no topo do friso)
FRISO_TOPO = 5.0      # largura do friso (anel e nervuras) no topo
FRISO_BASE = 11.0     # largura do friso na base
N_NERVURAS = 3        # nervuras radiais, igualmente espaçadas
ANG_NERVURA0 = 90.0   # posição da primeira nervura (graus, 90 = eixo +Y)

# ESTIMADOS — não constam nas fotos
ALTURA_FRISO = 45.0   # altura do anel e das nervuras
RAIO_FUNDO = 5.0      # concordância fundo/parede
ABA = 8.0             # largura da aba plana no topo
RAIO_BORDA = 1.5      # raio da borda enrolada na ponta da aba
ESPESSURA = 0.05      # espessura da folha

TAN = math.tan(math.radians(ANGULO))
R_FUNDO = D_FUNDO / 2
R_BOCA = R_FUNDO + ALTURA * TAN
SLOPE = (FRISO_BASE - FRISO_TOPO) / 2          # recuo de cada lado do friso
R_ANEL_IN_TOPO = D_ANEL / 2
R_ANEL_OUT_TOPO = R_ANEL_IN_TOPO + FRISO_TOPO
R_ANEL_IN_BASE = R_ANEL_IN_TOPO - SLOPE
R_ANEL_OUT_BASE = R_ANEL_OUT_TOPO + SLOPE

SAIDA = Path(__file__).parent / "saida"
SAIDA.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Modelo 3D
# ---------------------------------------------------------------------------
def tronco(folga=0.0):
    """Cavidade cônica da bandeja (o 'ar' que ela contém), deslocada `folga` para fora."""
    dx = folga / math.cos(math.radians(ANGULO)) - folga * TAN
    r0 = R_FUNDO + dx
    r1 = R_FUNDO + dx + (ALTURA + folga) * TAN
    return (
        cq.Workplane("XZ")
        .polyline([(0, -folga), (r0, -folga), (r1, ALTURA), (0, ALTURA)]).close()
        .revolve(360, (0, 0, 0), (0, 1, 0))
        .faces("<Z").edges().fillet(RAIO_FUNDO + folga)
    )


def frisos(recuo=0.0):
    """Volume ocupado pelo anel e pelas nervuras (encolhido de `recuo` = parte oca por baixo)."""
    h = ALTURA_FRISO - recuo
    abaixo = 3.0  # prolonga para baixo do fundo, deixando o friso aberto por baixo
    k = SLOPE / ALTURA_FRISO  # recuo lateral por mm de altura
    # anel: trapézio revolucionado
    anel = (
        cq.Workplane("XZ")
        .polyline([
            (R_ANEL_IN_BASE + recuo - k * abaixo, -abaixo), (R_ANEL_OUT_BASE - recuo + k * abaixo, -abaixo),
            (R_ANEL_OUT_TOPO - recuo, h), (R_ANEL_IN_TOPO + recuo, h),
        ]).close()
        .revolve(360, (0, 0, 0), (0, 1, 0))
    )
    # nervura ao longo de +X, seção trapezoidal no plano YZ
    wb = FRISO_BASE / 2 - recuo + k * abaixo
    wt = FRISO_TOPO / 2 - recuo
    nerv = (
        cq.Workplane("YZ").workplane(offset=R_ANEL_IN_TOPO + FRISO_TOPO / 2)
        .polyline([(-wb, -abaixo), (wb, -abaixo), (wt, h), (-wt, h)]).close()
        .extrude(R_BOCA + 20)
    )
    corpo = anel
    for i in range(N_NERVURAS):
        corpo = corpo.union(nerv.rotate((0, 0, 0), (0, 0, 1), ANG_NERVURA0 + i * 360 / N_NERVURAS))
    return corpo


def cavidade():
    """Ar dentro da bandeja: tronco menos os frisos."""
    return tronco().cut(frisos())


def bandeja():
    t = ESPESSURA
    # parte oca dos frisos: dentro da cavidade e atravessando o fundo (aberta por baixo),
    # mas sem furar a parede nem a concordância do fundo
    r_plano = R_FUNDO + RAIO_FUNDO * TAN - RAIO_FUNDO / math.cos(math.radians(ANGULO))
    alcance = tronco().union(cq.Workplane("XY").workplane(offset=-5).circle(r_plano).extrude(5))
    externo = tronco(t).cut(frisos(t).intersect(alcance))
    corpo = externo.cut(cavidade())
    # aba plana + borda enrolada
    r_ext_boca = R_BOCA + t / math.cos(math.radians(ANGULO))
    aba = (
        cq.Workplane("XY").workplane(offset=ALTURA - t)
        .circle(r_ext_boca + ABA).circle(R_BOCA).extrude(t)
    )
    # borda enrolada: tubo oco de folha (toro externo menos toro interno)
    toro = lambda r: cq.Workplane("XY").add(cq.Solid.makeTorus(r_ext_boca + ABA, r)).translate((0, 0, ALTURA - RAIO_BORDA))
    borda = toro(RAIO_BORDA).cut(toro(RAIO_BORDA - t))
    return corpo.union(aba).union(borda)


# ---------------------------------------------------------------------------
# Desenho técnico 2D
# ---------------------------------------------------------------------------
def desenho(volumes):
    doc = ezdxf.new("R2018", setup=True, units=ezdxf.units.MM)
    for nome, cor, tipo in [("CONTORNO", 7, "CONTINUOUS"), ("OCULTA", 8, "DASHED"), ("CENTRO", 1, "CENTER"),
                            ("COTAS", 3, "CONTINUOUS"), ("TEXTO", 7, "CONTINUOUS")]:
        doc.layers.add(nome, color=cor, linetype=tipo)
    estilo = doc.dimstyles.duplicate_entry("EZDXF", "BANDEJA")
    for k, v in dict(dimtxt=3.5, dimasz=3.0, dimexo=1.5, dimexe=1.5, dimlfac=1, dimdec=1, dimadec=0, dimzin=0).items():
        setattr(estilo.dxf, k, v)
    estilo.dxf.dimdsep = ord(",")
    cota = {"dimstyle": "BANDEJA", "dxfattribs": {"layer": "COTAS"},
            "override": {"dimlfac": 1, "dimdec": 1, "dimzin": 0, "dimdsep": ord(","), "dimadec": 0}}
    msp = doc.modelspace()
    L = lambda nome: {"layer": nome}
    r_aba = R_BOCA + ESPESSURA + ABA
    r_h = R_FUNDO + ALTURA_FRISO * TAN  # raio da parede na altura do topo dos frisos

    # --- Vista superior ----------------------------------------------------
    for r, lay in [(r_aba + RAIO_BORDA, "CONTORNO"), (R_BOCA, "CONTORNO"), (R_FUNDO, "OCULTA"),
                   (R_ANEL_IN_TOPO, "CONTORNO"), (R_ANEL_OUT_TOPO, "CONTORNO"),
                   (R_ANEL_IN_BASE, "OCULTA"), (R_ANEL_OUT_BASE, "OCULTA")]:
        msp.add_circle((0, 0), r, dxfattribs=L(lay))
    for i in range(N_NERVURAS):
        a = math.radians(ANG_NERVURA0 + i * 360 / N_NERVURAS)
        u, n = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
        for w, lay, r1 in [(FRISO_TOPO / 2, "CONTORNO", r_h), (FRISO_BASE / 2, "OCULTA", R_FUNDO)]:
            for s in (-1, 1):
                r0 = math.sqrt(max(R_ANEL_OUT_TOPO ** 2 - w ** 2, 0)) if lay == "CONTORNO" else math.sqrt(max(R_ANEL_OUT_BASE ** 2 - w ** 2, 0))
                p = lambda r: (u[0] * r + n[0] * w * s, u[1] * r + n[1] * w * s)
                msp.add_line(p(r0), p(r1), dxfattribs=L(lay))
    e = r_aba + 15
    msp.add_line((-e, 0), (e, 0), dxfattribs=L("CENTRO"))
    msp.add_line((0, -e), (0, e), dxfattribs=L("CENTRO"))
    msp.add_diameter_dim(center=(0, 0), radius=R_BOCA, angle=150, **cota).render()
    msp.add_diameter_dim(center=(0, 0), radius=R_ANEL_IN_TOPO, angle=20, **cota).render()
    msp.add_linear_dim(base=(0, -e - 18), p1=(-(r_aba + RAIO_BORDA), 0), p2=(r_aba + RAIO_BORDA, 0), **cota).render()
    msp.add_text("A", height=6, dxfattribs=L("TEXTO")).set_placement((4, e + 2))
    msp.add_text("A", height=6, dxfattribs=L("TEXTO")).set_placement((4, -e - 8))
    msp.add_text("VISTA SUPERIOR", height=5, dxfattribs=L("TEXTO")).set_placement(
        (0, e + 14), align=ezdxf.enums.TextEntityAlignment.BOTTOM_CENTER)

    # --- Corte A-A (plano x = 0; a nervura a 90° fica do lado direito) ------
    ox, oy = 0.0, -r_aba - 150

    def P(x, z):
        return (ox + x, oy + z)

    c, s = math.cos(math.radians(ANGULO)), math.sin(math.radians(ANGULO))
    xc = R_FUNDO + RAIO_FUNDO * TAN - RAIO_FUNDO / c
    xt, zt = xc + RAIO_FUNDO * c, RAIO_FUNDO - RAIO_FUNDO * s
    bf = math.tan(math.radians(90 - ANGULO) / 4)
    hf = ALTURA_FRISO
    esquerda = [  # lado sem nervura: parede, fundo, anel
        (*P(-r_aba, ALTURA), 0), (*P(-R_BOCA, ALTURA), 0), (*P(-xt, zt), bf), (*P(-xc, 0), 0),
        (*P(-R_ANEL_OUT_BASE, 0), 0), (*P(-R_ANEL_OUT_TOPO, hf), 0), (*P(-R_ANEL_IN_TOPO, hf), 0),
        (*P(-R_ANEL_IN_BASE, 0), 0), (*P(R_ANEL_IN_BASE, 0), 0), (*P(R_ANEL_IN_TOPO, hf), 0),
        (*P(r_h, hf), 0), (*P(R_BOCA, ALTURA), 0), (*P(r_aba, ALTURA), 0),
    ]
    msp.add_lwpolyline(esquerda, format="xyb", dxfattribs=L("CONTORNO"))
    # sob a nervura (oca): parede e fundo ocultos
    msp.add_lwpolyline([(*P(R_ANEL_IN_BASE, 0), 0), (*P(xc, 0), -bf), (*P(xt, zt), 0), (*P(r_h, hf), 0)],
                       format="xyb", dxfattribs=L("OCULTA"))
    for sx in (-1, 1):
        msp.add_circle(P(sx * (r_aba + RAIO_BORDA * 0), ALTURA - RAIO_BORDA), RAIO_BORDA, dxfattribs=L("CONTORNO"))
    msp.add_line(P(0, -10), P(0, ALTURA + 10), dxfattribs=L("CENTRO"))

    msp.add_linear_dim(base=P(0, -14), p1=P(-R_FUNDO, 0), p2=P(R_FUNDO, 0), **cota).render()
    msp.add_linear_dim(base=P(0, ALTURA + 16), p1=P(-R_BOCA, ALTURA), p2=P(R_BOCA, ALTURA), **cota).render()
    msp.add_linear_dim(base=P(-r_aba - 16, 0), p1=P(-R_FUNDO, 0), p2=P(-R_BOCA, ALTURA), angle=90, **cota).render()
    msp.add_linear_dim(base=P(-R_ANEL_OUT_TOPO - 14, 0), p1=P(-R_ANEL_OUT_BASE, 0), p2=P(-R_ANEL_OUT_TOPO, hf), angle=90, **cota).render()
    msp.add_linear_dim(base=P(0, hf + 8), p1=P(-R_ANEL_OUT_TOPO, hf), p2=P(-R_ANEL_IN_TOPO, hf), **cota).render()
    msp.add_linear_dim(base=P(0, -6), p1=P(-R_ANEL_OUT_BASE, 0), p2=P(-R_ANEL_IN_BASE, 0), **cota).render()
    msp.add_linear_dim(base=P(0, ALTURA + 8), p1=P(r_aba - ABA, ALTURA), p2=P(r_aba, ALTURA), **cota).render()
    msp.add_line(P(-R_FUNDO, 0), P(-R_FUNDO, 40), dxfattribs=L("CENTRO"))
    msp.add_angular_dim_3p(base=P(-R_FUNDO - 6, 32), center=P(-R_FUNDO, 0),
                           p1=P(-R_FUNDO, 40), p2=P(-R_FUNDO - 40 * TAN, 40), **cota).render()
    msp.add_text("CORTE A-A", height=5, dxfattribs=L("TEXTO")).set_placement(
        P(0, ALTURA + 26), align=ezdxf.enums.TextEntityAlignment.BOTTOM_CENTER)

    notas = [
        "BANDEJA REDONDA COM DIVISORIAS",
        f"Volume total calculado: {volumes['total']:.0f} ml (ate a boca)",
        f"Compartimento central: {volumes['central']:.0f} ml",
        f"Cada compartimento externo: ~{volumes['externo']:.0f} ml",
        "Frisos (anel e nervuras) estampados, ocos por baixo",
        "Medidas internas em mm",
        f"ESTIMADOS: altura dos frisos {ALTURA_FRISO:.0f}, raio do fundo R{RAIO_FUNDO:.0f}, aba {ABA:.0f}, folha {ESPESSURA:.2f}".replace(".", ","),
    ]
    for i, t in enumerate(notas):
        msp.add_text(t, height=6 if i == 0 else 4, dxfattribs=L("TEXTO")).set_placement((-r_aba, oy - 40 - i * 8))
    doc.saveas(SAIDA / "bandeja_redonda.dxf")


if __name__ == "__main__":
    cav = cavidade()
    total = cav.val().Volume() / 1000
    central = cav.intersect(cq.Workplane("XY").circle(R_ANEL_IN_TOPO).extrude(ALTURA)).val().Volume() / 1000
    externo = (total - central) / N_NERVURAS
    peca = bandeja()
    cq.exporters.export(peca, str(SAIDA / "bandeja_redonda.step"))
    cq.exporters.export(peca, str(SAIDA / "bandeja_redonda.stl"), tolerance=0.05, angularTolerance=0.1)
    desenho({"total": total, "central": central, "externo": externo})
    print(f"Diametro da boca:   {2 * R_BOCA:.1f} mm")
    print(f"Volume total:       {total:.0f} ml")
    print(f"Central:            {central:.0f} ml")
    print(f"Cada externo:       {externo:.0f} ml")
    print(f"Solido valido:      {peca.val().isValid()}")
