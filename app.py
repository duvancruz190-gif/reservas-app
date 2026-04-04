import streamlit as st 
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer
import json
import shutil
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas", layout="wide")

# --- REFRESH FIX ---
if "refresh" not in st.session_state:
    st.session_state.refresh = 0

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
        .stButton>button:hover { background-color: #003f7d; }
        .stTextInput>div>div>input { border-radius: 8px; }
        section[data-testid="stSidebar"] {
            background-color: #002b5c;
            color: white;
        }
        section[data-testid="stSidebar"] * { color: white !important; }
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
    "Producción": {"archivo": "reservas/firmas/Imagen1.png", "password": "1234"},
    "Logística": {"archivo": "reservas/firmas/LogisticaRojas.png", "password": "5678"},
}

# --- SESIÓN ---
if "login" not in st.session_state:
    st.session_state.login = False

# ================= LOGIN =================
if not st.session_state.login:

    col1, col2, col3 = st.columns([1,2,1])

    with col2:
        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png")

        st.markdown("<h2 style='text-align: center;'>Acceso al Sistema</h2>", unsafe_allow_html=True)
        st.caption("Gestión de Reservas - Eternit Colombiana")

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

    with st.sidebar:
        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png", width=180)

        st.write(f"👤 {st.session_state.user_name}")
        st.write(f"🔑 {st.session_state.rol}")

        if st.button("🚪 Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

    st.title("📋 Gestión de Reservas")
    rol = st.session_state.rol

    # ================= USUARIO =================
    if rol == "usuario":

        st.header("📤 Enviar Nueva Reserva")

        area = st.selectbox("Área", areas)

        # 🔄 uploader con reset automático
        archivos = st.file_uploader(
            "Subir PDF(s)",
            type=["pdf"],
            accept_multiple_files=True,
            key=f"uploader_{st.session_state.refresh}"
        )

        if archivos:
            for a in archivos:
                st.write(f"📄 {a.name}")

        if st.button("Enviar al Ingeniero"):
            if archivos:
                carpeta = f"reservas/pendientes/{area}"
                os.makedirs(carpeta, exist_ok=True)

                for arch in archivos:
                    nombre = f"{int(time.time())}_{arch.name}"
                    with open(f"{carpeta}/{nombre}", "wb") as f:
                        f.write(arch.getbuffer())

                cantidad = len(archivos)
                st.success(f"✅ Envío exitoso: {cantidad} archivo(s) enviado(s) a firma")

                # 🔄 limpiar uploader
                st.session_state.refresh += 1
                st.rerun()

            else:
                st.warning("Sube al menos un archivo")

    # ================= INGENIERO =================
    elif rol == "ingeniero":

        st.header("✍️ Firma de Documentos")

        if st.button("🔄 Actualizar"):
            st.session_state.refresh += 1
            st.rerun()

        _ = st.session_state.refresh

        for area in areas:

            carpeta = f"reservas/pendientes/{area}"
            if not os.path.exists(carpeta):
                continue

            archivos = os.listdir(carpeta)
            if not archivos:
                continue

            st.subheader(f"📂 {area}")

            for arc in archivos:

                ruta = f"{carpeta}/{arc}"

                with st.expander(f"📄 {arc}"):

                    try:
                        pdf_viewer(ruta, width=900, height=700)
                    except:
                        st.warning("No se pudo previsualizar")

                    pw = st.text_input("Contraseña", type="password", key=arc)

                    if st.button("Firmar", key=f"btn_{arc}"):

                        if area in firmas_contrasena and pw == firmas_contrasena[area]["password"]:

                            try:
                                doc = fitz.open(ruta)
                            except:
                                st.error("Error abriendo PDF")
                                continue

                            pagina_encontrada = None
                            rect_firma = None

                            for pagina in doc:

                                coinc = pagina.search_for("FIRMA 1")

                                if coinc:
                                    ref = coinc[0]
                                    pagina_encontrada = pagina

                                    rect_firma = fitz.Rect(ref.x0, ref.y0-80, ref.x1+120, ref.y0-10)
                                    break

                            if pagina_encontrada:
                                pagina_encontrada.insert_image(
                                    rect_firma,
                                    filename=firmas_contrasena[area]["archivo"],
                                    keep_proportion=True
                                )
                            else:
                                doc[-1].insert_image(
                                    fitz.Rect(200,700,450,800),
                                    filename=firmas_contrasena[area]["archivo"]
                                )

                            destino = f"reservas/firmadas/{area}"
                            os.makedirs(destino, exist_ok=True)

                            doc.save(f"{destino}/{arc}")
                            doc.close()
                            os.remove(ruta)

                            st.success("Firmado correctamente")
                            st.rerun()

                        else:
                            st.error("Contraseña incorrecta")

    # ================= ALMACÉN =================
    elif rol == "almacen":

        st.header("📦 Gestión de Documentos")

        if st.button("🔄 Actualizar"):
            st.session_state.refresh += 1
            st.rerun()

        _ = st.session_state.refresh

        vista = st.radio("Vista", ["Firmados", "Archivados"])
        area = st.selectbox("Área", ["Todas"] + areas)

        base = "reservas/firmadas" if vista == "Firmados" else "reservas/archivo"

        archivos = []

        if area == "Todas":
            for a in areas:
                carpeta = f"{base}/{a}"
                if os.path.exists(carpeta):
                    for f in os.listdir(carpeta):
                        archivos.append((a, f))
        else:
            carpeta = f"{base}/{area}"
            os.makedirs(carpeta, exist_ok=True)
            for f in os.listdir(carpeta):
                archivos.append((area, f))

        st.write(f"Total: {len(archivos)}")

        for a, f_name in archivos:

            ruta = f"{base}/{a}/{f_name}"

            col1, col2, col3 = st.columns([4,1,1])

            col1.write(f"[{a}] {f_name}")

            with open(ruta, "rb") as file:
                col2.download_button("⬇️", file, file_name=f_name)

            if col3.button("📁", key=ruta):
                destino = f"reservas/archivo/{a}"
                os.makedirs(destino, exist_ok=True)
                shutil.move(ruta, f"{destino}/{f_name}")
                st.rerun()
