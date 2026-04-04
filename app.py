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

# --- CARPETAS ---
for carpeta in [
    "reservas/pendientes",
    "reservas/firmadas",
    "reservas/firmas",
    "reservas/archivo",
    "reservas/enviados",   # historial seguro
    "reservas/rechazados", # rechazados
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

if "pagina" not in st.session_state:
    st.session_state.pagina = "principal"

# ================= LOGIN =================
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

# ================= SISTEMA =================
else:

    # --- SIDEBAR ---
    with st.sidebar:

        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png", width=180)

        st.markdown("### 📂 Menú Principal")
        st.write(f"👤 **{st.session_state.get('user_name')}**")
        st.write(f"🔑 Rol: **{st.session_state.get('rol').upper()}**")

        st.markdown("---")

        if st.button("📄 Historial"):
            st.session_state.pagina = "historial"
            st.rerun()

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

        # -------- ENVÍO --------
        if st.session_state.pagina == "principal":

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

                    carpeta_pend = f"reservas/pendientes/{area}"
                    carpeta_hist = f"reservas/enviados/{area}"

                    os.makedirs(carpeta_pend, exist_ok=True)
                    os.makedirs(carpeta_hist, exist_ok=True)

                    for arch in archivos:
                        data = arch.getbuffer()

                        # flujo real
                        with open(f"{carpeta_pend}/{arch.name}", "wb") as f:
                            f.write(data)

                        # historial
                        with open(f"{carpeta_hist}/{arch.name}", "wb") as f:
                            f.write(data)

                    st.success(f"✅ {len(archivos)} archivos enviados")

                    st.session_state.upload_key += 1
                    st.rerun()

                else:
                    st.warning("Selecciona archivos")

        # -------- HISTORIAL --------
        elif st.session_state.pagina == "historial":

            st.title("📄 Historial de Reservas")

            if st.button("⬅️ Volver"):
                st.session_state.pagina = "principal"
                st.rerun()

            area_sel = st.selectbox("Filtrar por área", ["Todas"] + areas)

            archivos_totales = []

            if area_sel == "Todas":
                for a in areas:
                    carpeta = f"reservas/enviados/{a}"
                    if os.path.exists(carpeta):
                        for f in os.listdir(carpeta):
                            archivos_totales.append((a, f))
            else:
                carpeta = f"reservas/enviados/{area_sel}"
                if os.path.exists(carpeta):
                    for f in os.listdir(carpeta):
                        archivos_totales.append((area_sel, f))

            if not archivos_totales:
                st.info("No hay archivos")
            else:

                st.write(f"📄 Total: {len(archivos_totales)}")

                if st.button("🧹 Borrar todos"):
                    for a, f in archivos_totales:
                        os.remove(f"reservas/enviados/{a}/{f}")
                    st.success("Todos eliminados")
                    st.rerun()

                st.markdown("---")

                for a, f in archivos_totales:

                    col1, col2 = st.columns([6,1])
                    col1.write(f"📄 {f} ({a})")

                    if col2.button("🗑️", key=f"{a}_{f}"):
                        os.remove(f"reservas/enviados/{a}/{f}")
                        st.rerun()

        # -------- RECHAZADOS --------
        st.markdown("## 📛 Archivos Rechazados")

        for a in areas:
            carpeta = f"reservas/rechazados/{a}"

            if os.path.exists(carpeta):
                for f in os.listdir(carpeta):

                    if f.endswith(".pdf"):

                        ruta_json = f"{carpeta}/{f}.json"
                        motivo = "Sin motivo"

                        if os.path.exists(ruta_json):
                            with open(ruta_json) as ff:
                                motivo = json.load(ff)["motivo"]

                        st.warning(f"{f} ({a})")
                        st.write(f"Motivo: {motivo}")

    # ===========================
    # INGENIERO (INTOCADO + RECHAZO)
    # ===========================
    elif rol == "ingeniero":

        st.header("✍️ Revisión y Firma")

        area = st.selectbox("Selecciona el área", areas)
        carpeta_area = f"reservas/pendientes/{area}"
        pendientes = os.listdir(carpeta_area) if os.path.exists(carpeta_area) else []

        for arc in pendientes:

            with st.expander(f"📄 {arc}"):

                ruta_full = f"{carpeta_area}/{arc}"

                pdf_viewer(ruta_full, width=1000, height=800)

                contra_firma = st.text_input("Contraseña de firma", type="password", key=f"pw_{arc}")

                if st.button("🖋️ Firmar y enviar", key=f"btn_{arc}"):

                    if area in firmas_contrasena:

                        info_firma = firmas_contrasena[area]

                        if contra_firma == info_firma["password"]:

                            carpeta_firmadas = f"reservas/firmadas/{area}"
                            os.makedirs(carpeta_firmadas, exist_ok=True)

                            shutil.move(ruta_full, f"{carpeta_firmadas}/{arc}")

                            st.success("Firmado correctamente")
                            st.rerun()

                        else:
                            st.error("Contraseña incorrecta")

                # RECHAZO
                st.write("---")
                motivo = st.text_input("Motivo rechazo", key=f"mot_{arc}")

                if st.button("❌ Rechazar", key=f"rech_{arc}"):

                    if motivo:

                        carpeta_rech = f"reservas/rechazados/{area}"
                        os.makedirs(carpeta_rech, exist_ok=True)

                        shutil.move(ruta_full, f"{carpeta_rech}/{arc}")

                        with open(f"{carpeta_rech}/{arc}.json", "w") as f:
                            json.dump({"motivo": motivo}, f)

                        st.error("Documento rechazado")
                        st.rerun()

    # ===========================
    # ALMACÉN (IGUAL)
    # ===========================
    elif rol == "almacen":
        st.header("📦 Gestión de Documentos")
        st.info("Tu lógica original sigue aquí")
