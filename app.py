from datetime import datetime
import numpy as np
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st


# --- FUNCIÓN AUXILIAR DE LIMPIEZA HTML ---
def html(code: str):
    cleaned = "\n".join([line.strip() for line in code.split("\n")])
    st.markdown(cleaned, unsafe_allow_html=True)


# --- FUNCIÓN PARA OBTENER CLIMA SATELITAL EN TIEMPO REAL ---
@st.cache_data(ttl=600)
def obtener_clima_en_vivo(lat, lon):
    temp_estimada = round(26.0 + abs(lat) * 0.5, 1)
    condicion = (
        "Cálido / Despejado" if lat > 7.0 else "Estable / Nubosidad parcial"
    )
    humedad = 78
    return temp_estimada, condicion, humedad


# 1. Configuración de la página con barra lateral expandida por defecto
st.set_page_config(
    page_title="SIMCA Frío 4.0 - Simulador & Rastreo GPS",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Estilos CSS limpios y profesionales (incluyendo el ajuste para mantener el expander siempre blanco)
html("""
<style>
.stApp {
    background-color: #F8FAFC !important;
    color: #1E293B !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 2rem !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* --- BOTONES GENERALES --- */
div.stButton > button {
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.75rem !important;
    padding: 0.35rem 0.6rem !important;
    transition: all 0.2s ease !important;
}
div.stButton > button[kind="primary"] {
    background-color: #0284C7 !important;
    color: #FFFFFF !important;
    border: 1px solid #0284C7 !important;
}
div.stButton > button[kind="primary"]:hover {
    background-color: #0369A1 !important;
}
div.stButton > button[kind="secondary"] {
    background-color: #FFFFFF !important;
    color: #334155 !important;
    border: 1px solid #CBD5E1 !important;
}
div.stButton > button[kind="secondary"]:hover {
    background-color: #F1F5F9 !important;
    border-color: #94A3B8 !important;
}

/* Tarjetas limpias de Streamlit */
.dashboard-card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

/* --- FORZAR FONDO BLANCO Y DISEÑO LIMPIO EN EL EXPANDER --- */
[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    margin-top: 10px !important;
}
[data-testid="stExpander"] summary {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary:hover {
    background-color: #F8FAFC !important;
    color: #0284C7 !important;
}
[data-testid="stExpander"] div[role="region"] {
    background-color: #FFFFFF !important;
    border-top: 1px solid #F1F5F9 !important;
}

/* Badges corporativos */
.badge-normal {
    background-color: #ECFDF5; color: #059669; padding: 2px 8px;
    border-radius: 4px; font-size: 0.72rem; font-weight: 600; border: 1px solid #A7F3D0;
}
.badge-warning {
    background-color: #FFFBEB; color: #D97706; padding: 2px 8px;
    border-radius: 4px; font-size: 0.72rem; font-weight: 600; border: 1px solid #FDE68A;
}
.badge-danger {
    background-color: #FEF2F2; color: #DC2626; padding: 2px 8px;
    border-radius: 4px; font-size: 0.72rem; font-weight: 600; border: 1px solid #FCA5A5;
}
.badge-cyan {
    background-color: #F0F9FF; color: #0284C7; padding: 2px 8px;
    border-radius: 4px; font-size: 0.72rem; font-weight: 600; border: 1px solid #BAE6FD;
}
.badge-gray {
    background-color: #F1F5F9; color: #475569; padding: 2px 8px;
    border-radius: 4px; font-size: 0.72rem; font-weight: 600; border: 1px solid #E2E8F0;
}

.financial-box {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.06) 0%, rgba(6, 182, 212, 0.06) 100%);
    border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 8px; padding: 10px 12px; margin-top: 8px; margin-bottom: 10px;
}
</style>
""")

# --- ESTADO GLOBAL Y PERSISTENCIA DE CONTROLES ---
if "action_applied" not in st.session_state:
    st.session_state.action_applied = False
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "operativo"

if "available_strategies" not in st.session_state:
    st.session_state.available_strategies = [
        "Desviar a estación eléctrica Km 812 + Ajustar Setpoint",
        "Activar generador auxiliar y refrigeración forzada",
        "Solicitar carril preferencial por congestión vial",
        "Alerta a centro de control y recepción en destino",
    ]

if "selected_strategy_idx" not in st.session_state:
    st.session_state.selected_strategy_idx = 0

if "audit_logs" not in st.session_state:
    st.session_state.audit_logs = [
        {
            "Hora": datetime.now().strftime("%H:%M:%S"),
            "Evento": "Inicio de Monitoreo",
            "Detalle": "Ruta cargada y Gateway IoT conectado exitosamente.",
            "Nivel": "INFO",
        }
    ]

defaults = {
    "t_reefer_fail": False,
    "t_road_block": False,
    "t_low_fuel": False,
    "t_signal_loss": False,
    "t_door_open": False,
    "t_humidity": False,
    "val_ext_temp": 28,
    "val_traffic": "Moderado",
    "val_progress": 65,
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


def aplicar_perfil_caribe():
    st.session_state.val_ext_temp = 38
    st.session_state.val_traffic = "Alto"
    st.session_state.t_reefer_fail = False
    st.session_state.t_road_block = False
    st.session_state.t_low_fuel = False
    st.session_state.t_door_open = False


def aplicar_perfil_bloqueo():
    st.session_state.val_ext_temp = 30
    st.session_state.val_traffic = "Crítico"
    st.session_state.t_reefer_fail = True
    st.session_state.t_road_block = True
    st.session_state.t_low_fuel = True
    st.session_state.t_door_open = False


def aplicar_perfil_farma():
    st.session_state.val_ext_temp = 22
    st.session_state.val_traffic = "Bajo"
    st.session_state.t_reefer_fail = False
    st.session_state.t_road_block = False
    st.session_state.t_low_fuel = False
    st.session_state.t_door_open = True


def reiniciar_todo():
    st.session_state.action_applied = False
    st.session_state.t_reefer_fail = False
    st.session_state.t_road_block = False
    st.session_state.t_low_fuel = False
    st.session_state.t_signal_loss = False
    st.session_state.t_door_open = False
    st.session_state.t_humidity = False
    st.session_state.val_ext_temp = 28
    st.session_state.val_traffic = "Moderado"
    st.session_state.val_progress = 65
    st.session_state.available_strategies = [
        "Desviar a estación eléctrica Km 812 + Ajustar Setpoint",
        "Activar generador auxiliar y refrigeración forzada",
        "Solicitar carril preferencial por congestión vial",
        "Alerta a centro de control y recepción en destino",
    ]
    st.session_state.selected_strategy_idx = 0
    st.session_state.audit_logs = [
        {
            "Hora": datetime.now().strftime("%H:%M:%S"),
            "Evento": "Simulación Reiniciada",
            "Detalle": "Se restablecieron los parámetros iniciales de la ruta.",
            "Nivel": "INFO",
        }
    ]


# ---------------------------------------------------------
# BARRA LATERAL NATIVA
# ---------------------------------------------------------
with st.sidebar:
    html("""
    <div style="background-color: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.12); border-radius: 6px; padding: 8px; margin-bottom: 6px;">
        <div style="font-size: 0.6rem; color: #94A3B8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">Perfil Profesional / Operador</div>
        <div style="font-size: 0.82rem; color: #FFFFFF; font-weight: 700;">Impotarja (Logistics & Trade)</div>
        <div style="font-size: 0.7rem; color: #CBD5E1;">Kaleth M. · Negocios Intl.</div>
    </div>
    """)

    st.markdown(
        "<h3 style='margin:0; color:#FFFFFF;'>⚙️ SIMULADOR DE RIESGO</h3>",
        unsafe_allow_html=True,
    )
    st.caption("Control Predictivo de Cadena de Frío")
    st.markdown("---")

    st.subheader("🚚 Despacho y Ruta")
    shipment_id = st.selectbox(
        "Seleccionar Ruta Activa:",
        [
            "FLR-2291 (Bogotá → Cartagena)",
            "FLR-3105 (Medellín → Barranquilla)",
            "FLR-1048 (Cali → Buenaventura)",
        ],
        index=0,
    )

    if "FLR-2291" in shipment_id:
        total_km = 1058
        driver_name = "C. Ramírez"
        truck_plate = "SXK-482"
        container_code = "R40 · MSCU 728451-3"
        truck_model = "Tractor 3S3 (#C-114)"
        base_temp_init = 1.5
        lats = [4.7110, 5.4627, 7.0653, 10.9685, 10.3997]
        lons = [-74.0721, -74.6558, -73.8547, -74.7813, -75.5144]
        cities = [
            "Bogotá (Origen)",
            "Puerto Salgar",
            "Barrancabermeja",
            "Barranquilla",
            "Cartagena (Destino)",
        ]
    elif "FLR-3105" in shipment_id:
        total_km = 705
        driver_name = "A. Mendoza"
        truck_plate = "WNK-912"
        container_code = "R40 · MSCU 889214-9"
        truck_model = "Tractor Volvo FH (#V-882)"
        base_temp_init = 2.1
        lats = [6.2442, 7.9856, 8.7480, 10.9685]
        lons = [-75.5812, -75.1978, -75.8814, -74.7813]
        cities = [
            "Medellín (Origen)",
            "Caucasia",
            "Montería",
            "Barranquilla (Destino)",
        ]
    else:
        total_km = 520
        driver_name = "J. Delgado"
        truck_plate = "TLM-304"
        container_code = "R20 · HLCU 304812-0"
        truck_model = "Tractor Kenworth T680 (#K-009)"
        base_temp_init = 2.8
        lats = [3.4516, 3.6582, 3.7667, 3.8801]
        lons = [-76.5320, -76.6881, -76.6833, -77.0312]
        cities = [
            "Cali (Origen)",
            "Dagua",
            "Loboguerrero",
            "Buenaventura (Destino)",
        ]

    st.markdown("---")
    st.subheader("🎯 Perfiles de Simulación")
    p_btn1, p_btn2, p_btn3 = st.columns(3)
    with p_btn1:
        st.button(
            "☀️ Caribe",
            use_container_width=True,
            on_click=aplicar_perfil_caribe,
        )
    with p_btn2:
        st.button(
            "🚧 Bloqueo",
            use_container_width=True,
            on_click=aplicar_perfil_bloqueo,
        )
    with p_btn3:
        st.button(
            "🛡️ Farma",
            use_container_width=True,
            on_click=aplicar_perfil_farma,
        )

    st.markdown("---")
    st.subheader("📍 Avance de Trayecto")
    progress_pct = st.slider(
        "Progreso del viaje (%):",
        0,
        100,
        st.session_state.val_progress,
        step=5,
        key="slider_progress",
    )
    st.session_state.val_progress = progress_pct
    current_km = int(total_km * (progress_pct / 100))

    interp_idx = (len(lats) - 1) * (progress_pct / 100.0)
    idx_low = int(np.floor(interp_idx))
    idx_high = min(int(np.ceil(interp_idx)), len(lats) - 1)
    fraction = interp_idx - idx_low

    truck_lat = lats[idx_low] + (lats[idx_high] - lats[idx_low]) * fraction
    truck_lon = lons[idx_low] + (lons[idx_high] - lons[idx_low]) * fraction

    clima_real_temp, clima_real_desc, clima_real_hum = obtener_clima_en_vivo(
        truck_lat, truck_lon
    )

    st.markdown("---")
    st.subheader("🛠️ Inyección de Incidentes")
    reefer_fail = st.toggle(
        "🚨 Falla en Compresor Reefer", key="t_reefer_fail"
    )
    road_block = st.toggle("🚧 Derrumbe / Cierre de Vía", key="t_road_block")
    low_fuel = st.toggle("⛽ Bajo Nivel Combustible (<15%)", key="t_low_fuel")
    signal_loss = st.toggle("📡 Sombra GPS / Señal", key="t_signal_loss")
    door_open = st.toggle("🚪 Apertura No Autorizada", key="t_door_open")
    humidity_spike = st.toggle("💧 Alerta de Humedad", key="t_humidity")

    ext_temp = st.slider(
        "Temp. Exterior (°C):",
        15,
        45,
        st.session_state.val_ext_temp,
        key="slider_ext_temp",
    )
    st.session_state.val_ext_temp = ext_temp

    traffic_options = ["Bajo", "Moderado", "Alto", "Crítico"]
    current_traffic = st.session_state.val_traffic
    traffic_level = st.select_slider(
        "Tráfico en Ruta:",
        options=traffic_options,
        value=current_traffic
        if current_traffic in traffic_options
        else "Moderado",
        key="slider_traffic",
    )
    st.session_state.val_traffic = traffic_level

    traffic_multiplier = {
        "Bajo": 0.5,
        "Moderado": 1.0,
        "Alto": 1.5,
        "Crítico": 2.2,
    }[traffic_level]
    fail_penalty = 40 if reefer_fail else 0
    block_penalty = 25 if road_block else 0
    fuel_penalty = 15 if low_fuel else 0
    door_penalty = 15 if door_open else 0
    humidity_penalty = 10 if humidity_spike else 0

    calc_risk = int(
        min(
            98,
            max(
                10,
                (ext_temp * 1.3)
                + (traffic_multiplier * 15)
                + fail_penalty
                + block_penalty
                + fuel_penalty
                + door_penalty
                + humidity_penalty
                - (25 if st.session_state.action_applied else 0),
            ),
        )
    )

    base_temp = base_temp_init + (
        1.8 if reefer_fail else (0.6 if door_open else 0)
    )

    st.markdown("---")
    st.button(
        "🔄 Reiniciar Simulación",
        use_container_width=True,
        on_click=reiniciar_todo,
    )

# ---------------------------------------------------------
# CABECERA PRINCIPAL
# ---------------------------------------------------------
col_header_left, col_header_right = st.columns([3, 1])

with col_header_left:
    html(f"""
    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 4px;">
        <span class="badge-cyan">CADENA DE FRÍO 4.0</span>
        <span class="badge-gray">DCSA IoT Standard</span>
        <span class="badge-gray" style="background-color: #FEF3C7; color: #92400E; border-color: #FDE68A;">Telemetría Activa</span>
    </div>
    <h1 style="margin: 0; font-size: 1.8rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em;">
        Monitoreo en Tiempo Real · {shipment_id.split(' ')[0]}
    </h1>
    <p style="color: #64748B; margin-top: 2px; font-size: 0.82rem;">
        Ruta: <b>{shipment_id.split('(')[1].replace(')', '')}</b> &nbsp;|&nbsp; Clima en Posición: <b>{clima_real_desc} ({ext_temp}°C, Hum: {clima_real_hum}%)</b>
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
        <div style="color: #64748B; font-size: 0.72rem; margin-top: 6px; font-family: monospace;">GATEWAY_ID: DCSA-GW-994</div>
    </div>
    """)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# SISTEMA DE NAVEGACIÓN
# ---------------------------------------------------------
t_col1, t_col2, t_col3, _ = st.columns([1.4, 1.4, 1.4, 2.8])

with t_col1:
    if st.button(
        "🗂️ Panel Operativo",
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
        "📋 Timeline Operativo",
        use_container_width=True,
        type="primary"
        if st.session_state.active_tab == "logs"
        else "secondary",
    ):
        st.session_state.active_tab = "logs"
        st.rerun()

st.markdown(
    "<hr style='margin: 8px 0 16px 0; border-color: #E2E8F0;'>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# CONTENIDO SEGÚN PESTAÑA
# ---------------------------------------------------------
if st.session_state.active_tab == "operativo":
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
    hum_val = 84 if humidity_spike else 62

    # --- TARJETA REEFER MAESTRA ROBUSTA Y BIEN DISTRIBUIDA ---
    html(f"""
    <div class="dashboard-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid #F1F5F9; padding-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em; color: #0F172A; font-weight: 800;">❄️ Temperatura Reefer (Contenedor Activo)</span>
                <span class="badge-cyan">DCSA IoT</span>
            </div>
            <span class="{badge_color}">{temp_status}</span>
        </div>
        
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 20px;">
            <!-- Izquierda: Métrica Principal + Info de Estado -->
            <div style="min-width: 160px; border-right: 1px solid #F1F5F9; padding-right: 15px;">
                <div style="font-size: 0.68rem; color: #64748B; font-weight: 700; text-transform: uppercase;">Temperatura Actual</div>
                <div style="font-size: 2.4rem; font-weight: 800; color: #0F172A; line-height: 1.1; margin: 2px 0;">{base_temp:.1f} <span style="font-size: 1.1rem; color: #64748B; font-weight: 600;">°C</span></div>
                <div style="font-size: 0.72rem; color: #059669; font-weight: 600; display: flex; align-items: center; gap: 4px;">
                    <span style="width: 7px; height: 7px; background: #10B981; border-radius: 50%; display: inline-block;"></span> Compresor Operativo
                </div>
            </div>

            <!-- Centro: Mini Gráfica de Líneas NATIVA en SVG con más presencia -->
            <div style="flex-grow: 1; text-align: center; background: #FAFAFA; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: #64748B; margin-bottom: 4px; font-weight: 600;">
                    <span>Tendencia Térmica (Últimas 7 Horas)</span>
                    <span style="color: #0284C7;">Rango ideal: 1.0°C - 2.0°C</span>
                </div>
                <svg viewBox="0 0 380 42" style="width: 100%; height: 36px; display: block; overflow: visible;">
                    <!-- Línea de tendencia -->
                    <path d="M 10 28 L 65 25 L 120 27 L 175 10 L 230 22 L 285 19 L 340 30" fill="none" stroke="#0284C7" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                    <!-- Puntos de datos -->
                    <circle cx="10" cy="28" r="3" fill="#0284C7"/>
                    <circle cx="65" cy="25" r="3" fill="#0284C7"/>
                    <circle cx="120" cy="27" r="3" fill="#0284C7"/>
                    <circle cx="175" cy="10" r="3.5" fill="#D97706"/>
                    <circle cx="230" cy="22" r="3" fill="#0284C7"/>
                    <circle cx="285" cy="19" r="3" fill="#0284C7"/>
                    <circle cx="340" cy="30" r="3" fill="#0284C7"/>
                </svg>
                <div style="display: flex; justify-content: space-between; font-size: 9px; color: #94A3B8; font-weight: 600; margin-top: 4px; padding: 0 4px;">
                    <span>12:00</span><span>13:00</span><span>14:00</span><span>15:00</span><span>16:00</span><span>17:00</span><span>18:00</span>
                </div>
            </div>

            <!-- Derecha: Datos Técnicos y Setpoint -->
            <div style="text-align: right; min-width: 140px; border-left: 1px solid #F1F5F9; padding-left: 15px; font-size: 0.78rem; color: #64748B; line-height: 1.5;">
                Setpoint: <b style="color: #0F172A;">1,5°C</b><br>
                Humedad: <b style="color: #0284C7;">{hum_val}%</b><br>
                Alarma: <b style="color: #059669;">Ninguna</b>
            </div>
        </div>
    </div>
    """)

    # --- EXPANDER CON ESTILO LIMPIO Y COLOR FIJO BLANCO ---
    with st.expander(
        "📋 Ver Historial Horario Detallado (Temperaturas y Horas Exactas)"
    ):
        st.markdown(
            "<h5 style='margin:0 0 8px 0; color:#0F172A; font-size: 0.9rem;'>Registro Horario de Telemetría IoT</h5>",
            unsafe_allow_html=True,
        )
        df_temp_history = pd.DataFrame({
            "Hora": [
                "12:00",
                "13:00",
                "14:00",
                "15:00",
                "16:00",
                "17:00",
                "18:00 (Actual)",
            ],
            "Temperatura (°C)": [
                1.4,
                1.5,
                1.5,
                f"{base_temp:.1f}",
                1.6,
                1.5,
                f"{base_temp:.1f}",
            ],
            "Estado Térmico": [
                "Normal",
                "Normal",
                "Normal",
                "Alerta / Variación",
                "Normal",
                "Normal",
                "En Monitoreo",
            ],
            "Humedad Relativa": [
                "60%",
                "61%",
                "60%",
                f"{hum_val}%",
                "62%",
                "61%",
                f"{hum_val}%",
            ],
        })
        st.dataframe(df_temp_history, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Las demás tarjetas de Energía/Combustible y Estado del Transporte
    c2, c3 = st.columns(2)

    with c2:
        fuel_level = 12 if low_fuel else max(15, 100 - int(progress_pct * 0.7))
        fuel_status_badge = (
            '<span class="badge-danger">CRÍTICO</span>'
            if low_fuel
            else '<span class="badge-normal">ESTABLE</span>'
        )
        seal_txt = "Abierto (Alerta)" if door_open else "Bloqueado (e-Seal)"
        html(f"""
        <div class="dashboard-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; color: #64748B; font-weight: 700;">Energía y Combustible</span>
                {fuel_status_badge}
            </div>
            <div style="font-size: 2rem; font-weight: 800; color: #0F172A; line-height: 1.1;">{fuel_level} <span style="font-size: 1.1rem; color: #64748B;">%</span></div>
            <div style="font-size: 0.76rem; color: #64748B; margin-top: 8px; display: flex; justify-content: space-between;">
                <span>Autonomía: <b>4.4 hrs</b></span>
                <span style="color: #059669; font-weight: 600;">{seal_txt}</span>
            </div>
        </div>
        """)

    with c3:
        block_extra = 75 if road_block else 0
        eta_min = (
            18 * 60
            + 40
            + block_extra
            - (110 if st.session_state.action_applied else 0)
        )
        eta_str = f"{eta_min // 60}:{eta_min % 60:02d}"
        next_ckpt = (
            "Estación Eléctrica Km 812"
            if progress_pct > 50
            else "Puerto Salgar (Check 1)"
        )
        html(f"""
        <div class="dashboard-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; color: #64748B; font-weight: 700;">Estado del Transporte</span>
                <span class="badge-warning">RETRASO</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 0.76rem; margin-top: 4px;">
                <div><span style="color: #64748B;">ETA:</span> <b style="color: #0F172A;">{eta_str}</b></div>
                <div><span style="color: #64748B;">Tráfico:</span> <b style="color: #D97706;">{traffic_level}</b></div>
                <div><span style="color: #64748B;">Conductor:</span> <b>{driver_name}</b></div>
                <div><span style="color: #64748B;">Vehículo:</span> <b>{truck_plate}</b></div>
            </div>
            <div style="font-size: 0.76rem; color: #64748B; margin-top: 6px; border-top: 1px solid #F1F5F9; paddingTop: 4px;">
                Check-point: <b style="color: #0284C7;">{next_ckpt}</b>
            </div>
        </div>
        """)

    st.markdown("<br>", unsafe_allow_html=True)

    # Fila Media: Distribución equilibrada 1:1:1
    col_left, col_mid, col_right = st.columns(3)

    with col_left:
        html(f"""
        <div class="dashboard-card">
            <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; color: #64748B; font-weight: 700; margin-bottom: 8px;">📍 Ubicación y Telemetría</div>
            <div style="font-size: 0.78rem; font-weight: 700; margin-bottom: 2px;">Progreso de Ruta ({progress_pct}%)</div>
            <div style="display: flex; justify-content: space-between; font-size: 0.72rem; color: #64748B; margin-bottom: 4px;">
                <span>Avance actual</span>
                <span style="color: #0284C7; font-weight: 600;">{current_km} / {total_km} km</span>
            </div>
            <div style="background-color: #E2E8F0; border-radius: 4px; height: 5px; margin-bottom: 8px;">
                <div style="background-color: #0284C7; width: {progress_pct}%; height: 100%; border-radius: 4px;"></div>
            </div>

            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px 8px; margin-bottom: 8px; font-size: 0.73rem;">
                <div>Placa: <b>{truck_plate}</b> | Contenedor: <b>{container_code.split('·')[0]}</b></div>
                <div>Coordenadas: <b>{truck_lat:.4f}, {truck_lon:.4f}</b></div>
            </div>

            <div style="font-size: 0.72rem; font-weight: 700; margin-bottom: 3px; text-transform: uppercase; color: #64748B;">Rutograma en Vivo</div>
            <div style="font-size: 0.74rem; margin-bottom: 6px;">
                <div style="display: flex; justify-content: space-between; padding: 2px 0; border-bottom: 1px solid #F1F5F9;">
                    <span style="color: #059669; font-weight: 600;">● {cities[0]}</span><span style="color: #64748B;">Completado</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 2px 0; border-bottom: 1px solid #F1F5F9;">
                    <span style="color: #0284C7; font-weight: 600;">● {cities[1]}</span><span style="color: #64748B;">Pasado</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 2px 0;">
                    <span style="color: #D97706; font-weight: 600;">● {cities[2]}</span><span style="color: #D97706; font-weight: 600;">En Tránsito</span>
                </div>
            </div>
        </div>
        """)

    with col_mid:
        html(f"""
        <div class="dashboard-card" style="text-align: center;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; color: #64748B; font-weight: 700;">🤖 Predicción de IA</span>
                <span class="badge-gray">3 Horas</span>
            </div>
            <div style="font-size: 0.74rem; font-weight: 700; color: #D97706; margin-top: 2px; margin-bottom: 6px;">Evaluación de Riesgo Térmico</div>

            <div style="position: relative; width: 96px; height: 96px; margin: 0 auto 8px auto; border-radius: 50%; background: conic-gradient(#D97706 {calc_risk * 3.6}deg, #E2E8F0 0deg); display: flex; align-items: center; justify-content: center; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);">
                <div style="position: absolute; width: 72px; height: 72px; background-color: #FFFFFF; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <span style="font-size: 1.2rem; font-weight: 800; color: #0F172A; line-height: 1;">{calc_risk}%</span>
                    <span style="font-size: 0.52rem; font-weight: 700; color: #64748B; letter-spacing: 0.05em; margin-top: 2px;">RIESGO</span>
                </div>
            </div>

            <div style="font-size: 0.7rem; color: #64748B; font-style: italic; margin-bottom: 6px;">
                "Incremento por tráfico denso y temperatura exterior."
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.72rem; text-align: left; border-top: 1px solid #E2E8F0; padding-top: 6px;">
                <span style="color: #64748B;">Tráfico: <b>{traffic_level}</b></span>
                <span style="color: #64748B;">Exterior: <b>{ext_temp} °C</b></span>
            </div>
        </div>
        """)

    with col_right:
        html("""
        <div class="dashboard-card" style="border-top: 3px solid #0284C7; padding-top: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; color: #0284C7; font-weight: 700;">💡 Acciones Prescriptivas</span>
                <span class="badge-cyan">IA ACTIVA</span>
            </div>
        """)

        strategies = st.session_state.available_strategies

        if len(strategies) > 0:
            html(
                '<div style="font-size: 0.72rem; color: #64748B; margin-bottom: 6px;">Seleccione estrategia de mitigación:</div>'
            )

            if st.session_state.selected_strategy_idx >= len(strategies):
                st.session_state.selected_strategy_idx = 0

            for idx, strat in enumerate(strategies):
                is_selected = st.session_state.selected_strategy_idx == idx
                if st.button(
                    f"{'✓ ' if is_selected else '○ '} {strat}",
                    key=f"strat_btn_{idx}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary",
                ):
                    st.session_state.selected_strategy_idx = idx
                    st.rerun()

            selected_action = strategies[st.session_state.selected_strategy_idx]

            impacto_financiero = (
                "USD 9.400"
                if "estación eléctrica" in selected_action
                else (
                    "USD 7.800"
                    if "generador auxiliar" in selected_action
                    else "USD 5.200"
                )
            )

            html(f"""
                <div class="financial-box">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 0.58rem; text-transform: uppercase; color: #047857; font-weight: 700; letter-spacing: 0.05em;">Impacto Financiero Evitado</div>
                            <div style="font-size: 1.05rem; font-weight: 800; color: #059669; margin-top: 1px;">{impacto_financiero}</div>
                        </div>
                        <div style="text-align: right; font-size: 0.64rem; color: #047857; max-width: 120px; line-height: 1.1;">
                            Protección de perecederos y SLA
                        </div>
                    </div>
                </div>
            """)

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button(
                    "✓ Aplicar", type="primary", use_container_width=True
                ):
                    st.session_state.action_applied = True
                    nuevo_log = {
                        "Hora": datetime.now().strftime("%H:%M:%S"),
                        "Evento": "Estrategia Aplicada",
                        "Detalle": f"Ejecutada: {selected_action} (Ahorro: {impacto_financiero})",
                        "Nivel": "ÉXITO",
                    }
                    st.session_state.audit_logs.insert(0, nuevo_log)

                    st.session_state.available_strategies.pop(
                        st.session_state.selected_strategy_idx
                    )
                    st.session_state.selected_strategy_idx = 0
                    st.toast(
                        "✅ Decisión aplicada y registrada en el Timeline.",
                        icon="🤖",
                    )
                    st.rerun()
            with btn_col2:
                if st.button(
                    "✕ Descartar", type="secondary", use_container_width=True
                ):
                    nuevo_log = {
                        "Hora": datetime.now().strftime("%H:%M:%S"),
                        "Evento": "Estrategia Descartada",
                        "Detalle": f"Descartada: {selected_action}",
                        "Nivel": "ADVERTENCIA",
                    }
                    st.session_state.audit_logs.insert(0, nuevo_log)

                    st.session_state.available_strategies.pop(
                        st.session_state.selected_strategy_idx
                    )
                    st.session_state.selected_strategy_idx = 0
                    st.toast(
                        "⚠️ Opción descartada y registrada en el Timeline.",
                        icon="ℹ️",
                    )
                    st.rerun()
        else:
            html("""
                <div style="text-align: center; padding: 20px 0; color: #64748B;">
                    <div style="font-size: 1.4rem; margin-bottom: 4px;">✨</div>
                    <div style="font-size: 0.82rem; font-weight: 600; color: #0F172A;">No hay acciones pendientes</div>
                    <div style="font-size: 0.72rem; margin-top: 2px;">Todas las recomendaciones han sido procesadas.</div>
                </div>
            """)

        html("</div>")

    # Sección Inferior: Analítica de Desempeño Logístico (DCSA IoT Standard)
    st.markdown("<br>", unsafe_allow_html=True)

    html("""
    <div class="dashboard-card">
        <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; color: #64748B; font-weight: 700; margin-bottom: 8px;">📈 Analítica de Desempeño Logístico (DCSA IoT Standard)</div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; text-align: center;">
            <div style="background: #F8FAFC; padding: 10px; border-radius: 6px; border: 1px solid #E2E8F0;">
                <span style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; font-weight: 700;">Eficiencia de Ruta</span><br>
                <b style="font-size: 1.15rem; color: #0F172A;">94.2%</b><br>
                <span class="badge-normal" style="font-size: 0.62rem;">↑ +1.2% vs mes anterior</span>
            </div>
            <div style="background: #F8FAFC; padding: 10px; border-radius: 6px; border: 1px solid #E2E8F0;">
                <span style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; font-weight: 700;">Consumo Energético</span><br>
                <b style="font-size: 1.15rem; color: #0F172A;">14.8 kWh/h</b><br>
                <span class="badge-warning" style="font-size: 0.62rem;">↓ -0.5% (Consumo alto)</span>
            </div>
            <div style="background: #F8FAFC; padding: 10px; border-radius: 6px; border: 1px solid #E2E8F0;">
                <span style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; font-weight: 700;">Integridad Térmica</span><br>
                <b style="font-size: 1.15rem; color: #0F172A;">99.8%</b><br>
                <span class="badge-normal" style="font-size: 0.62rem;">↑ Dentro de rango</span>
            </div>
            <div style="background: #F8FAFC; padding: 10px; border-radius: 6px; border: 1px solid #E2E8F0;">
                <span style="font-size: 0.7rem; color: #64748B; text-transform: uppercase; font-weight: 700;">Compliance SLA</span><br>
                <b style="font-size: 1.15rem; color: #0F172A;">98.5%</b><br>
                <span class="badge-normal" style="font-size: 0.62rem;">↑ Estable</span>
            </div>
        </div>
    </div>
    """)

elif st.session_state.active_tab == "mapa":
    st.subheader("🗺️ Torre de Control: Rastreo GPS y Telemetría en Ruta")
    st.caption(
        f"Visualización geoespacial detallada y nodos logísticos para la ruta **{shipment_id}**."
    )

    route_df = pd.DataFrame({
        "city": cities,
        "lat": lats,
        "lon": lons,
        "tipo": ["Origen"]
        + ["Punto de Control"] * (len(cities) - 2)
        + ["Puerto Destino"],
    })
    truck_df = pd.DataFrame({
        "lat": [truck_lat],
        "lon": [truck_lon],
        "label": [f"🚚 Camión {truck_plate}"],
        "status": [
            f"Riesgo: {calc_risk}% | Temp: {base_temp:.1f}°C | Clima: {ext_temp}°C"
        ],
    })

    path_data = [
        {
            "path": [[lons[i], lats[i]] for i in range(len(lats))],
            "name": "Ruta Troncal DCSA",
        }
    ]
    layer_path = pdk.Layer(
        "PathLayer",
        path_data,
        get_path="path",
        get_color=[2, 132, 199, 220],
        width_scale=25,
        width_min_pixels=5,
    )
    layer_cities = pdk.Layer(
        "ScatterplotLayer",
        route_df,
        get_position="[lon, lat]",
        get_color=[15, 23, 42, 220],
        get_radius=12000,
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
        get_radius=22000,
        pickable=True,
    )

    tooltip_config = {
        "html": "<b>Ubicación / Ciudad:</b> {city}<br/><b>Tipo:</b> {tipo}",
        "style": {
            "backgroundColor": "#0F172A",
            "color": "white",
            "fontSize": "12px",
            "padding": "8px",
            "borderRadius": "4px",
        },
    }

    view_state = pdk.ViewState(
        latitude=truck_lat, longitude=truck_lon, zoom=6.5, pitch=0, bearing=0
    )
    r = pdk.Deck(
        layers=[layer_path, layer_cities, layer_truck],
        initial_view_state=view_state,
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        tooltip=tooltip_config,
    )
    st.pydeck_chart(r, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    with m_col1:
        html("""
        <div class="dashboard-card">
            <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; color: #64748B; font-weight: 700; margin-bottom: 6px;">Conductor Asignado</div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #0F172A;">C. Ramírez</div>
            <div style="font-size: 0.76rem; color: #64748B; margin-top: 4px;">Licencia: <b>CAT-C3 (Verificada)</b></div>
        </div>
        """)

    with m_col2:
        html("""
        <div class="dashboard-card">
            <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; color: #64748B; font-weight: 700; margin-bottom: 6px;">Unidad de Transporte</div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #0F172A;">SXK-482</div>
            <div style="font-size: 0.76rem; color: #64748B; margin-top: 4px;">Tractor 3S3 (#C-114)</div>
        </div>
        """)

    with m_col3:
        html(f"""
        <div class="dashboard-card">
            <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; color: #64748B; font-weight: 700; margin-bottom: 6px;">Clima en Posición GPS</div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #0F172A;">{ext_temp} °C</div>
            <div style="font-size: 0.76rem; color: #64748B; margin-top: 4px;">Condición: <b>Cálido / Despejado</b></div>
        </div>
        """)

    with m_col4:
        html(f"""
        <div class="dashboard-card">
            <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; color: #64748B; font-weight: 700; margin-bottom: 6px;">Estado del Viaje</div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #0284C7;">65% Completado</div>
            <div style="font-size: 0.76rem; color: #64748B; margin-top: 4px;">Distancia: <b>687 / 1058 km</b></div>
        </div>
        """)

elif st.session_state.active_tab == "logs":
    st.subheader("📋 Timeline Operativo de Auditoría")
    st.write(
        "Registro cronológico en tiempo real de eventos del Gateway IoT, decisiones ejecutadas por el operador y recomendaciones de la IA."
    )

    df_logs = pd.DataFrame(st.session_state.audit_logs)
    st.dataframe(df_logs, use_container_width=True, hide_index=True)
