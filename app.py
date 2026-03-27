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
    "Producción": {"archivo": "reservas/firmas/Imagen1.png", "password": "1234"},
    "Logística": {"archivo": "reservas/firmas/LogisticaRojas.png", "password": "5678"},
}

# --- SESIÓN ---
if "login" not in st.session_state:
    st.session_state.login = False

# LOGIN
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

# SISTEMA
else:

    with st.sidebar:
        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png", width=180)

        st.write(f"👤 {st.session_state.get('user_name')}")
        st.write(f"🔑 Rol: {st.session_state.get('rol')}")

        if st.button("Cerrar sesión"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    rol = st.session_state.get('rol')
    st.title("📋 Gestión de Reservas")

    # INGENIERO
    if rol == "ingeniero":

        st.header("✍️ Firma de documentos")

        area = st.selectbox("Área", areas)
        carpeta = f"reservas/pendientes/{area}"
        archivos = os.listdir(carpeta) if os.path.exists(carpeta) else []

        for arc in archivos:

            ruta = f"{carpeta}/{arc}"

            with st.expander(arc):

                pdf_viewer(ruta, width=1000, height=800)

                pw = st.text_input("Contraseña", type="password", key=arc)

                if st.button("Firmar", key=f"btn_{arc}"):

                    info = firmas_contrasena.get(area)

                    if not info:
                        st.error("No hay firma configurada")
                        continue

                    if pw != info["password"]:
                        st.error("Contraseña incorrecta")
                        continue

                    doc = fitz.open(ruta)
                    pagina = doc[0]

                    coincidencias = pagina.search_for("FIRMA 1")

                    if coincidencias:

                        ref = coincidencias[0]
                        lineas = []

                        for d in pagina.get_drawings():
                            for item in d["items"]:
                                if item[0] == "l":
                                    x1, y1 = item[1]
                                    x2, y2 = item[2]

                                    if abs(y1 - y2) < 2 and y1 < ref.y0:
                                        lineas.append((x1, y1, x2, y2))

                        if lineas:

                            x1, y1, x2, y2 = lineas[0]

                            # 🔥 AJUSTES PRO
                            alto = (x2 - x1) * 0.25
                            ancho_firma = (x2 - x1) * 0.5
                            x_centro = (x1 + x2) / 2

                            rect_firma = fitz.Rect(
                                x_centro - ancho_firma / 2,
                                y1 - alto,
                                x_centro + ancho_firma / 2,
                                y1
                            )

                            pagina.insert_image(rect_firma, filename=info["archivo"])

                    destino = f"reservas/firmadas/{area}"
                    os.makedirs(destino, exist_ok=True)

                    doc.save(f"{destino}/{arc}")
                    doc.close()

                    os.remove(ruta)

                    st.success("Firmado correctamente")
                    st.rerun()
