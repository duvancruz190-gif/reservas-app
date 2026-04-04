import streamlit as st 
import os
import json
import time
from datetime import datetime
import pandas as pd
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
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

# --- ESTADOS DE SESIÓN ---
if "refresh" not in st.session_state:
    st.session_state.refresh = 0
if "mensaje_envio" not in st.session_state:
    st.session_state.mensaje_envio = ""
if "historial" not in st.session_state:
    st.session_state.historial = cargar_historial()

# --- 🎨 ESTILO PROFESIONAL (FONDO BLANCO + TIPOGRAFÍA OSWALD) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&display=swap');

        /* FONDO BLANCO */
        .stApp {
            background-color: #FFFFFF;
        }

        /* TÍTULOS PROFESIONALES */
        h1, h2, h3 {
            font-family: 'Oswald', sans-serif !important;
            color: #333333 !important;
            text-transform: uppercase;
        }

        /* SIDEBAR GRIS SUAVE */
        section[data-testid="stSidebar"] {
            background-color: #F8F9FA !important;
            border-right: 1px solid #E0E0E0;
        }

        /* BOTONES ETERNIT */
        .stButton>button, div.stDownloadButton > button {
            background-color: #FFFFFF !important;
            color: #333333 !important;
            border: 1px solid #DCDCDC !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease;
        }

        .stButton>button:hover {
            border-color: #E30613 !important;
            color: #E30613 !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        }

        /* LÍNEA DE ACENTO ROJO */
        .divider-red {
            height: 4px;
            background-color: #E30613;
            margin-bottom: 20px;
            border-radius: 2px;
        }
    </style>
""", unsafe_allow_html=True)

# --- CARPETAS ---
for carpeta in ["reservas/pendientes", "assets"]:
    os.makedirs(carpeta, exist_ok=True)

areas = ["Producción", "Calidad", "Mantenimiento", "Logística", "Recursos Humanos", "Financiera", "Almacén"]
usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"}
}

# --- LOGIN ---
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.write("") 
        # Usamos tu archivo local para que no falle
        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png", use_container_width=True)
        
        st.markdown("<h2 style='text-align: center;'>ACCESO PRIVADO</h2>", unsafe_allow_html=True)
        
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")

        if st.button("INGRESAR AL SISTEMA", use_container_width=True):
            if u in usuarios and usuarios[u]["password"] == p:
                st.session_state.login = True
                st.session_state.rol = usuarios[u]["rol"]
                st.session_state.user_name = u
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

# ================= PANEL PRINCIPAL =================
else:
    with st.sidebar:
        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png", width=160)
        st.markdown("<div class='divider-red'></div>", unsafe_allow_html=True)
        
        st.write(f"👤 **Usuario:** {st.session_state.user_name}")
        st.write(f"🔑 **Rol:** {st.session_state.rol}")
        
        st.markdown("---")
        with st.expander("📜 HISTORIAL DE ENVÍOS"):
            if st.session_state.historial:
                area_f = st.selectbox("Filtrar Área", ["Todas"] + areas)
                hist_f = st.session_state.historial if area_f == "Todas" else [h for h in st.session_state.historial if h["area"] == area_f]
                
                excel = generar_excel(hist_f)
                st.download_button("📥 DESCARGAR REPORTE", excel, "reporte_eternit.xlsx", use_container_width=True)
                
                for h in reversed(hist_f):
                    st.caption(f"📅 {h['fecha']}")
                    st.write(f"📍 {h['area']} ({h['cantidad']} Docs)")
            else:
                st.info("No hay envíos registrados.")

        if st.button("🚪 CERRAR SESIÓN", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # --- CONTENIDO ---
    st.markdown("<h1>Panel de Gestión <span style='color:#E30613'>Eternit</span></h1>", unsafe_allow_html=True)
    st.markdown("<div class='divider-red'></div>", unsafe_allow_html=True)

    if st.session_state.rol == "usuario":
        st.subheader("📥 Carga de Nueva Reserva")
        
        if st.session_state.mensaje_envio:
            st.success(st.session_state.mensaje_envio)
            st.session_state.mensaje_envio = ""

        c1, c2 = st.columns(2)
        with c1:
            area_sel = st.selectbox("Área Destino", areas)
        with c2:
            archivos = st.file_uploader("Subir PDF(s)", type=["pdf"], accept_multiple_files=True, key=f"up_{st.session_state.refresh}")

        if st.button("🚀 ENVIAR AL INGENIERO", use_container_width=True):
            if archivos:
                path = f"reservas/pendientes/{area_sel}"
                os.makedirs(path, exist_ok=True)
                nombres = [a.name for a in archivos]

                for a in archivos:
                    fname = f"{int(time.time())}_{a.name}"
                    with open(f"{path}/{fname}", "wb") as f:
                        f.write(a.getbuffer())

                st.session_state.mensaje_envio = f"✅ ¡Enviado con éxito!"
                
                nuevo = {
                    "area": area_sel, "cantidad": len(archivos),
                    "archivos": nombres, "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                st.session_state.historial.append(nuevo)
                guardar_historial(st.session_state.historial)
                st.session_state.refresh += 1
                st.rerun()
            else:
                st.warning("Por favor suba un archivo.")
