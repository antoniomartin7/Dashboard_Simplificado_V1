# app.py — Dashboard Simplificado de Inversión
# Ejecutar con: streamlit run app.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

import statistics

from obtener_datos import obtener_datos

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Simplificado",
    layout="wide",
    page_icon="📊",
)

st.markdown("""
<style>
.main .block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    max-width: 1400px;
}
h1 { font-size: 1.8rem !important; }

/* Tabla resumen mejorada */
.summary-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.88em;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid rgba(128,128,128,0.15);
}
.summary-table th {
    background: linear-gradient(135deg, rgba(30,136,229,0.22), rgba(30,136,229,0.10));
    color: #90caf9;
    padding: 10px 12px;
    text-align: center;
    font-weight: 700;
    font-size: 0.92em;
    letter-spacing: 0.3px;
    border-bottom: 2px solid rgba(30,136,229,0.25);
}
.summary-table td {
    padding: 9px 12px;
    text-align: center;
    border-bottom: 1px solid rgba(128,128,128,0.08);
    font-weight: 500;
}
.summary-table tr:nth-child(even) {
    background: rgba(255,255,255,0.015);
}
.summary-table tr:hover {
    background: rgba(30,136,229,0.06);
}

/* Tarjetas KPI resumen */
.kpi-row {
    display: flex;
    gap: 12px;
    margin-bottom: 18px;
}
.kpi-card {
    flex: 1;
    background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01));
    border: 1px solid rgba(128,128,128,0.18);
    border-radius: 12px;
    padding: 16px 14px;
    text-align: center;
}
.kpi-card-title {
    font-size: 0.72em;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-weight: 600;
    margin-bottom: 6px;
}
.kpi-card-value {
    font-size: 1.6em;
    font-weight: 700;
    margin-bottom: 2px;
}
.kpi-card-sub {
    font-size: 0.73em;
    color: #666;
}

/* Otras tarjetas */
.update-info {
    color: #888;
    font-size: 0.85em;
    margin-top: -10px;
    margin-bottom: 15px;
}
.metric-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(128,128,128,0.2);
    border-radius: 10px;
    padding: 14px 16px;
    text-align: center;
    min-height: 90px;
}
.metric-label {
    font-size: 0.78em;
    color: #999;
    margin-bottom: 4px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.metric-value {
    font-size: 1.55em;
    font-weight: 700;
    margin-bottom: 2px;
}
.company-header {
    border-left: 4px solid #1E88E5;
    padding-left: 12px;
    margin-bottom: 8px;
}
.company-name {
    font-size: 1.3em;
    font-weight: 700;
    margin-bottom: 0;
}
.company-price {
    font-size: 1.1em;
    color: #ccc;
}
.explainer {
    background: rgba(30,136,229,0.07);
    border-left: 3px solid #1E88E5;
    padding: 10px 14px;
    border-radius: 4px;
    font-size: 0.88em;
    color: #bbb;
    margin-bottom: 12px;
}
.section-header {
    font-size: 1.05em;
    font-weight: 700;
    color: #90caf9;
    margin-top: 20px;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(30,136,229,0.2);
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ─────────────────────────────────────────────
COLOR_MAP = {
    "good": "color:#00c853;",
    "neutral": "color:#ffab40;",
    "bad": "color:#ff1744;",
    "na": "color:#666;",
}


def fmt_ratio(v, sufijo="x"):
    if v is None or v == 0:
        return "N/A"
    if v == -1.0:
        return "Neg."
    return f"{v:.1f}{sufijo}"


def fmt_pct(v):
    if v is None or v == 0:
        return "N/A"
    return f"{v * 100:.1f}%"


def fmt_money(v):
    if v is None or v == 0:
        return "N/A"
    if abs(v) >= 1e12:
        return f"${v / 1e12:.1f}T"
    if abs(v) >= 1e9:
        return f"${v / 1e9:.1f}B"
    if abs(v) >= 1e6:
        return f"${v / 1e6:.1f}M"
    return f"${v:,.0f}"


def _color_per(v, lo=15, hi=25):
    if v is None or v == 0:
        return "na"
    if v < 0:
        return "bad"
    if v <= lo:
        return "good"
    if v <= hi:
        return "neutral"
    return "bad"


def _color_deuda(v):
    if v is None:
        return "na"
    if v < 2:
        return "good"
    if v < 4:
        return "neutral"
    return "bad"


def _color_yield(v, bueno=0.04, medio=0.02):
    if v is None or v == 0:
        return "na"
    if v >= bueno:
        return "good"
    if v >= medio:
        return "neutral"
    return "bad"


def _style(cls):
    return COLOR_MAP.get(cls, "")


def crear_gauge(valor, titulo, rango_max=40, umbrales=None):
    if umbrales is None:
        umbrales = [15, 25]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=max(0, valor) if valor and valor > 0 else 0,
        number={'suffix': 'x', 'font': {'size': 22}},
        title={'text': titulo, 'font': {'size': 12}},
        gauge={
            'axis': {'range': [0, rango_max], 'tickwidth': 1,
                     'tickcolor': 'rgba(128,128,128,0.3)'},
            'bar': {'color': '#1E88E5', 'thickness': 0.3},
            'bgcolor': 'rgba(0,0,0,0)',
            'borderwidth': 0,
            'steps': [
                {'range': [0, umbrales[0]], 'color': 'rgba(0,200,83,0.15)'},
                {'range': [umbrales[0], umbrales[1]], 'color': 'rgba(255,145,0,0.15)'},
                {'range': [umbrales[1], rango_max], 'color': 'rgba(213,0,0,0.12)'},
            ],
        },
    ))
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=10),
        height=170,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    return fig


def crear_grafico_precio(history, ticker):
    if history is None or history.empty:
        return None
    df = history[['Close']].copy().reset_index()
    df.columns = ['Fecha', 'Precio']
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Fecha'], y=df['Precio'],
        mode='lines',
        line=dict(color='#1E88E5', width=1.8),
        fill='tozeroy',
        fillcolor='rgba(30,136,229,0.08)',
        hovertemplate='%{x|%d %b %Y}<br>$%{y:.2f}<extra></extra>',
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        height=280,
        xaxis=dict(showgrid=False, zeroline=False, title=None),
        yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)',
                   zeroline=False, title=None, tickprefix='$'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title=dict(text=f"Precio 5 años — {ticker}", font=dict(size=13)),
        hovermode='x unified',
    )
    return fig


# ─────────────────────────────────────────────
# TABLA RESUMEN HTML
# ─────────────────────────────────────────────
def generar_tabla(resultados):
    filas = ""
    for r in resultados:
        t = r['ticker']
        d = r['datos']
        nombre = d.get('nombre', t)
        is_reit = d.get('is_reit', False)

        precio = d.get('precio', 0)
        precio_str = f"${precio:.2f}" if precio else "N/A"

        # Columna PER NTM (siempre PER NTM)
        per_ntm = d.get('per_ntm', 0)
        per_ntm_str = fmt_ratio(per_ntm)
        s_ntm = _style(_color_per(per_ntm))

        # Columna PER LTM / P/FFO (para REITs muestra P/FFO)
        if is_reit:
            per_ltm_v = d.get('p_ffo', 0)
            per_ltm_str = fmt_ratio(per_ltm_v)
            s_ltm = _style(_color_per(per_ltm_v, 12, 18))
            lbl_ltm = ' P/FFO'
        else:
            per_ltm_v = d.get('per_ltm', 0)
            per_ltm_str = fmt_ratio(per_ltm_v)
            s_ltm = _style(_color_per(per_ltm_v))
            lbl_ltm = ''

        p_fcf = d.get('p_fcf', 0)
        p_fcf_str = fmt_ratio(p_fcf)
        s_fcf = _style(_color_per(p_fcf, 12, 20))

        deuda = d.get('deuda_ebitda')
        deuda_str = fmt_ratio(deuda)
        s_deuda = _style(_color_deuda(deuda))

        div_y = d.get('div_yield', 0)
        div_str = fmt_pct(div_y)
        s_div = _style(_color_yield(div_y, 0.03, 0.015))

        bb = d.get('buyback_yield', 0)
        bb_str = fmt_pct(bb)
        s_bb = _style(_color_yield(bb, 0.02, 0.005))

        ty = d.get('total_yield', 0)
        ty_str = fmt_pct(ty)
        s_ty = _style(_color_yield(ty, 0.04, 0.02))

        reit_tag = ' <span style="color:#AB47BC;font-size:0.7em;">[REIT]</span>' if is_reit else ''

        filas += (
            f'<tr>'
            f'<td style="text-align:left;font-weight:600;">{t}{reit_tag}</td>'
            f'<td style="text-align:left;color:#aaa;font-size:0.85em;">{nombre}</td>'
            f'<td>{precio_str}</td>'
            f'<td style="{s_ntm}">{per_ntm_str}</td>'
            f'<td style="{s_ltm}">{per_ltm_str}{lbl_ltm}</td>'
            f'<td style="{s_fcf}">{p_fcf_str}</td>'
            f'<td style="{s_deuda}">{deuda_str}</td>'
            f'<td style="{s_div}">{div_str}</td>'
            f'<td style="{s_bb}">{bb_str}</td>'
            f'<td style="{s_ty}">{ty_str}</td>'
            f'</tr>'
        )

    html = (
        '<table class="summary-table">'
        '<thead><tr>'
        '<th style="text-align:left;">Ticker</th>'
        '<th style="text-align:left;">Empresa</th>'
        '<th>Precio</th>'
        '<th>PER NTM</th>'
        '<th>PER LTM / P/FFO</th>'
        '<th>P/FCF</th>'
        '<th>Deuda/EBITDA</th>'
        '<th>Div Yield</th>'
        '<th>Buyback Yield</th>'
        '<th>Total Yield</th>'
        '</tr></thead>'
        f'<tbody>{filas}</tbody>'
        '</table>'
    )
    return html


# ─────────────────────────────────────────────
# APLICACIÓN PRINCIPAL
# ─────────────────────────────────────────────
st.title("📊 Dashboard Simplificado de Inversión")

st.markdown(
    '<div class="explainer">'
    '<b>¿Qué es esto?</b> Este dashboard analiza tu cartera de inversión usando '
    'datos en tiempo real de Yahoo Finance. Calcula los ratios fundamentales clave '
    'para evaluar si una acción está cara o barata, si la empresa tiene mucha deuda '
    'y cuánto devuelve al accionista en dividendos y recompras de acciones.'
    '</div>',
    unsafe_allow_html=True
)

# --- CARGAR EXCEL ---
ruta_excel = os.path.join(os.path.dirname(__file__), "Referencias.xlsx")
try:
    df_refs = pd.read_excel(ruta_excel)
    if 'Nombre' in df_refs.columns:
        mapa_nombres = dict(zip(
            df_refs['Ticker'],
            df_refs['Ticker'] + " (" + df_refs['Nombre'].astype(str) + ")"
        ))
    else:
        mapa_nombres = {t: t for t in df_refs['Ticker']}
    if 'Es_REIT' in df_refs.columns:
        set_reits = set(df_refs[df_refs['Es_REIT'] == True]['Ticker'].tolist())
    else:
        set_reits = set()

    # Separar por lista
    if 'Lista' in df_refs.columns:
        tickers_cartera = df_refs[df_refs['Lista'] == 'Cartera']['Ticker'].tolist()
        tickers_seguimiento = df_refs[df_refs['Lista'] == 'Seguimiento']['Ticker'].tolist()
    else:
        tickers_cartera = df_refs['Ticker'].tolist()
        tickers_seguimiento = []

except FileNotFoundError:
    st.error("⚠️ No se encuentra 'Referencias.xlsx'.")
    st.stop()
except Exception as e:
    st.error(f"Error leyendo Referencias.xlsx: {e}")
    st.stop()

# --- SIDEBAR ---
st.sidebar.header("⚙️ Configuración")

# — Mi Cartera —
st.sidebar.subheader("💼 Empresas de Mi Cartera")

if "cartera_sel" not in st.session_state:
    st.session_state["cartera_sel"] = tickers_cartera.copy()


def sel_todas_cartera():
    st.session_state["cartera_sel"] = tickers_cartera.copy()


def sel_ninguna_cartera():
    st.session_state["cartera_sel"] = []


c1, c2 = st.sidebar.columns(2)
c1.button("✅ Todas", on_click=sel_todas_cartera, use_container_width=True, key="btn_all_cartera")
c2.button("❌ Ninguna", on_click=sel_ninguna_cartera, use_container_width=True, key="btn_none_cartera")

sel_cartera = st.sidebar.multiselect(
    "Cartera:", options=tickers_cartera,
    format_func=lambda x: mapa_nombres.get(x, x),
    key="cartera_sel",
)

# — Seguimiento —
if tickers_seguimiento:
    st.sidebar.subheader("👁️ Empresas en Seguimiento")

    if "seguimiento_sel" not in st.session_state:
        st.session_state["seguimiento_sel"] = []

    def sel_todas_seg():
        st.session_state["seguimiento_sel"] = tickers_seguimiento.copy()

    def sel_ninguna_seg():
        st.session_state["seguimiento_sel"] = []

    c3, c4 = st.sidebar.columns(2)
    c3.button("✅ Todas", on_click=sel_todas_seg, use_container_width=True, key="btn_all_seg")
    c4.button("❌ Ninguna", on_click=sel_ninguna_seg, use_container_width=True, key="btn_none_seg")

    sel_seguimiento = st.sidebar.multiselect(
        "Seguimiento:", options=tickers_seguimiento,
        format_func=lambda x: mapa_nombres.get(x, x),
        key="seguimiento_sel",
    )
else:
    sel_seguimiento = []

# Combinar selección
seleccion = sel_cartera + sel_seguimiento

st.sidebar.divider()
st.sidebar.caption(f"📌 {len(sel_cartera)} de cartera + {len(sel_seguimiento)} en seguimiento seleccionadas")

# Guía rápida de ratios en el sidebar
with st.sidebar.expander("📖 ¿Qué significa cada ratio?", expanded=False):
    st.markdown("""
**PER (Price/Earnings Ratio)**
Cuántos años de beneficios estás pagando por la acción.
- **LTM**: Últimos 12 meses (datos reales)
- **NTM**: Próximos 12 meses (estimaciones de analistas)
- < 15x → Barato | 15-25x → Normal | > 25x → Caro

**P/FCF (Price/Free Cash Flow)**
Cuántos años de flujo de caja libre estás pagando. El FCF es el dinero real que genera la empresa después de invertir.
- < 12x → Barato | 12-20x → Normal | > 20x → Caro

**Deuda Neta / EBITDA**
Cuántos años tardaría la empresa en pagar toda su deuda con sus beneficios operativos.
- < 2x → Baja deuda | 2-4x → Moderada | > 4x → Alta deuda

**Dividend Yield**
% del precio que recibes cada año en dividendos.

**Buyback Yield**
% de acciones que la empresa recompra cada año (reduce acciones en circulación, lo que aumenta tu participación).

**Total Yield = Div Yield + Buyback Yield**
Todo lo que la empresa te devuelve como accionista.
- > 4% → Muy bueno | 2-4% → Aceptable | < 2% → Bajo

**P/FFO (solo REITs)**
Las inmobiliarias (REITs) usan FFO en vez de beneficio neto porque incluyen mucha depreciación contable que no es gasto real.
""")

# --- EJECUCIÓN ---
if st.button("🚀 Analizar Cartera", type="primary", use_container_width=True):

    if not seleccion:
        st.warning("Selecciona al menos una empresa.")
        st.stop()

    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
    st.markdown(f'<div class="update-info">📅 Última actualización: {ahora}</div>',
                unsafe_allow_html=True)

    barra = st.progress(0, text="Descargando datos...")
    resultados = []
    errores = []

    for i, ticker in enumerate(seleccion):
        barra.progress(
            (i + 1) / len(seleccion),
            text=f"Analizando {ticker} ({i + 1}/{len(seleccion)})..."
        )
        is_reit = ticker in set_reits
        datos = obtener_datos(ticker, is_reit=is_reit)
        if datos:
            resultados.append({'ticker': ticker, 'datos': datos})
        else:
            errores.append(ticker)

    barra.empty()

    if errores:
        st.warning(f"⚠️ Sin datos: {', '.join(errores)}")

    if not resultados:
        st.error("No se obtuvo información de ninguna empresa.")
        st.stop()

    # ═══════════════════════════════════════
    # TABS
    # ═══════════════════════════════════════
    tab_resumen, tab_detalle = st.tabs(
        ["📊 Visión General", "🔍 Detalle por Empresa"]
    )

    # ─── TAB 1: RESUMEN ───
    with tab_resumen:

        # ── KPI CARDS: Resumen rápido de la cartera ──
        per_ltm_vals = [r['datos'].get('per_ltm', 0) for r in resultados
                        if r['datos'].get('per_ltm', 0) and r['datos']['per_ltm'] > 0]
        per_ntm_vals = [r['datos'].get('per_ntm', 0) for r in resultados
                        if r['datos'].get('per_ntm', 0) and r['datos']['per_ntm'] > 0]
        pfcf_vals = [r['datos'].get('p_fcf', 0) for r in resultados
                     if r['datos'].get('p_fcf', 0) and r['datos']['p_fcf'] > 0]
        ty_vals_kpi = [r['datos'].get('total_yield', 0) for r in resultados
                       if r['datos'].get('total_yield', 0)]
        deuda_vals_kpi = [r['datos'].get('deuda_ebitda') for r in resultados
                          if r['datos'].get('deuda_ebitda') is not None]

        med_per_ltm = statistics.median(per_ltm_vals) if per_ltm_vals else 0
        med_per_ntm = statistics.median(per_ntm_vals) if per_ntm_vals else 0
        med_pfcf = statistics.median(pfcf_vals) if pfcf_vals else 0
        avg_ty = sum(ty_vals_kpi) / len(ty_vals_kpi) if ty_vals_kpi else 0
        med_deuda = statistics.median(deuda_vals_kpi) if deuda_vals_kpi else 0

        st.markdown(
            '<div class="kpi-row">'
            '<div class="kpi-card">'
            '<div class="kpi-card-title">PER NTM Mediana</div>'
            f'<div class="kpi-card-value" style="{_style(_color_per(med_per_ntm))}">{med_per_ntm:.1f}x</div>'
            f'<div class="kpi-card-sub">{len(per_ntm_vals)} empresas con datos</div>'
            '</div>'
            '<div class="kpi-card">'
            '<div class="kpi-card-title">PER LTM Mediana</div>'
            f'<div class="kpi-card-value" style="{_style(_color_per(med_per_ltm))}">{med_per_ltm:.1f}x</div>'
            f'<div class="kpi-card-sub">{len(per_ltm_vals)} empresas con datos</div>'
            '</div>'
            '<div class="kpi-card">'
            '<div class="kpi-card-title">P/FCF Mediana</div>'
            f'<div class="kpi-card-value" style="{_style(_color_per(med_pfcf, 12, 20))}">{med_pfcf:.1f}x</div>'
            f'<div class="kpi-card-sub">{len(pfcf_vals)} empresas con datos</div>'
            '</div>'
            '<div class="kpi-card">'
            '<div class="kpi-card-title">Total Yield Medio</div>'
            f'<div class="kpi-card-value" style="{_style(_color_yield(avg_ty, 0.04, 0.02))}">{avg_ty*100:.1f}%</div>'
            f'<div class="kpi-card-sub">Dividendos + Recompras</div>'
            '</div>'
            '<div class="kpi-card">'
            '<div class="kpi-card-title">Deuda/EBITDA Mediana</div>'
            f'<div class="kpi-card-value" style="{_style(_color_deuda(med_deuda))}">{med_deuda:.1f}x</div>'
            f'<div class="kpi-card-sub">{len(deuda_vals_kpi)} empresas con datos</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True
        )

        # ── Tabla resumen ──
        st.markdown('<div class="section-header">📋 Detalle por Empresa</div>',
                    unsafe_allow_html=True)
        st.caption(
            'Verde = favorable · Naranja = neutral · Rojo = desfavorable · '
            'Todos los ratios calculados con el precio actual.'
        )

        html_tabla = generar_tabla(resultados)
        st.markdown(html_tabla, unsafe_allow_html=True)

        st.markdown("")

        # ── Gráficos comparativos ──
        st.markdown('<div class="section-header">📊 Comparativa Visual</div>',
                    unsafe_allow_html=True)

        tickers_list = [r['ticker'] for r in resultados]

        # Gráfico 1: Valoración — Bullet/horizontal para mejor legibilidad con muchos tickers
        CAP_VAL = 50
        per_ntm_real = [max(0, r['datos'].get('per_ntm', 0) or 0) for r in resultados]
        per_ltm_real = [max(0, (r['datos'].get('p_ffo', 0) if r['datos'].get('is_reit') else r['datos'].get('per_ltm', 0)) or 0) for r in resultados]
        p_fcf_real = [max(0, r['datos'].get('p_fcf', 0) or 0) for r in resultados]

        per_ntm = [min(v, CAP_VAL) for v in per_ntm_real]
        per_ltm = [min(v, CAP_VAL) for v in per_ltm_real]
        p_fcf = [min(v, CAP_VAL) for v in p_fcf_real]

        fig_val = go.Figure()
        fig_val.add_trace(go.Bar(
            name='PER NTM', y=tickers_list, x=per_ntm,
            orientation='h', marker_color='#42A5F5',
            marker_line=dict(width=0),
            customdata=per_ntm_real,
            hovertemplate='%{y}: <b>%{customdata:.2f}x</b><extra>PER NTM</extra>',
            text=[f' {v:.1f}x' if v > CAP_VAL else '' for v in per_ntm_real],
            textposition='inside',
            insidetextanchor='end',
            textfont=dict(size=9, color='white'),
        ))
        fig_val.add_trace(go.Bar(
            name='PER LTM / P/FFO', y=tickers_list, x=per_ltm,
            orientation='h', marker_color='#66BB6A',
            marker_line=dict(width=0),
            customdata=per_ltm_real,
            hovertemplate='%{y}: <b>%{customdata:.2f}x</b><extra>PER LTM / P/FFO</extra>',
            text=[f' {v:.1f}x' if v > CAP_VAL else '' for v in per_ltm_real],
            textposition='inside',
            insidetextanchor='end',
            textfont=dict(size=9, color='white'),
        ))
        fig_val.add_trace(go.Bar(
            name='P/FCF', y=tickers_list, x=p_fcf,
            orientation='h', marker_color='#FFA726',
            marker_line=dict(width=0),
            customdata=p_fcf_real,
            hovertemplate='%{y}: <b>%{customdata:.2f}x</b><extra>P/FCF</extra>',
            text=[f' {v:.1f}x' if v > CAP_VAL else '' for v in p_fcf_real],
            textposition='inside',
            insidetextanchor='end',
            textfont=dict(size=9, color='white'),
        ))
        fig_val.add_vline(x=15, line_dash="dot", line_color="rgba(0,200,83,0.4)",
                          annotation_text="15x", annotation_position="top")
        fig_val.add_vline(x=25, line_dash="dot", line_color="rgba(255,23,68,0.4)",
                          annotation_text="25x", annotation_position="top")
        fig_val.update_layout(
            barmode='group',
            title=dict(text='Múltiplos de Valoración', font=dict(size=15)),
            height=max(350, len(tickers_list) * 38),
            margin=dict(l=70, r=30, t=50, b=30),
            legend=dict(orientation='h', y=1.08, x=0.5, xanchor='center'),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(autorange='reversed'),
            xaxis=dict(title='Veces (x)', range=[0, CAP_VAL], dtick=5,
                       showgrid=True, gridcolor='rgba(128,128,128,0.15)',
                       gridwidth=0.5, griddash='dot'),
            bargap=0.25,
            bargroupgap=0.08,
            hoverlabel=dict(font=dict(size=16)),
        )
        st.plotly_chart(fig_val, use_container_width=True)

        # Gráfico 2 y 3 lado a lado
        col1, col2 = st.columns(2)

        # Gráfico 2: Total Yield descompuesto (stacked horizontal)
        with col1:
            div_vals = [r['datos'].get('div_yield', 0) * 100 for r in resultados]
            bb_vals = [max(0, r['datos'].get('buyback_yield', 0) * 100) for r in resultados]

            fig_yield = go.Figure()
            fig_yield.add_trace(go.Bar(
                name='Dividendo', y=tickers_list, x=div_vals,
                orientation='h',
                marker_color='#AB47BC',
                marker_line=dict(width=0),
                hovertemplate='%{y}: <b>%{x:.2f}%</b><extra>Dividendo</extra>',
            ))
            fig_yield.add_trace(go.Bar(
                name='Recompras', y=tickers_list, x=bb_vals,
                orientation='h',
                marker_color='#26A69A',
                marker_line=dict(width=0),
                hovertemplate='%{y}: <b>%{x:.2f}%</b><extra>Recompras</extra>',
            ))
            fig_yield.add_vline(x=4, line_dash="dot", line_color="rgba(0,200,83,0.5)",
                                annotation_text="4%", annotation_position="top")
            max_yield = max((d + b for d, b in zip(div_vals, bb_vals)), default=10)
            yield_dtick = 2 if max_yield <= 20 else 5
            fig_yield.update_layout(
                barmode='stack',
                title=dict(text='Retorno al Accionista (Total Yield)', font=dict(size=14)),
                height=max(320, len(tickers_list) * 32),
                margin=dict(l=60, r=20, t=50, b=30),
                legend=dict(orientation='h', y=1.08, x=0.5, xanchor='center'),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(autorange='reversed'),
                xaxis=dict(title='%', dtick=yield_dtick,
                           showgrid=True, gridcolor='rgba(128,128,128,0.15)',
                           gridwidth=0.5, griddash='dot'),
                bargap=0.2,
                hoverlabel=dict(font=dict(size=16)),
            )
            st.plotly_chart(fig_yield, use_container_width=True)

        # Gráfico 3: Deuda — barras horizontales con colores por zona
        with col2:
            deuda_vals = []
            for r in resultados:
                v = r['datos'].get('deuda_ebitda')
                deuda_vals.append(v if v is not None else 0)

            colors = ['#00c853' if v < 2 else '#ffab40' if v < 4 else '#ff1744'
                      for v in deuda_vals]

            fig_deuda = go.Figure()
            fig_deuda.add_trace(go.Bar(
                name='Deuda Neta / EBITDA',
                y=tickers_list, x=deuda_vals,
                orientation='h',
                marker_color=colors,
                marker_line=dict(width=0),
                hovertemplate='%{y}: <b>%{x:.2f}x</b><extra>DN/EBITDA</extra>',
            ))
            fig_deuda.add_vline(x=2, line_dash="dash", line_color="#00c853",
                                annotation_text="Baja", annotation_position="top")
            fig_deuda.add_vline(x=4, line_dash="dash", line_color="#ff1744",
                                annotation_text="Alta", annotation_position="top")
            max_deuda = max(deuda_vals) if deuda_vals else 10
            deuda_dtick = 2 if max_deuda <= 20 else 5
            fig_deuda.update_layout(
                title=dict(text='Nivel de Deuda (DN / EBITDA)', font=dict(size=14)),
                height=max(320, len(tickers_list) * 32),
                margin=dict(l=60, r=20, t=50, b=30),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(autorange='reversed'),
                xaxis=dict(title='Veces (x)', dtick=deuda_dtick,
                           showgrid=True, gridcolor='rgba(128,128,128,0.15)',
                           gridwidth=0.5, griddash='dot'),
                showlegend=False,
                bargap=0.2,
                hoverlabel=dict(font=dict(size=16)),
            )
            st.plotly_chart(fig_deuda, use_container_width=True)

    # ─── TAB 2: DETALLE ───
    with tab_detalle:
        for r in resultados:
            ticker = r['ticker']
            d = r['datos']
            nombre = d.get('nombre', ticker)
            is_reit = d.get('is_reit', False)

            st.markdown("---")

            st.markdown(
                f'<div class="company-header">'
                f'<div class="company-name">{ticker} — {nombre}'
                f'{" <span style=&quot;color:#AB47BC;&quot;>[REIT]</span>" if is_reit else ""}'
                f'</div>'
                f'<div class="company-price">'
                f'Precio: ${d.get("precio", 0):.2f} &nbsp;|&nbsp; '
                f'Market Cap: {fmt_money(d.get("market_cap", 0))}'
                f'</div></div>',
                unsafe_allow_html=True
            )

            with st.expander(f"Ver detalle de {ticker}", expanded=True):

                # Gauges
                if is_reit:
                    st.markdown("##### Valoración REIT")
                    g1, g2, g3 = st.columns(3)
                    with g1:
                        v = d.get('p_ffo', 0) or 0
                        st.plotly_chart(crear_gauge(v, "P/FFO", 40, [12, 18]),
                                        use_container_width=True, key=f"g1_{ticker}")
                        st.caption(f"MCap / FFO TTM ({fmt_money(d.get('ffo_ttm', 0))})")
                    with g2:
                        v = d.get('per_ltm', 0) or 0
                        st.plotly_chart(crear_gauge(v, "PER LTM", 50, [15, 25]),
                                        use_container_width=True, key=f"g2_{ticker}")
                    with g3:
                        v = d.get('p_fcf', 0) or 0
                        st.plotly_chart(crear_gauge(v, "P/FCF", 50, [12, 22]),
                                        use_container_width=True, key=f"g3_{ticker}")
                else:
                    st.markdown("##### Valoración")
                    g1, g2, g3 = st.columns(3)
                    with g1:
                        v = d.get('per_ntm', 0) or 0
                        st.plotly_chart(crear_gauge(v, "PER NTM", 50, [15, 25]),
                                        use_container_width=True, key=f"g1_{ticker}")
                    with g2:
                        v = d.get('per_ltm', 0) or 0
                        st.plotly_chart(crear_gauge(v, "PER LTM", 50, [15, 25]),
                                        use_container_width=True, key=f"g2_{ticker}")
                    with g3:
                        v = d.get('p_fcf', 0) or 0
                        st.plotly_chart(crear_gauge(v, "P/FCF", 50, [12, 22]),
                                        use_container_width=True, key=f"g3_{ticker}")

                # Tarjetas: Deuda + Yields
                st.markdown("##### Deuda y Retorno al Accionista")
                c1, c2, c3, c4 = st.columns(4)

                deuda_v = d.get('deuda_ebitda')
                deuda_color = _color_deuda(deuda_v)
                with c1:
                    st.markdown(
                        '<div class="metric-card">'
                        '<div class="metric-label">Deuda / EBITDA</div>'
                        f'<div class="metric-value" style="{_style(deuda_color)}">'
                        f'{fmt_ratio(deuda_v)}</div>'
                        f'<div style="font-size:0.75em;color:#888;">'
                        f'Deuda: {fmt_money(d.get("total_debt", 0))} | '
                        f'Caja: {fmt_money(d.get("total_cash", 0))}</div>'
                        '</div>',
                        unsafe_allow_html=True
                    )

                div_y = d.get('div_yield', 0)
                with c2:
                    st.markdown(
                        '<div class="metric-card">'
                        '<div class="metric-label">Dividend Yield</div>'
                        f'<div class="metric-value" style="{_style(_color_yield(div_y, 0.03, 0.015))}">'
                        f'{fmt_pct(div_y)}</div></div>',
                        unsafe_allow_html=True
                    )

                bb = d.get('buyback_yield', 0)
                with c3:
                    st.markdown(
                        '<div class="metric-card">'
                        '<div class="metric-label">Buyback Yield</div>'
                        f'<div class="metric-value" style="{_style(_color_yield(bb, 0.02, 0.005))}">'
                        f'{fmt_pct(bb)}</div></div>',
                        unsafe_allow_html=True
                    )

                ty = d.get('total_yield', 0)
                with c4:
                    st.markdown(
                        '<div class="metric-card">'
                        '<div class="metric-label">Total Yield</div>'
                        f'<div class="metric-value" style="{_style(_color_yield(ty, 0.04, 0.02))}">'
                        f'{fmt_pct(ty)}</div></div>',
                        unsafe_allow_html=True
                    )

                # Gráfico de precio
                fig_precio = crear_grafico_precio(d.get('history'), ticker)
                if fig_precio:
                    st.plotly_chart(fig_precio, use_container_width=True,
                                    key=f"price_{ticker}")
