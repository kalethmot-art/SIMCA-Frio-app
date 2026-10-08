import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="SIMCA Frío 4.0 | Dashboard Logístico",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS PERSONALIZADO Y DISEÑO PROFESIONAL (MODO CLARO / CORPORATIVO) ---
st.markdown(
    """
    <style>
    /* Estilos generales y tipografía */
    .main {
        background-color: #f8fafc;
        color: #1e293b;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Tarjetas de métricas ejecutivas */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
    }
    
    /* Alertas de temperatura dinámicas */
    .alert-critical {
        background-color: #fee2e2;
        border-left: 5px solid #ef4444;
        padding: 15px;
        border-radius: 6px;
        color: #991b1b;
        font-weight: 600;
        margin-bottom: 15px;
    }
    
    .alert-normal {
        background-color: #dcfce7;
        border-left: 5px solid #22c55e;
        padding: 15px;
        border-radius: 6px;
        color: #166534;
        font-weight: 600;
        margin-bottom: 15px;
    }

    /* Encabezados y títulos */
    h1, h2, h3 {
        color: #0f172a;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- BARRA LATERAL (FILTROS Y CONTROL DE FLOTA) ---
st.sidebar.image(
    "https://img.icons8.com/color/96/snowflake.png", width=70
)  # Ícono representativo
st.sidebar.title("SIMCA Frío 4.0")
st.sidebar.markdown(
    "**Logística 4.0 y Cadena de Frío Inteligente**\n*Negocios Internacionales*"
)
st.sidebar.markdown("---")

st.sidebar.subheader("🎛️ Filtros de Monitoreo")
selected_route = st.sidebar.selectbox(
    "Seleccionar Ruta / Corredor",
    [
        "Bogotá - Medellín",
        "Bogotá - Cali",
        "Medellín - Costa Caribe",
        "Nacional General",
    ],
)
selected_fleet = st.sidebar.selectbox(
    "Tipo de Unidad / Tracto",
    ["Todos", "Tractocamión Furgón Refrigenrado", "Turbo Convectivo"],
)

# Rango óptimo de temperatura configurable
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Parámetros de Control")
temp_min, temp_max = st.sidebar.slider(
    "Rango Óptimo de Temperatura (°C)", -5.0, 15.0, (2.0, 8.0)
)

# --- SIMULACIÓN DE DATOS Y TELEMETRÍA (EJEMPLO DINÁMICO) ---
np.random.seed(42)
days = pd.date_range(start="2026-10-01", periods=24, freq="H")
df_telemetry = pd.DataFrame(
    {
        "Timestamp": days,
        "Temperatura_C": np.random.uniform(1.5, 9.5, size=24),
        "Humedad_Pct": np.random.uniform(60, 85, size=24),
        "Velocidad_KmH": np.random.uniform(40, 90, size=24),
    }
)

# Calcular excursión térmica
excursiones = df_telemetry[
    (df_telemetry["Temperatura_C"] < temp_min)
    | (df_telemetry["Temperatura_C"] > temp_max]
)
pct_estabilidad = (
    (len(df_telemetry) - len(excursiones)) / len(df_telemetry)
) * 100

# --- CONTENIDO PRINCIPAL ---
st.title("❄️ Dashboard Ejecutivo de Cadena de Frío")
st.markdown(
    "Monitoreo en tiempo real de variables críticas, estabilidad de empaques avanzados y cumplimiento de SLAs logísticos."
)

# Panel de Alertas Dinámicas
if len(excursiones) > 0:
    st.markdown(
        f"""
        <div class="alert-critical">
            ⚠️ <b>ALERTA CRÍTICA DE CADENA DE FRÍO:</b> Se han detectado <b>{len(excursiones)} registros</b> fuera del rango óptimo ({temp_min}°C - {temp_max}°C) en la ruta seleccionada. Se requiere verificación del empaque activo.
        </div>
    """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <div class="alert-normal">
            ✅ <b>ESTADO ÓPTIMO:</b> Toda la flota opera dentro de los rangos térmicos establecidos y estables.
        </div>
    """,
        unsafe_allow_html=True,
    )

# --- TARJETAS DE MÉTRICAS EJECUTIVAS (KPIs) ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <h4>Estabilidad Térmica</h4>
            <h2 style="color: {'#22c55e' if pct_estabilidad > 85 else '#ef4444'};">{pct_estabilidad:.1f}%</h2>
            <p style="font-size: 12px; color: #64748b;">Cumplimiento de rango</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

with col2:
    temp_actual = df_telemetry["Temperatura_C"].iloc[-1]
    st.markdown(
        f"""
        <div class="metric-card">
            <h4>Temperatura Actual</h4>
            <h2 style="color: #0284c7;">{temp_actual:.2f} °C</h2>
            <p style="font-size: 12px; color: #64748b;">Sensor de cabina/carga</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

with col3:
    humedad_prom = df_telemetry["Humedad_Pct"].mean()
    st.markdown(
        f"""
        <div class="metric-card">
            <h4>Humedad Relativa</h4>
            <h2 style="color: #0f172a;">{humedad_prom:.1f}%</h2>
            <p style="font-size: 12px; color: #64748b;">Promedio del trayecto</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        """
        <div class="metric-card">
            <h4>Estado del Tracto</h4>
            <h2 style="color: #22c55e;">Activo</h2>
            <p style="font-size: 12px; color: #64748b;">GPS y Telemetría OK</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# --- SECCIÓN DE GRÁFICOS ANALÍTICOS (PLOTLY) ---
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.subheader("📈 Comportamiento Térmico vs Tiempo")
    fig_temp = go.Figure()
    fig_temp.add_trace(
        go.Scatter(
            x=df_telemetry["Timestamp"],
            y=df_telemetry["Temperatura_C"],
            mode="lines+markers",
            name="Temperatura (°C)",
            line=dict(color="#0284c7", width=3),
        )
    )
    # Líneas de umbral
    fig_temp.add_hline(
        y=temp_max,
        line_dash="dash",
        line_color="red",
        annotation_text="Límite Máximo",
    )
    fig_temp.add_hline(
        y=temp_min,
        line_dash="dash",
        line_color="blue",
        annotation_text="Límite Mínimo",
    )
    fig_temp.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        height=350,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_temp, use_container_width=True)

with col_graf2:
    st.subheader("💧 Humedad y Estabilidad del Contenedor")
    fig_hum = go.Figure()
    fig_hum.add_trace(
        go.Bar(
            x=df_telemetry["Timestamp"],
            y=df_telemetry["Humedad_Pct"],
            name="Humedad (%)",
            marker_color="#38bdf8",
        )
    )
    fig_hum.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        height=350,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_hum, use_container_width=True)

# --- PIE DE PÁGINA PROFESIONAL ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; font-size: 13px;'>SIMCA Frío 4.0 — Sistema Inteligente de Monitoreo de Cadena de Frío | Desarrollado para Gestión Logística</div>",
    unsafe_allow_html=True,
)
