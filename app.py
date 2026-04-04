import streamlit as st
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer
import json
import shutil

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
}

section[data-testid="stSidebar"] {
    background-color: #002b5c;
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

        st.markdown("### 📂 Menú")
        st.write(f"👤 {st.session_state.user_name}")
        st.write(f"🔑 {st.session_state.rol}")

        st.markdown("---")

        # SOLO HISTORIAL
        if st.button("📄 Historial"):
            st.session_state.pagina = "historial"
            st.rerun()

        st.markdown("---")

        if st.button("🚪 Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

    rol = st.session_state.rol

    # ================= USUARIO =================
    if rol == "usuario":

        # -------- PANTALLA ENVIAR --------
        if st.session_state.pagina == "principal":

            st.title("📤 Enviar Reservas")

            area = st.selectbox("Selecciona el área", areas)

            if "upload_key" not in st.session_state:
                st.session_state.upload_key = 0

            archivos = st.file_uploader(
                "Subir PDFs",
                type=["pdf"],
                accept_multiple_files=True,
                key=st.session_state.upload_key
            )

            if st.button("Enviar al Ingeniero"):

                if archivos:

                    carpeta = f"reservas/pendientes/{area}"
                    os.makedirs(carpeta, exist_ok=True)

                    for arch in archivos:
                        with open(f"{carpeta}/{arch.name}", "wb") as f:
                            f.write(arch.getbuffer())

                    st.success(f"✅ {len(archivos)} archivos enviados con éxito")

                    st.session_state.upload_key += 1
                    st.rerun()

                else:
                    st.warning("Selecciona al menos un archivo")

        # -------- PANTALLA HISTORIAL --------
        elif st.session_state.pagina == "historial":

            st.title("📄 Historial de Reservas")

            if st.button("⬅️ Volver"):
                st.session_state.pagina = "principal"
                st.rerun()

            area_sel = st.selectbox("Filtrar por área", ["Todas"] + areas)

            archivos_totales = []

            if area_sel == "Todas":
                for a in areas:
                    carpeta = f"reservas/pendientes/{a}"
                    if os.path.exists(carpeta):
                        for f in os.listdir(carpeta):
                            archivos_totales.append((a, f))
            else:
                carpeta = f"reservas/pendientes/{area_sel}"
                if os.path.exists(carpeta):
                    for f in os.listdir(carpeta):
                        archivos_totales.append((area_sel, f))

            if not archivos_totales:
                st.info("No hay archivos")
            else:

                st.write(f"📄 Total: {len(archivos_totales)}")

                if st.button("🧹 Borrar todos"):
                    for a, f in archivos_totales:
                        os.remove(f"reservas/pendientes/{a}/{f}")
                    st.success("Todos eliminados")
                    st.rerun()

                st.markdown("---")

                for a, f in archivos_totales:

                    col1, col2 = st.columns([6,1])
                    col1.write(f"📄 {f} ({a})")

                    if col2.button("🗑️", key=f"{a}_{f}"):
                        os.remove(f"reservas/pendientes/{a}/{f}")
                        st.rerun()

    # ================= INGENIERO =================
    elif rol == "ingeniero":

        st.header("✍️ Revisión y Firma")

        colA, colB = st.columns([5,1])
        with colA:
            st.subheader("📂 Documentos pendientes")
        with colB:
            if st.button("🔄 Actualizar"):
                st.rerun()

        area = st.selectbox("Selecciona el área", areas)
        carpeta_area = f"reservas/pendientes/{area}"
        pendientes = os.listdir(carpeta_area) if os.path.exists(carpeta_area) else []

        if not pendientes:
            st.info("No hay documentos pendientes en esta área.")

        for arc in pendientes:

            with st.expander(f"📄 {arc}"):

                ruta_full = f"{carpeta_area}/{arc}"

                st.write("### Vista previa")
                try:
                    pdf_viewer(ruta_full, width=1000, height=800)
                except:
                    with open(ruta_full, "rb") as f:
                        st.download_button("Descargar PDF", f, file_name=arc)

                st.write("---")

                contra_firma = st.text_input("Contraseña de firma", type="password", key=f"pw_{arc}")

                if st.button("🖋️ Firmar y enviar", key=f"btn_{arc}"):

                    if area in firmas_contrasena:

                        info_firma = firmas_contrasena[area]

                        if contra_firma == info_firma["password"]:

                            if os.path.exists(info_firma["archivo"]):

                                doc = fitz.open(ruta_full)
                                pagina = doc[0]

                                pagina.insert_image(
                                    fitz.Rect(200, 700, 450, 800),
                                    filename=info_firma["archivo"]
                                )

                                carpeta_firmadas = f"reservas/firmadas/{area}"
                                os.makedirs(carpeta_firmadas, exist_ok=True)

                                doc.save(f"{carpeta_firmadas}/{arc}")
                                doc.close()

                                os.remove(ruta_full)

                                st.success("✅ Firmado correctamente")
                                st.rerun()
