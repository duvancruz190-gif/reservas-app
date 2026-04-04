import streamlit as st
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer
import json
import shutil
import time

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

        .stTextInput>div>div>input { border-radius: 8px; }

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

        # 🔥 CAMBIO: múltiples archivos
        archivos = st.file_uploader("Subir PDF(s)", type=["pdf"], accept_multiple_files=True)

        if st.button("Enviar al Ingeniero"):
            if archivos:

                carpeta_area = f"reservas/pendientes/{area}"
                os.makedirs(carpeta_area, exist_ok=True)

                enviados = 0

                for arch in archivos:
                    try:
                        nombre_unico = f"{int(time.time()*1000)}_{arch.name}"

                        with open(f"{carpeta_area}/{nombre_unico}", "wb") as f:
                            f.write(arch.getbuffer())

                        enviados += 1

                    except Exception as e:
                        st.error(f"Error con {arch.name}: {e}")

                # ✅ MENSAJE DINÁMICO
                if enviados == 1:
                    st.success(f"✅ 1 archivo enviado con éxito al ingeniero de {area}")
                elif enviados > 1:
                    st.success(f"✅ {enviados} archivos enviados con éxito al ingeniero de {area}")
                else:
                    st.warning("No se pudo enviar ningún archivo.")

                st.rerun()

            else:
                st.warning("Selecciona al menos un archivo.")

    # ===========================
    # INGENIERO
    # ===========================
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

                                rect_firma = None
                                coincidencias = pagina.search_for("FIRMA 1")

                                if coincidencias:
                                    ref = coincidencias[0]
                                    rect_firma = fitz.Rect(ref.x0, ref.y0 - 80, ref.x1, ref.y0)
                                else:
                                    rect_firma = fitz.Rect(200, 700, 450, 800)

                                pagina.insert_image(
                                    rect_firma,
                                    filename=info_firma["archivo"],
                                    rotate=90
                                )

                                carpeta_firmadas = f"reservas/firmadas/{area}"
                                os.makedirs(carpeta_firmadas, exist_ok=True)

                                doc.save(f"{carpeta_firmadas}/{arc}")
                                doc.close()

                                os.remove(ruta_full)

                                st.success("✅ Firmado correctamente y enviado a almacén")
                                st.rerun()

                            else:
                                st.error("❌ No se encontró la firma")
                        else:
                            st.error("❌ Contraseña incorrecta")
                    else:
                        st.error("❌ No hay firma configurada")

    # ===========================
    # ALMACÉN
    # ===========================
    elif rol == "almacen":

        st.header("📦 Gestión de Documentos")

        estado_file = "reservas/firmadas/estado.json"

        if os.path.exists(estado_file):
            with open(estado_file, "r") as f:
                estados = json.load(f)
        else:
            estados = {}

        vista = st.radio("Vista", ["Firmados", "Archivados"])
        area = st.selectbox("Selecciona el área", areas)

        carpeta_area = f"reservas/firmadas/{area}" if vista == "Firmados" else f"reservas/archivo/{area}"
        os.makedirs(carpeta_area, exist_ok=True)

        archivos = os.listdir(carpeta_area)

        busqueda = st.text_input("🔍 Buscar")

        if busqueda:
            archivos = [f for f in archivos if busqueda.lower() in f.lower()]

        if not archivos:
            st.info("No hay documentos aquí.")

        for f_name in archivos:

            ruta = f"{carpeta_area}/{f_name}"
            icono = "💛" if estados.get(f"{area}/{f_name}", False) else "💙"

            col1, col2, col3, col4 = st.columns([3,1,1,1])
            col1.write(f"{icono} {f_name}")

            with open(ruta, "rb") as file:
                if col2.download_button("⬇️", file, file_name=f_name):
                    estados[f"{area}/{f_name}"] = True
                    with open(estado_file, "w") as ff:
                        json.dump(estados, ff)

            if vista == "Firmados":
                if col3.button("📁", key=f"arch_{ruta}"):
                    destino = f"reservas/archivo/{area}"
                    os.makedirs(destino, exist_ok=True)
                    shutil.move(ruta, f"{destino}/{f_name}")
                    st.rerun()

            if col4.button("🗑️", key=f"del_{ruta}"):
                os.remove(ruta)
                st.rerun()
```
