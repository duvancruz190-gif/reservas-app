import streamlit as st
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer
import json
import shutil
import pandas as pd

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas", layout="wide")

# --- ESTILO EMPRESARIAL ---
st.markdown("""
    <style>
        .stApp {
            background-color: #f5f7fa;
        }

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

        .stTextInput>div>div>input {
            border-radius: 8px;
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

# --- CREAR CARPETAS ---
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
        st.caption("Gestión de Reservas - Eternit Colombiana")

        st.markdown("---")

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

    # --- SIDEBAR ---
    with st.sidebar:

        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png", width=180)

        st.markdown("### 📂 Menú Principal")
        st.write(f"👤 *{st.session_state.get('user_name')}*")
        st.write(f"🔑 Rol: *{st.session_state.get('rol').upper()}*")

        st.markdown("---")

        if st.button("🚪 Cerrar Sesión", use_container_width=True):
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

        # --- Subir varios archivos ---
        archivos = st.file_uploader(
            "Subir PDF(s)",
            type=["pdf"],
            accept_multiple_files=True
        )

        if st.button("Enviar al Ingeniero"):
            if archivos:
                carpeta_area = f"reservas/pendientes/{area}"
                os.makedirs(carpeta_area, exist_ok=True)

                for arch in archivos:
                    with open(f"{carpeta_area}/{arch.name}", "wb") as f:
                        f.write(arch.getbuffer())

                st.success(f"✅ Documento(s) enviado(s): {len(archivos)} archivo(s).")
            else:
                st.warning("Selecciona al menos un archivo.")

        # ===========================
        # Historial del usuario
        # ===========================
        st.sidebar.header("🕒 Historial de Envíos")

        area_hist = st.sidebar.selectbox("Filtrar por área", ["Todos"] + areas)

        historial = []
        base_path = "reservas/pendientes"
        for a in areas:
            carpeta_area = f"{base_path}/{a}"
            if os.path.exists(carpeta_area):
                for f_name in os.listdir(carpeta_area):
                    if area_hist == "Todos" or area_hist == a:
                        historial.append({"Área": a, "Archivo": f_name, "Ruta": f"{carpeta_area}/{f_name}"})

        if historial:
            df_hist = pd.DataFrame(historial)
            for idx, row in df_hist.iterrows():
                with st.sidebar.expander(f"{row['Archivo']} ({row['Área']})"):
                    col1, col2, col3 = st.columns([4,1,1])
                    col1.write(row['Archivo'])
                    with open(row['Ruta'], "rb") as file:
                        col2.download_button("⬇️", file, file_name=row['Archivo'])
                    if col3.button("🗑️", key=f"del_{row['Ruta']}"):
                        os.remove(row['Ruta'])
                        st.rerun()  # refresca el historial al borrar

            # Descargar historial completo en Excel
            excel_df = df_hist.drop(columns=["Ruta"])
            excel_path = "historial.xlsx"
            excel_df.to_excel(excel_path, index=False)
            with open(excel_path, "rb") as f:
                st.sidebar.download_button("📥 Descargar Historial Excel", f, file_name="historial.xlsx")
        else:
            st.sidebar.info("No hay envíos registrados.")

    # ===========================
    # INGENIERO
    # ===========================
    elif rol == "ingeniero":
        # Aquí va tu código original del ingeniero
        pass

    # ===========================
    # ALMACÉN
    # ===========================
    elif rol == "almacen":
        # Aquí va tu código original de almacén
        pass
