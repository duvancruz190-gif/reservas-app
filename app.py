import streamlit as st
import os
import fitz  # PyMuPDF
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from streamlit_pdf_viewer import pdf_viewer
import json

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas Interactiva", layout="wide")

# Crear carpetas base y por áreas
areas = ["Producción", "Calidad", "Mantenimiento", "Logística",
         "Recursos Humanos", "Ambiental", "Salud Ocupacional",
         "Marketing", "Financiera", "Almacén"]

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

# Firmas con contraseña
firmas_contrasena = {
    "Producción": {"archivo": "reservas/firmas/carlos_alfonso.jpeg", "password": "1234"},
    # Agrega más firmas por área
}

# Sesión
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
    # Menú lateral
    with st.sidebar:
        st.title("📂 Menú Principal")
        st.write(f"👤 Usuario: **{st.session_state.get('user_name', 'Usuario')}**")
        st.write(f"🔑 Rol: **{st.session_state.get('rol', '').upper()}**")
        st.write("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

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
                with open(f"{carpeta_area}/{arch.name}", "wb") as f:
                    f.write(arch.getbuffer())
                st.success(f"✅ Documento enviado a {area}.")
            else:
                st.warning("Selecciona un archivo.")

    # ===========================
    # --- VISTA INGENIERO ---
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

                # --- VER PDF COMPLETO ---
                st.write("### Previsualización del PDF")
                try:
                    pdf_viewer(ruta_full, width=700)
                except:
                    with open(ruta_full, "rb") as f:
                        st.download_button("Descargar PDF", f, file_name=arc)

                # --- SUBIR FIRMA ---
                if area in firmas_contrasena:
                    info_firma = firmas_contrasena[area]
                    st.write(f"Firma asignada: {os.path.basename(info_firma['archivo'])}")
                    contra_firma = st.text_input("Ingresa la contraseña de la firma", type="password", key=f"pw_{arc}")
                    firma_upload = st.file_uploader("Sube la imagen de la firma para arrastrar", type=["jpeg","png"], key=f"firma_{arc}")

                    if firma_upload:
                        firma_img = Image.open(firma_upload)
                        st.write("Arrastra la firma sobre el canvas:")
                        pdf_doc = fitz.open(ruta_full)
                        pagina = pdf_doc[0]
                        pix = pagina.get_pixmap()
                        canvas_result = st_canvas(
                            fill_color="rgba(0,0,0,0)",
                            stroke_width=2,
                            stroke_color="blue",
                            height=pix.height,
                            width=pix.width,
                            background_color="white",
                            drawing_mode="freedraw",
                            key=f"canvas_{arc}"
                        )

                        if st.button(f"🖋️ Firmar PDF", key=f"f_{arc}"):
                            if contra_firma != info_firma["password"]:
                                st.error("❌ Contraseña incorrecta")
                            else:
                                # Aplicar firma en PDF según posición del canvas
                                if canvas_result.json_data:
                                    objects = canvas_result.json_data["objects"]
                                    for obj in objects:
                                        if obj["type"] == "image":
                                            x0 = obj["left"]
                                            y0 = obj["top"]
                                            w = obj["width"]
                                            h = obj["height"]
                                            scale_x = pagina.rect.width / canvas_result.width
                                            scale_y = pagina.rect.height / canvas_result.height
                                            rect = fitz.Rect(
                                                x0*scale_x, y0*scale_y, (x0+w)*scale_x, (y0+h)*scale_y
                                            )
                                            pagina.insert_image(rect, filename=info_firma["archivo"])

                                carpeta_firmadas = f"reservas/firmadas/{area}"
                                pdf_doc.save(f"{carpeta_firmadas}/{arc}")
                                pdf_doc.close()
                                os.remove(ruta_full)
                                st.success("✅ PDF firmado y enviado a Almacén")
                                st.rerun()

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
            color = "💛" if estados.get(f"{area}/{f}", False) else "💙"
            col_a, col_b = st.columns([3,1])
            col_a.markdown(f"{color} {f}")
            with open(f"{carpeta_area}/{f}", "rb") as file:
                if col_b.download_button("Descargar", file, file_name=f, key=f"dl_{area}_{f}"):
                    estados[f"{area}/{f}"] = True
                    with open(estado_file, "w") as ff:
                        json.dump(estados, ff)
