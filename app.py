import streamlit as st
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer
import json
import shutil

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
            padding: 10px;
        }

        section[data-testid="stSidebar"] * {
            color: white !important;
        }

        .historial-item {
            background-color: #003f7d;
            padding: 6px;
            border-radius: 6px;
            margin-bottom: 4px;
        }
    </style>
""", unsafe_allow_html=True)

# --- CREAR CARPETAS ---
for carpeta in [
    "reservas/pendientes",
    "reservas/firmadas",
    "reservas/firmas",
    "reservas/archivo",
    "reservas/historial",
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

    rol = st.session_state.get('rol')

    # ===========================
    # USUARIO
    # ===========================
    if rol == "usuario":

        # --- BARRA LATERAL ---
        with st.sidebar:
            if os.path.exists("assets/ETERNITTTTT.png"):
                st.image("assets/ETERNITTTTT.png", width=180)

            st.markdown("### 📜 Historial de Reservas")
            st.write(f"👤 Usuario: *{st.session_state.get('user_name')}*")
            st.write(f"🔑 Rol: *{st.session_state.get('rol').upper()}*")
            st.markdown("---")

            # Cargar historial
            historial_file = "reservas/historial_usuario.json"
            if os.path.exists(historial_file):
                with open(historial_file, "r") as f:
                    historial = json.load(f)
            else:
                historial = []

            # Filtros
            filtro_area = st.selectbox("Filtrar por área", ["Todas"] + areas)
            busqueda_nombre = st.text_input("Buscar por nombre de archivo")

            # Filtrar historial
            filtrados = [
                item for item in historial
                if (filtro_area == "Todas" or item["area"] == filtro_area)
                and (busqueda_nombre.lower() in item["nombre"].lower())
            ]

            # Mostrar historial
            st.markdown("#### 🔹 Resultados")
            if filtrados:
                for item in filtrados:
                    st.markdown(
                        f"<div class='historial-item'><b>{item['nombre']}</b> ({item['area']})</div>",
                        unsafe_allow_html=True
                    )
            else:
                st.info("No hay documentos para mostrar.")

            # Botones estilo profesional
            if st.button("🗑️ Eliminar historial mostrado"):
                historial = [item for item in historial if item not in filtrados]
                with open(historial_file, "w") as f:
                    json.dump(historial, f)
                st.success("✅ Historial eliminado correctamente")
                st.experimental_rerun()

            if st.button("🚪 Cerrar Sesión"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        # --- CUERPO PRINCIPAL ---
        st.title("📤 Enviar Nueva Reserva (Masiva)")

        st.markdown(
            "<p style='color:#003f7d;font-weight:bold;'>Seleccione un área y los archivos PDF que desea enviar al ingeniero.</p>",
            unsafe_allow_html=True
        )

        area = st.selectbox("Selecciona el área", areas)
        archivos = st.file_uploader("Subir PDFs", type=["pdf"], accept_multiple_files=True)

        if st.button("📤 Enviar al Ingeniero"):
            if archivos:
                carpeta_area = f"reservas/pendientes/{area}"
                os.makedirs(carpeta_area, exist_ok=True)

                enviados = 0
                for arch in archivos:
                    with open(f"{carpeta_area}/{arch.name}", "wb") as f:
                        f.write(arch.getbuffer())
                    enviados += 1

                st.success(f"✅ Se enviaron {enviados} archivo(s) a {area}.")

                # Guardar historial
                if os.path.exists(historial_file):
                    with open(historial_file, "r") as f:
                        historial = json.load(f)
                else:
                    historial = []

                for arch in archivos:
                    historial.append({"nombre": arch.name, "area": area})
                with open(historial_file, "w") as f:
                    json.dump(historial, f)

                st.info("Puede consultar su historial en la barra lateral.")

            else:
                st.warning("⚠️ Seleccione al menos un archivo PDF.")

    # ===========================
    # INGENIERO Y ALMACÉN (sin cambios)
    # ===========================
    else:
        st.info("Módulo de Ingeniero o Almacén se mantiene igual que antes.")
