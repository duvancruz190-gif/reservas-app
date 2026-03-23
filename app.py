import streamlit as st
import os
import fitz  # PyMuPDF
from PIL import Image
import json

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
st.set_page_config(page_title="Gestión de Reservas Interactiva", layout="wide")

areas = ["Producción", "Calidad", "Mantenimiento", "Logística",
         "Recursos Humanos", "Ambiental", "Salud Ocupacional",
         "Marketing", "Financiera", "Almacén"]

for carpeta in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas"]:
    os.makedirs(carpeta, exist_ok=True)
for area in areas:
    os.makedirs(f"reservas/pendientes/{area}", exist_ok=True)
    os.makedirs(f"reservas/firmadas/{area}", exist_ok=True)

usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# -----------------------------
# Firmas con contraseña
# -----------------------------
firmas_contrasena = {
    "Producción": {"archivo": "reservas/firmas/carlos_alfonso.jpeg", "password": "1234"},
    # Agrega más áreas y sus firmas aquí
}

# -----------------------------
# Sesión
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
    if st.button("Ingresar", use_container_width=True):
        if u in usuarios and usuarios[u]["password"] == p:
            st.session_state.login = True
            st.session_state.rol = usuarios[u]["rol"]
            st.session_state.user_name = u
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

# -----------------------------
# APP PRINCIPAL
# -----------------------------
else:
    # Menú lateral
    with st.sidebar:
        st.title("📂 Menú Principal")
        st.write(f"👤 Usuario: **{st.session_state.get('user_name', 'Usuario')}**")
        st.write(f"🔑 Rol: **{st.session_state.get('rol', '').upper()}**")
        st.write("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

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
                with open(f"{carpeta_area}/{arch.name}", "wb") as f:
                    f.write(arch.getbuffer())
                st.success(f"✅ Documento enviado a {area}.")
            else:
                st.warning("Selecciona un archivo.")

    # ===========================
    # INGENIERO
    # ===========================
    elif rol == "ingeniero":
        st.header("✍️ Revisión y Firma Interactiva")
        area = st.selectbox("Selecciona el área a revisar", areas)
        carpeta_area = f"reservas/pendientes/{area}"
        pendientes = os.listdir(carpeta_area) if os.path.exists(carpeta_area) else []

        if not pendientes:
            st.info("No hay documentos pendientes en esta área.")

        for arc in pendientes:
            with st.expander(f"📄 Revisar Archivo: {arc}", expanded=False):
                ruta_full = f"{carpeta_area}/{arc}"

                # --------------------------
                # Convertir PDF a imagen
                # --------------------------
                pdf_doc = fitz.open(ruta_full)
                pagina = pdf_doc[0]
                pix = pagina.get_pixmap()
                pdf_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                st.image(pdf_img, caption="PDF de referencia", use_column_width=True)

                # --------------------------
                # Contraseña de firma
                # --------------------------
                if area in firmas_contrasena:
                    info_firma = firmas_contrasena[area]
                    contra_firma = st.text_input("Ingresa la contraseña de la firma", type="password", key=f"pw_{arc}")

                    if contra_firma == info_firma["password"]:
                        st.success("✅ Contraseña correcta. Ajusta la posición de la firma con los sliders.")

                        firma_img = Image.open(info_firma["archivo"])
                        st.image(firma_img, width=150, caption="Firma para colocar")

                        # Sliders para posicionar firma
                        x_pos = st.slider("Posición X", 0, pix.width - 100, 400)
                        y_pos = st.slider("Posición Y", 0, pix.height - 100, 700)

                        if st.button(f"🖋️ Firmar PDF", key=f"f_{arc}"):
                            rect = fitz.Rect(x_pos, y_pos, x_pos + firma_img.width, y_pos + firma_img.height)
                            pagina.insert_image(rect, filename=info_firma["archivo"])
                            carpeta_firmadas = f"reservas/firmadas/{area}"
                            pdf_doc.save(f"{carpeta_firmadas}/{arc}")
                            pdf_doc.close()
                            os.remove(ruta_full)
                            st.success("✅ PDF firmado y enviado a Almacén")
                            st.rerun()
                    else:
                        if contra_firma:
                            st.error("❌ Contraseña incorrecta")

    # ===========================
    # ALMACÉN
    # ===========================
    elif rol == "almacen":
        st.header("📦 Documentos Listos")
        estado_file = "reservas/firmadas/estado.json"
        if os.path.exists(estado_file):
            with open(estado_file, "r") as f:
                estados = json.load(f)
        else:
            estados = {}

        area = st.selectbox("Selecciona el área", areas)
        carpeta_area = f"reservas/firmadas/{area}"
        firmados = os.listdir(carpeta_area) if os.path.exists(carpeta_area) else []

        for f in firmados:
            color = "💛" if estados.get(f"{area}/{f}", False) else "💙"
            col_a, col_b = st.columns([3,1])
            col_a.markdown(f"{color} {f}")
            with open(f"{carpeta_area}/{f}", "rb") as file:
                if col_b.download_button("Descargar", file, file_name=f, key=f"dl_{area}_{f}"):
                    estados[f"{area}/{f}"] = True
                    with open(estado_file, "w") as ff:
                        json.dump(estados, ff)
