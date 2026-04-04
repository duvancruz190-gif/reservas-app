import streamlit as st 
import os
import json
import time
from datetime import datetime
import pandas as pd
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas - Eternit", layout="wide")

# --- ARCHIVO HISTORIAL ---
HISTORIAL_FILE = "reservas/historial.json"

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, "r") as f:
            return json.load(f)
    return []

def guardar_historial(data):
    with open(HISTORIAL_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generar_excel(historial):
    datos = []
    for h in historial:
        for archivo in h["archivos"]:
            datos.append({
                "Fecha": h["fecha"],
                "Área": h["area"],
                "Archivo": archivo,
                "Cantidad": 1,
                "Total envío": h["cantidad"]
            })
    df = pd.DataFrame(datos)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Historial')
    return output.getvalue()

# --- ESTADOS ---
if "refresh" not in st.session_state:
    st.session_state.refresh = 0
if "mensaje_envio" not in st.session_state:
    st.session_state.mensaje_envio = ""
if "historial" not in st.session_state:
    st.session_state.historial = cargar_historial()

# --- ESTILO PROFESIONAL MEJORADO ---
st.markdown("""
<style>
/* Importar fuente profesional Inter */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

/* Aplicar fuente a toda la aplicación */
html, body, [class*="st-"], .stMarkdown {
    font-family: 'Inter', sans-serif !important;
}

/* Títulos con jerarquía y espaciado moderno */
h1, h2, h3 {
    font-weight: 700 !important;
    letter-spacing: -0.03em !important;
    color: #ffffff !important;
}

/* Etiquetas de inputs (Usuario, Contraseña, etc) */
label {
    font-weight: 600 !important;
    color: #cbd5e0 !important; /* Gris azulado claro */
    text-transform: uppercase;
    font-size: 0.75rem !important;
    letter-spacing: 0.05em;
}

/* BARRA LATERAL */
section[data-testid="stSidebar"] {
    background-color: #1a264d !important; /* Azul más profundo */
}
section[data-testid="stSidebar"] * {
    color: #f8fafc !important;
}

/* BOTONES SIDEBAR */
section[data-testid="stSidebar"] .stButton>button,
section[data-testid="stSidebar"] div.stDownloadButton>button {
    background-color: #2d3e75 !important;
    color: white !important;
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.1);
    font-weight: 600;
    transition: all 0.3s;
}
section[data-testid="stSidebar"] .stButton>button:hover {
    background-color: #3b4c8a !important;
    border-color: #4a5da8;
}

/* BOTÓN PRINCIPAL DE ENVÍO (USUARIO) */
div.usuario-button button {
    background-color: #e2e8f0 !important; /* Gris claro profesional */
    color: #1a264d !important;
    font-weight: 700;
    border-radius: 10px;
    height: 50px;
    border: none;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
}

/* INPUTS REDONDEADOS Y LIMPIOS */
.stTextInput>div>div>input { 
    border-radius: 10px; 
    border: 1px solid #d1d5db;
    padding: 10px;
}

/* TEXTO DE CAPTION Y SECUNDARIOS */
.stCaption, p {
    color: #e2e8f0;
}
</style>
""", unsafe_allow_html=True)

# --- CARPETAS ---
for carpeta in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas", "reservas/archivo", "assets"]:
    os.makedirs(carpeta, exist_ok=True)

# --- DATOS ---
areas = ["Producción", "Calidad", "Mantenimiento", "Logística", "Recursos Humanos", "Ambiental", "Salud Ocupacional", "Marketing", "Financiera", "Almacén"]
usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# --- LOGIN ---
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png", use_container_width=True)
        st.markdown("<h2 style='text-align: center; margin-top: -20px;'>Acceso al Sistema</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 0.9rem; opacity: 0.8;'>Gestión de Reservas - Eternit Colombiana</p>", unsafe_allow_html=True)
        
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar al portal", use_container_width=True):
            if u in usuarios and usuarios[u]["password"] == p:
                st.session_state.login = True
                st.session_state.rol = usuarios[u]["rol"]
                st.session_state.user_name = u
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

# ================= SISTEMA =================
else:
    with st.sidebar:
        if os.path.exists("assets/ETERNITTTTT.png"):
            # Ajustado para evitar estiramiento y mejorar nitidez
            st.image("assets/ETERNITTTTT.png", width=190)
        
        st.markdown(f"### Bienvenid@, **{st.session_state.user_name.capitalize()}**")
        st.caption(f"Rol: {st.session_state.rol}")
        st.divider()

        # HISTORIAL
        with st.expander("📜 Historial de Envíos"):
            if st.session_state.historial:
                area_filtro = st.selectbox("Filtrar por área", ["Todas"] + areas)
                historial_filtrado = st.session_state.historial if area_filtro == "Todas" else [h for h in st.session_state.historial if h["area"] == area_filtro]
                
                excel = generar_excel(historial_filtrado)
                st.download_button(label="📥 Descargar Reporte Excel", data=excel, file_name="historial_eternit.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                
                if st.button("🗑️ Limpiar historial", use_container_width=True):
                    st.session_state.historial = []
                    guardar_historial([])
                    st.rerun()
                
                for h in reversed(historial_filtrado):
                    with st.expander(f"📅 {h['fecha'].split(' ')[0]} - {h['area']}"):
                        for nombre in h["archivos"]:
                            st.caption(f"📄 {nombre}")
            else:
                st.caption("No hay registros previos.")
        
        st.divider()
        if st.button("🚪 Cerrar Sesión Segura", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.title("📋 Gestión de Reservas Digitales")
    rol = st.session_state.rol

    # ================= VISTA USUARIO =================
    if rol == "usuario":
        st.header("📤 Enviar Nueva Reserva")
        if st.session_state.mensaje_envio:
            st.success(st.session_state.mensaje_envio)
            st.session_state.mensaje_envio = ""

        col_a, col_b = st.columns([1, 2])
        with col_a:
            area = st.selectbox("Seleccione el Área", areas)
        
        archivos = st.file_uploader("Arrastre o seleccione sus archivos PDF", type=["pdf"], accept_multiple_files=True, key=f"uploader_{st.session_state.refresh}")

        if archivos:
            st.info(f"Seleccionados: {len(archivos)} archivo(s)")

        st.markdown('<div class="usuario-button">', unsafe_allow_html=True)
        if st.button("ENVIAR A REVISIÓN", key="btn_usuario", use_container_width=True):
            if archivos:
                carpeta = f"reservas/pendientes/{area}"
                os.makedirs(carpeta, exist_ok=True)
                nombres = []
                for arch in archivos:
                    nombre_final = f"{int(time.time())}_{arch.name}"
                    nombres.append(arch.name)
                    with open(f"{carpeta}/{nombre_final}", "wb") as f:
                        f.write(arch.getbuffer())
                
                nuevo = {
                    "area": area,
                    "cantidad": len(archivos),
                    "archivos": nombres,
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.historial.append(nuevo)
                guardar_historial(st.session_state.historial)
                st.session_state.mensaje_envio = "✅ Archivos enviados con éxito al ingeniero."
                st.session_state.refresh += 1
                st.rerun()
            else:
                st.warning("⚠️ Por favor suba al menos un archivo PDF.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Nota: Aquí puedes expandir las vistas para 'ingeniero' y 'almacen'
    else:
        st.info(f"Panel de control para rol: **{rol}** en desarrollo.")
