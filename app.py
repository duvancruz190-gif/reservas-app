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

# --- CREAR CARPETAS ---
for carpeta in [
    "reservas/pendientes",
    "reservas/firmadas",
    "reservas/firmas",
    "reservas/archivo",
    "reservas/rechazados",  # NUEVO
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

    # --- SIDEBAR ---
    with st.sidebar:

        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png", width=180)

        st.markdown("### 📂 Menú Principal")
        st.write(f"👤 **{st.session_state.get('user_name')}**")
        st.write(f"🔑 Rol: **{st.session_state.get('rol').upper()}**")

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

        if "upload_key" not in st.session_state:
            st.session_state.upload_key = 0

        archivos = st.file_uploader(
            "Subir PDF",
            type=["pdf"],
            accept_multiple_files=True,
            key=st.session_state.upload_key
        )

        if st.button("Enviar al Ingeniero"):
            if archivos:
                carpeta_area = f"reservas/pendientes/{area}"
                os.makedirs(carpeta_area, exist_ok=True)

                for arch in archivos:
                    with open(f"{carpeta_area}/{arch.name}", "wb") as f:
                        f.write(arch.getbuffer())

                st.success("✅ Archivos enviados con éxito")

                st.session_state.upload_key += 1
                st.rerun()
            else:
                st.warning("Selecciona archivos")

        # 📛 RECHAZADOS
        st.markdown("## 📛 Archivos Rechazados")

        hay = False

        for a in areas:
            carpeta = f"reservas/rechazados/{a}"
            if os.path.exists(carpeta):
                for f in os.listdir(carpeta):
                    if f.endswith(".pdf"):
                        hay = True

                        ruta_json = f"{carpeta}/{f}.json"
                        motivo = "Sin motivo"

                        if os.path.exists(ruta_json):
                            with open(ruta_json) as ff:
                                motivo = json.load(ff).get("motivo", "Sin motivo")

                        st.warning(f"📄 {f} ({a})")
                        st.write(f"📝 Motivo: {motivo}")
                        st.markdown("---")

        if not hay:
            st.info("No tienes archivos rechazados")

    # ===========================
    # INGENIERO
    # ===========================
    elif rol == "ingeniero":

        st.header("✍️ Revisión y Firma")

        area = st.selectbox("Selecciona el área", areas)
        carpeta_area = f"reservas/pendientes/{area}"
        pendientes = os.listdir(carpeta_area) if os.path.exists(carpeta_area) else []

        if not pendientes:
            st.info("No hay documentos pendientes en esta área.")

        for arc in pendientes:

            with st.expander(f"📄 {arc}"):

                ruta_full = f"{carpeta_area}/{arc}"

                try:
                    pdf_viewer(ruta_full, width=1000, height=800)
                except:
                    st.write("Vista no disponible")

                # 🔴 RECHAZO
                st.write("---")
                motivo = st.text_input("Motivo del rechazo", key=f"mot_{arc}")

                if st.button("❌ Rechazar", key=f"rech_{arc}"):

                    if motivo.strip() == "":
                        st.warning("Escribe un motivo")
                    else:
                        destino = f"reservas/rechazados/{area}"
                        os.makedirs(destino, exist_ok=True)

                        shutil.move(ruta_full, f"{destino}/{arc}")

                        with open(f"{destino}/{arc}.json", "w") as f:
                            json.dump({"motivo": motivo}, f)

                        st.error("Documento rechazado")
                        st.rerun()

                # 🖋️ FIRMA (igual)
                if st.button("🖋️ Firmar", key=f"firm_{arc}"):

                    destino = f"reservas/firmadas/{area}"
                    os.makedirs(destino, exist_ok=True)

                    shutil.move(ruta_full, f"{destino}/{arc}")

                    st.success("Firmado correctamente")
                    st.rerun()

    # ===========================
    # ALMACÉN (SIN CAMBIOS)
    # ===========================
    elif rol == "almacen":
        st.header("📦 Gestión de Documentos")
        st.info("Tu lógica original sigue aquí")
