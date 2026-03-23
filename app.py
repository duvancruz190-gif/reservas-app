import streamlit as st
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer
import json

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas", layout="wide")

# Carpetas
for carpeta in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas"]:
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

# --- LOGIN ---
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
        st.write("---")

        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.title("📋 Gestión de Reservas")
    rol = st.session_state.get('rol')

    # ===========================
    # --- USUARIO ---
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

                st.success(f"✅ Documento enviado a {area}.")
            else:
                st.warning("Selecciona un archivo.")

    # ===========================
    # --- INGENIERO ---
    # ===========================
    elif rol == "ingeniero":
        st.header("✍️ Revisión y Firma")
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
                    pdf_viewer(ruta_full, width=None)
                except:
                    with open(ruta_full, "rb") as f:
                        st.download_button("Descargar PDF", f, file_name=arc)

                st.write("---")

                contra_firma = st.text_input(
                    "Contraseña de firma", type="password", key=f"pw_{arc}"
                )

                if st.button("🖋️ Firmar y enviar", key=f"btn_{arc}"):

                    if area in firmas_contrasena:
                        info_firma = firmas_contrasena[area]

                        if contra_firma == info_firma["password"]:

                            if os.path.exists(info_firma["archivo"]):

                                doc = fitz.open(ruta_full)
                                pagina = doc[0]

                                # 🔥 BUSCAR "FIRMA 1"
                                coincidencias = pagina.search_for("FIRMA 1")

                                if coincidencias:
                                    ref = coincidencias[0]

                                    x_centro = (ref.x0 + ref.x1) / 2

                                    # 🔥 AJUSTE FINO PARA LÍNEA
                                    y_linea_real = ref.y0 - 25

                                    ancho_firma = 220
                                    alto_firma = 80

                                    rect_firma = fitz.Rect(
                                        x_centro - ancho_firma / 2,
                                        y_linea_real - alto_firma,
                                        x_centro + ancho_firma / 2,
                                        y_linea_real
                                    )

                                else:
                                    # fallback
                                    page_width = pagina.rect.width
                                    page_height = pagina.rect.height

                                    rect_firma = fitz.Rect(
                                        page_width / 2 - 90,
                                        page_height - 180,
                                        page_width / 2 + 90,
                                        page_height - 110
                                    )

                                # Insertar firma
                                pagina.insert_image(rect_firma, filename=info_firma["archivo"])

                                carpeta_firmadas = f"reservas/firmadas/{area}"
                                os.makedirs(carpeta_firmadas, exist_ok=True)

                                doc.save(f"{carpeta_firmadas}/{arc}")
                                doc.close()

                                os.remove(ruta_full)

                                st.success("✅ Firmado correctamente")
                                st.rerun()

                            else:
                                st.error("❌ No se encontró la imagen de firma")

                        else:
                            st.error("❌ Contraseña incorrecta")

                    else:
                        st.error("❌ No hay firma configurada para esta área")

    # ===========================
    # --- ALMACÉN ---
    # ===========================
    elif rol == "almacen":
        st.header("📦 Documentos Firmados")

        estado_file = "reservas/firmadas/estado.json"

        if os.path.exists(estado_file):
            with open(estado_file, "r") as f:
                estados = json.load(f)
        else:
            estados = {}

        area = st.selectbox("Selecciona el área", areas)
        carpeta_area = f"reservas/firmadas/{area}"
        firmados = os.listdir(carpeta_area) if os.path.exists(carpeta_area) else []

        for f_name in firmados:
            estado = estados.get(f"{area}/{f_name}", False)
            icono = "💛" if estado else "💙"

            col1, col2 = st.columns([3, 1])
            col1.write(f"{icono} {f_name}")

            with open(f"{carpeta_area}/{f_name}", "rb") as file:
                if col2.download_button("Descargar", file, file_name=f_name):
                    estados[f"{area}/{f_name}"] = True

                    with open(estado_file, "w") as ff:
                        json.dump(estados, ff)
