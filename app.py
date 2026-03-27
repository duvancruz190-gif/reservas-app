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
    "Producción": {"archivo": "reservas/firmas/Imagen1.png", "password": "1234"},
    "Logística": {"archivo": "reservas/firmas/LogisticaRojas.png", "password": "5678"},
}

# --- SESIÓN ---
if "login" not in st.session_state:
    st.session_state.login = False

# ================= LOGIN =================
if not st.session_state.login:

    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if u in usuarios and usuarios[u]["password"] == p:
            st.session_state.login = True
            st.session_state.rol = usuarios[u]["rol"]
            st.session_state.user_name = u
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

# ================= SISTEMA =================
else:

    rol = st.session_state.get('rol')
    st.title("📋 Gestión de Reservas")

    # ================= USUARIO =================
    if rol == "usuario":

        area = st.selectbox("Área", areas)
        arch = st.file_uploader("PDF", type=["pdf"])

        if st.button("Enviar"):
            if arch:
                ruta = f"reservas/pendientes/{area}"
                os.makedirs(ruta, exist_ok=True)
                with open(f"{ruta}/{arch.name}", "wb") as f:
                    f.write(arch.getbuffer())
                st.success("Enviado")

    # ================= INGENIERO =================
    elif rol == "ingeniero":

        area = st.selectbox("Área", areas)
        carpeta = f"reservas/pendientes/{area}"
        archivos = os.listdir(carpeta) if os.path.exists(carpeta) else []

        for arc in archivos:

            ruta = f"{carpeta}/{arc}"

            st.subheader(arc)
            pdf_viewer(ruta)

            pw = st.text_input("Clave firma", type="password", key=arc)

            if st.button("Firmar", key=f"b_{arc}"):

                if area in firmas_contrasena:
                    info = firmas_contrasena[area]

                    if pw == info["password"]:

                        doc = fitz.open(ruta)
                        pagina = doc[0]

                        ref = pagina.search_for("FIRMA 1")[0]

                        x1, y1 = ref.x0, ref.y0
                        x2 = ref.x1

                        # 🔥 FIRMA PEQUEÑA Y PEGADA
                        ancho_firma = 100
                        alto = 35
                        x_centro = (x1 + x2) / 2

                        rect_firma = fitz.Rect(
                            x_centro - ancho_firma / 2,
                            y1 - alto + 2,
                            x_centro + ancho_firma / 2,
                            y1 + 1
                        )

                        pagina.insert_image(rect_firma, filename=info["archivo"])

                        destino = f"reservas/firmadas/{area}"
                        os.makedirs(destino, exist_ok=True)

                        doc.save(f"{destino}/{arc}")
                        doc.close()

                        os.remove(ruta)
                        st.success("Firmado")
                        st.rerun()

    # ================= ALMACÉN =================
    elif rol == "almacen":

        estado_file = "reservas/firmadas/estado.json"

        if os.path.exists(estado_file):
            estados = json.load(open(estado_file))
        else:
            estados = {}

        rutas = []

        for area in areas:
            carpeta = f"reservas/firmadas/{area}"
            if os.path.exists(carpeta):
                for f in os.listdir(carpeta):
                    rutas.append((area, f, f"{carpeta}/{f}"))

        for area, f_name, ruta in rutas:

            estado = estados.get(f"{area}/{f_name}", False)
            color = "🟥" if not estado else "🟩"

            col1, col2, col3 = st.columns([5,1,1])

            col1.write(f"{color} {area} | {f_name}")

            with open(ruta, "rb") as file:
                if col2.download_button("⬇️", file, file_name=f_name):
                    estados[f"{area}/{f_name}"] = True
                    json.dump(estados, open(estado_file, "w"))

            if col3.button("📁", key=ruta):
                destino = f"reservas/archivo/{area}"
                os.makedirs(destino, exist_ok=True)
                shutil.move(ruta, f"{destino}/{f_name}")
                st.rerun()
