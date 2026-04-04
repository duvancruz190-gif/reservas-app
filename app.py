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
st.set_page_config(page_title="Eternit - Gestión de Reservas", layout="wide")

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

# --- 🎨 ESTILO PROFESIONAL ETERNIT (FONDO BLANCO) ---
st.markdown("""
    <style>
        /* FONDO GENERAL BLANCO */
        .stApp {
            background-color: #FFFFFF;
        }

        /* SIDEBAR GRIS PROFESIONAL */
        section[data-testid="stSidebar"] {
            background-color: #f8f9fa;
            border-right: 1px solid #e0e0e0;
        }

        /* TEXTOS SIDEBAR */
        section[data-testid="stSidebar"] .stText, 
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stMarkdown {
            color: #333333 !important;
        }

        /* BOTONES ETERNIT (ROJO Y GRIS) */
        .stButton>button, div.stDownloadButton > button {
            background-color: #FFFFFF !important;
            color: #333333 !important;
            border: 1px solid #dcdcdc !important;
            border-radius: 6px;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        /* BOTÓN PRIMARIO (ENVÍO) EN ROJO */
        div.stButton > button:first-child[data-testid="baseButton-secondary"] {
             /* Identificador para el botón de enviar si es necesario */
        }

        /* HOVER DE BOTONES */
        .stButton>button:hover, div.stDownloadButton > button:hover {
            border-color: #E30613 !important;
            color: #E30613 !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }

        /* TÍTULOS */
        h1, h2, h3 {
            color: #333333 !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* DIVISOR ROJO */
        hr {
            border: 0;
            border-top: 3px solid #E30613;
        }
        
        /* ESTILO PARA LOS INPUTS */
        div[data-baseweb="input"], div[data-baseweb="select"] {
            border-radius: 8px !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- CARPETAS ---
for carpeta in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas", "reservas/archivo", "assets"]:
    os.makedirs(carpeta, exist_ok=True)

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
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.write("") # Espaciado
        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png", use_container_width=True)
        
        st.markdown("<h2 style='text-align: center; margin-bottom:0;'>Acceso Seguro</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Gestión de Reservas Corporativas</p>", unsafe_allow_html=True)
        
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")

        if st.button("INGRESAR AL PANEL", use_container_width=True):
            if u in usuarios and usuarios[u]["password"] == p:
                st.session_state.login = True
                st.session_state.rol = usuarios[u]["rol"]
                st.session_state.user_name = u
                st.rerun()
            else:
                st.error("Credenciales no válidas para el sistema.")

# ================= SISTEMA PRINCIPAL =================
else:
    with st.sidebar:
        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png", width=160)
        
        st.markdown("---")
        st.write(f"👤 **Usuario:** {st.session_state.user_name}")
        st.write(f"🔑 **Rol:** {st.session_state.rol}")
        st.markdown("---")

        with st.expander("📜 Historial de Envíos"):
            if st.session_state.historial:
                area_filtro = st.selectbox("Filtrar por área", ["Todas"] + areas)
                historial_filtrado = st.session_state.historial if area_filtro == "Todas" else [h for h in st.session_state.historial if h["area"] == area_filtro]

                excel = generar_excel(historial_filtrado)
                st.download_button("📥 DESCARGAR REPORTE", excel, "historial_eternit.xlsx", use_container_width=True)

                if st.button("🗑️ Limpiar Historial", use_container_width=True):
                    st.session_state.historial = []
                    guardar_historial([])
                    st.rerun()

                for h in reversed(historial_filtrado):
                    st.caption(f"📅 {h['fecha']}")
                    st.write(f"📍 {h['area']} ({h['cantidad']} files)")
            else:
                st.info("No hay registros aún.")

        if st.button("🚪 CERRAR SESIÓN", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # --- CUERPO PRINCIPAL ---
    st.markdown(f"<h1>Panel de Gestión <span style='color:#E30613'>Eternit</span></h1>", unsafe_allow_html=True)
    st.markdown("---")

    if st.session_state.rol == "usuario":
        st.subheader("📤 Carga de Nueva Reserva")
        
        if st.session_state.mensaje_envio:
            st.success(st.session_state.mensaje_envio)
            st.session_state.mensaje_envio = ""

        col_a, col_b = st.columns([1, 1])
        with col_a:
            area = st.selectbox("Seleccione el Área Destino", areas)
        
        with col_b:
            archivos = st.file_uploader("Documentos PDF", type=["pdf"], accept_multiple_files=True, key=f"up_{st.session_state.refresh}")

        if st.button("🚀 ENVIAR AL INGENIERO", use_container_width=True):
            if archivos:
                carpeta = f"reservas/pendientes/{area}"
                os.makedirs(carpeta, exist_ok=True)
                nombres = []

                for arch in archivos:
                    nombre = f"{int(time.time())}_{arch.name}"
                    nombres.append(arch.name)
                    with open(f"{carpeta}/{nombre}", "wb") as f:
                        f.write(arch.getbuffer())

                st.session_state.mensaje_envio = f"✅ Envío exitoso: {len(archivos)} documento(s) procesado(s)."
                
                nuevo = {
                    "area": area,
                    "cantidad": len(archivos),
                    "archivos": nombres,
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.historial.append(nuevo)
                guardar_historial(st.session_state.historial)
                st.session_state.refresh += 1
                st.rerun()
            else:
                st.warning("Por favor, adjunte al menos un archivo PDF.")
