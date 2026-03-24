import streamlit as st
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer
import json
import shutil

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas", layout="wide")

# --- CREAR CARPETAS ---
for carpeta in [
    "reservas/pendientes",
    "reservas/firmadas",
    "reservas/firmas",
    "reservas/archivo"
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

    st.title("🔐 Acceso al Sistema")

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

else:

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("📂 Menú Principal")
        st.write(f"👤 Usuario: **{st.session_state.get('user_name')}**")
        st.write(f"🔑 Rol: **{st.session_state.get('rol').upper()}**")

        if st.button("🚪 Cerrar Sesión"):
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
        arch = st.file_uploader("Subir PDF", type=["pdf"])

        if st.button("Enviar al Ingeniero"):
            if arch:
                carpeta_area = f"reservas/pendientes/{area}"
                os.makedirs(carpeta_area, exist_ok=True)

                with open(f"{carpeta_area}/{arch.name}", "wb") as f:
                    f.write(arch.getbuffer())

                st.success("✅ Documento enviado")
            else:
                st.warning("Selecciona un archivo")

    # ===========================
    # INGENIERO
    # ===========================
    elif rol == "ingeniero":

        st.header("✍️ Revisión y Firma")

        area = st.selectbox("Selecciona el área", areas)

        carpeta_area = f"reservas/pendientes/{area}"
        pendientes = os.listdir(carpeta_area) if os.path.exists(carpeta_area) else []

        if not pendientes:
            st.info("No hay documentos pendientes")

        for arc in pendientes:

            with st.expander(f"📄 {arc}"):

                ruta_full = f"{carpeta_area}/{arc}"

                pdf_viewer(ruta_full)

                contra_firma = st.text_input("Contraseña", type="password", key=arc)

                if st.button("Firmar", key=f"btn_{arc}"):

                    info = firmas_contrasena.get(area)

                    if not info:
                        st.error("No hay firma configurada")
                        continue

                    if contra_firma != info["password"]:
                        st.error("Contraseña incorrecta")
                        continue

                    doc = fitz.open(ruta_full)
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

                                    if abs(y1 - y2) < 2:
                                        if abs(y1 - ref.y0) < 50:
                                            lineas.append((x1, y1, x2, y2))

                        if lineas:

                            linea = sorted(lineas, key=lambda x: x[1])[0]
                            x1, y1, x2, y2 = linea

                            ancho_firma = (x2 - x1) * 1.05
                            alto_firma = ancho_firma * 0.35

                            x_inicio = x1 + ((x2 - x1) - ancho_firma) / 2

                            # 🔥 AJUSTE FINO (10 mm arriba)
                            ajuste_mm = 28
                            y_inicio = y1 - alto_firma - ajuste_mm

                            rect_firma = fitz.Rect(
                                x_inicio,
                                y_inicio,
                                x_inicio + ancho_firma,
                                y_inicio + alto_firma
                            )

                        else:
                            rect_firma = fitz.Rect(200, 700, 450, 800)

                    else:
                        rect_firma = fitz.Rect(200, 700, 450, 800)

                    pagina.insert_image(rect_firma, filename=info["archivo"])

                    destino = f"reservas/firmadas/{area}"
                    os.makedirs(destino, exist_ok=True)

                    doc.save(f"{destino}/{arc}")
                    doc.close()

                    os.remove(ruta_full)

                    st.success("✅ Firmado correctamente")
                    st.rerun()

    # ===========================
    # ALMACÉN
    # ===========================
    elif rol == "almacen":

        st.header("📦 Documentos")

        area = st.selectbox("Área", areas)

        carpeta = f"reservas/firmadas/{area}"
        os.makedirs(carpeta, exist_ok=True)

        archivos = os.listdir(carpeta)

        for f_name in archivos:

            ruta = f"{carpeta}/{f_name}"

            col1, col2, col3 = st.columns([4,1,1])

            col1.write(f_name)

            with open(ruta, "rb") as file:
                col2.download_button("⬇️", file, file_name=f_name)

            if col3.button("📁", key=f_name):
                destino = f"reservas/archivo/{area}"
                os.makedirs(destino, exist_ok=True)
                shutil.move(ruta, f"{destino}/{f_name}")
                st.rerun()
