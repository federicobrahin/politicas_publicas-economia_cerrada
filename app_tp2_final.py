# -*- coding: utf-8 -*-
"""
SIMULADOR DE POLÍTICAS PÚBLICAS EN ECONOMÍA CERRADA  —  VERSIÓN FINAL
Trabajo Práctico N.º 2 — Economía para Ingenieros — UNSTA
Prof. Antonio Raúl García

Diseño: estética "cuaderno técnico" en modo OSCURO, con navegación en
barra superior (no lateral) y panel de parámetros plegable y centrado.

Funciones PRO (desafío +10% y extra):
  - Comparador de escenarios A vs B lado a lado
  - Exportación de todas las tablas a CSV (descarga)
  - Análisis de sensibilidad (gasto y pérdida de eficiencia vs política)
  - Excedentes graficados + puntos rotulados con letras (A, B, C)
  - Indicador de eficiencia del gasto, lecturas económicas automáticas

Integrantes:
  * Antúnez Ruiz Huidobro, Facundo
  * Brahin, Federico Tomás
  * Gordillo Toledo, Rodrigo Gabriel
  * Matos Villalba, Luis Humberto

Ejecutar con:  streamlit run app_tp2_final.py
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# ======================================================================
# CONFIGURACIÓN Y ESTILO  (cuaderno técnico OSCURO)
# ======================================================================
st.set_page_config(
    page_title="Laboratorio de Políticas Públicas · UNSTA",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap');

    /* Fondo oscuro con un leve degradé cálido arriba */
    .stApp {
        background:
            radial-gradient(1100px 500px at 50% -8%, #20283a 0%, #0e1320 60%),
            #0e1320;
        color: #d9e2ee;
    }
    section.main > div { font-family: 'Inter', sans-serif; }

    h1, h2, h3 {
        font-family: 'Fraunces', serif !important;
        color: #f3efe6; letter-spacing: -0.01em;
    }
    h1 { font-weight: 600; }

    /* Cintillo / eyebrow */
    .eyebrow {
        font-family: 'Inter', sans-serif; font-size: 0.72rem; font-weight: 600;
        letter-spacing: 0.18em; text-transform: uppercase; color: #d98a4f;
        margin-bottom: 2px;
    }
    .regla { height: 2px; background: #c9742f; border: 0; margin: 6px 0 18px 0;
             opacity: 0.55; }

    /* Cabecera principal */
    .cab {
        text-align: center; padding: 10px 0 2px 0;
    }
    .cab .sup { font-family:'Inter',sans-serif; font-size:0.72rem; font-weight:600;
                letter-spacing:0.22em; text-transform:uppercase; color:#d98a4f; }
    .cab h1 { font-size: 2.0rem; margin: 4px 0 2px 0; }
    .cab .sub { color:#94a3b8; font-size:0.9rem; }

    /* Tarjetas de dato */
    .dato {
        background: #161d2e; border: 1px solid #283149; border-radius: 8px;
        padding: 12px 14px; height: 100%;
    }
    .dato .k { font-size: 0.68rem; letter-spacing: 0.08em; text-transform: uppercase;
               color: #8493ab; }
    .dato .v { font-family: 'Fraunces', serif; font-size: 1.5rem; color: #f3efe6;
               line-height: 1.1; margin-top: 2px; }
    .dato .v small { font-size: 0.82rem; color: #8493ab; }

    /* Lecturas económicas */
    .lec {
        background: #141b2b; border: 1px solid #283149; border-left: 4px solid #c9742f;
        border-radius: 8px; padding: 14px 16px; color: #cdd9ec;
        font-size: 0.92rem; line-height: 1.55;
    }
    .lec.ok   { border-left-color:#3fae6b; }
    .lec.warn { border-left-color:#e0973f; }
    .lec.bad  { border-left-color:#d65448; }

    /* Barra de navegación superior: estilizamos el radio horizontal como pills */
    div[role="radiogroup"] > label {
        background:#161d2e; border:1px solid #283149; border-radius:999px;
        padding:6px 16px; margin-right:8px;
    }
    div[role="radiogroup"] > label:hover { border-color:#c9742f; }

    .stDataFrame { border: 1px solid #283149; border-radius: 8px; }
    [data-testid="stHeader"] { background: transparent; }

    /* Botón de descarga */
    .stDownloadButton button {
        background:#c9742f; color:#fff; border:0; border-radius:8px;
        font-weight:600;
    }
    .stDownloadButton button:hover { background:#b4632a; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Paleta de gráficos (tinta cálida sobre fondo oscuro)
COL_DEM  = "#5b9bd5"   # demanda  (azul)
COL_OFE  = "#4fb477"   # oferta   (verde)
COL_OFE2 = "#d98a4f"   # oferta desplazada (terracota)
COL_EQ   = "#e0655b"   # equilibrio (bordó/coral)
COL_EC   = "rgba(91,155,213,0.22)"
COL_EP   = "rgba(79,180,119,0.22)"
COL_FISC = "rgba(217,138,79,0.28)"
COL_DWL  = "rgba(224,101,91,0.34)"
PAPER    = "#0e1320"
PLOT_BG  = "#141b2b"
GRID     = "#23304a"

# ======================================================================
# NÚCLEO ECONÓMICO  (validado en versiones anteriores)
# ======================================================================
def equilibrio(a, b, c, d):
    P = (a - c) / (b + d)
    return P, a - b * P

def precio_demanda(Q, a, b):
    return (a - Q) / b

def precio_oferta(Q, c, d):
    return (Q - c) / d

def excedente_consumidor(Q, P_pagado, a, b):
    return 0.5 * Q * max(a / b - P_pagado, 0.0)

def excedente_productor(Q, P_recibido, c, d):
    return P_recibido * Q - (Q ** 2 / 2 - c * Q) / d

def resolver_subsidio(a, b, c, d, s):
    Pc = (a - c - d * s) / (b + d)
    return Pc, Pc + s, a - b * Pc

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
    return {"P0": P0, "Q0": Q0, "EC0": EC0, "EP0": EP0, "W0": W0,
            "Pc": Pc, "Pv": Pv, "Q1": Q1, "EC1": EC1, "EP1": EP1,
            "gasto": gasto, "W1": W1, "dwl": W0 - W1}

def resolver_precio_maximo(a, b, c, d, p_techo):
    P0, Q0 = equilibrio(a, b, c, d)
    vinc = p_techo < P0
    Qd = a - b * p_techo
    Qo = c + d * p_techo
    return {"P0": P0, "Q0": Q0, "vinculante": vinc, "Qd": Qd, "Qo": Qo,
            "escasez": max(Qd - Qo, 0.0),
            "Q_transada": Qo if vinc else Q0, "p_techo": p_techo}

def bienestar_precio_maximo(a, b, c, d, p_techo):
    base = resolver_precio_maximo(a, b, c, d, p_techo)
    P0, Q0 = base["P0"], base["Q0"]
    EC0 = excedente_consumidor(Q0, P0, a, b)
    EP0 = excedente_productor(Q0, P0, c, d)
    W0 = EC0 + EP0
    if base["vinculante"]:
        Qt = base["Q_transada"]
        Pd_en_Qt = precio_demanda(Qt, a, b)
        EC1 = 0.5 * Qt * ((a / b - p_techo) + (Pd_en_Qt - p_techo))
        EP1 = excedente_productor(Qt, p_techo, c, d)
        W1 = EC1 + EP1
        dwl = W0 - W1
    else:
        Qt = Q0
        EC1, EP1, W1, dwl = EC0, EP0, W0, 0.0
    out = dict(base)
    out.update({"EC0": EC0, "EP0": EP0, "W0": W0, "EC1": EC1, "EP1": EP1,
                "W1": W1, "dwl": dwl, "Qt": Qt})
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

def dato(col, k, v, sufijo="", ayuda=None):
    extra = f" title='{ayuda}'" if ayuda else ""
    col.markdown(
        f"<div class='dato'{extra}><div class='k'>{k}</div>"
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
        title=dict(text=titulo, font=dict(family="Fraunces, serif", size=17, color="#f3efe6")),
        height=500, paper_bgcolor=PAPER, plot_bgcolor=PLOT_BG,
        font=dict(family="Inter, sans-serif", color="#cdd9ec"),
        xaxis_title="Cantidad (Q)", yaxis_title="Precio (P)",
        xaxis=dict(range=[0, a * 1.05], gridcolor=GRID, zerolinecolor=GRID),
        yaxis=dict(range=[0, p_top], gridcolor=GRID, zerolinecolor=GRID),
        legend=dict(orientation="h", y=-0.18, x=0, font=dict(size=10)))
    return fig

def csv_download(df, nombre, etiqueta):
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(etiqueta, csv, file_name=nombre, mime="text/csv")

# ======================================================================
# CABECERA + BARRA DE NAVEGACIÓN SUPERIOR
# ======================================================================
st.markdown(
    """
    <div class='cab'>
      <div class='sup'>TP N.º 2 · Economía para Ingenieros · UNSTA · Prof. R. García</div>
      <h1>Laboratorio de Políticas Públicas</h1>
      <div class='sub'>Mercados en economía cerrada · subsidios y controles de precios</div>
    </div>
    """, unsafe_allow_html=True)
st.write("")

# Navegación horizontal (radio estilizado como pills)
nav_cols = st.columns([1, 6, 1])
with nav_cols[1]:
    seccion_activa = st.radio(
        "nav", label_visibility="collapsed", horizontal=True,
        options=["Mercado y excedentes", "Subsidio (Ej. 1)",
                 "Precio máximo (Ej. 2)", "Comparador", "Fórmulas"],
    )

# ----------------------------------------------------------------------
# PANEL DE PARÁMETROS — franja superior plegable y centrada
# (se oculta en la sección «Fórmulas», pero las variables se siguen
#  calculando para no romper el resto de la app)
# ----------------------------------------------------------------------
# Tooltip del selector según la sección activa
if seccion_activa in ("Subsidio (Ej. 1)", "Precio máximo (Ej. 2)"):
    ayuda_preset = "Completar a, b, c, d y el valor de la política."
else:
    ayuda_preset = "Completar a, b, c, d"

mostrar_panel = seccion_activa != "Fórmulas"

if mostrar_panel:
    panel = st.expander("⚙  Parámetros del mercado y carga de datos del enunciado",
                        expanded=True)
else:
    panel = st.container()  # contenedor invisible: agrupa los widgets sin mostrarlos

with panel:
    if mostrar_panel:
        pc1, pc2 = st.columns([2, 3])
        with pc1:
            preset = st.selectbox(
                "Cargar datos del enunciado",
                ["Personalizado",
                 "Ej. 1 — Subsidio al transporte",
                 "Ej. 2 — Precio máximo a alquileres"],
                help=ayuda_preset,
            )
        if preset == "Ej. 1 — Subsidio al transporte":
            da, db, dc, dd = 1500.0, 25.0, 0.0, 15.0
        elif preset == "Ej. 2 — Precio máximo a alquileres":
            da, db, dc, dd = 1800.0, 20.0, 0.0, 12.0
        else:
            da, db, dc, dd = 1000.0, 30.0, 0.0, 20.0

        g = st.columns(4)
        a = g[0].number_input("a · intercepto demanda", value=da, step=10.0,
                              help="Cantidad demandada cuando el precio es 0 (Qd = a − bP).")
        b = g[1].number_input("b · pendiente demanda", value=db, step=1.0, min_value=0.01,
                              help="Cuánto cae la cantidad demandada por cada peso de aumento.")
        c = g[2].number_input("c · intercepto oferta", value=dc, step=10.0,
                              help="Cantidad ofrecida cuando el precio es 0 (Qo = c + dP).")
        d = g[3].number_input("d · pendiente oferta", value=dd, step=1.0, min_value=0.01,
                              help="Cuánto sube la cantidad ofrecida por cada peso de aumento.")
        st.caption("Funciones:  Qd = a − bP    ·    Qo = c + dP")
    else:
        # En «Fórmulas» no se muestra el panel; usamos valores por defecto
        # para que el resto del archivo no falle.
        preset = "Personalizado"
        a, b, c, d = 1000.0, 30.0, 0.0, 20.0

# Defaults de política
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
st.write("")

# ======================================================================
# SECCIÓN 1 — MERCADO Y EXCEDENTES
# ======================================================================
if seccion_activa == "Mercado y excedentes":
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
        with st.expander("Ver excedentes paso a paso"):
            st.markdown(
                f"- **Precio de equilibrio:** P\\* = (a − c)/(b + d) = "
                f"({fmt(a,0)} − {fmt(c,0)})/({fmt(b,0)} + {fmt(d,0)}) = **${fmt(P0)}**\n"
                f"- **Cantidad:** Q\\* = a − bP\\* = **{fmt(Q0)} u.**\n"
                f"- **EC** = ½ · Q\\* · (a/b − P\\*) = **${fmt(EC0_g)}**\n"
                f"- **EP** = área entre P\\* y la oferta = **${fmt(EP0_g)}**")

# ======================================================================
# SECCIÓN 2 — SUBSIDIO
# ======================================================================
elif seccion_activa == "Subsidio (Ej. 1)":
    titulo = "Subsidio al transporte público" if preset.startswith("Ej. 1") \
        else "Subsidio por unidad al productor"
    seccion("Ejercicio 1 · intervención", titulo)
    if preset.startswith("Ej. 2"):
        lec("Tenés cargados los datos del <b>Ejercicio 2 (alquileres)</b>. Para el "
            "subsidio del enunciado, elegí <b>Ej. 1</b> en el panel de parámetros.",
            "warn")
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
        # Indicador extra de eficiencia del gasto
        if R["gasto"] > 0:
            efic = (R["W1"] - R["W0"] + R["gasto"]) / R["gasto"]
            dato(st, "Bienestar privado ganado por $1 de gasto", f"${fmt(efic)}",
                 ayuda="Cuánto suben EC+EP por cada peso gastado. Menos de $1 "
                       "significa que el gasto supera lo que ganan las partes.")
            st.write("")
        if s > 0:
            lec(f"Con s = <b>${fmt(s)}</b>: el usuario paga <b>${fmt(R['Pc'])}</b> "
                f"(antes ${fmt(P0)}) y la empresa cobra <b>${fmt(R['Pv'])}</b>. Ganan "
                f"ambas partes, pero el Estado gasta <b>${fmt(R['gasto'])}</b> (lo "
                f"pagan los contribuyentes) y el bienestar neto cae "
                f"<b>${fmt(R['dwl'])}</b>: la pérdida de eficiencia (área coral).",
                "warn")
            st.write("")
            lec(f"El <b>triángulo coral</b> del gráfico es la <b>pérdida de "
                f"eficiencia</b>: con el subsidio el mercado transa "
                f"<b>{fmt(R['Q1'])}</b> unidades en lugar de las <b>{fmt(Q0)}</b> de "
                f"equilibrio. Esas <b>{fmt(R['Q1'] - Q0)}</b> unidades de más cuestan "
                f"producirlas más de lo que los usuarios realmente las valoran, y esa "
                f"diferencia (${fmt(R['dwl'])}) es bienestar que se pierde.", "info")

    st.write("")
    seccion("Bienestar", "Antes y después del subsidio")
    df_b = pd.DataFrame({
        "Concepto": ["Excedente del consumidor", "Excedente del productor",
                     "Gasto del Estado", "Bienestar total (W)"],
        "Sin subsidio": [f"{R['EC0']:.2f}", f"{R['EP0']:.2f}", "0.00", f"{R['W0']:.2f}"],
        "Con subsidio": [f"{R['EC1']:.2f}", f"{R['EP1']:.2f}",
                         f"-{R['gasto']:.2f}", f"{R['W1']:.2f}"],
        "Variación": [f"{R['EC1']-R['EC0']:+.2f}", f"{R['EP1']-R['EP0']:+.2f}",
                      f"-{R['gasto']:.2f}", f"-{R['dwl']:.2f}"],
    })
    st.dataframe(df_b, hide_index=True, use_container_width=True)
    csv_download(df_b, "bienestar_subsidio.csv", "⬇  Descargar tabla de bienestar (CSV)")

    st.write("")
    seccion("Simulación", "Barrido de subsidios")
    valores_s = [0, 5, 10, 15, 20] if preset.startswith("Ej. 1") else [0, 2, 4, 6, 8, 10]
    filas = []
    for sv in valores_s:
        r = bienestar_subsidio(a, b, c, d, float(sv))
        filas.append({"Subsidio (s)": sv, "Cantidad": round(r["Q1"], 2),
                      "Precio usuario": round(r["Pc"], 2), "Gasto público": round(r["gasto"], 2),
                      "Bienestar total": round(r["W1"], 2), "Perdida eficiencia": round(r["dwl"], 2)})
    df_sim = pd.DataFrame(filas)
    st.dataframe(df_sim, hide_index=True, use_container_width=True)
    csv_download(df_sim, "simulacion_subsidio.csv", "⬇  Descargar simulación (CSV)")

    # --- PRO: gráfico de sensibilidad ---
    st.write("")
    with st.expander("📈  Análisis de sensibilidad — gasto y pérdida vs subsidio"):
        s_grid = np.linspace(0, max(P0 * 1.5, 20), 40)
        gasto_grid = [bienestar_subsidio(a, b, c, d, float(x))["gasto"] for x in s_grid]
        dwl_grid = [bienestar_subsidio(a, b, c, d, float(x))["dwl"] for x in s_grid]
        figs = go.Figure()
        figs.add_trace(go.Scatter(x=s_grid, y=gasto_grid, name="Gasto público",
                                  line=dict(color=COL_OFE2, width=3)))
        figs.add_trace(go.Scatter(x=s_grid, y=dwl_grid, name="Pérdida de eficiencia",
                                  line=dict(color=COL_EQ, width=3)))
        figs.add_vline(x=s, line_dash="dash", line_color="#8493ab",
                       annotation_text=f"s = {fmt(s)}")
        figs.update_layout(height=340, paper_bgcolor=PAPER, plot_bgcolor=PLOT_BG,
                           font=dict(family="Inter, sans-serif", color="#cdd9ec"),
                           xaxis_title="Subsidio por unidad (s)", yaxis_title="$",
                           xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID),
                           legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(figs, use_container_width=True)
        lec("El gasto crece de forma aproximadamente lineal con el subsidio, pero "
            "la pérdida de eficiencia crece de forma cuadrática: por eso los "
            "subsidios grandes son cada vez menos rentables socialmente.", "info")

    lec("A mayor subsidio, mejor precio y cantidad para el usuario, pero el gasto "
        "público crece más que proporcionalmente y la pérdida de eficiencia se "
        "agranda: cada peso adicional compra cada vez menos bienestar.", "info")

# ======================================================================
# SECCIÓN 3 — PRECIO MÁXIMO
# ======================================================================
elif seccion_activa == "Precio máximo (Ej. 2)":
    titulo = "Precio máximo a los alquileres" if preset.startswith("Ej. 2") \
        else "Precio máximo (techo de precio)"
    seccion("Ejercicio 2 · intervención", titulo)
    if preset.startswith("Ej. 1"):
        lec("Tenés cargados los datos del <b>Ejercicio 1 (transporte)</b>. Para el "
            "precio máximo del enunciado, elegí <b>Ej. 2</b> en el panel de "
            "parámetros.", "warn")
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
            fig.add_trace(go.Scatter(x=[0, 0, Qt, Qt], y=[ptecho, a / b, Pd_en_Qt, ptecho],
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
            st.write("")
            lec(f"El <b>triángulo coral</b> del gráfico es la <b>pérdida de "
                f"eficiencia</b>: con el tope solo se transan <b>{fmt(R['Qt'])}</b> "
                f"unidades en lugar de las <b>{fmt(Q0)}</b> de equilibrio. Esas "
                f"<b>{fmt(Q0 - R['Qt'])}</b> unidades que dejan de intercambiarse "
                f"habrían generado valor tanto para inquilinos como para propietarios, "
                f"y ese valor perdido (${fmt(R['dwl'])}) es bienestar que desaparece.",
                "info")
        else:
            lec(f"El tope de ${fmt(ptecho)} está por encima del equilibrio "
                f"(${fmt(P0)}): <b>no es vinculante</b> y el mercado opera como si no "
                f"existiera.", "ok")

    st.write("")
    seccion("Bienestar", "Antes y después del tope")
    df_b = pd.DataFrame({
        "Concepto": ["Excedente del consumidor", "Excedente del productor",
                     "Bienestar total (W)"],
        "Sin tope": [f"{R['EC0']:.2f}", f"{R['EP0']:.2f}", f"{R['W0']:.2f}"],
        "Con tope": [f"{R['EC1']:.2f}", f"{R['EP1']:.2f}", f"{R['W1']:.2f}"],
        "Variación": [f"{R['EC1']-R['EC0']:+.2f}", f"{R['EP1']-R['EP0']:+.2f}",
                      f"-{R['dwl']:.2f}"],
    })
    st.dataframe(df_b, hide_index=True, use_container_width=True)
    csv_download(df_b, "bienestar_precio_maximo.csv", "⬇  Descargar tabla de bienestar (CSV)")

    st.write("")
    seccion("Simulación", "Barrido de precios máximos")
    valores_p = [70, 60, 50, 40, 30] if preset.startswith("Ej. 2") \
        else [round(P0 * x, 0) for x in (1.25, 1.0, 0.85, 0.7, 0.55)]
    filas = []
    for pv in valores_p:
        r = resolver_precio_maximo(a, b, c, d, float(pv))
        filas.append({"Precio max": pv, "Cant. demandada": round(r["Qd"], 2),
                      "Cant. ofrecida": round(r["Qo"], 2),
                      "Escasez": round(r["escasez"], 2) if r["vinculante"] else 0,
                      "Vinculante": "Si" if r["vinculante"] else "No"})
    df_sim = pd.DataFrame(filas)
    st.dataframe(df_sim, hide_index=True, use_container_width=True)
    csv_download(df_sim, "simulacion_precio_maximo.csv", "⬇  Descargar simulación (CSV)")

    st.write("")
    with st.expander("📈  Análisis de sensibilidad — escasez vs precio máximo"):
        p_grid = np.linspace(P0 * 0.3, P0 * 1.2, 40)
        esc_grid = [resolver_precio_maximo(a, b, c, d, float(x))["escasez"] for x in p_grid]
        figs = go.Figure()
        figs.add_trace(go.Scatter(x=p_grid, y=esc_grid, name="Escasez",
                                  line=dict(color=COL_EQ, width=3), fill="tozeroy",
                                  fillcolor="rgba(224,101,91,0.15)"))
        figs.add_vline(x=ptecho, line_dash="dash", line_color="#8493ab",
                       annotation_text=f"Pmáx actual = {fmt(ptecho)}")
        figs.add_vline(x=P0, line_dash="dot", line_color=COL_OFE,
                       annotation_text=f"Equilibrio P* = {fmt(P0)} (umbral de escasez)")
        figs.update_layout(height=340, paper_bgcolor=PAPER, plot_bgcolor=PLOT_BG,
                           font=dict(family="Inter, sans-serif", color="#cdd9ec"),
                           xaxis_title="Precio máximo", yaxis_title="Escasez (u.)",
                           xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID),
                           legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(figs, use_container_width=True)
        lec("La escasez aparece recién cuando el tope cae por debajo de P\\* y luego "
            "crece de forma acelerada: cuanto más ambicioso el control, más grave el "
            "desabastecimiento.", "info")

    lec("Cuanto más bajo el tope, mayor la escasez: sube la cantidad demandada y "
        "baja la ofrecida. Un tope pensado para ayudar reduce la vivienda "
        "disponible.", "info")

# ======================================================================
# SECCIÓN 4 — COMPARADOR DE ESCENARIOS  (PRO)
# ======================================================================
elif seccion_activa == "Comparador":
    seccion("Función avanzada", "Comparador de escenarios")
    lec("A continuación, configure 2 políticas y compare los efectos de las mismas "
        "sobre un mismo mercado.", "info")
    st.write("")

    cA, cB = st.columns(2, gap="large")
    resultados = {}
    for col, etq in [(cA, "A"), (cB, "B")]:
        with col:
            st.markdown(f"#### Escenario {etq}")
            tipo = st.selectbox(f"Política {etq}", ["Subsidio", "Precio máximo"],
                                key=f"tipo_{etq}")
            if tipo == "Subsidio":
                val = st.slider(f"Subsidio (s) — {etq}", 0.0, float(max(P0 * 1.5, 20)),
                                float(s_default), step=0.5, key=f"s_{etq}")
                r = bienestar_subsidio(a, b, c, d, val)
                resultados[etq] = {
                    "Política": f"Subsidio ${fmt(val)}",
                    "Cantidad": r["Q1"], "Precio usuario": r["Pc"],
                    "Costo fiscal": r["gasto"], "Bienestar (W)": r["W1"],
                    "Pérdida eficiencia": r["dwl"]}
            else:
                val = st.slider(f"Precio máximo — {etq}", 1.0, float(P0 * 1.5),
                                float(ptecho_default), step=1.0, key=f"p_{etq}")
                r = bienestar_precio_maximo(a, b, c, d, val)
                resultados[etq] = {
                    "Política": f"Tope ${fmt(val)}",
                    "Cantidad": r["Qt"], "Precio usuario": val,
                    "Costo fiscal": 0.0, "Bienestar (W)": r["W1"],
                    "Pérdida eficiencia": r["dwl"]}
            r0 = resultados[etq]
            dd1, dd2 = st.columns(2)
            dato(dd1, "Bienestar (W)", f"${fmt(r0['Bienestar (W)'])}")
            dato(dd2, "Pérdida efic.", f"${fmt(r0['Pérdida eficiencia'])}")

    st.write("")
    seccion("Resultado", "Comparación lado a lado")
    df_cmp = pd.DataFrame([resultados["A"], resultados["B"]], index=["Escenario A", "Escenario B"])
    df_cmp_fmt = df_cmp.copy()
    for col in ["Cantidad", "Precio usuario", "Costo fiscal", "Bienestar (W)", "Pérdida eficiencia"]:
        df_cmp_fmt[col] = df_cmp[col].map(lambda x: fmt(x))
    st.dataframe(df_cmp_fmt, use_container_width=True)
    csv_download(df_cmp.reset_index(), "comparador_escenarios.csv",
                 "⬇  Descargar comparación (CSV)")

    # Veredicto automático
    wa, wb = resultados["A"]["Bienestar (W)"], resultados["B"]["Bienestar (W)"]
    if abs(wa - wb) < 1e-6:
        lec("Ambos escenarios dejan el mismo bienestar total.", "info")
    else:
        mejor = "A" if wa > wb else "B"
        lec(f"En términos de <b>bienestar total</b>, el <b>Escenario {mejor}</b> es "
            f"superior (${fmt(max(wa, wb))} frente a ${fmt(min(wa, wb))}).<br><br>"
            f"En casos reales, el bienestar no es el único criterio ya que una "
            f"política puede preferirse por razones distributivas aunque se esté "
            f"sacrificando algo de eficiencia.", "ok")

# ======================================================================
# SECCIÓN 5 — FÓRMULAS
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
    st.caption("App del TP N.º 2 · Economía para Ingenieros · UNSTA")
