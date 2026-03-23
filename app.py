import streamlit as st
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer
import json

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas", layout="wide")

# Carpetas principales
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

# --- FIRMAS CON CONTRASEÑA ---
firmas_contrasena = {
    "Producción": {"archivo": "reservas/firmas/carlos_alfonso.jpeg", "password": "1234"},
    # Puedes agregar más áreas con su firma y contraseña:
    # "Calidad": {"archivo": "reservas/firmas/calidad.jpeg", "password": "5678"},
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
    # MENÚ LATERAL
    with st.sidebar:
        st.title("📂 Menú Principal")
        st.write(f"👤 Usuario: **{st.session_state.get('user_name', 'Usuario')}**")
        st.write(f"🔑 Rol: **{st.session_state.get('rol', '').upper()}**")
        st.write("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    st.title("📋 Gestión de Reservas")
    rol = st.session_state.get('rol')

    # ===========================
    # --- VISTA USUARIO ---
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
    # --- VISTA INGENIERO ---
    # ===========================
    elif rol == "ingeniero":
        st.header("✍️ Revisión y Firma")
        area = st.selectbox("Selecciona el área a revisar", areas)
        carpeta_area = f"reservas/pendientes/{area}"
        pendientes = os.listdir(carpeta_area) if os.path.exists(carpeta_area) else []

        if not pendientes:
            st.info("No hay documentos pendientes en esta área.")

        for arc in pendientes:
            with st.expander(f"📄 Revisar Archivo: {arc}", expanded=False):
                ruta_full = f"{carpeta_area}/{arc}"
                st.write("### Previsualización:")
                try:
                    pdf_viewer(ruta_full, width=700)
                except:
                    st.error("El visor falló. Usa el botón de abajo para revisar.")
                    with open(ruta_full, "rb") as f:
                        st.download_button("📂 Descargar para revisar", f, file_name=arc)

                st.write("---")

                # Pedir contraseña para la firma si existe
                contra_firma = st.text_input(
                    "Ingresa la contraseña de la firma (si aplica)", 
                    type="password", key=f"pw_{arc}"
                )

                if st.button(f"🖋️ Firmar y Enviar a Almacén", key=f"f_{area}_{arc}"):
                    # Verificar si hay firma con contraseña para el área
                    if area in firmas_contrasena:
                        info_firma = firmas_contrasena[area]
                        if contra_firma == info_firma["password"]:
                            if os.path.exists(info_firma["archivo"]):
                                doc = fitz.open(ruta_full)
                                pagina = doc[0]
                                pagina.insert_image(fitz.Rect(400, 700, 550, 800), filename=info_firma["archivo"])
                                carpeta_firmadas = f"reservas/firmadas/{area}"
                                os.makedirs(carpeta_firmadas, exist_ok=True)
                                doc.save(f"{carpeta_firmadas}/{arc}")
                                doc.close()
                                os.remove(ruta_full)
                                st.success("✅ Firmado correctamente y enviado a almacen.")
                                st.rerun()
                            else:
                                st.error(f"❌ No existe la firma '{info_firma['archivo']}'")
                        else:
                            st.error("❌ Contraseña incorrecta para la firma.")
                    else:
                        st.error("❌ No hay firma configurada para esta área.")

    # ===========================
    # --- VISTA ALMACÉN ---
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
            # Azul = no descargado, Amarillo = descargado
            color = "💛" if estados.get(f"{area}/{f}", False) else "💙"
            col_a, col_b = st.columns([3, 1])
            col_a.markdown(f"{color} {f}")
            with open(f"{carpeta_area}/{f}", "rb") as file:
                if col_b.download_button("Descargar", file, file_name=f, key=f"dl_{area}_{f}"):
                    estados[f"{area}/{f}"] = True  # Marca como descargado
                    with open(estado_file, "w") as ff:
                        json.dump(estados, ff)
