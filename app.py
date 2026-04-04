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
                "Fecha": h["fecha"], "Área": h["area"],
                "Archivo": archivo, "Cantidad": 1, "Total envío": h["cantidad"]
            })
    df = pd.DataFrame(datos)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Historial')
    return output.getvalue()

# --- ESTADOS ---
if "refresh" not in st.session_state: st.session_state.refresh = 0
if "mensaje_envio" not in st.session_state: st.session_state.mensaje_envio = ""
if "historial" not in st.session_state: st.session_state.historial = cargar_historial()

# --- 🎨 ESTILO EXACTO A TU IMAGEN (PROFESIONAL) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

        /* FONDO BLANCO PURO */
        .stApp {
            background-color: #FFFFFF;
        }

        /* TIPOGRAFÍA GENERAL */
        * {
            font-family: 'Inter', sans-serif;
        }

        /* TÍTULOS LOGIN */
        .login-title {
            color: #2C3E50;
            font-size: 32px;
            font-weight: 600;
            text-align: center;
            margin-top: 20px;
            margin-bottom: 5px;
        }
        
        .login-subtitle {
            color: #95A5A6;
            font-size: 14px;
            text-align: center;
            margin-bottom: 30px;
        }

        /* INPUTS GRISES COMO EN TU IMAGEN */
        div[data-baseweb="input"] {
            background-color: #F0F2F6 !important;
            border: none !important;
            border-radius: 8px !important;
        }

        /* BOTÓN AZUL (IGUAL A TU IMAGEN) */
        .stButton>button {
            background-color: #005CAA !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            height: 45px;
            font-weight: 600;
            width: 100%;
            transition: 0.3s;
        }

        .stButton>button:hover {
            background-color: #004485 !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }

        /* SIDEBAR PROFESIONAL */
        section[data-testid="stSidebar"] {
            background-color: #F8F9FA !important;
            border-right: 1px solid #E0E0E0;
        }

        /* LÍNEA DE ACENTO ETERNIT */
        .line-accent {
            height: 3px;
            background: linear-gradient(to right, #E30613, #333);
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# --- CARPETAS ---
for carpeta in ["reservas/pendientes", "assets"]: os.makedirs(carpeta, exist_ok=True)

areas = ["Producción", "Calidad", "Mantenimiento", "Logística", "Financiera", "Almacén"]
usuarios = {"usuario": {"password": "123", "rol": "usuario"}, "ingeniero": {"password": "999", "rol": "ingeniero"}}

# --- LOGIN ---
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.write("") 
        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png", use_container_width=True)
        
        st.markdown("<div class='login-title'>Acceso al Sistema</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-subtitle'>Gestión de Reservas - Eternit Colombiana</div>", unsafe_allow_html=True)
        
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")

        st.write("")
        if st.button("Ingresar", use_container_width=True):
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
        st.markdown("<div class='line-accent'></div>", unsafe_allow_html=True)
        
        st.write(f"👤 **Usuario:** {st.session_state.user_name}")
        st.write(f"🔑 **Rol:** {st.session_state.rol}")
        
        st.markdown("---")
        with st.expander("📜 HISTORIAL DE ENVÍOS"):
            if st.session_state.historial:
                area_f = st.selectbox("Filtrar Área", ["Todas"] + areas)
                hist_f = st.session_state.historial if area_f == "Todas" else [h for h in st.session_state.historial if h["area"] == area_f]
                
                excel = generar_excel(hist_f)
                st.download_button("📥 DESCARGAR REPORTE", excel, "reporte_eternit.xlsx")
                
                for h in reversed(hist_f):
                    st.caption(f"📅 {h['fecha']}")
                    st.write(f"📍 {h['area']} ({h['cantidad']} Docs)")
            else:
                st.info("Sin registros.")

        if st.button("Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

    # --- CUERPO ---
    st.markdown(f"<h1>Panel de Gestión <span style='color:#E30613'>Eternit</span></h1>", unsafe_allow_html=True)
    st.markdown("<div class='line-accent'></div>", unsafe_allow_html=True)

    if st.session_state.rol == "usuario":
        st.subheader("Carga de Nueva Reserva")
        
        if st.session_state.mensaje_envio:
            st.success(st.session_state.mensaje_envio)
            st.session_state.mensaje_envio = ""

        c1, c2 = st.columns(2)
        with c1:
            area_sel = st.selectbox("Área Destino", areas)
        with c2:
            archivos = st.file_uploader("Documentos PDF", type=["pdf"], accept_multiple_files=True, key=f"up_{st.session_state.refresh}")

        if st.button("Enviar al Ingeniero"):
            if archivos:
                path = f"reservas/pendientes/{area_sel}"
                os.makedirs(path, exist_ok=True)
                for a in archivos:
                    with open(f"{path}/{int(time.time())}_{a.name}", "wb") as f:
                        f.write(a.getbuffer())

                st.session_state.mensaje_envio = f"✅ ¡Enviado con éxito!"
                nuevo = {
                    "area": area_sel, "cantidad": len(archivos),
                    "archivos": [a.name for a in archivos], "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
                }
                st.session_state.historial.append(nuevo)
                guardar_historial(st.session_state.historial)
                st.session_state.refresh += 1
                st.rerun()
            else:
                st.warning("Adjunte archivos.")
