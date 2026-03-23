import streamlit as st
import os
import fitz  # PyMuPDF
from PIL import Image
import json
import matplotlib.pyplot as plt

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
st.set_page_config(page_title="Gestión de Reservas PRO", layout="wide")

areas = ["Producción", "Calidad", "Mantenimiento", "Logística",
         "Recursos Humanos", "Ambiental", "Salud Ocupacional",
         "Marketing", "Financiera", "Almacén"]

# Crear carpetas
for carpeta in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas"]:
    os.makedirs(carpeta, exist_ok=True)
for area in areas:
    os.makedirs(f"reservas/pendientes/{area}", exist_ok=True)
    os.makedirs(f"reservas/firmadas/{area}", exist_ok=True)

# Usuarios
usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# Firma con contraseña
firmas_contrasena = {
    "Producción": {"archivo": "reservas/firmas/carlos_alfonso.jpeg", "password": "1234"}
}

# -----------------------------
# SESIÓN
# -----------------------------
if "login" not in st.session_state:
    st.session_state.login = False

# -----------------------------
# LOGIN
# -----------------------------
if not st.session_state.login:
    st.title("🔐 Acceso al Sistema")
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

# -----------------------------
# APP
# -----------------------------
else:
    with st.sidebar:
        st.title("📂 Menú")
        st.write(f"👤 {st.session_state.user_name}")
        st.write(f"🔑 {st.session_state.rol.upper()}")
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.rerun()

    rol = st.session_state.rol

    # ===========================
    # USUARIO
    # ===========================
    if rol == "usuario":
        st.header("📤 Subir PDF")
        area = st.selectbox("Área", areas)
        archivo = st.file_uploader("PDF", type=["pdf"])

        if st.button("Enviar"):
            if archivo:
                with open(f"reservas/pendientes/{area}/{archivo.name}", "wb") as f:
                    f.write(archivo.getbuffer())
                st.success("✅ Enviado")
            else:
                st.warning("Sube un archivo")

    # ===========================
    # INGENIERO
    # ===========================
    elif rol == "ingeniero":
        st.header("✍️ Firmar Documentos")

        area = st.selectbox("Área", areas)
        carpeta = f"reservas/pendientes/{area}"
        archivos = os.listdir(carpeta)

        if not archivos:
            st.info("Sin documentos")

        for archivo in archivos:
            with st.expander(f"📄 {archivo}"):

                ruta = f"{carpeta}/{archivo}"

                pdf = fitz.open(ruta)
                pagina = pdf[0]
                pix = pagina.get_pixmap()

                pdf_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Contraseña
                if area in firmas_contrasena:
                    info = firmas_contrasena[area]
                    pw = st.text_input("Contraseña firma", type="password", key=archivo)

                    if pw == info["password"]:
                        st.success("✅ Correcta")

                        firma = Image.open(info["archivo"])

                        # Sliders
                        x = st.slider("X", 0, pix.width - 150, 200, key=f"x_{archivo}")
                        y = st.slider("Y", 0, pix.height - 150, 400, key=f"y_{archivo}")

                        # -------- VISUAL --------
                        fig, ax = plt.subplots()
                        ax.imshow(pdf_img)

                        ax.imshow(firma, extent=(
                            x,
                            x + 150,
                            y + 80,
                            y
                        ))

                        ax.axis("off")
                        st.pyplot(fig)

                        # -------- FIRMAR --------
                        if st.button("Firmar", key=f"btn_{archivo}"):

                            rect = fitz.Rect(x, y, x + 150, y + 80)
                            pagina.insert_image(rect, filename=info["archivo"])

                            destino = f"reservas/firmadas/{area}/{archivo}"
                            pdf.save(destino)
                            pdf.close()

                            os.remove(ruta)

                            st.success("✅ Firmado y enviado a almacén")
                            st.rerun()

                    elif pw:
                        st.error("❌ Incorrecta")

    # ===========================
    # ALMACÉN
    # ===========================
    elif rol == "almacen":
        st.header("📦 Almacén")

        estado_path = "reservas/firmadas/estado.json"

        if os.path.exists(estado_path):
            estados = json.load(open(estado_path))
        else:
            estados = {}

        area = st.selectbox("Área", areas)
        carpeta = f"reservas/firmadas/{area}"
        archivos = os.listdir(carpeta)

        for archivo in archivos:
            key = f"{area}/{archivo}"
            color = "💛" if estados.get(key) else "💙"

            col1, col2 = st.columns([3,1])
            col1.write(f"{color} {archivo}")

            with open(f"{carpeta}/{archivo}", "rb") as f:
                if col2.download_button("Descargar", f, file_name=archivo):
                    estados[key] = True
                    json.dump(estados, open(estado_path, "w"))
