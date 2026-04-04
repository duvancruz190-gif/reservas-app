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

# --- 🎨 ESTILO LIMPIO Y PROFESIONAL ---
st.markdown("""
    <style>
        /* FONDO GENERAL */
        .stApp {
            background-color: #f8f8f8;
            color: #333;
        }

        /* SIDEBAR */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            color: #333 !important;
        }

        /* BOTONES */
        .stButton>button,
        div.stDownloadButton > button {
            background-color: #d21b28 !important; /* rojo corporativo Eternit */
            color: white !important;
            border-radius: 8px;
            height: 45px;
            font-weight: bold;
            border: 2px solid #b51724;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
        }
        .stButton>button:hover,
        div.stDownloadButton > button:hover {
            background-color: #b51724 !important;
            transform: translateY(-1px);
        }

        /* EXPANDERS */
        .streamlit-expanderHeader {
            background-color: #f0f0f0 !important;
            color: #333 !important;
            border-radius: 6px;
            font-weight: bold;
        }
        .streamlit-expanderContent {
            background-color: #fff !important;
            border-radius: 6px;
        }

        /* SELECTBOX */
        div[data-baseweb="select"] > div {
            background-color: #fff !important;
            color: #333 !important;
            border: 1px solid #d21b28 !important;
            border-radius: 8px;
        }
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] input {
            color: #333 !important;
        }

        /* LISTBOX */
        ul[role="listbox"] {
            background-color: #fff !important;
        }
        li[role="option"] {
            background-color: #fff !important;
            color: #333 !important;
        }
        li[role="option"]:hover {
            background-color: #d21b28 !important;
            color: white !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #333;
        }

        img {
            max-width: 100%;
            height: auto;
            object-fit: contain;
        }
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

# --- FIRMAS ---
firmas_contrasena = {
    "Producción": {"archivo": "reservas/firmas/Imagen1.png", "password": "1234"},
    "Logística": {"archivo": "reservas/firmas/LogisticaRojas.png", "password": "5678"},
}

# --- LOGIN UNIFICADO ---
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        # Logo limpio uniforme para todos
        if os.path.exists("assets/ETERNIT_LOGO_LIMPIO.png"):
            st.image("assets/ETERNIT_LOGO_LIMPIO.png", width=250)

        st.markdown("<h2 style='text-align: center;'>Acceso al Sistema</h2>", unsafe_allow_html=True)
        st.caption("Gestión de Reservas - Eternit Colombiana")

        usuario_input = st.text_input("Usuario")
        contrasena_input = st.text_input("Contraseña", type="password")

        if st.button("Ingresar", use_container_width=True):
            if usuario_input in usuarios and usuarios[usuario_input]["password"] == contrasena_input:
                st.session_state.login = True
                st.session_state.rol = usuarios[usuario_input]["rol"]
                st.session_state.user_name = usuario_input
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

# ================= SISTEMA =================
else:

    with st.sidebar:
        # Logo limpio en sidebar
        if os.path.exists("assets/ETERNIT_LOGO_LIMPIO.png"):
            st.image("assets/ETERNIT_LOGO_LIMPIO.png", width=200)
        st.write(f"👤 {st.session_state.user_name}")
        st.write(f"🔑 {st.session_state.rol}")

        with st.expander("📜 Historial de Envíos"):
            if st.session_state.historial:
                area_filtro = st.selectbox("Filtrar por área", ["Todas"] + areas)
                historial_filtrado = st.session_state.historial if area_filtro=="Todas" else [h for h in st.session_state.historial if h["area"]==area_filtro]
                excel = generar_excel(historial_filtrado)
                st.download_button("📥 Descargar Excel", excel, "historial.xlsx")
                if st.button("🗑️ Borrar historial"):
                    st.session_state.historial = []
                    guardar_historial([])
                    st.rerun()
                for h in reversed(historial_filtrado):
                    with st.expander(f"{h['fecha']} - {h['area']} ({h['cantidad']})"):
                        for nombre in h["archivos"]:
                            st.write(f"📄 {nombre}")

        if st.button("🚪 Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

    st.title("📋 Gestión de Reservas")

    if st.session_state.rol == "usuario":
        st.header("📤 Enviar Nueva Reserva")
        if st.session_state.mensaje_envio:
            st.success(st.session_state.mensaje_envio)
            st.session_state.mensaje_envio = ""
        area = st.selectbox("Área", areas)
        archivos = st.file_uploader(
            "Subir PDF(s)",
            type=["pdf"],
            accept_multiple_files=True,
            key=f"up_{st.session_state.refresh}"
        )
        if st.button("Enviar al Ingeniero"):
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
                st.session_state.mensaje_envio = f"✅ {cantidad} archivo(s) enviado(s)"
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
                st.warning("Sube archivo")
