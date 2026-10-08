import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st


# --- FUNCIÓN AUXILIAR DE LIMPIEZA HTML ---
def html(code: str):
  cleaned = "\n".join([line.strip() for line in code.split("\n")])
  st.markdown(cleaned, unsafe_allow_html=True)


# 1. Configuración de la página
st.set_page_config(
    page_title="SIMCA Frío 4.0 - Simulador & Rastreo GPS",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Estilos CSS Personalizados
html("""
<style>
.stApp {
    background-color: #F8FAFC !important;
    color: #1E293B !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* --- ESTILO DE BOTONES GENERALES --- */
div.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    transition: all 0.2s ease !important;
}

/* Botón Primario (Acciones / Pestaña Activa) */
div.stButton > button[kind="primary"] {
    background-color: #0284C7 !important;
    color: #FFFFFF !important;
    border: 1px solid #0284C7 !important;
    box-shadow: 0 4px 6px -1px rgba(2, 132, 199, 0.2);
}
div.stButton > button[kind="primary"]:hover {
    background-color: #0369A1 !important;
    border-color: #0369A1 !important;
}

/* Botón Secundario (Pestañas Inactivas / Descartar) */
div.stButton > button[kind="secondary"] {
    background-color: #FFFFFF !important;
    color: #334155 !important;
    border: 1px solid #CBD5E1 !important;
}
div.stButton > button[kind="secondary"]:hover {
    background-color: #F1F5F9 !important;
    color: #0F172A !important;
    border-color: #94A3B8 !important;
}

/* Contenedores tipo Tarjeta */
.dashboard-card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* Badges */
.badge-normal {
    background-color: #ECFDF5;
    color: #059669;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid #A7F3D0;
}
.badge-warning {
    background-color: #FFFBEB;
    color: #D97706;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid #FDE68A;
}
.badge-danger {
    background-color: #FEF2F2;
    color: #DC2626;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid #FCA5A5;
}
.badge-cyan {
    background-color: #F0F9FF;
    color: #0284C7;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid #BAE6FD;
}
.badge-gray {
    background-color: #F1F5F9;
    color: #64748B;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    border: 1px solid #E2E8F0;
}

/* Títulos y Subtítulos */
.card-title {
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748B;
    font-weight: 700;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}
.main-metric {
    font-size: 2.5rem;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.1;
}
.sub-detail {
    font-size: 0.8rem;
    color: #64748B;
    margin-top: 6px;
}

/* Cajas de impacto */
.financial-box {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(6, 182, 212, 0.08) 100%);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 10px;
    padding: 14px;
    margin-top: 15px;
}
.financial-title {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #059669;
    font-weight: 700;
}
.financial-value {
    font-size: 1.8rem;
    font-weight: 800;
    color: #059669;
}

/* Timeline */
.timeline-item {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    font-size: 0.83rem;
    border-bottom: 1px solid #E2E8F0;
}
.timeline-item:last-child {
    border-bottom: none;
}
</style>
""")

# --- MANEJO DE ESTADO GLOBAL ---
if "action_applied" not in st.session_state:
  st.session_state.action_applied = False

if "active_tab" not in st.session_state:
  st.session_state.active_tab = "operativo"

# ---------------------------------------------------------
# BARRA LATERAL (SIDEBAR): SIMULADOR DE RIESGO
# ---------------------------------------------------------
with st.sidebar:
  st.title("🧪 SIMULADOR DE RIESGO")
  st.caption("Herramienta de simulación de contingencias en frío.")

  st.markdown("---")

  # 1. Seleccionar Despacho
  shipment_id = st.selectbox(
      "🚚 Seleccionar Despacho / Ruta:",
      [
          "FLR-2291 (Bogotá → Cartagena)",
          "FLR-3105 (Medellín → Barranquilla)",
          "FLR-1048 (Cali → Buenaventura)",
      ],
      index=0,
  )

  # Configuración según ruta elegida
  if "FLR-2291" in shipment_id:
    total_km = 1058
    driver_name = "C. Ramírez"
    truck_plate = "SXK-482"
    truck_model = "Tractor 3S3 (#C-114)"
    base_temp_init = 1.5
    lats = [4.7110, 5.4627, 7.0653, 10.9685, 10.3997]
    lons = [-74.0721, -74.6558, -73.8547, -74.7813, -75.5144]
    cities = [
        "Bogotá",
        "Puerto Salgar",
        "Barrancabermeja",
        "Barranquilla",
        "Cartagena",
    ]

  elif "FLR-3105" in shipment_id:
    total_km = 705
    driver_name = "A. Mendoza"
    truck_plate = "WNK-912"
    truck_model = "Tractor Volvo FH (#V-882)"
    base_temp_init = 2.1
    lats = [6.2442, 7.9856, 8.7480, 10.9685]
    lons = [-75.5812, -75.1978, -75.8814, -74.7813]
    cities = ["Medellín", "Caucasia", "Montería", "Barranquilla"]

  else:
    total_km = 520
    driver_name = "J. Delgado"
    truck_plate = "TLM-304"
    truck_model = "Tractor Kenworth T680 (#K-009)"
    base_temp_init = 2.8
    lats = [3.4516, 3.6582, 3.7667, 3.8801]
    lons = [-76.5320, -76.6881, -76.6833, -77.0312]
    cities = ["Cali", "Dagua", "Loboguerrero", "Buenaventura"]

  st.markdown("---")
  st.subheader("⚡ Presets Rápida de Escenarios")
  p_col1, p_col2 = st.columns(2)

  with p_col1:
    if st.button("☀️ Verano Extremo"):
      st.session_state.preset_ext_temp = 38
      st.session_state.preset_traffic = "Crítico"
      st.session_state.preset_fail = False
  with p_col2:
    if st.button("⚠️ Falla Reefer"):
      st.session_state.preset_ext_temp = 32
      st.session_state.preset_fail = True

  default_temp = st.session_state.get("preset_ext_temp", 28)
  default_traffic_idx = (
      3 if st.session_state.get("preset_traffic") == "Crítico" else 2
  )
  default_fail = st.session_state.get("preset_fail", False)

  st.markdown("---")
  st.subheader("📍 Simulación de Avance y Posición")
  progress_pct = st.slider(
      "Progreso del viaje (%):", 0, 100, 65, step=5, key="prog_slider"
  )
  current_km = int(total_km * (progress_pct / 100))

  # Interpolación de coordenadas GPS para posición del camión
  interp_idx = (len(lats) - 1) * (progress_pct / 100.0)
  idx_low = int(np.floor(interp_idx))
  idx_high = min(int(np.ceil(interp_idx)), len(lats) - 1)
  fraction = interp_idx - idx_low

  truck_lat = lats[idx_low] + (lats[idx_high] - lats[idx_low]) * fraction
  truck_lon = lons[idx_low] + (lons[idx_high] - lons[idx_low]) * fraction

  st.markdown("---")
  st.subheader("🛠️ Inyección de Incidentes / Variable")
  reefer_fail = st.toggle("🚨 Falla en Compresor Reefer", value=default_fail)
  door_open = st.toggle("🚪 Puertas Abiertas en Inspección (15 min)")

  ext_temp = st.slider(
      "Temperatura Exterior (°C):", 15, 45, default_temp, key="temp_slider"
  )
  traffic_level = st.select_slider(
      "Tráfico en Ruta:",
      options=["Bajo", "Moderado", "Alto", "Crítico"],
      value=["Bajo", "Moderado", "Alto", "Crítico"][default_traffic_idx],
  )

  traffic_multiplier = {
      "Bajo": 0.5,
      "Moderado": 1.0,
      "Alto": 1.5,
      "Crítico": 2.2,
  }[traffic_level]
  fail_penalty = 40 if reefer_fail else 0
  door_penalty = 15 if door_open else 0

  calc_risk = int(
      min(
          98,
          max(
              10,
              (ext_temp * 1.3)
              + (traffic_multiplier * 15)
              + fail_penalty
              + door_penalty
              - (25 if st.session_state.action_applied else 0),
          ),
      )
  )

  base_temp = base_temp_init + (1.8 if reefer_fail else (0.6 if door_open else 0))

  st.markdown("---")
  if st.button("🔄 Restablecer Simulador", use_container_width=True):
    st.session_state.action_applied = False
    st.session_state.preset_ext_temp = 28
    st.session_state.preset_fail = False
    st.rerun()

# ---------------------------------------------------------
# CABECERA PRINCIPAL
# ---------------------------------------------------------
col_header_left, col_header_right = st.columns([3, 1])

with col_header_left:
  html(f"""
    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 6px;">
        <span class="badge-cyan">❄️ CADENA DE FRÍO</span>
        <span class="badge-gray">Estándar DCSA IoT · Gateway Activo</span>
        <span class="badge-gray" style="background-color: #FEF3C7; color: #92400E; border-color: #FDE68A;">🧪 Modo Simulación Activo</span>
    </div>
    <h1 style="margin: 0; font-size: 2.1rem; font-weight: 800; color: #0F172A;">
        Monitoreo en Tiempo Real · {shipment_id.split(" ")[0]}
    </h1>
    <p style="color: #64748B; margin-top: 4px; font-size: 0.88rem;">
        Ruta: <b>{shipment_id.split('(')[1].replace(')', '')}</b> &nbsp;|&nbsp; Placa Camión: <b>{truck_plate}</b> ({truck_model})
    </p>
    """)

with col_header_right:
  if st.session_state.action_applied:
    status_badge, status_text = (
        "badge-normal",
        "✓ ACCIÓN OPTIMIZADA APLICADA",
    )
  elif calc_risk > 60:
    status_badge, status_text = "badge-danger", "🚨 RIESGO ALTO DETECTADO"
  elif calc_risk > 35:
    status_badge, status_text = "badge-warning", "⚠️ ATENCIÓN REQUERIDA"
  else:
    status_badge, status_text = "badge-normal", "✓ OPERACIÓN NORMAL"

  html(f"""
    <div style="text-align: right;">
        <span class="{status_badge}">{status_text}</span>
        <div style="color: #64748B; font-size: 0.78rem; margin-top: 8px;">🔄 Sincronización GPS: Activa</div>
    </div>
    """)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# SISTEMA DE NAVEGACIÓN POR BOTONES (REEMPLAZANDO LOS TABS NATIVOS)
# ---------------------------------------------------------
t_col1, t_col2, t_col3, _ = st.columns([1.5, 1.5, 1.5, 2.5])

with t_col1:
  if st.button(
      "📊 Panel de Control Operativo",
      use_container_width=True,
      type="primary"
      if st.session_state.active_tab == "operativo"
      else "secondary",
  ):
    st.session_state.active_tab = "operativo"
    st.rerun()

with t_col2:
  if st.button(
      "🗺️ Rastreo GPS Satelital",
      use_container_width=True,
      type="primary"
      if st.session_state.active_tab == "mapa"
      else "secondary",
  ):
    st.session_state.active_tab = "mapa"
    st.rerun()

with t_col3:
  if st.button(
      "📋 Bitácora DCSA & Eventos",
      use_container_width=True,
      type="primary"
      if st.session_state.active_tab == "logs"
      else "secondary",
  ):
    st.session_state.active_tab = "logs"
    st.rerun()

st.markdown("<hr style='margin: 10px 0 20px 0; border-color: #CBD5E1;'>", unsafe_allow_html=True)

# ---------------------------------------------------------
# CONTENIDO SEGÚN LA PESTAÑA ACTIVA
# ---------------------------------------------------------
if st.session_state.active_tab == "operativo":
  # FILA 1: MÉTRICAS
  c1, c2, c3 = st.columns(3)

  # --- TARJETA 1: TEMPERATURA ---
  with c1:
    temp_status = (
        "NORMAL"
        if base_temp <= 2.5
        else ("ADVERTENCIA" if base_temp <= 3.5 else "CRÍTICO")
    )
    badge_color = (
        "badge-normal"
        if temp_status == "NORMAL"
        else ("badge-warning" if temp_status == "ADVERTENCIA" else "badge-danger")
    )

    html(f"""
        <div class="dashboard-card">
            <div class="card-title">
                <span>🌡️ Temperatura Reefer</span>
                <span class="{badge_color}">{temp_status}</span>
            </div>
            <div class="main-metric">{base_temp:.1f} <span style="font-size: 1.4rem; color: #64748B;">°C</span></div>
            <div class="sub-detail">
                Setpoint deseado: <b>1,5 °C</b> &nbsp;|&nbsp; Umbral máx: <b>2,5 °C</b>
            </div>
        </div>
        """)

    hours = [f"{i}:00" for i in range(12, 19)]
    temps = [
        base_temp + 0.2,
        base_temp + 0.1,
        base_temp,
        base_temp - 0.1,
        base_temp + 0.1,
        base_temp,
        base_temp,
    ]
    fig_temp = go.Figure()
    fig_temp.add_trace(
        go.Scatter(
            x=hours,
            y=temps,
            mode="lines+markers",
            line=dict(
                color="#EF4444" if base_temp > 2.5 else "#0284C7", width=2.5
            ),
            fill="tozeroy",
            fillcolor=(
                "rgba(239, 68, 68, 0.08)"
                if base_temp > 2.5
                else "rgba(2, 132, 199, 0.08)"
            ),
        )
    )
    fig_temp.update_layout(
        height=90,
        margin=dict(l=0, r=0, t=5, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False, visible=True, tickfont=dict(color="#64748B", size=9)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#E2E8F0",
            range=[0, 5],
            tickfont=dict(color="#64748B", size=9),
        ),
    )
    st.plotly_chart(
        fig_temp, use_container_width=True, config={"displayModeBar": False}
    )

  # --- TARJETA 2: ENERGÍA Y BATERÍA ---
  with c2:
    fuel_level = max(10, 100 - int(progress_pct * 0.7))
    html(f"""
        <div class="dashboard-card">
            <div class="card-title">
                <span>⚡ Energía y Combustible</span>
                <span class="badge-normal">ESTABLE</span>
            </div>
            <div class="main-metric">{fuel_level} <span style="font-size: 1.4rem; color: #64748B;">%</span></div>
            <div class="sub-detail">Autonomía estimada disponible para el reefer.</div>
            <div style="background-color: #E2E8F0; border-radius: 6px; height: 8px; margin: 12px 0; overflow: hidden;">
                <div style="background-color: {'#10B981' if fuel_level > 30 else '#EF4444'}; width: {fuel_level}%; height: 100%;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #64748B;">
                <span>Reserva crítica: 20%</span>
                <span>Capacidad total: 100%</span>
            </div>
            <hr style="border-color: #E2E8F0; margin: 12px 0;">
            <div style="display: flex; justify-content: space-between; font-size: 0.82rem;">
                <div><span style="color:#64748B;">Autonomía:</span> <b>{fuel_level * 0.08:.1f} hrs</b></div>
                <div><span style="color:#64748B;">Fuente:</span> <b>Diésel + Batería</b></div>
            </div>
        </div>
        """)

  # --- TARJETA 3: ESTADO DEL TRANSPORTE ---
  with c3:
    eta_min = 18 * 60 + 40 - (110 if st.session_state.action_applied else 0)
    eta_str = f"{eta_min // 60}:{eta_min % 60:02d}"
    delay_tag = (
        '<span class="badge-warning">RETRASO ESTIMADO</span>'
        if calc_risk > 50
        else '<span class="badge-normal">A TIEMPO</span>'
    )

    html(f"""
        <div class="dashboard-card">
            <div class="card-title">
                <span>🚛 Estado del Transporte</span>
                {delay_tag}
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85rem;">
                <div><span style="color:#64748B;">Estado:</span><br><b>En tránsito</b></div>
                <div><span style="color:#64748B;">Tráfico en Ruta:</span><br><b style="color: #D97706;">{traffic_level}</b></div>
                <div><span style="color:#64748B;">ETA Estimado:</span><br><b style="font-size: 1.1rem; color: #0F172A;">{eta_str}</b></div>
                <div><span style="color:#64748B;">Velocidad Media:</span><br><b>62 km/h</b></div>
                <div><span style="color:#64748B;">Conductor:</span><br><b>{driver_name}</b></div>
                <div><span style="color:#64748B;">Vehículo ID:</span><br><b>{truck_model}</b></div>
            </div>
        </div>
        """)

  # FILA 2: DETALLES, IA Y ACCIÓN
  col_left, col_mid, col_right = st.columns([1.2, 1, 1.1])

  with col_left:
    html(f"""
        <div class="dashboard-card">
            <div class="card-title">📍 Ubicación y Telemetría Integrada</div>
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 8px;">
                <b>Progreso de Ruta ({progress_pct}%)</b>
                <span style="color: #0284C7; font-weight: 600;">{current_km} / {total_km} km</span>
            </div>
            <div style="background-color: #E2E8F0; border-radius: 6px; height: 6px; margin-bottom: 15px;">
                <div style="background-color: #0284C7; width: {progress_pct}%; height: 100%; border-radius: 6px;"></div>
            </div>
            
            <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; margin-bottom: 15px;">
                <div style="font-size: 0.75rem; color: #64748B; text-transform: uppercase;">Detalles del Vehículo y Carga</div>
                <div style="font-size: 0.82rem; margin-top: 4px; color: #1E293B;"><b>Placa Camión:</b> {truck_plate}</div>
                <div style="font-size: 0.82rem; color: #1E293B;"><b>Contenedor:</b> R40 · MSCU 728451-3</div>
                <div style="font-size: 0.78rem; color: #64748B; margin-top: 2px;">Coordenadas GPS: {truck_lat:.4f}, {truck_lon:.4f}</div>
            </div>

            <div style="font-size: 0.78rem; color: #64748B; font-weight: 700; margin-bottom: 8px;">RUTOGRAMA EN TIEMPO REAL</div>
            <div class="timeline-item"><span style="color: {'#10B981' if progress_pct >= 0 else '#64748B'};">● {cities[0]} (Origen)</span><span style="color:#64748B;">Completado</span></div>
            <div class="timeline-item"><span style="color: {'#10B981' if progress_pct >= 40 else '#64748B'};">● {cities[1] if len(cities)>1 else 'Punto 1'}</span><span style="color:#64748B;">{'Pasado' if progress_pct >= 40 else 'Pendiente'}</span></div>
            <div class="timeline-item"><span style="color: {'#D97706' if progress_pct >= 70 and progress_pct < 95 else '#64748B'};">● {cities[2] if len(cities)>2 else 'Punto 2'}</span><span style="color:#64748B;">En Tránsito</span></div>
            <div class="timeline-item"><span style="color: {'#0284C7' if progress_pct == 100 else '#64748B'};">● {cities[-1]} (Destino)</span><span style="color:#64748B;">ETA {eta_str}</span></div>
        </div>
        """)

  with col_mid:
    risk_color = (
        "#EF4444"
        if calc_risk > 60
        else ("#D97706" if calc_risk > 30 else "#10B981")
    )

    html("""
        <div class="dashboard-card">
            <div class="card-title">
                <span>🤖 Predicción de IA</span>
                <span class="badge-gray">PRÓXIMAS 3 HORAS</span>
            </div>
            <div style="text-align: center; margin: 10px 0;">
                <div style="font-size: 0.85rem; color: #D97706; font-weight: 700;">⚠️ Evaluación del Riesgo Térmico</div>
            </div>
        </div>
        """)

    fig_risk = go.Figure(
        go.Pie(
            values=[calc_risk, 100 - calc_risk],
            hole=0.75,
            marker_colors=[risk_color, "#E2E8F0"],
            textinfo="none",
        )
    )
    fig_risk.update_layout(
        height=150,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        annotations=[
            dict(
                text=(
                    f"<b>{calc_risk}%</b><br><span"
                    " style='font-size:10px;color:#64748B;'>RIESGO</span>"
                ),
                x=0.5,
                y=0.5,
                font_size=22,
                font_color="#0F172A",
                showarrow=False,
            )
        ],
    )
    st.plotly_chart(
        fig_risk, use_container_width=True, config={"displayModeBar": False}
    )

    risk_msg = (
        "El sistema predice un incremento en el riesgo térmico debido a"
        " factores climáticos, tráfico o fallas detectadas."
        if calc_risk > 50
        else (
            "Condiciones operativas estables. No se anticipan desviaciones"
            " térmicas en las próximas 3 horas."
        )
    )

    html(f"""
        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <p style="font-size: 0.8rem; color: #334155; line-height: 1.4;">
                "{risk_msg}"
            </p>
            <hr style="border-color: #E2E8F0; margin: 10px 0;">
            <div style="font-size: 0.78rem; color: #64748B; display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span>Tráfico detectado:</span><b style="color:#1E293B;">{traffic_level}</b>
            </div>
            <div style="font-size: 0.78rem; color: #64748B; display: flex; justify-content: space-between;">
                <span>Temperatura exterior:</span><b style="color:#1E293B;">{ext_temp}°C</b>
            </div>
        </div>
        """)

  with col_right:
    html(f"""
        <div class="dashboard-card">
            <div class="card-title">
                <span>💡 Acción Recomendada</span>
                <span class="badge-cyan">PRESCRIPTIVO</span>
            </div>
            <div style="font-size: 0.92rem; font-weight: 700; color: #0F172A; margin-bottom: 10px;">
                Conectar el reefer al próximo punto eléctrico y ajustar preventivamente el sistema.
            </div>
            <ol style="font-size: 0.8rem; color: #334155; padding-left: 18px; margin-bottom: 12px;">
                <li style="margin-bottom: 6px;"><b>Desviar a la estación eléctrica Km 812</b>.</li>
                <li style="margin-bottom: 6px;">Bajar el setpoint a <b>1,5 °C</b> durante 45 min.</li>
                <li>Notificar al conductor ({driver_name}) del nuevo ETA.</li>
            </ol>
            
            <div class="financial-box">
                <div class="financial-title">IMPACTO FINANCIERO EVITADO</div>
                <div class="financial-value">USD 9.400</div>
                <div style="font-size: 0.75rem; color: #059669; margin-top: 2px;">
                    → Evita pérdida total por daño de carga sensible.
                </div>
            </div>
        </div>
        """)

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
      if st.button(
          "✓ Aplicar Acción", type="primary", use_container_width=True
      ):
        st.session_state.action_applied = True
        st.toast("✅ Acción prescriptiva aplicada con éxito.", icon="❄️")
        st.rerun()

    with btn_col2:
      if st.button("✕ Descartar", type="secondary", use_container_width=True):
        st.session_state.action_applied = False
        st.toast("⚠️ Recomendación ignorada.", icon="ℹ️")
        st.rerun()

elif st.session_state.active_tab == "mapa":
  st.subheader("🗺️ Rastreo Satelital GPS en Tiempo Real")
  st.caption(
      "Visualización interactiva de la ruta y posición dinámica del camión."
  )

  route_df = pd.DataFrame({"city": cities, "lat": lats, "lon": lons})
  truck_df = pd.DataFrame({
      "lat": [truck_lat],
      "lon": [truck_lon],
      "label": [f"🚚 Camión {truck_plate}"],
  })

  path_data = [
      {"path": [[lons[i], lats[i]] for i in range(len(lats))], "name": "Ruta"}
  ]
  layer_path = pdk.Layer(
      "PathLayer",
      path_data,
      get_path="path",
      get_color=[2, 132, 199, 255],
      width_scale=20,
      width_min_pixels=4,
  )

  layer_cities = pdk.Layer(
      "ScatterplotLayer",
      route_df,
      get_position="[lon, lat]",
      get_color=[71, 85, 105, 200],
      get_radius=15000,
      pickable=True,
  )

  truck_color_rgb = (
      [239, 68, 68, 255] if calc_risk > 50 else [16, 185, 129, 255]
  )
  layer_truck = pdk.Layer(
      "ScatterplotLayer",
      truck_df,
      get_position="[lon, lat]",
      get_color=truck_color_rgb,
      get_radius=25000,
      pickable=True,
  )

  view_state = pdk.ViewState(
      latitude=truck_lat, longitude=truck_lon, zoom=6, pitch=0
  )
  r = pdk.Deck(
      layers=[layer_path, layer_cities, layer_truck],
      initial_view_state=view_state,
      map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
      tooltip={"text": "{city}\n{label}"},
  )

  st.pydeck_chart(r)

  map_info1, map_info2, map_info3 = st.columns(3)
  with map_info1:
    st.info(f"📍 **Coordenadas GPS:** {truck_lat:.4f} N, {truck_lon:.4f} W")
  with map_info2:
    st.info(f"🚛 **Placa:** {truck_plate} | **Conductor:** {driver_name}")
  with map_info3:
    st.info("📡 **Señal Gateway DCSA:** Excelente (Sincronizado)")

elif st.session_state.active_tab == "logs":
  st.subheader("📋 Registro Telemétrico DCSA IoT")
  st.write(
      "Eventos e incidentes registrados por el Gateway a lo largo del viaje."
  )

  log_data = [
      {
          "Hora": "18:14:10",
          "Evento / Sensor": "Telemetría GPS",
          "Detalle": f"Posición actual Lat {truck_lat:.4f}, Lon {truck_lon:.4f}",
          "Nivel": "INFO",
      },
      {
          "Hora": "18:12:00",
          "Evento / Sensor": "Temperatura Reefer",
          "Detalle": f"Lectura actual: {base_temp:.1f} °C",
          "Nivel": "NORMAL" if base_temp <= 2.5 else "ALERTA",
      },
      {
          "Hora": "18:00:45",
          "Evento / Sensor": "Evaluación de Riesgo IA",
          "Detalle": f"Calculado riesgo térmico de {calc_risk}%",
          "Nivel": "ALERTA" if calc_risk > 50 else "NORMAL",
      },
      {
          "Hora": "17:42:10",
          "Evento / Sensor": "Sensor de Puertas",
          "Detalle": (
              "Apertura detectada (Inspección)"
              if door_open
              else "Puerta sellada y asegurada"
          ),
          "Nivel": "ADVERTENCIA" if door_open else "NORMAL",
      },
  ]
  st.table(log_data)
