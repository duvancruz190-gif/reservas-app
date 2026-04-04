import streamlit as st 
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer
import json
import shutil
import time
from datetime import datetime
import pandas as pd
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas", layout="wide")

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

# --- ESTILO ---
st.markdown("""
<style>
/* BARRA LATERAL COMPLETA AZUL */
section[data-testid="stSidebar"] {
    background-color: #002b5c !important;
    color: white !important;
}

/* Forzar color blanco en todos los textos de la sidebar */
section[data-testid="stSidebar"] * {
    color: white !important;
}

/* BOTONES DE LA SIDEBAR */
section[data-testid="stSidebar"] .stButton>button {
    background-color: #005baa !important;
    color: white !important;
    border-radius: 8px;
    height: 45px;
    font-weight: bold;
}

/* HOVER BOTONES SIDEBAR */
section[data-testid="stSidebar"] .stButton>button:hover {
    background-color: #003f7d !important;
}

/* BOTONES EXCEL DESCARGA EN SIDEBAR */
section[data-testid="stSidebar"] div.stDownloadButton > button {
    background-color: #005baa !important;
    color: white !important;
}

section[data-testid="stSidebar"] div.stDownloadButton > button:hover {
    background-color: #003f7d !important;
}

/* BOTONES USUARIO (CENTRO) GRIS */
div.usuario-button button {
    background-color: #d3d3d3 !important;
    color: black !important;
    font-weight: bold;
    border-radius: 8px;
    height: 45px;
}

div.usuario-button button:hover {
    background-color: #b0b0b0 !important;
}

/* INPUTS */
.stTextInput>div>div>input { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- CARPETAS ---
for carpeta in [
    "reservas/pendientes",
    "reservas/firmadas",
    "reservas/firmas",
    "reservas/archivo",
    "assets"
]:
    os.makedirs(carpeta, exist_ok=True)

# --- ÁREAS ---
areas = ["Producción", "Calidad", "Mantenimiento", "Logística",
         "Recursos Humanos", "Ambiental", "Salud Ocupacional",
         "Marketing", "Financiera", "Almacén"]

# --- USUARIOS ---
usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# --- LOGIN ---
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:

    col1, col2, col3 = st.columns([1,2,1])

    with col2:
        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png")

        st.markdown("<h2 style='text-align: center;'>Acceso al Sistema</h2>", unsafe_allow_html=True)
        st.caption("Gestión de Reservas - Eternit Colombiana")

        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")

        if st.button("Ingresar", use_container_width=True):
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
            st.image("assets/ETERNITTTTT.png", width=180)

        st.write(f"👤 {st.session_state.user_name}")
        st.write(f"🔑 {st.session_state.rol}")

        # HISTORIAL
        with st.expander("📜 Historial de Envíos"):

            if st.session_state.historial:

                area_filtro = st.selectbox("Filtrar por área", ["Todas"] + areas)

                if area_filtro == "Todas":
                    historial_filtrado = st.session_state.historial
                else:
                    historial_filtrado = [
                        h for h in st.session_state.historial if h["area"] == area_filtro
                    ]

                excel = generar_excel(historial_filtrado)
                st.download_button(
                    label="📥 Descargar Excel",
                    data=excel,
                    file_name="historial_envios.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                if st.button("🗑️ Borrar historial"):
                    st.session_state.historial = []
                    guardar_historial([])
                    st.rerun()

                for h in reversed(historial_filtrado):
                    with st.expander(f"{h['fecha']} - {h['area']} ({h['cantidad']})"):
                        for nombre in h["archivos"]:
                            st.write(f"📄 {nombre}")

            else:
                st.caption("Sin registros")

        if st.button("🚪 Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

    st.title("📋 Gestión de Reservas")
    rol = st.session_state.rol

    # ================= USUARIO =================
    if rol == "usuario":

        st.header("📤 Enviar Nueva Reserva")

        if st.session_state.mensaje_envio:
            st.success(st.session_state.mensaje_envio)
            st.session_state.mensaje_envio = ""

        area = st.selectbox("Área", areas)

        archivos = st.file_uploader(
            "Subir PDF(s)",
            type=["pdf"],
            accept_multiple_files=True,
            key=f"uploader_{st.session_state.refresh}"
        )

        if archivos:
            for a in archivos:
                st.write(f"📄 {a.name}")

        # BOTÓN USUARIO gris
        st.markdown('<div class="usuario-button">', unsafe_allow_html=True)
        if st.button("Enviar al Ingeniero", key="btn_usuario"):
            if archivos:
                carpeta = f"reservas/pendientes/{area}"
                os.makedirs(carpeta, exist_ok=True)

                nombres = []

                for arch in archivos:
                    nombre = f"{int(time.time())}_{arch.name}"
                    nombres.append(arch.name)
                    with open(f"{carpeta}/{nombre}", "wb") as f:
                        f.write(arch.getbuffer())

                cantidad = len(archivos)

                mensaje = "✅ 1 archivo enviado correctamente" if cantidad == 1 else f"✅ {cantidad} archivos enviados correctamente"
                st.session_state.mensaje_envio = mensaje

                nuevo = {
                    "area": area,
                    "cantidad": cantidad,
                    "archivos": nombres,
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                st.session_state.historial.append(nuevo)
                guardar_historial(st.session_state.historial)

                st.session_state.refresh += 1
                st.rerun()

            else:
                st.warning("Sube al menos un archivo")
        st.markdown('</div>', unsafe_allow_html=True)
