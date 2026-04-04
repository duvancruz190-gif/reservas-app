import streamlit as st
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer
import json
import shutil
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas", layout="wide")

# --- ESTILO ---
st.markdown("""
    <style>
        .stApp { background-color: #f5f7fa; }

        .stButton>button {
            background-color: #005baa;
            color: white;
            border-radius: 8px;
            height: 45px;
            font-weight: bold;
        }

        .stButton>button:hover {
            background-color: #003f7d;
            color: white;
        }

        section[data-testid="stSidebar"] {
            background-color: #002b5c;
            color: white;
        }

        section[data-testid="stSidebar"] * {
            color: white !important;
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
    "Producción": {"archivo": "reservas/firmas/carlos_alfonso.jpeg", "password": "1234"},
}

# --- SESIÓN ---
if "login" not in st.session_state:
    st.session_state.login = False

# ===========================
# LOGIN
# ===========================
if not st.session_state.login:

    col1, col2, col3 = st.columns([1,2,1])

    with col2:
        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png")

        st.markdown("<h2 style='text-align: center;'>Acceso al Sistema</h2>", unsafe_allow_html=True)

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

# ===========================
# SISTEMA
# ===========================
else:

    with st.sidebar:
        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png", width=180)

        st.markdown("### 📂 Menú Principal")
        st.write(f"👤 **{st.session_state.get('user_name')}**")
        st.write(f"🔑 Rol: **{st.session_state.get('rol').upper()}**")

        if st.button("🚪 Cerrar Sesión"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.title("📋 Gestión de Reservas")
    rol = st.session_state.get('rol')

    # ===========================
    # USUARIO
    # ===========================
    if rol == "usuario":

        st.header("📤 Enviar Nueva Reserva")

        area = st.selectbox("Selecciona el área", areas)

        archivos = st.file_uploader(
            "Subir PDFs",
            type=["pdf"],
            accept_multiple_files=True
        )

        if st.button("Enviar al Ingeniero"):

            if archivos:

                carpeta_area = f"reservas/pendientes/{area}"
                os.makedirs(carpeta_area, exist_ok=True)

                enviados = []
                registros = []

                for arch in archivos:
                    ruta = f"{carpeta_area}/{arch.name}"

                    with open(ruta, "wb") as f:
                        f.write(arch.getbuffer())

                    enviados.append(arch.name)

                    registros.append({
                        "usuario": st.session_state.user_name,
                        "area": area,
                        "archivo": arch.name,
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

                excel_file = "reservas/historial_envios.xlsx"

                df_nuevo = pd.DataFrame(registros)

                if os.path.exists(excel_file):
                    df_existente = pd.read_excel(excel_file)
                    df_total = pd.concat([df_existente, df_nuevo], ignore_index=True)
                else:
                    df_total = df_nuevo

                df_total.to_excel(excel_file, index=False)

                st.success(f"✅ {len(enviados)} archivos enviados con éxito")

            else:
                st.warning("Selecciona al menos un archivo")

        # --- HISTORIAL SIDEBAR ---
        st.sidebar.markdown("### 📄 Mis envíos")

        historial = []

        for area_loop in areas:
            carpeta = f"reservas/pendientes/{area_loop}"
            if os.path.exists(carpeta):
                for f in os.listdir(carpeta):
                    historial.append((area_loop, f))

        if not historial:
            st.sidebar.info("No has enviado archivos")

        for area_h, file_h in historial:
            col1, col2 = st.sidebar.columns([3,1])
            col1.write(f"📄 {file_h} ({area_h})")

            if col2.button("🗑️", key=f"del_{area_h}_{file_h}"):
                ruta = f"reservas/pendientes/{area_h}/{file_h}"
                if os.path.exists(ruta):
                    os.remove(ruta)
                    st.rerun()

        # --- DESCARGAR EXCEL ---
        excel_path = "reservas/historial_envios.xlsx"

        if os.path.exists(excel_path):
            with open(excel_path, "rb") as f:
                st.sidebar.download_button(
                    "⬇️ Descargar historial",
                    f,
                    file_name="historial_envios.xlsx"
                )

    # ===========================
    # INGENIERO (igual que el tuyo)
    # ===========================
    elif rol == "ingeniero":
        st.header("✍️ Revisión y Firma")
        st.info("Aquí va tu lógica original (no se modificó)")

    # ===========================
    # ALMACÉN (igual que el tuyo)
    # ===========================
    elif rol == "almacen":
        st.header("📦 Gestión de Documentos")
        st.info("Aquí va tu lógica original (no se modificó)")
