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
    "Producción":{"archivo":"reservas/firmas/carlos_alfonso.jpeg","password":"1234"},
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

    # -------- SIDEBAR --------
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

        # ---- ENVÍO ----
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

        # ---- HISTORIAL ----
        elif st.session_state.pagina == "historial":

            st.title("📄 Historial")

            archivos_totales = []
            for a in areas:
                ruta = f"reservas/enviados/{a}"
                if os.path.exists(ruta):
                    for f in os.listdir(ruta):
                        archivos_totales.append((a,f))

            if not archivos_totales:
                st.info("No hay archivos")
            else:

                if st.button("🧹 Borrar todo"):
                    for a,f in archivos_totales:
                        os.remove(f"reservas/enviados/{a}/{f}")
                    st.rerun()

                for a,f in archivos_totales:
                    col1,col2 = st.columns([6,1])
                    col1.write(f"{f} ({a})")

                    if col2.button("🗑️", key=f"hist_{a}_{f}"):
                        os.remove(f"reservas/enviados/{a}/{f}")
                        st.rerun()

        # ---- RECHAZADOS ----
        elif st.session_state.pagina == "rechazados":

            st.title("📛 Archivos Rechazados")

            rechazados = []
            for a in areas:
                ruta = f"reservas/rechazados/{a}"
                if os.path.exists(ruta):
                    for f in os.listdir(ruta):
                        if f.endswith(".pdf"):
                            rechazados.append((a,f))

            if not rechazados:
                st.info("No hay rechazados")
            else:

                if st.button("🧹 Borrar todos"):
                    for a,f in rechazados:
                        os.remove(f"reservas/rechazados/{a}/{f}")
                        json_path = f"reservas/rechazados/{a}/{f}.json"
                        if os.path.exists(json_path):
                            os.remove(json_path)
                    st.rerun()

                for a,f in rechazados:

                    motivo = "Sin motivo"
                    ruta_json = f"reservas/rechazados/{a}/{f}.json"

                    if os.path.exists(ruta_json):
                        with open(ruta_json) as ff:
                            motivo = json.load(ff)["motivo"]

                    col1,col2 = st.columns([6,1])
                    col1.warning(f"{f} ({a})")
                    col1.write(f"Motivo: {motivo}")

                    if col2.button("🗑️", key=f"rech_{a}_{f}"):
                        os.remove(f"reservas/rechazados/{a}/{f}")
                        if os.path.exists(ruta_json):
                            os.remove(ruta_json)
                        st.rerun()

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

                    if pw == firmas_contrasena.get(area,{}).get("password"):

                        ruta_firma = firmas_contrasena[area]["archivo"]

                        if os.path.exists(ruta_firma):

                            doc = fitz.open(ruta)
                            page = doc[0]
                            rect = fitz.Rect(200,700,450,800)

                            page.insert_image(rect, filename=ruta_firma)

                            os.makedirs(f"reservas/firmadas/{area}", exist_ok=True)
                            doc.save(f"reservas/firmadas/{area}/{arc}")
                            doc.close()

                            os.remove(ruta)
                            st.rerun()

                        else:
                            st.error(f"No se encontró la firma en: {ruta_firma}")

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

        if not archivos:
            st.info("No hay documentos")
        else:

            if vista == "Archivados":
                if st.button("🧹 Borrar todos los archivados"):
                    for f in archivos:
                        os.remove(f"{carpeta}/{f}")
                    st.rerun()

            for f in archivos:

                ruta = f"{carpeta}/{f}"

                if vista == "Firmados":
                    col1,col2,col3,col4 = st.columns([4,1,1,1])
                else:
                    col1,col2,col3 = st.columns([5,1,1])

                col1.write(f)

                with open(ruta,"rb") as file:
                    col2.download_button("⬇️", file, file_name=f)

                if vista == "Firmados":

                    if col3.button("📁", key=f"a{f}"):
                        os.makedirs(f"reservas/archivo/{area}", exist_ok=True)
                        shutil.move(ruta, f"reservas/archivo/{area}/{f}")
                        st.rerun()

                    if col4.button("🗑️", key=f"del_f{f}"):
                        os.remove(ruta)
                        st.rerun()

                else:

                    if col3.button("🗑️", key=f"del_a{f}"):
                        os.remove(ruta)
                        st.rerun()
