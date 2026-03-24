import streamlit as st
import os
import fitz  # PyMuPDF
import json
import shutil
import io
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas - Firma Pro", layout="wide")

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

# --- FIRMAS CONFIGURADAS ---
# Asegúrate de que las rutas a las imágenes de firma existan
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
        st.write("---")

        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.title("📋 Gestión de Reservas Digitales")
    rol = st.session_state.get('rol')

    # ===========================
    # ROL: USUARIO
    # ===========================
    if rol == "usuario":
        st.header("📤 Enviar Nueva Reserva")
        area_u = st.selectbox("Selecciona tu área", areas)
        arch = st.file_uploader("Subir PDF", type=["pdf"])

        if st.button("Enviar al Ingeniero"):
            if arch:
                carpeta_area = f"reservas/pendientes/{area_u}"
                os.makedirs(carpeta_area, exist_ok=True)
                with open(f"{carpeta_area}/{arch.name}", "wb") as f:
                    f.write(arch.getbuffer())
                st.success(f"✅ Documento enviado correctamente a {area_u}.")
            else:
                st.warning("Por favor, selecciona un archivo PDF.")

    # ===========================
    # ROL: INGENIERO (FIRMA INTERACTIVA)
    # ===========================
    elif rol == "ingeniero":
        st.header("✍️ Revisión y Firma con Mouse")
        st.info("Instrucciones: Selecciona el área, abre el documento y dibuja un recuadro donde quieras colocar la firma.")

        area_ing = st.selectbox("Área a revisar", areas)
        carpeta_area = f"reservas/pendientes/{area_ing}"
        pendientes = os.listdir(carpeta_area) if os.path.exists(carpeta_area) else []

        if not pendientes:
            st.info(f"No hay documentos pendientes para el área de {area_ing}.")

        for arc in pendientes:
            file_id = arc.replace(".", "_")
            with st.expander(f"📄 Documento: {arc}", expanded=True):
                ruta_full = f"{carpeta_area}/{arc}"
                info_firma = firmas_contrasena.get(area_ing)

                if not info_firma:
                    st.error(f"❌ No hay firma configurada para el área {area_ing}.")
                    continue

                # --- CONVERTIR PDF A IMAGEN USANDO PYMUPDF (Sin Poppler) ---
                doc_pdf = fitz.open(ruta_full)
                pagina_orig = doc_pdf[0]
                pix = pagina_orig.get_pixmap(dpi=72) # Coincidencia 1:1 con puntos PDF
                img_data = pix.tobytes("png")
                pdf_page_img = Image.open(io.BytesIO(img_data))
                w_pdf, h_pdf = pdf_page_img.size

                st.write("🖱️ **Dibuja un recuadro** para posicionar la firma:")
                
                # Canvas interactivo
                canvas_result = st_canvas(
                    fill_color="rgba(255, 165, 0, 0.3)", # Naranja transparente
                    stroke_width=2,
                    stroke_color="#FF0000",
                    background_image=pdf_page_img,
                    update_streamlit=True,
                    height=h_pdf,
                    width=w_pdf,
                    drawing_mode="rect",
                    key=f"canvas_{file_id}",
                )

                # Captura de coordenadas
                rect_coords = None
                if canvas_result.json_data and canvas_result.json_data["objects"]:
                    obj = canvas_result.json_data["objects"][-1]
                    l, t = obj["left"], obj["top"]
                    w, h = obj["width"] * obj["scaleX"], obj["height"] * obj["scaleY"]
                    rect_coords = fitz.Rect(l, t, l + w, t + h)
                    st.success("📍 Posición de firma establecida.")

                st.write("---")
                contra_f = st.text_input("Introduce tu clave de firma", type="password", key=f"pw_{arc}")

                if st.button("🖋️ Estampar Firma y Enviar", key=f"btn_{arc}"):
                    if contra_f == info_firma["password"]:
                        if rect_coords:
                            if os.path.exists(info_firma["archivo"]):
                                # Insertar imagen en el PDF real
                                pagina_orig.insert_image(rect_coords, filename=info_firma["archivo"])
                                
                                # Guardar en carpeta de firmados
                                carpeta_firmadas = f"reservas/firmadas/{area_ing}"
                                os.makedirs(carpeta_firmadas, exist_ok=True)
                                
                                doc_pdf.save(f"{carpeta_firmadas}/{arc}")
                                doc_pdf.close()
                                
                                # Eliminar el pendiente
                                os.remove(ruta_full)
                                
                                st.success("✅ Documento firmado con éxito.")
                                st.rerun()
                            else:
                                st.error("❌ El archivo de imagen de la firma no existe.")
                        else:
                            st.error("❌ Debes dibujar primero el recuadro donde irá la firma.")
                    else:
                        st.error("❌ Clave de firma incorrecta.")

    # ===========================
    # ROL: ALMACÉN
    # ===========================
    elif rol == "almacen":
        st.header("📦 Control de Documentos Firmados")

        # Cargar estados de descarga
        estado_file = "reservas/firmadas/estado.json"
        if os.path.exists(estado_file):
            with open(estado_file, "r") as f:
                estados = json.load(f)
        else:
            estados = {}

        vista = st.radio("Sección", ["Firmados (Pendientes de Almacén)", "Archivados"], horizontal=True)
        area_alm = st.selectbox("Selecciona el área", areas)

        carpeta_alm = f"reservas/firmadas/{area_alm}" if vista == "Firmados (Pendientes de Almacén)" else f"reservas/archivo/{area_alm}"
        os.makedirs(carpeta_alm, exist_ok=True)

        archivos = os.listdir(carpeta_alm)
        busqueda = st.text_input("🔍 Buscar archivo...")
        if busqueda:
            archivos = [f for f in archivos if busqueda.lower() in f.lower()]

        st.write(f"📄 Total documentos: {len(archivos)}")

        for f_name in archivos:
            ruta = f"{carpeta_alm}/{f_name}"
            # Icono según si ya se descargó antes
            icono = "✅" if estados.get(f"{area_alm}/{f_name}", False) else "🆕"

            col1, col2, col3, col4 = st.columns([4,1,1,1])
            col1.write(f"{icono} {f_name}")

            # Botón Descargar
            with open(ruta, "rb") as file:
                if col2.download_button("⬇️", file, file_name=f_name, key=f"dl_{ruta}"):
                    estados[f"{area_alm}/{f_name}"] = True
                    with open(estado_file, "w") as ff:
                        json.dump(estados, ff)

            # Botón Archivar
            if vista == "Firmados (Pendientes de Almacén)":
                if col3.button("📁", key=f"arc_{ruta}", help="Mover a archivos"):
                    destino = f"reservas/archivo/{area_alm}"
                    os.makedirs(destino, exist_ok=True)
                    shutil.move(ruta, f"{destino}/{f_name}")
                    st.rerun()

            # Botón Eliminar
            if col4.button("🗑️", key=f"del_{ruta}", help="Borrar permanentemente"):
                os.remove(ruta)
                st.rerun()
