import streamlit as st 
import os
import fitz
from streamlit_pdf_viewer import pdf_viewer
import json
import shutil
import time
from datetime import datetime
import pandas as pd
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas", layout="wide")

# --- ARCHIVO HISTORIAL ---
HISTORIAL_FILE = "reservas/historial.json"

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, "r") as f:
            return json.load(f)
    return []

def guardar_historial(data):
    with open(HISTORIAL_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- EXCEL ---
def generar_excel(historial):
    datos = []

    for h in historial:
        for archivo in h["archivos"]:
            datos.append({
                "Fecha": h["fecha"],
                "Área": h["area"],
                "Archivo": archivo,
                "Cantidad": 1,
                "Total envío": h["cantidad"]
            })

    df = pd.DataFrame(datos)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Historial')

    return output.getvalue()

# --- ESTADOS ---
if "refresh" not in st.session_state:
    st.session_state.refresh = 0

if "mensaje_envio" not in st.session_state:
    st.session_state.mensaje_envio = ""

if "historial" not in st.session_state:
    st.session_state.historial = cargar_historial()

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

        /* BOTÓN EXCEL */
        div.stDownloadButton > button {
            background-color: #005baa !important;
            color: white !important;
            border-radius: 8px;
            height: 45px;
            font-weight: bold;
        }

        div.stDownloadButton > button:hover {
            background-color: #003f7d !important;
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
areas = ["Producción","Calidad","Mantenimiento","Logística",
         "Recursos Humanos","Ambiental","Salud Ocupacional",
         "Marketing","Financiera","Almacén"]

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

# --- LOGIN ---
if "login" not in st.session_state:
    st.session_state.login = False

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
            st.error("Error")

else:

    # ===== SIDEBAR =====
    with st.sidebar:
        st.write(f"👤 {st.session_state.user_name}")
        st.write(f"🔑 {st.session_state.rol}")

        st.markdown("### 📜 Historial")

        if st.session_state.historial:

            excel = generar_excel(st.session_state.historial)
            st.download_button("📥 Descargar Excel", excel, "historial.xlsx")

            if st.button("🗑️ Borrar"):
                st.session_state.historial = []
                guardar_historial([])
                st.rerun()

            for h in reversed(st.session_state.historial[-5:]):
                with st.expander(f"{h['area']} ({h['cantidad']})"):
                    st.caption(h["fecha"])
                    for nombre in h["archivos"]:
                        st.write(f"📄 {nombre}")

        if st.button("🚪 Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

    # ===== USUARIO =====
    if st.session_state.rol == "usuario":

        st.title("📤 Enviar Reserva")

        if st.session_state.mensaje_envio:
            st.success(st.session_state.mensaje_envio)
            st.session_state.mensaje_envio = ""

        area = st.selectbox("Área", areas)

        archivos = st.file_uploader(
            "PDF",
            type=["pdf"],
            accept_multiple_files=True,
            key=f"up_{st.session_state.refresh}"
        )

        if st.button("Enviar"):
            if archivos:
                carpeta = f"reservas/pendientes/{area}"
                os.makedirs(carpeta, exist_ok=True)

                nombres = []

                for arch in archivos:
                    nombre = f"{int(time.time())}_{arch.name}"
                    nombres.append(arch.name)
                    with open(f"{carpeta}/{nombre}", "wb") as f:
                        f.write(arch.getbuffer())

                cantidad = len(archivos)

                mensaje = "✅ 1 archivo enviado" if cantidad == 1 else f"✅ {cantidad} archivos enviados"
                st.session_state.mensaje_envio = mensaje

                nuevo = {
                    "area": area,
                    "cantidad": cantidad,
                    "archivos": nombres,
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                st.session_state.historial.append(nuevo)
                guardar_historial(st.session_state.historial)

                st.session_state.refresh += 1
                st.rerun()

            else:
                st.warning("Sube archivo")

    # ===== INGENIERO =====
    elif st.session_state.rol == "ingeniero":

        st.title("✍️ Firmar")

        for area in areas:

            carpeta = f"reservas/pendientes/{area}"
            if not os.path.exists(carpeta):
                continue

            archivos = os.listdir(carpeta)

            for arc in archivos:

                ruta = f"{carpeta}/{arc}"

                with st.expander(arc):

                    try:
                        pdf_viewer(ruta)
                    except:
                        pass

                    pw = st.text_input("Clave", key=arc)

                    if st.button("Firmar", key=f"f{arc}"):

                        if area in firmas_contrasena and pw == firmas_contrasena[area]["password"]:

                            doc = fitz.open(ruta)
                            doc[-1].insert_image(
                                fitz.Rect(200,700,450,800),
                                filename=firmas_contrasena[area]["archivo"]
                            )

                            destino = f"reservas/firmadas/{area}"
                            os.makedirs(destino, exist_ok=True)

                            doc.save(f"{destino}/{arc}")
                            doc.close()
                            os.remove(ruta)

                            st.rerun()
