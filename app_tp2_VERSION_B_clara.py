# -*- coding: utf-8 -*-
"""
SIMULADOR DE POLÍTICAS PÚBLICAS EN ECONOMÍA CERRADA  —  VERSIÓN B
Trabajo Práctico N.º 2 — Economía para Ingenieros — UNSTA
Prof. Antonio Raúl García

Mismo núcleo económico que la Versión A (validado), pero con una
distribución y estética distintas: diseño claro tipo "cuaderno técnico",
navegación por secciones en el lateral (una a la vez), gráfico amplio,
excedentes graficados y puntos rotulados con letras.

Integrantes:
  * Antúnez Ruiz Huidobro, Facundo
  * Brahin, Federico Tomás
  * Gordillo Toledo, Rodrigo Gabriel
  * Matos Villalba, Luis Humberto

Ejecutar con:  streamlit run app_tp2_B.py
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# ======================================================================
# CONFIGURACIÓN Y ESTILO  (papel claro / tinta azul-grafito)
# ======================================================================
st.set_page_config(
    page_title="Laboratorio de Políticas Públicas · UNSTA",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Inter:wght@400;500;600&display=swap');

    .stApp {
        background:
            linear-gradient(0deg, rgba(15,42,71,0.015), rgba(15,42,71,0.015)),
            #f7f5ef;
        color: #1f2a38;
    }
    /* Líneas guía sutiles tipo papel cuadriculado en el fondo del main */
    section.main > div { font-family: 'Inter', sans-serif; }

    h1, h2, h3 { font-family: 'Fraunces', serif !important; color: #16263a; letter-spacing: -0.01em; }
    h1 { font-weight: 600; }

    /* Eyebrow / cintillo de sección */
    .eyebrow {
        font-family: 'Inter', sans-serif; font-size: 0.72rem; font-weight: 600;
        letter-spacing: 0.18em; text-transform: uppercase; color: #b4632a;
        margin-bottom: 2px;
    }
    .regla { height: 2px; background: #16263a; border: 0; margin: 6px 0 18px 0; }

    /* Tarjetas de dato (en vez de st.metric, para controlar estética) */
    .dato {
        background: #fffdf8; border: 1px solid #e4ddcd; border-radius: 4px;
        padding: 12px 14px;
    }
    .dato .k { font-size: 0.7rem; letter-spacing: 0.08em; text-transform: uppercase; color: #7a8595; }
    .dato .v { font-family: 'Fraunces', serif; font-size: 1.5rem; color: #16263a; line-height: 1.1; margin-top: 2px; }
    .dato .v small { font-size: 0.85rem; color: #7a8595; }

    /* Nota / lectura económica */
    .lec {
        background: #fffdf8; border: 1px solid #e4ddcd; border-left: 4px solid #16263a;
        border-radius: 4px; padding: 14px 16px; color: #2b3a4d;
        font-size: 0.92rem; line-height: 1.55;
    }
    .lec.ok   { border-left-color:#2f7d4f; }
    .lec.warn { border-left-color:#b4632a; }
    .lec.bad  { border-left-color:#9e2b25; }

    /* Sidebar claro */
    section[data-testid="stSidebar"] {
        background: #16263a;
    }
    section[data-testid="stSidebar"] * { color: #e7eef6 !important; }
    section[data-testid="stSidebar"] .stRadio label { color: #e7eef6 !important; }

    /* Tablas */
    .stDataFrame { border: 1px solid #e4ddcd; border-radius: 4px; }
    [data-testid="stHeader"] { background: transparent; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Paleta de gráficos (tinta sobre papel)
COL_DEM  = "#2563a8"   # demanda  (azul)
COL_OFE  = "#2f7d4f"   # oferta   (verde)
COL_OFE2 = "#b4632a"   # oferta desplazada (terracota)
COL_EQ   = "#9e2b25"   # equilibrio (bordó)
COL_EC   = "rgba(37,99,168,0.18)"
COL_EP   = "rgba(47,125,79,0.18)"
COL_FISC = "rgba(180,99,42,0.22)"
COL_DWL  = "rgba(158,43,37,0.28)"
PAPER    = "#f7f5ef"
GRID     = "#e2dccc"

# ======================================================================
# NÚCLEO ECONÓMICO (idéntico al validado en la Versión A)
# ======================================================================
def equilibrio(a, b, c, d):
    P = (a - c) / (b + d)
    Q = a - b * P
    return P, Q

def precio_demanda(Q, a, b):
    return (a - Q) / b

def precio_oferta(Q, c, d):
    return (Q - c) / d

def excedente_consumidor(Q, P_pagado, a, b):
    choke = a / b
    return 0.5 * Q * max(choke - P_pagado, 0.0)

def excedente_productor(Q, P_recibido, c, d):
    return P_recibido * Q - (Q ** 2 / 2 - c * Q) / d

def resolver_subsidio(a, b, c, d, s):
    Pc = (a - c - d * s) / (b + d)
    Pv = Pc + s
    Q = a - b * Pc
    return Pc, Pv, Q

def bienestar_subsidio(a, b, c, d, s):
    P0, Q0 = equilibrio(a, b, c, d)
    EC0 = excedente_consumidor(Q0, P0, a, b)
    EP0 = excedente_productor(Q0, P0, c, d)
    W0 = EC0 + EP0
    Pc, Pv, Q1 = resolver_subsidio(a, b, c, d, s)
    EC1 = excedente_consumidor(Q1, Pc, a, b)
    EP1 = excedente_productor(Q1, Pv, c, d)
    gasto = s * Q1
    W1 = EC1 + EP1 - gasto
    dwl = W0 - W1
    return {"P0": P0, "Q0": Q0, "EC0": EC0, "EP0": EP0, "W0": W0,
            "Pc": Pc, "Pv": Pv, "Q1": Q1, "EC1": EC1, "EP1": EP1,
            "gasto": gasto, "W1": W1, "dwl": dwl}

def resolver_precio_maximo(a, b, c, d, p_techo):
    P0, Q0 = equilibrio(a, b, c, d)
    vinculante = p_techo < P0
    Qd = a - b * p_techo
    Qo = c + d * p_techo
    escasez = Qd - Qo
    Q_transada = Qo if vinculante else Q0
    return {"P0": P0, "Q0": Q0, "vinculante": vinculante,
            "Qd": Qd, "Qo": Qo, "escasez": max(escasez, 0.0),
            "Q_transada": Q_transada, "p_techo": p_techo}

def bienestar_precio_maximo(a, b, c, d, p_techo):
    base = resolver_precio_maximo(a, b, c, d, p_techo)
    P0, Q0 = base["P0"], base["Q0"]
    EC0 = excedente_consumidor(Q0, P0, a, b)
    EP0 = excedente_productor(Q0, P0, c, d)
    W0 = EC0 + EP0
    if base["vinculante"]:
        Qt = base["Q_transada"]
        Pd_en_Qt = precio_demanda(Qt, a, b)
        choke_dem = a / b
        EC1 = 0.5 * Qt * ((choke_dem - p_techo) + (Pd_en_Qt - p_techo))
        EP1 = excedente_productor(Qt, p_techo, c, d)
        W1 = EC1 + EP1
        dwl = W0 - W1
    else:
        Qt = Q0
        EC1, EP1, W1, dwl = EC0, EP0, W0, 0.0
    out = dict(base)
    out.update({"EC0": EC0, "EP0": EP0, "W0": W0,
                "EC1": EC1, "EP1": EP1, "W1": W1, "dwl": dwl, "Qt": Qt})
    return out

# ======================================================================
# HELPERS DE INTERFAZ
# ======================================================================
def fmt(x, dec=2):
    try:
        return f"{x:,.{dec}f}".replace(",", "·").replace(".", ",").replace("·", ".")
    except Exception:
        return str(x)

def seccion(eyebrow, titulo):
    st.markdown(f"<div class='eyebrow'>{eyebrow}</div>", unsafe_allow_html=True)
    st.markdown(f"## {titulo}")
    st.markdown("<hr class='regla'>", unsafe_allow_html=True)

def dato(col, k, v, sufijo=""):
    col.markdown(
        f"<div class='dato'><div class='k'>{k}</div>"
        f"<div class='v'>{v}<small>{sufijo}</small></div></div>",
        unsafe_allow_html=True)

def lec(texto, tipo="info"):
    clase = {"info": "lec", "ok": "lec ok", "warn": "lec warn", "bad": "lec bad"}[tipo]
    st.markdown(f"<div class='{clase}'>{texto}</div>", unsafe_allow_html=True)

def grilla_precios(a, b, c, d, extra_top=1.15):
    p_top = (a / b) * extra_top
    return np.linspace(0, p_top, 200), p_top

def base_layout(fig, a, p_top, titulo):
    fig.update_layout(
        title=dict(text=titulo, font=dict(family="Fraunces, serif", size=18, color="#16263a")),
        height=520, paper_bgcolor=PAPER, plot_bgcolor="#fffdf8",
        font=dict(family="Inter, sans-serif", color="#2b3a4d"),
        xaxis_title="Cantidad (Q)", yaxis_title="Precio (P)",
        xaxis=dict(range=[0, a * 1.05], gridcolor=GRID, zerolinecolor=GRID),
        yaxis=dict(range=[0, p_top], gridcolor=GRID, zerolinecolor=GRID),
        legend=dict(orientation="h", y=-0.18, x=0))
    return fig

# ======================================================================
# SIDEBAR — IDENTIDAD, NAVEGACIÓN Y PARÁMETROS
# ======================================================================
with st.sidebar:
    st.markdown("## Laboratorio")
    st.markdown("##### Políticas públicas · economía cerrada")
    st.caption("TP N.º 2 · Economía para Ingenieros · UNSTA")
    st.markdown("---")

    seccion_activa = st.radio(
        "Ir a la sección",
        ["1 · Mercado y excedentes",
         "2 · Subsidio (Ejercicio 1)",
         "3 · Precio máximo (Ejercicio 2)",
         "4 · Fórmulas"],
    )
    st.markdown("---")

    preset = st.selectbox(
        "Cargar datos del enunciado",
        ["Personalizado",
         "Ej. 1 — Subsidio al transporte",
         "Ej. 2 — Precio máximo a alquileres"],
        help="Solo completa a, b, c, d y el valor de la política con los datos "
             "del enunciado. No cambia de sección.",
    )

    if preset == "Ej. 1 — Subsidio al transporte":
        da, db, dc, dd = 1500.0, 25.0, 0.0, 15.0
    elif preset == "Ej. 2 — Precio máximo a alquileres":
        da, db, dc, dd = 1800.0, 20.0, 0.0, 12.0
    else:
        da, db, dc, dd = 1000.0, 30.0, 0.0, 20.0

    st.markdown("**Demanda · Qd = a − bP**")
    a = st.number_input("a (intercepto)", value=da, step=10.0)
    b = st.number_input("b (pendiente)", value=db, step=1.0, min_value=0.01)
    st.markdown("**Oferta · Qo = c + dP**")
    c = st.number_input("c (intercepto)", value=dc, step=10.0)
    d = st.number_input("d (pendiente)", value=dd, step=1.0, min_value=0.01)

    # Defaults de política (usados en cada sección)
    s_default = 8.0 if preset.startswith("Ej. 1") else 4.0
    if preset.startswith("Ej. 2"):
        ptecho_default = 40.0
    else:
        _P0, _ = equilibrio(a, b, c, d)
        ptecho_default = round(_P0 * 0.75, 1)

# Validación
if (b + d) == 0:
    st.error("La suma de pendientes (b + d) no puede ser 0.")
    st.stop()

P0, Q0 = equilibrio(a, b, c, d)
EC0_g = excedente_consumidor(Q0, P0, a, b)
EP0_g = excedente_productor(Q0, P0, c, d)

# ======================================================================
# SECCIÓN 1 — MERCADO Y EXCEDENTES
# ======================================================================
if seccion_activa.startswith("1"):
    seccion("Situación inicial", "El mercado libre y su bienestar")

    colg, colr = st.columns([3, 2], gap="large")
    with colg:
        p_arr, p_top = grilla_precios(a, b, c, d)
        qd = np.clip(a - b * p_arr, 0, None)
        qo = np.clip(c + d * p_arr, 0, None)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[0, 0, Q0], y=[P0, a / b, P0], fill="toself",
                                 fillcolor=COL_EC, line=dict(width=0),
                                 name="Excedente consumidor", hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=[0, 0, Q0], y=[P0, max(-c / d, 0), P0], fill="toself",
                                 fillcolor=COL_EP, line=dict(width=0),
                                 name="Excedente productor", hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=qd, y=p_arr, name="Demanda",
                                 line=dict(color=COL_DEM, width=3)))
        fig.add_trace(go.Scatter(x=qo, y=p_arr, name="Oferta",
                                 line=dict(color=COL_OFE, width=3)))
        fig.add_trace(go.Scatter(x=[Q0], y=[P0], mode="markers+text", text=["C"],
                                 textposition="top center",
                                 textfont=dict(size=15, color=COL_EQ),
                                 marker=dict(color=COL_EQ, size=13,
                                             line=dict(color="white", width=1)),
                                 name="C · Equilibrio (P*, Q*)"))
        base_layout(fig, a, p_top, "Mercado competitivo en equilibrio")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("**C** · Punto de equilibrio del mercado libre (P\\*, Q\\*)")

    with colr:
        d1, d2 = st.columns(2)
        dato(d1, "Precio equilibrio", f"${fmt(P0)}")
        dato(d2, "Cantidad equilibrio", f"{fmt(Q0)}", " u.")
        st.write("")
        d3, d4 = st.columns(2)
        dato(d3, "Exc. consumidor", f"${fmt(EC0_g)}")
        dato(d4, "Exc. productor", f"${fmt(EP0_g)}")
        st.write("")
        dato(st, "Bienestar total (W)", f"${fmt(EC0_g + EP0_g)}")
        st.write("")
        lec("El <b>excedente del consumidor</b> (azul) mide lo que los compradores "
            "valoran por encima de lo que pagan; el <b>excedente del productor</b> "
            "(verde) mide lo que reciben por encima de su costo. La suma es el "
            "<b>bienestar total</b>, máximo en competencia. Toda intervención que "
            "aleje la cantidad del equilibrio lo reduce.", "info")

# ======================================================================
# SECCIÓN 2 — SUBSIDIO
# ======================================================================
elif seccion_activa.startswith("2"):
    titulo = "Subsidio al transporte público" if preset.startswith("Ej. 1") \
        else "Subsidio por unidad al productor"
    seccion("Ejercicio 1 · intervención", titulo)

    if preset.startswith("Ej. 2"):
        lec("Tenés cargados los datos del <b>Ejercicio 2 (alquileres)</b>. "
            "Para el subsidio del enunciado, elegí <b>Ej. 1</b> en la barra "
            "lateral.", "warn")
        st.write("")

    s = st.slider("Subsidio por unidad (s)", 0.0, float(max(P0 * 1.5, 20)),
                  float(s_default), step=0.5)
    R = bienestar_subsidio(a, b, c, d, s)

    colg, colr = st.columns([3, 2], gap="large")
    with colg:
        p_arr, p_top = grilla_precios(a, b, c, d)
        qd = np.clip(a - b * p_arr, 0, None)
        qo = np.clip(c + d * p_arr, 0, None)
        qo_sub = np.clip(c + d * (p_arr + s), 0, None)
        fig = go.Figure()
        if s > 0:
            fig.add_trace(go.Scatter(x=[0, 0, R["Q1"]], y=[R["Pc"], a / b, R["Pc"]],
                                     fill="toself", fillcolor=COL_EC, line=dict(width=0),
                                     name="Excedente consumidor", hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=[0, 0, R["Q1"]], y=[R["Pv"], max(-c / d, 0), R["Pv"]],
                                     fill="toself", fillcolor=COL_EP, line=dict(width=0),
                                     name="Excedente productor", hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=qd, y=p_arr, name="Demanda",
                                 line=dict(color=COL_DEM, width=3)))
        fig.add_trace(go.Scatter(x=qo, y=p_arr, name="Oferta original",
                                 line=dict(color=COL_OFE, width=3)))
        if s > 0:
            fig.add_trace(go.Scatter(x=qo_sub, y=p_arr, name="Oferta con subsidio",
                                     line=dict(color=COL_OFE2, width=3, dash="dash")))
            fig.add_trace(go.Scatter(x=[0, R["Q1"], R["Q1"], 0],
                                     y=[R["Pc"], R["Pc"], R["Pv"], R["Pv"]],
                                     fill="toself", fillcolor=COL_FISC, line=dict(width=0),
                                     name="Costo fiscal", hoverinfo="skip"))
            fig.add_trace(go.Scatter(
                x=[Q0, R["Q1"], R["Q1"]],
                y=[P0, precio_demanda(R["Q1"], a, b), precio_oferta(R["Q1"], c, d)],
                fill="toself", fillcolor=COL_DWL, line=dict(width=0),
                name="Pérdida de eficiencia", hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=[R["Q1"]], y=[R["Pc"]], mode="markers+text",
                                     text=["A"], textposition="bottom right",
                                     textfont=dict(size=15, color=COL_DEM),
                                     marker=dict(color=COL_DEM, size=12,
                                                 line=dict(color="white", width=1)),
                                     name="A · Precio comprador (Pc)"))
            fig.add_trace(go.Scatter(x=[R["Q1"]], y=[R["Pv"]], mode="markers+text",
                                     text=["B"], textposition="top right",
                                     textfont=dict(size=15, color=COL_OFE2),
                                     marker=dict(color=COL_OFE2, size=12,
                                                 line=dict(color="white", width=1)),
                                     name="B · Precio vendedor (Pv)"))
        fig.add_trace(go.Scatter(x=[Q0], y=[P0], mode="markers+text", text=["C"],
                                 textposition="top center",
                                 textfont=dict(size=15, color=COL_EQ),
                                 marker=dict(color=COL_EQ, size=13,
                                             line=dict(color="white", width=1)),
                                 name="C · Equilibrio original (P*)"))
        base_layout(fig, a, p_top, "Efecto del subsidio sobre el mercado")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("**A** · Precio que paga el comprador (Pc)   |   "
                   "**B** · Precio que recibe el vendedor (Pv)   |   "
                   "**C** · Equilibrio original")

    with colr:
        d1, d2 = st.columns(2)
        dato(d1, "Paga el usuario (Pc)", f"${fmt(R['Pc'])}")
        dato(d2, "Recibe la empresa (Pv)", f"${fmt(R['Pv'])}")
        st.write("")
        d3, d4 = st.columns(2)
        dato(d3, "Cantidad", f"{fmt(R['Q1'])}", " u.")
        dato(d4, "Gasto del Estado", f"${fmt(R['gasto'])}")
        st.write("")
        if s > 0:
            lec(f"Con s = <b>${fmt(s)}</b>: el usuario paga <b>${fmt(R['Pc'])}</b> "
                f"(antes ${fmt(P0)}) y la empresa cobra <b>${fmt(R['Pv'])}</b>. "
                f"Ganan ambas partes, pero el Estado gasta <b>${fmt(R['gasto'])}</b> "
                f"(lo pagan los contribuyentes) y el bienestar neto cae "
                f"<b>${fmt(R['dwl'])}</b>: es la pérdida de eficiencia (área bordó).",
                "warn")

    st.write("")
    seccion("Bienestar", "Antes y después del subsidio")
    df_b = pd.DataFrame({
        "Concepto": ["Excedente del consumidor", "Excedente del productor",
                     "Gasto del Estado", "Bienestar total (W)"],
        "Sin subsidio": [f"${fmt(R['EC0'])}", f"${fmt(R['EP0'])}", "$0,00", f"${fmt(R['W0'])}"],
        "Con subsidio": [f"${fmt(R['EC1'])}", f"${fmt(R['EP1'])}",
                         f"–${fmt(R['gasto'])}", f"${fmt(R['W1'])}"],
        "Variación": [f"+${fmt(R['EC1']-R['EC0'])}", f"+${fmt(R['EP1']-R['EP0'])}",
                      f"–${fmt(R['gasto'])}", f"–${fmt(R['dwl'])}"],
    })
    st.dataframe(df_b, hide_index=True, use_container_width=True)

    st.write("")
    seccion("Simulación", "Barrido de subsidios")
    valores_s = [0, 5, 10, 15, 20] if preset.startswith("Ej. 1") else [0, 2, 4, 6, 8, 10]
    filas = []
    for sv in valores_s:
        r = bienestar_subsidio(a, b, c, d, float(sv))
        filas.append({"Subsidio (s)": f"${fmt(sv,0)}", "Cantidad": f"{fmt(r['Q1'])} u.",
                      "Precio usuario": f"${fmt(r['Pc'])}", "Gasto público": f"${fmt(r['gasto'])}",
                      "Bienestar total": f"${fmt(r['W1'])}", "Pérdida eficiencia": f"${fmt(r['dwl'])}"})
    st.dataframe(pd.DataFrame(filas), hide_index=True, use_container_width=True)
    lec("A mayor subsidio, mejor precio y cantidad para el usuario, pero el gasto "
        "público crece más que proporcionalmente y la pérdida de eficiencia se "
        "agranda: cada peso adicional compra cada vez menos bienestar.", "info")

# ======================================================================
# SECCIÓN 3 — PRECIO MÁXIMO
# ======================================================================
elif seccion_activa.startswith("3"):
    titulo = "Precio máximo a los alquileres" if preset.startswith("Ej. 2") \
        else "Precio máximo (techo de precio)"
    seccion("Ejercicio 2 · intervención", titulo)

    if preset.startswith("Ej. 1"):
        lec("Tenés cargados los datos del <b>Ejercicio 1 (transporte)</b>. "
            "Para el precio máximo del enunciado, elegí <b>Ej. 2</b> en la barra "
            "lateral.", "warn")
        st.write("")

    ptecho = st.slider("Precio máximo (Pmáx)", 1.0, float(P0 * 1.5),
                       float(ptecho_default), step=1.0)
    R = bienestar_precio_maximo(a, b, c, d, ptecho)

    colg, colr = st.columns([3, 2], gap="large")
    with colg:
        p_arr, p_top = grilla_precios(a, b, c, d)
        qd = np.clip(a - b * p_arr, 0, None)
        qo = np.clip(c + d * p_arr, 0, None)
        fig = go.Figure()
        if R["vinculante"]:
            Qt = R["Qt"]
            Pd_en_Qt = precio_demanda(Qt, a, b)
            fig.add_trace(go.Scatter(x=[0, 0, Qt, Qt],
                                     y=[ptecho, a / b, Pd_en_Qt, ptecho],
                                     fill="toself", fillcolor=COL_EC, line=dict(width=0),
                                     name="Excedente consumidor", hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=[0, 0, Qt], y=[ptecho, max(-c / d, 0), ptecho],
                                     fill="toself", fillcolor=COL_EP, line=dict(width=0),
                                     name="Excedente productor", hoverinfo="skip"))
        else:
            fig.add_trace(go.Scatter(x=[0, 0, Q0], y=[P0, a / b, P0], fill="toself",
                                     fillcolor=COL_EC, line=dict(width=0),
                                     name="Excedente consumidor", hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=[0, 0, Q0], y=[P0, max(-c / d, 0), P0], fill="toself",
                                     fillcolor=COL_EP, line=dict(width=0),
                                     name="Excedente productor", hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=qd, y=p_arr, name="Demanda",
                                 line=dict(color=COL_DEM, width=3)))
        fig.add_trace(go.Scatter(x=qo, y=p_arr, name="Oferta",
                                 line=dict(color=COL_OFE, width=3)))
        fig.add_hline(y=ptecho, line_dash="dash", line_color=COL_OFE2,
                      annotation_text="Precio máximo", annotation_position="top left")
        fig.add_trace(go.Scatter(x=[Q0], y=[P0], mode="markers+text", text=["C"],
                                 textposition="top center",
                                 textfont=dict(size=15, color=COL_EQ),
                                 marker=dict(color=COL_EQ, size=13,
                                             line=dict(color="white", width=1)),
                                 name="C · Equilibrio libre (P*)"))
        if R["vinculante"]:
            fig.add_trace(go.Scatter(
                x=[R["Qt"], Q0, R["Qt"]],
                y=[precio_demanda(R["Qt"], a, b), P0, precio_oferta(R["Qt"], c, d)],
                fill="toself", fillcolor=COL_DWL, line=dict(width=0),
                name="Pérdida de eficiencia", hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=[R["Qo"]], y=[ptecho], mode="markers+text",
                                     text=["A"], textposition="bottom right",
                                     textfont=dict(size=15, color=COL_OFE),
                                     marker=dict(color=COL_OFE, size=12,
                                                 line=dict(color="white", width=1)),
                                     name="A · Cantidad ofrecida (lo que se vende)"))
            fig.add_trace(go.Scatter(x=[R["Qd"]], y=[ptecho], mode="markers+text",
                                     text=["B"], textposition="bottom left",
                                     textfont=dict(size=15, color=COL_DEM),
                                     marker=dict(color=COL_DEM, size=12,
                                                 line=dict(color="white", width=1)),
                                     name="B · Cantidad demandada (lo que se quiere)"))
            fig.add_trace(go.Scatter(x=[R["Qo"], R["Qd"]], y=[ptecho, ptecho],
                                     mode="lines", name="Escasez (A→B)",
                                     line=dict(color=COL_EQ, width=5)))
        base_layout(fig, a, p_top, "Efecto del precio máximo sobre el mercado")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("**A** · Cantidad ofrecida al tope (lo que se vende)   |   "
                   "**B** · Cantidad demandada (lo que se querría)   |   "
                   "**C** · Equilibrio libre")

    with colr:
        d1, d2 = st.columns(2)
        dato(d1, "Cant. demandada", f"{fmt(R['Qd'])}", " u.")
        dato(d2, "Cant. ofrecida", f"{fmt(R['Qo'])}", " u.")
        st.write("")
        if R["vinculante"]:
            dato(st, "Escasez", f"{fmt(R['escasez'])}", " u.")
        else:
            dato(st, "Escasez", "0,00", " u. (no vinculante)")
        st.write("")
        if R["vinculante"]:
            lec(f"El tope de <b>${fmt(ptecho)}</b> está por debajo del equilibrio "
                f"(${fmt(P0)}): es <b>vinculante</b>. Se demandan <b>{fmt(R['Qd'])}</b> "
                f"pero solo se ofrecen <b>{fmt(R['Qo'])}</b> → escasez de "
                f"<b>{fmt(R['escasez'])}</b> u. Ganan los inquilinos que consiguen "
                f"contrato; pierden los propietarios y quienes quedan sin vivienda. "
                f"El bienestar cae <b>${fmt(R['dwl'])}</b>.", "bad")
        else:
            lec(f"El tope de ${fmt(ptecho)} está por encima del equilibrio "
                f"(${fmt(P0)}): <b>no es vinculante</b> y el mercado opera como si "
                f"no existiera.", "ok")

    st.write("")
    seccion("Bienestar", "Antes y después del tope")
    df_b = pd.DataFrame({
        "Concepto": ["Excedente del consumidor", "Excedente del productor",
                     "Bienestar total (W)"],
        "Sin tope": [f"${fmt(R['EC0'])}", f"${fmt(R['EP0'])}", f"${fmt(R['W0'])}"],
        "Con tope": [f"${fmt(R['EC1'])}", f"${fmt(R['EP1'])}", f"${fmt(R['W1'])}"],
        "Variación": [f"{'+' if R['EC1']>=R['EC0'] else '–'}${fmt(abs(R['EC1']-R['EC0']))}",
                      f"–${fmt(abs(R['EP1']-R['EP0']))}", f"–${fmt(R['dwl'])}"],
    })
    st.dataframe(df_b, hide_index=True, use_container_width=True)

    st.write("")
    seccion("Simulación", "Barrido de precios máximos")
    valores_p = [70, 60, 50, 40, 30] if preset.startswith("Ej. 2") \
        else [round(P0 * x, 0) for x in (1.25, 1.0, 0.85, 0.7, 0.55)]
    filas = []
    for pv in valores_p:
        r = resolver_precio_maximo(a, b, c, d, float(pv))
        filas.append({"Precio máx.": f"${fmt(pv,0)}", "Cant. demandada": f"{fmt(r['Qd'])} u.",
                      "Cant. ofrecida": f"{fmt(r['Qo'])} u.",
                      "Escasez": f"{fmt(r['escasez'])} u." if r["vinculante"] else "—",
                      "¿Vinculante?": "Sí" if r["vinculante"] else "No"})
    st.dataframe(pd.DataFrame(filas), hide_index=True, use_container_width=True)
    lec("Cuanto más bajo el tope, mayor la escasez: sube la cantidad demandada y "
        "baja la ofrecida. Un tope pensado para ayudar reduce la vivienda "
        "disponible.", "info")

# ======================================================================
# SECCIÓN 4 — FÓRMULAS
# ======================================================================
else:
    seccion("Referencia", "Modelo económico y fórmulas")
    st.markdown("**Funciones del mercado**")
    st.latex(r"Q_d = a - bP \qquad Q_o = c + dP")
    st.markdown("**Equilibrio competitivo**")
    st.latex(r"P^* = \frac{a - c}{b + d} \qquad Q^* = a - bP^*")
    st.markdown("**Excedentes**")
    st.latex(r"EC = \tfrac{1}{2}\,Q\,(\tfrac{a}{b} - P_{pagado})")
    st.latex(r"EP = P_{recibido}\cdot Q - \frac{1}{d}\!\left(\frac{Q^2}{2} - cQ\right)")
    st.markdown("**Subsidio por unidad (s)**")
    st.latex(r"P_c = \frac{a - c - d\,s}{b + d}, \quad P_v = P_c + s, \quad Q_1 = a - bP_c")
    st.latex(r"\text{Gasto} = s\cdot Q_1 \qquad W = EC + EP - \text{Gasto}")
    st.markdown("**Precio máximo (vinculante si Pmáx < P\\*)**")
    st.latex(r"Q_d = a - bP_{max}, \quad Q_o = c + dP_{max}, \quad \text{Escasez} = Q_d - Q_o")
    st.markdown("<hr class='regla'>", unsafe_allow_html=True)
    lec("La <b>pérdida de eficiencia</b> es el bienestar que desaparece porque la "
        "cantidad transada se aleja de la de equilibrio. En el subsidio se transan "
        "unidades de más; en el precio máximo, de menos. El triángulo bordó del "
        "gráfico mide esa pérdida.", "info")
    st.caption("App del TP N.º 2 · Economía para Ingenieros · UNSTA")
