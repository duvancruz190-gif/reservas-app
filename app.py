import streamlit as st
import os
import fitz
from streamlit_pdf_viewer import pdf_viewer
import json
import shutil

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
.stButton>button:hover { background-color: #003f7d; }
section[data-testid="stSidebar"] { background-color: #002b5c; }
section[data-testid="stSidebar"] * { color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- CARPETAS ---
for carpeta in [
    "reservas/pendientes","reservas/firmadas","reservas/firmas",
    "reservas/archivo","reservas/enviados","reservas/rechazados","assets"
]:
    os.makedirs(carpeta, exist_ok=True)

areas = ["Producción","Calidad","Mantenimiento","Logística",
         "Recursos Humanos","Ambiental","Salud Ocupacional",
         "Marketing","Financiera","Almacén"]

usuarios = {
    "usuario":{"password":"123","rol":"usuario"},
    "ingeniero":{"password":"999","rol":"ingeniero"},
    "almacen":{"password":"000","rol":"almacen"}
}

firmas_contrasena = {
    "Producción":{"archivo":"reservas/firmas/Imagen1.png","password":"1234"},
    "Logística":{"archivo":"reservas/firmas/LogisticaRojas.png","password":"5678"},
}

if "login" not in st.session_state:
    st.session_state.login = False

# ================= LOGIN =================
if not st.session_state.login:

    col1, col2, col3 = st.columns([1,2,1])

    with col2:
        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png")

        st.markdown("<h2 style='text-align:center;'>Acceso al Sistema</h2>", unsafe_allow_html=True)

        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")

        if st.button("Ingresar", use_container_width=True):
            if u in usuarios and usuarios[u]["password"] == p:
                st.session_state.login = True
                st.session_state.rol = usuarios[u]["rol"]
                st.session_state.user_name = u
                st.session_state.pagina = "principal"
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

# ================= SISTEMA =================
else:

    with st.sidebar:

        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png", width=180)

        st.markdown("### 👤 Usuario")
        st.write(f"**{st.session_state.user_name}**")
        st.write(f"Rol: {st.session_state.rol}")

        st.markdown("---")

        if st.session_state.rol == "usuario":

            if st.button("📤 Enviar"):
                st.session_state.pagina = "principal"
                st.rerun()

            if st.button("📄 Historial"):
                st.session_state.pagina = "historial"
                st.rerun()

            if st.button("📛 Rechazados"):
                st.session_state.pagina = "rechazados"
                st.rerun()

            st.markdown("---")

        if st.button("🚪 Cerrar sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    rol = st.session_state.rol
    st.title("📋 Gestión de Reservas")

    # ================= USUARIO =================
    if rol == "usuario":

        if "pagina" not in st.session_state:
            st.session_state.pagina = "principal"

        if "upload_key" not in st.session_state:
            st.session_state.upload_key = 0

        # -------- PRINCIPAL --------
        if st.session_state.pagina == "principal":

            st.header("📤 Enviar Nueva Reserva")
            area = st.selectbox("Área", areas)

            archivos = st.file_uploader(
                "Subir PDFs",
                type=["pdf"],
                accept_multiple_files=True,
                key=st.session_state.upload_key
            )

            if st.button("Enviar"):
                if archivos:
                    os.makedirs(f"reservas/pendientes/{area}", exist_ok=True)
                    os.makedirs(f"reservas/enviados/{area}", exist_ok=True)

                    for arch in archivos:
                        data = arch.getbuffer()

                        with open(f"reservas/pendientes/{area}/{arch.name}", "wb") as f:
                            f.write(data)

                        with open(f"reservas/enviados/{area}/{arch.name}", "wb") as f:
                            f.write(data)

                    st.success(f"{len(archivos)} archivos enviados")
                    st.session_state.upload_key += 1
                    st.rerun()

        # -------- HISTORIAL --------
        elif st.session_state.pagina == "historial":

            st.header("📄 Historial de Envíos")
            area = st.selectbox("Área", areas, key="hist_area")

            carpeta = f"reservas/enviados/{area}"
            os.makedirs(carpeta, exist_ok=True)

            archivos = os.listdir(carpeta)

            if not archivos:
                st.info("No hay archivos en historial")
            else:
                for f in archivos:
                    ruta = f"{carpeta}/{f}"
                    col1, col2 = st.columns([4,1])
                    col1.write(f)

                    with open(ruta, "rb") as file:
                        col2.download_button("⬇️", file, file_name=f)

        # -------- RECHAZADOS --------
        elif st.session_state.pagina == "rechazados":

            st.header("📛 Documentos Rechazados")
            area = st.selectbox("Área", areas, key="rech_area")

            carpeta = f"reservas/rechazados/{area}"
            os.makedirs(carpeta, exist_ok=True)

            archivos = [f for f in os.listdir(carpeta) if not f.endswith(".json")]

            if not archivos:
                st.info("No hay documentos rechazados")
            else:
                for f in archivos:
                    ruta = f"{carpeta}/{f}"
                    motivo_path = f"{ruta}.json"

                    col1, col2 = st.columns([4,1])
                    col1.write(f)

                    if os.path.exists(motivo_path):
                        with open(motivo_path) as m:
                            motivo = json.load(m).get("motivo","")
                            st.warning(f"Motivo: {motivo}")

                    with open(ruta, "rb") as file:
                        col2.download_button("⬇️", file, file_name=f)

    # ================= INGENIERO =================
    elif rol == "ingeniero":
        st.header("✍️ Revisión y Firma")

        col1, col2 = st.columns([5,1])
        with col1:
            area = st.selectbox("Área", areas)
        with col2:
            if st.button("🔄"):
                st.rerun()

        carpeta = f"reservas/pendientes/{area}"
        archivos = os.listdir(carpeta) if os.path.exists(carpeta) else []

        for arc in archivos:
            with st.expander(arc):

                ruta = f"{carpeta}/{arc}"
                pdf_viewer(ruta)

                pw = st.text_input("Contraseña", type="password", key=arc)

                if st.button("Firmar", key=f"f{arc}"):

                    datos_firma = firmas_contrasena.get(area)

                    if datos_firma and pw == datos_firma.get("password"):

                        ruta_firma = datos_firma["archivo"]

                        if os.path.exists(ruta_firma):
                            doc = fitz.open(ruta)
                            pagina = doc[-1]
                            rect = fitz.Rect(350, 500, 500, 650)
                            pagina.insert_image(rect, filename=ruta_firma)

                            os.makedirs(f"reservas/firmadas/{area}", exist_ok=True)
                            doc.save(f"reservas/firmadas/{area}/{arc}")
                            doc.close()

                            os.remove(ruta)
                            st.success("✅ Documento firmado")
                            st.rerun()

                motivo = st.text_input("Motivo", key=f"m{arc}")

                if st.button("Rechazar", key=f"r{arc}"):

                    if motivo:
                        os.makedirs(f"reservas/rechazados/{area}", exist_ok=True)
                        shutil.move(ruta, f"reservas/rechazados/{area}/{arc}")

                        with open(f"reservas/rechazados/{area}/{arc}.json","w") as f:
                            json.dump({"motivo":motivo},f)

                        st.rerun()

    # ================= ALMACÉN =================
    elif rol == "almacen":

        st.header("📦 Gestión de Documentos")

        col1, col2 = st.columns([5,1])
        with col1:
            area = st.selectbox("Área", areas)
        with col2:
            if st.button("🔄", key="refresh_almacen"):
                st.rerun()

        vista = st.radio("Vista", ["Firmados","Archivados"])

        carpeta = f"reservas/firmadas/{area}" if vista=="Firmados" else f"reservas/archivo/{area}"
        os.makedirs(carpeta, exist_ok=True)

        archivos = os.listdir(carpeta)

        seleccionados = []

        for f in archivos:
            ruta = f"{carpeta}/{f}"
            col1,col2,col3,col4,col5 = st.columns([3,1,1,1,1])

            check = col1.checkbox(f, key=f"chk_{f}")

            with open(ruta,"rb") as file:
                col2.download_button("⬇️", file, file_name=f)

            if col3.button("📁", key=f"a{f}"):
                os.makedirs(f"reservas/archivo/{area}", exist_ok=True)
                shutil.move(ruta, f"reservas/archivo/{area}/{f}")
                st.rerun()

            if col4.button("🗑️", key=f"del_{f}"):
                os.remove(ruta)
                st.rerun()

            if check:
                seleccionados.append(ruta)

        if seleccionados:
            if st.button("🗑️ Eliminar seleccionados"):
                for r in seleccionados:
                    os.remove(r)
                st.success("Eliminados correctamente")
                st.rerun()
