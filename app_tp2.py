# -*- coding: utf-8 -*-
"""
SIMULADOR DE POLÍTICAS PÚBLICAS EN ECONOMÍA CERRADA
Trabajo Práctico N.º 2 — Economía para Ingenieros — UNSTA
Prof. Antonio Raúl García

Enfoque: análisis de BIENESTAR (excedentes, resultado fiscal, variación
del bienestar social) para Subsidios y Precio Máximo, sobre los dos
ejercicios obligatorios del enunciado.

Integrantes:
  * Antúnez Ruiz Huidobro, Facundo
  * Brahin, Federico Tomás
  * Gordillo Toledo, Rodrigo Gabriel
  * Matos Villalba, Luis Humberto

Ejecutar con:  streamlit run app_tp2.py
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# ======================================================================
# CONFIGURACIÓN GENERAL Y ESTILO
# ======================================================================
st.set_page_config(
    page_title="Políticas Públicas · Economía Cerrada · UNSTA",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Paleta y estilo (dashboard sobrio, fondo oscuro) ---
st.markdown(
    """
    <style>
    /* Tipografía y fondo general */
    .stApp {
        background: radial-gradient(1200px 600px at 80% -10%, #14203a 0%, #0b1120 55%);
        color: #e6edf7;
    }
    /* Tarjetas de métricas */
    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, #131c30 0%, #0f1626 100%);
        border: 1px solid #233149;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset;
    }
    div[data-testid="stMetricLabel"] p {
        color: #8aa0c0 !important;
        font-size: 0.78rem !important;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] {
        color: #f2f6fc !important;
        font-weight: 700;
    }
    /* Encabezados */
    h1, h2, h3 { color: #f2f6fc; letter-spacing: -0.01em; }
    /* Tablas */
    .stDataFrame { border-radius: 12px; overflow: hidden; }
    /* Cajita de "lectura" económica */
    .nota {
        background: #0f1a2e;
        border-left: 3px solid #3b82f6;
        border-radius: 8px;
        padding: 14px 16px;
        color: #cdd9ec;
        font-size: 0.92rem;
        line-height: 1.5;
    }
    .nota-ok   { border-left-color:#22c55e; }
    .nota-warn { border-left-color:#f59e0b; }
    .nota-bad  { border-left-color:#ef4444; }
    /* Banda de título */
    .titulo-banda {
        background: linear-gradient(90deg, #1d4ed8 0%, #2563eb 40%, #0ea5e9 100%);
        border-radius: 14px; padding: 18px 22px; margin-bottom: 4px;
        box-shadow: 0 10px 30px -12px rgba(37,99,235,0.6);
    }
    .titulo-banda h1 { color: white; margin: 0; font-size: 1.55rem; }
    .titulo-banda p  { color: #dce9ff; margin: 4px 0 0 0; font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Colores de referencia para los gráficos (constantes para reutilizar)
COL_DEM   = "#60a5fa"   # demanda
COL_OFE   = "#34d399"   # oferta
COL_OFE2  = "#a78bfa"   # oferta desplazada
COL_EQ    = "#f87171"   # equilibrio
COL_EC    = "rgba(96,165,250,0.28)"   # relleno excedente consumidor
COL_EP    = "rgba(52,211,153,0.28)"   # relleno excedente productor
COL_FISC  = "rgba(245,158,11,0.30)"   # relleno costo fiscal
COL_DWL   = "rgba(239,68,68,0.35)"    # relleno pérdida de eficiencia

# ======================================================================
# NÚCLEO ECONÓMICO  (todas las fórmulas viven acá)
# ======================================================================
#
# Convención de funciones (igual que el enunciado):
#     Demanda:  Qd = a - b·P      ->   P = (a - Q)/b      (precio de demanda)
#     Oferta:   Qo = c + d·P      ->   P = (Q - c)/d      (precio de oferta)
#
# Notación de excedentes en función de cantidades/precios sobre el EJE PRECIO:
#     Precio máximo de disposición a pagar (corte demanda con eje P):  a/b
#     Precio mínimo al que aparece oferta  (corte oferta con eje P):    -c/d
# ----------------------------------------------------------------------


def equilibrio(a, b, c, d):
    """Equilibrio competitivo sin intervención."""
    P = (a - c) / (b + d)
    Q = a - b * P
    return P, Q


def precio_demanda(Q, a, b):
    """Precio sobre la curva de demanda para una cantidad Q (altura de la demanda)."""
    return (a - Q) / b


def precio_oferta(Q, c, d):
    """Precio sobre la curva de oferta para una cantidad Q (altura de la oferta)."""
    return (Q - c) / d


def excedente_consumidor(Q, P_pagado, a, b):
    """
    Área entre la curva de demanda y el precio que paga el consumidor,
    desde 0 hasta Q. Como la demanda es lineal, es un triángulo:
        base = Q ; altura = (precio_choke_demanda - P_pagado)
    donde precio_choke_demanda = a/b (intercepto de la demanda con el eje P).
    """
    choke = a / b
    altura = max(choke - P_pagado, 0.0)
    return 0.5 * Q * altura


def excedente_productor(Q, P_recibido, c, d):
    """
    Área entre el precio que recibe el productor y la curva de oferta,
    desde 0 hasta Q. Triángulo:
        base = Q ; altura = (P_recibido - precio_choke_oferta)
    donde precio_choke_oferta = -c/d (intercepto de la oferta con el eje P).
    Si c > 0 la oferta corta el eje Q en c, y el "choke" de precio es negativo:
    en ese caso el excedente del productor es un trapecio, que calculamos
    igual con la integral exacta (más robusto que el triángulo).
    """
    # Integral exacta del área entre P_recibido y la inversa de oferta P=(Q-c)/d
    # EP = ∫_0^Q [P_recibido - (q - c)/d] dq  = P_recibido·Q - (Q²/2 - c·Q)/d
    return P_recibido * Q - (Q ** 2 / 2 - c * Q) / d


# ----------------------------------------------------------------------
# ESCENARIO 1: SUBSIDIO POR UNIDAD (s)
# ----------------------------------------------------------------------
def resolver_subsidio(a, b, c, d, s):
    """
    Subsidio de 's' pesos por unidad al productor.
    Efecto: la oferta se desplaza hacia abajo/derecha. El productor recibe
    's' más por cada unidad que el consumidor paga.

    Condición de equilibrio con subsidio:
        Qd(Pc) = Qo(Pv)   con   Pv = Pc + s
        a - b·Pc = c + d·(Pc + s)
        Pc = (a - c - d·s) / (b + d)
        Pv = Pc + s
        Q  = a - b·Pc
    """
    Pc = (a - c - d * s) / (b + d)   # precio que paga el consumidor
    Pv = Pc + s                      # precio que recibe el productor
    Q = a - b * Pc
    return Pc, Pv, Q


def bienestar_subsidio(a, b, c, d, s):
    """Devuelve un diccionario con TODO el análisis de bienestar del subsidio."""
    P0, Q0 = equilibrio(a, b, c, d)
    EC0 = excedente_consumidor(Q0, P0, a, b)
    EP0 = excedente_productor(Q0, P0, c, d)
    W0 = EC0 + EP0  # sin gasto público inicial

    Pc, Pv, Q1 = resolver_subsidio(a, b, c, d, s)
    EC1 = excedente_consumidor(Q1, Pc, a, b)
    EP1 = excedente_productor(Q1, Pv, c, d)
    gasto = s * Q1                       # erogación del Estado
    W1 = EC1 + EP1 - gasto               # bienestar total = EC + EP - costo fiscal
    dwl = W0 - W1                         # pérdida irrecuperable de eficiencia

    return {
        "P0": P0, "Q0": Q0, "EC0": EC0, "EP0": EP0, "W0": W0,
        "Pc": Pc, "Pv": Pv, "Q1": Q1, "EC1": EC1, "EP1": EP1,
        "gasto": gasto, "W1": W1, "dwl": dwl,
    }


# ----------------------------------------------------------------------
# ESCENARIO 2: PRECIO MÁXIMO (techo de precio)
# ----------------------------------------------------------------------
def resolver_precio_maximo(a, b, c, d, p_techo):
    """
    Precio máximo legal 'p_techo'.
    - Si p_techo >= P_eq: NO es vinculante, el mercado opera en equilibrio.
    - Si p_techo <  P_eq: la cantidad la fija el lado corto = la OFERTA.
        Qd = a - b·p_techo   (lo que se quiere comprar)
        Qo = c + d·p_techo   (lo que se quiere/puede vender)  <-- cantidad transada
        escasez = Qd - Qo
    """
    P0, Q0 = equilibrio(a, b, c, d)
    vinculante = p_techo < P0

    Qd = a - b * p_techo
    Qo = c + d * p_techo
    escasez = Qd - Qo

    if vinculante:
        Q_transada = Qo            # lado corto
    else:
        Q_transada = Q0
    return {
        "P0": P0, "Q0": Q0, "vinculante": vinculante,
        "Qd": Qd, "Qo": Qo, "escasez": max(escasez, 0.0),
        "Q_transada": Q_transada, "p_techo": p_techo,
    }


def bienestar_precio_maximo(a, b, c, d, p_techo):
    """Análisis de bienestar del precio máximo."""
    base = resolver_precio_maximo(a, b, c, d, p_techo)
    P0, Q0 = base["P0"], base["Q0"]

    EC0 = excedente_consumidor(Q0, P0, a, b)
    EP0 = excedente_productor(Q0, P0, c, d)
    W0 = EC0 + EP0

    if base["vinculante"]:
        Qt = base["Q_transada"]                  # = Qo al precio techo
        # Consumidores: compran Qt y pagan p_techo, pero el precio que los
        # racionaría a esa cantidad sobre la demanda es precio_demanda(Qt).
        # EC = área entre demanda y p_techo, de 0 a Qt (trapecio).
        Pd_en_Qt = precio_demanda(Qt, a, b)
        choke_dem = a / b
        # EC = trapecio: lados (choke_dem - p_techo) y (Pd_en_Qt - p_techo), base Qt
        EC1 = 0.5 * Qt * ((choke_dem - p_techo) + (Pd_en_Qt - p_techo))
        # Productores: venden Qt y reciben p_techo.
        EP1 = excedente_productor(Qt, p_techo, c, d)
        W1 = EC1 + EP1
        dwl = W0 - W1
    else:
        Qt = Q0
        EC1, EP1, W1, dwl = EC0, EP0, W0, 0.0

    out = dict(base)
    out.update({
        "EC0": EC0, "EP0": EP0, "W0": W0,
        "EC1": EC1, "EP1": EP1, "W1": W1, "dwl": dwl, "Qt": Qt,
    })
    return out


# ======================================================================
# COMPONENTES DE INTERFAZ REUTILIZABLES
# ======================================================================
def fmt(x, dec=2):
    """Formatea números con separador de miles y 'dec' decimales."""
    try:
        return f"{x:,.{dec}f}".replace(",", "·").replace(".", ",").replace("·", ".")
    except Exception:
        return str(x)


def banda_titulo(titulo, subtitulo):
    st.markdown(
        f"""<div class="titulo-banda"><h1>{titulo}</h1><p>{subtitulo}</p></div>""",
        unsafe_allow_html=True,
    )


def nota(texto, tipo="info"):
    clase = {"info": "nota", "ok": "nota nota-ok",
             "warn": "nota nota-warn", "bad": "nota nota-bad"}.get(tipo, "nota")
    st.markdown(f"""<div class="{clase}">{texto}</div>""", unsafe_allow_html=True)


def grilla_precios(a, b, c, d, extra_top=1.15):
    """Vector de precios para dibujar curvas, de 0 al choke de demanda."""
    p_top = (a / b) * extra_top
    return np.linspace(0, p_top, 200), p_top


# ======================================================================
# SIDEBAR — PARÁMETROS DEL MERCADO
# ======================================================================
with st.sidebar:
    st.markdown("### Parámetros del mercado")
    st.caption("Funciones lineales del enunciado:")
    st.latex(r"Q_d = a - b\,P \qquad Q_o = c + d\,P")

    preset = st.selectbox(
        "Cargar caso del enunciado",
        ["Personalizado",
         "Ej. 1 — Subsidio al transporte",
         "Ej. 2 — Precio máximo a alquileres"],
    )

    # Valores por defecto según preset
    if preset == "Ej. 1 — Subsidio al transporte":
        da, db, dc, dd = 1500.0, 25.0, 0.0, 15.0
    elif preset == "Ej. 2 — Precio máximo a alquileres":
        da, db, dc, dd = 1800.0, 20.0, 0.0, 12.0
    else:
        da, db, dc, dd = 1000.0, 30.0, 0.0, 20.0

    st.markdown("**Demanda**")
    a = st.number_input("a — intercepto demanda", value=da, step=10.0)
    b = st.number_input("b — pendiente demanda", value=db, step=1.0, min_value=0.01)
    st.markdown("**Oferta**")
    c = st.number_input("c — intercepto oferta", value=dc, step=10.0)
    d = st.number_input("d — pendiente oferta", value=dd, step=1.0, min_value=0.01)

    st.markdown("---")
    st.caption("Política a simular en cada pestaña:")
    if preset == "Ej. 1 — Subsidio al transporte":
        s_default = 8.0
    else:
        s_default = 4.0
    if preset == "Ej. 2 — Precio máximo a alquileres":
        ptecho_default = 40.0
    else:
        P0_tmp, _ = equilibrio(a, b, c, d)
        ptecho_default = round(P0_tmp * 0.75, 1)

# Validación mínima
if (b + d) == 0:
    st.error("La suma de pendientes (b + d) no puede ser 0.")
    st.stop()

P0, Q0 = equilibrio(a, b, c, d)
if P0 < 0 or Q0 < 0:
    st.warning("Con estos parámetros el equilibrio da precio o cantidad negativos. "
               "Revisá los valores de a, b, c y d.")

# ======================================================================
# CABECERA
# ======================================================================
banda_titulo(
    "Simulador de Políticas Públicas — Economía Cerrada",
    "TP N.º 2 · Economía para Ingenieros · UNSTA · Prof. R. García",
)
st.write("")

# Métricas de la situación inicial (comunes a todo)
EC0_g = excedente_consumidor(Q0, P0, a, b)
EP0_g = excedente_productor(Q0, P0, c, d)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Precio de equilibrio", f"${fmt(P0)}")
m2.metric("Cantidad de equilibrio", f"{fmt(Q0)} u.")
m3.metric("Excedente consumidor", f"${fmt(EC0_g)}")
m4.metric("Excedente productor", f"${fmt(EP0_g)}")

st.write("")

# ======================================================================
# PESTAÑAS PRINCIPALES
# ======================================================================
tab_eq, tab_sub, tab_pmax, tab_doc = st.tabs(
    ["Equilibrio y excedentes",
     "Ejercicio 1 · Subsidio",
     "Ejercicio 2 · Precio máximo",
     "Guía y fórmulas"]
)

# ----------------------------------------------------------------------
# TAB 0 — EQUILIBRIO Y EXCEDENTES (situación inicial)
# ----------------------------------------------------------------------
with tab_eq:
    st.subheader("Situación inicial del mercado")
    colg, colr = st.columns([2, 1])

    with colg:
        p_arr, p_top = grilla_precios(a, b, c, d)
        qd = np.clip(a - b * p_arr, 0, None)
        qo = np.clip(c + d * p_arr, 0, None)

        fig = go.Figure()
        # Relleno excedente consumidor (triángulo demanda por encima de P0)
        fig.add_trace(go.Scatter(
            x=[0, 0, Q0], y=[P0, a / b, P0],
            fill="toself", fillcolor=COL_EC, line=dict(width=0),
            name="Excedente consumidor", hoverinfo="skip"))
        # Relleno excedente productor (entre P0 y oferta)
        fig.add_trace(go.Scatter(
            x=[0, 0, Q0], y=[P0, max(-c / d, 0), P0],
            fill="toself", fillcolor=COL_EP, line=dict(width=0),
            name="Excedente productor", hoverinfo="skip"))
        # Curvas
        fig.add_trace(go.Scatter(x=qd, y=p_arr, name="Demanda",
                                 line=dict(color=COL_DEM, width=3)))
        fig.add_trace(go.Scatter(x=qo, y=p_arr, name="Oferta",
                                 line=dict(color=COL_OFE, width=3)))
        # Punto de equilibrio
        fig.add_trace(go.Scatter(x=[Q0], y=[P0], mode="markers+text",
                                 text=["E"], textposition="top center",
                                 marker=dict(color=COL_EQ, size=12),
                                 name="Equilibrio"))
        fig.update_layout(
            template="plotly_dark", height=460,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Cantidad (Q)", yaxis_title="Precio (P)",
            xaxis=dict(range=[0, a * 1.05], gridcolor="#1e2a40"),
            yaxis=dict(range=[0, p_top], gridcolor="#1e2a40"),
            legend=dict(orientation="h", y=1.08))
        st.plotly_chart(fig, use_container_width=True)

    with colr:
        st.metric("Bienestar total (W)", f"${fmt(EC0_g + EP0_g)}")
        st.write("")
        nota(
            "El <b>excedente del consumidor</b> (azul) es lo que los compradores "
            "estaban dispuestos a pagar por encima del precio que efectivamente "
            "pagan. El <b>excedente del productor</b> (verde) es lo que reciben "
            "por encima de su costo. La suma es el <b>bienestar total</b>: en un "
            "mercado libre, este valor es el máximo posible, y cualquier "
            "intervención que cambie la cantidad transada lo reduce.",
            "info")

# ----------------------------------------------------------------------
# TAB 1 — EJERCICIO 1: SUBSIDIO
# ----------------------------------------------------------------------
with tab_sub:
    banda = "Subsidio al transporte público" if preset.startswith("Ej. 1") \
            else "Subsidio por unidad al productor"
    st.subheader(banda)

    cpar, cgraf = st.columns([1, 2])
    with cpar:
        s = st.slider("Subsidio por unidad (s)", 0.0,
                      float(max(P0 * 1.5, 20)), float(s_default), step=0.5)
        R = bienestar_subsidio(a, b, c, d, s)

        st.metric("Precio que paga el usuario (Pc)", f"${fmt(R['Pc'])}")
        st.metric("Precio que recibe la empresa (Pv)", f"${fmt(R['Pv'])}")
        st.metric("Cantidad de equilibrio", f"{fmt(R['Q1'])} u.")
        st.metric("Gasto total del Estado", f"${fmt(R['gasto'])}")

    with cgraf:
        p_arr, p_top = grilla_precios(a, b, c, d)
        qd = np.clip(a - b * p_arr, 0, None)
        qo = np.clip(c + d * p_arr, 0, None)
        # Oferta con subsidio: Qo' = c + d(P + s)  -> se ve desplazada a la derecha
        qo_sub = np.clip(c + d * (p_arr + s), 0, None)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=qd, y=p_arr, name="Demanda",
                                 line=dict(color=COL_DEM, width=3)))
        fig.add_trace(go.Scatter(x=qo, y=p_arr, name="Oferta original",
                                 line=dict(color=COL_OFE, width=3)))
        if s > 0:
            fig.add_trace(go.Scatter(x=qo_sub, y=p_arr, name="Oferta con subsidio",
                                     line=dict(color=COL_OFE2, width=3, dash="dash")))
            # Costo fiscal: rectángulo entre Pv y Pc, de 0 a Q1
            fig.add_trace(go.Scatter(
                x=[0, R["Q1"], R["Q1"], 0],
                y=[R["Pc"], R["Pc"], R["Pv"], R["Pv"]],
                fill="toself", fillcolor=COL_FISC, line=dict(width=0),
                name="Costo fiscal", hoverinfo="skip"))
            # Pérdida de eficiencia (triángulo entre Q0 y Q1)
            fig.add_trace(go.Scatter(
                x=[Q0, R["Q1"], R["Q1"]],
                y=[P0, precio_demanda(R["Q1"], a, b), precio_oferta(R["Q1"], c, d)],
                fill="toself", fillcolor=COL_DWL, line=dict(width=0),
                name="Pérdida de eficiencia", hoverinfo="skip"))
            # Puntos nuevos
            fig.add_trace(go.Scatter(x=[R["Q1"]], y=[R["Pc"]], mode="markers",
                                     marker=dict(color=COL_DEM, size=11),
                                     name="Precio comprador"))
            fig.add_trace(go.Scatter(x=[R["Q1"]], y=[R["Pv"]], mode="markers",
                                     marker=dict(color=COL_OFE2, size=11),
                                     name="Precio vendedor"))
        # Equilibrio original
        fig.add_trace(go.Scatter(x=[Q0], y=[P0], mode="markers",
                                 marker=dict(color=COL_EQ, size=12),
                                 name="Equilibrio original"))
        fig.update_layout(
            template="plotly_dark", height=480,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Cantidad (Q)", yaxis_title="Precio (P)",
            xaxis=dict(range=[0, a * 1.05], gridcolor="#1e2a40"),
            yaxis=dict(range=[0, p_top], gridcolor="#1e2a40"),
            legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig, use_container_width=True)

    # ---- Tabla de bienestar antes/después ----
    st.markdown("#### Análisis de bienestar")
    df_b = pd.DataFrame({
        "Concepto": ["Excedente del consumidor", "Excedente del productor",
                     "Gasto del Estado", "Bienestar total (W)"],
        "Sin subsidio": [f"${fmt(R['EC0'])}", f"${fmt(R['EP0'])}",
                         "$0,00", f"${fmt(R['W0'])}"],
        "Con subsidio": [f"${fmt(R['EC1'])}", f"${fmt(R['EP1'])}",
                         f"–${fmt(R['gasto'])}", f"${fmt(R['W1'])}"],
        "Variación": [f"+${fmt(R['EC1']-R['EC0'])}", f"+${fmt(R['EP1']-R['EP0'])}",
                      f"–${fmt(R['gasto'])}", f"–${fmt(R['dwl'])}"],
    })
    st.dataframe(df_b, hide_index=True, use_container_width=True)

    if s > 0:
        nota(
            f"Con un subsidio de <b>${fmt(s)}</b> por unidad, el usuario paga "
            f"<b>${fmt(R['Pc'])}</b> (antes ${fmt(P0)}) y la empresa cobra "
            f"<b>${fmt(R['Pv'])}</b>. Ganan consumidores y productores, pero el "
            f"Estado gasta <b>${fmt(R['gasto'])}</b> financiados por todos los "
            f"contribuyentes. Como ese gasto supera la suma de lo ganado por las "
            f"dos partes, el bienestar social neto cae en "
            f"<b>${fmt(R['dwl'])}</b>: esa es la <b>pérdida irrecuperable de "
            f"eficiencia</b> (área roja), generada porque se transan unidades "
            f"cuyo costo de producción supera lo que el consumidor realmente "
            f"valora.", "warn")

    # ---- Tabla de simulación (barrido) ----
    st.markdown("#### Simulación de escenarios")
    valores_s = [0, 5, 10, 15, 20] if preset.startswith("Ej. 1") else [0, 2, 4, 6, 8, 10]
    filas = []
    for sv in valores_s:
        r = bienestar_subsidio(a, b, c, d, float(sv))
        filas.append({
            "Subsidio (s)": f"${fmt(sv,0)}",
            "Cantidad": f"{fmt(r['Q1'])} u.",
            "Precio usuario": f"${fmt(r['Pc'])}",
            "Gasto público": f"${fmt(r['gasto'])}",
            "Bienestar total": f"${fmt(r['W1'])}",
            "Pérdida eficiencia": f"${fmt(r['dwl'])}",
        })
    st.dataframe(pd.DataFrame(filas), hide_index=True, use_container_width=True)
    nota(
        "A medida que sube el subsidio, la cantidad y el precio al usuario "
        "mejoran, pero el gasto público crece más que proporcionalmente y la "
        "pérdida de eficiencia se agranda. Es el costo de la política: cada peso "
        "de subsidio adicional compra cada vez menos bienestar.", "info")

# ----------------------------------------------------------------------
# TAB 2 — EJERCICIO 2: PRECIO MÁXIMO
# ----------------------------------------------------------------------
with tab_pmax:
    banda = "Precio máximo a los alquileres" if preset.startswith("Ej. 2") \
            else "Precio máximo (techo de precio)"
    st.subheader(banda)

    cpar, cgraf = st.columns([1, 2])
    with cpar:
        ptecho = st.slider("Precio máximo (Pmáx)", 1.0,
                           float(P0 * 1.5), float(ptecho_default), step=1.0)
        R = bienestar_precio_maximo(a, b, c, d, ptecho)

        st.metric("Cantidad demandada", f"{fmt(R['Qd'])} u.")
        st.metric("Cantidad ofrecida", f"{fmt(R['Qo'])} u.")
        if R["vinculante"]:
            st.metric("Escasez", f"{fmt(R['escasez'])} u.", delta="vinculante",
                      delta_color="inverse")
        else:
            st.metric("Escasez", "0,00 u.", delta="no vinculante")

    with cgraf:
        p_arr, p_top = grilla_precios(a, b, c, d)
        qd = np.clip(a - b * p_arr, 0, None)
        qo = np.clip(c + d * p_arr, 0, None)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=qd, y=p_arr, name="Demanda",
                                 line=dict(color=COL_DEM, width=3)))
        fig.add_trace(go.Scatter(x=qo, y=p_arr, name="Oferta",
                                 line=dict(color=COL_OFE, width=3)))
        fig.add_hline(y=ptecho, line_dash="dash", line_color="#fbbf24",
                      annotation_text="Precio máximo",
                      annotation_position="top left")
        fig.add_trace(go.Scatter(x=[Q0], y=[P0], mode="markers",
                                 marker=dict(color=COL_EQ, size=12),
                                 name="Equilibrio libre"))
        if R["vinculante"]:
            # Brecha de escasez al precio techo
            fig.add_trace(go.Scatter(
                x=[R["Qo"], R["Qd"]], y=[ptecho, ptecho],
                mode="markers+lines", name="Escasez",
                line=dict(color=COL_EQ, width=5)))
            # Pérdida de eficiencia (triángulo entre Qo transada y Q0)
            fig.add_trace(go.Scatter(
                x=[R["Qt"], Q0, R["Qt"]],
                y=[precio_demanda(R["Qt"], a, b), P0, precio_oferta(R["Qt"], c, d)],
                fill="toself", fillcolor=COL_DWL, line=dict(width=0),
                name="Pérdida de eficiencia", hoverinfo="skip"))
        fig.update_layout(
            template="plotly_dark", height=480,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Cantidad (Q)", yaxis_title="Precio (P)",
            xaxis=dict(range=[0, a * 1.05], gridcolor="#1e2a40"),
            yaxis=dict(range=[0, p_top], gridcolor="#1e2a40"),
            legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig, use_container_width=True)

    # ---- Tabla de bienestar ----
    st.markdown("#### Análisis de bienestar")
    df_b = pd.DataFrame({
        "Concepto": ["Excedente del consumidor", "Excedente del productor",
                     "Bienestar total (W)"],
        "Sin tope": [f"${fmt(R['EC0'])}", f"${fmt(R['EP0'])}", f"${fmt(R['W0'])}"],
        "Con tope": [f"${fmt(R['EC1'])}", f"${fmt(R['EP1'])}", f"${fmt(R['W1'])}"],
        "Variación": [f"{'+' if R['EC1']>=R['EC0'] else '–'}${fmt(abs(R['EC1']-R['EC0']))}",
                      f"–${fmt(abs(R['EP1']-R['EP0']))}",
                      f"–${fmt(R['dwl'])}"],
    })
    st.dataframe(df_b, hide_index=True, use_container_width=True)

    if R["vinculante"]:
        nota(
            f"El tope de <b>${fmt(ptecho)}</b> está por debajo del equilibrio "
            f"(${fmt(P0)}), así que es <b>vinculante</b>. Al precio regulado los "
            f"inquilinos quieren <b>{fmt(R['Qd'])}</b> unidades pero solo se "
            f"ofrecen <b>{fmt(R['Qo'])}</b>: hay una <b>escasez de "
            f"{fmt(R['escasez'])}</b> unidades. Los que consiguen vivienda pagan "
            f"menos (ganan), pero muchos quedan sin acceso y los propietarios "
            f"retiran unidades del mercado. El bienestar total cae "
            f"<b>${fmt(R['dwl'])}</b>.", "bad")
    else:
        nota(
            f"El tope de ${fmt(ptecho)} está por encima del equilibrio "
            f"(${fmt(P0)}): <b>no es vinculante</b> y el mercado opera como si no "
            f"existiera la regulación.", "ok")

    # ---- Tabla de simulación ----
    st.markdown("#### Simulación de escenarios")
    valores_p = [70, 60, 50, 40, 30] if preset.startswith("Ej. 2") \
        else [round(P0*x, 0) for x in (1.25, 1.0, 0.85, 0.7, 0.55)]
    filas = []
    for pv in valores_p:
        r = resolver_precio_maximo(a, b, c, d, float(pv))
        filas.append({
            "Precio máx.": f"${fmt(pv,0)}",
            "Cant. demandada": f"{fmt(r['Qd'])} u.",
            "Cant. ofrecida": f"{fmt(r['Qo'])} u.",
            "Escasez": f"{fmt(r['escasez'])} u." if r["vinculante"] else "—",
            "¿Vinculante?": "Sí" if r["vinculante"] else "No",
        })
    st.dataframe(pd.DataFrame(filas), hide_index=True, use_container_width=True)
    nota(
        "Cuanto más bajo se fija el precio máximo, mayor es la escasez: la "
        "cantidad demandada sube y la ofrecida baja, ampliando la brecha. Un "
        "tope pensado para ayudar termina reduciendo la vivienda disponible.",
        "info")

# ----------------------------------------------------------------------
# TAB 3 — GUÍA Y FÓRMULAS
# ----------------------------------------------------------------------
with tab_doc:
    st.subheader("Modelo económico y fórmulas")
    st.markdown("**Funciones del mercado**")
    st.latex(r"Q_d = a - bP \qquad Q_o = c + dP")
    st.markdown("**Equilibrio competitivo** (iguala cantidades y despeja P):")
    st.latex(r"P^* = \frac{a - c}{b + d} \qquad Q^* = a - bP^*")

    st.markdown("**Excedentes** (áreas de triángulos/trapecios):")
    st.latex(r"EC = \tfrac{1}{2}\,Q\,(P_{choke}^{dem} - P_{pagado})"
             r"\qquad P_{choke}^{dem} = \tfrac{a}{b}")
    st.latex(r"EP = P_{recibido}\cdot Q - \frac{1}{d}\!\left(\frac{Q^2}{2} - cQ\right)")

    st.markdown("**Subsidio por unidad (s)** — se traslada el precio del vendedor:")
    st.latex(r"P_c = \frac{a - c - d\,s}{b + d}, \quad P_v = P_c + s, "
             r"\quad Q_1 = a - bP_c")
    st.latex(r"\text{Gasto fiscal} = s\cdot Q_1 \qquad "
             r"W = EC + EP - \text{Gasto fiscal}")

    st.markdown("**Precio máximo (Pmáx)** — vinculante si Pmáx < P*:")
    st.latex(r"Q_d = a - bP_{max}, \quad Q_o = c + dP_{max}, "
             r"\quad \text{Escasez} = Q_d - Q_o")
    st.latex(r"Q_{transada} = Q_o \;(\text{lado corto})")

    st.markdown("---")
    st.markdown(
        "**Cómo leer la pérdida de eficiencia (DWL):** es el bienestar que "
        "desaparece porque la cantidad transada se aleja de la de equilibrio. "
        "En el subsidio se transan unidades de más (su costo supera el valor "
        "para el consumidor); en el precio máximo se transan unidades de menos "
        "(quedan intercambios valiosos sin realizar). En ambos casos el "
        "triángulo rojo del gráfico mide esa pérdida.")

    st.caption("App desarrollada para el TP N.º 2 · Economía para Ingenieros · UNSTA")
