import streamlit as st
import os
import fitz  # PyMuPDF
import io
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión de Firmas Pro v6", layout="wide")

# --- CREACIÓN AUTOMÁTICA DE CARPETAS ---
for carpeta in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas", "reservas/archivo"]:
    os.makedirs(carpeta, exist_ok=True)

# --- CONFIGURACIÓN DE DATOS ---
areas = ["Producción", "Calidad", "Mantenimiento", "Logística",
         "Recursos Humanos", "Ambiental", "Salud Ocupacional",
         "Marketing", "Financiera", "Almacén"]

usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# IMPORTANTE: Asegúrate de que el archivo exista en 'reservas/firmas/'
# Ejemplo: sube 'carlos_alfonso.jpeg' a la carpeta 'reservas/firmas/' en GitHub
firmas_contrasena = {
    "Producción": {"archivo": "reservas/firmas/carlos_alfonso.jpeg", "password": "1234"},
}

# --- CONTROL DE SESIÓN ---
if "login" not in st.session_state:
    st.session_state.login = False

# ===========================
# LOGIN
# ===========================
if not st.session_state.login:
    st.title("🔐 Acceso al Sistema de Firmas")
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
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.title("📂 Menú Principal")
        st.write(f"👤 Usuario: **{st.session_state.user_name}**")
        st.write(f"🔑 Rol: **{st.session_state.rol.upper()}**")
        st.write("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    st.title("📋 Panel de Gestión de Reservas Digitales")
    rol = st.session_state.get('rol')

    # ===========================
    # ROL: USUARIO (ENVÍO)
    # ===========================
    if rol == "usuario":
        st.header("📤 Enviar Nueva Reserva")
        area_u = st.selectbox("Selecciona área de destino", areas)
        arch = st.file_uploader("Subir PDF de Reserva", type=["pdf"])

        if st.button("Enviar para Firma"):
            if arch:
                path_dest = f"reservas/pendientes/{area_u}"
                os.makedirs(path_dest, exist_ok=True)
                with open(f"{path_dest}/{arch.name}", "wb") as f:
                    f.write(arch.getbuffer())
                st.success(f"✅ Documento enviado al área de {area_u}")
            else:
                st.warning("Selecciona un archivo PDF.")

    # ===========================
    # ROL: INGENIERO (FIRMA ESTABLE)
    # ===========================
    elif rol == "ingeniero":
        st.header("✍️ Ubicación Estampado de Firma")
        
        area_ing = st.selectbox("Área a Revisar", areas)
        dir_pendientes = f"reservas/pendientes/{area_ing}"
        lista_pendientes = os.listdir(dir_pendientes) if os.path.exists(dir_pendientes) else []

        if not lista_pendientes:
            st.info(f"No hay documentos pendientes para el área de {area_ing}.")

        for doc_name in lista_pendientes:
            id_u = doc_name.replace(".", "_")
            with st.expander(f"📄 Archivo: {doc_name}", expanded=True):
                path_doc = f"{dir_pendientes}/{doc_name}"
                info_f = firmas_contrasena.get(area_ing)
                
                if not info_f:
                    st.error("⚠️ Área sin firma configurada en el servidor."); continue

                # --- PROCESAMIENTO DEL PDF ---
                doc_pdf = fitz.open(path_doc)
                page = doc_pdf[0]
                # Usamos 72 DPI para que el canvas coincida exacto con las coordenadas del PDF
                pix = page.get_pixmap(dpi=72)
                img_pil = Image.open(io.BytesIO(pix.tobytes("png")))
                w, h = img_pil.size

                # PROCESAMIENTO DE REFERENCIA: Mostramos la miniatura con cuadrícula
                st.info("🖱️ **Dibuja un recuadro** en el lienzo gris simulando la ubicación en el PDF.")

                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.image(img_pil, caption="1. Documento Original (Míralo aquí)", use_container_width=True)

                with col2:
                    st.write("2. Dibuja el recuadro aquí (Lienzo Gris):")
                    # NO usamos background_image, evitando el AttributeError
                    canvas_out = st_canvas(
                        fill_color="rgba(255, 165, 0, 0.3)", # Naranja transparente para el recuadro
                        stroke_width=2,
                        stroke_color="#ff0000",
                        background_color="#eeeeee", # Fondo gris claro neutro
                        update_streamlit=True,
                        height=h,
                        width=w,
                        drawing_mode="rect",
                        key=f"canvas_{id_u}",
                    )

                # --- VALIDACIÓN DE COORDENADAS ---
                rect_final = None
                if canvas_out.json_data and canvas_out.json_data["objects"]:
                    o = canvas_out.json_data["objects"][-1]
                    # Calculamos el rectángulo para PyMuPDF
                    x0, y0 = o["left"], o["top"]
                    x1, y1 = x0 + (o["width"] * o["scaleX"]), y0 + (o["height"] * o["scaleY"])
                    rect_final = fitz.Rect(x0, y0, x1, y1)
                    st.success("📍 Posición capturada correctamente.")

                # --- PROCESO DE FIRMA ---
                st.write("---")
                pass_ing = st.text_input("Clave para firmar", type="password", key=f"p_{id_u}")

                if st.button("🖋️ Aplicar Firma", key=f"b_{id_u}"):
                    if pass_ing == info_f["password"] and rect_final:
                        if os.path.exists(info_f["archivo"]):
                            # Estampar firma en el PDF real
                            page.insert_image(rect_final, filename=info_f["archivo"])
                            
                            # Guardar y mover
                            out_dir = f"reservas/firmadas/{area_ing}"
                            os.makedirs(out_dir, exist_ok=True)
                            doc_pdf.save(f"{out_p}/{d}")
                            doc_pdf.save(f"{out_dir}/{doc_name}")
                            doc_pdf.close()
                            
                            os.remove(path_doc)
                            st.success("✅ Firma aplicada con éxito.")
                            st.rerun()
                        else:
                            st.error(f"❌ No se encontró la firma en la carpeta del servidor: {info_f['archivo']}")
                    else:
                        st.error("❌ Clave incorrecta o falta recuadro en el lienzo.")

    # ===========================
    # ROL: ALMACÉN (DESCARGA)
    # ===========================
    elif rol == "almacen":
        st.header("📦 Control de Salida de Almacén")
        v_tipo = st.radio("Ver:", ["Nuevos Firmados", "Histórico Archivados"], horizontal=True)
        v_area = st.selectbox("Selecciona el Área", areas)

        path_alm = f"reservas/firmadas/{v_area}" if v_tipo == "Nuevos Firmados" else f"reservas/archivo/{v_area}"
        os.makedirs(path_alm, exist_ok=True)

        docs_alm = os.listdir(path_alm)
        for d in docs_alm:
            p_full = f"{path_alm}/{d}"
            col1, col2, col3 = st.columns([4, 1, 1])
            col1.write(f"📄 {d}")
            
            with open(p_full, "rb") as f_bytes:
                col2.download_button("📥 Descargar", f_bytes, file_name=d, key=f"d_{p_full}")

            if v_tipo == "Nuevos Firmados":
                if col3.button("📁 Archivar", key=f"a_{p_full}"):
                    dest_arch = f"reservas/archivo/{v_area}"
                    os.makedirs(dest_arch, exist_ok=True)
                    shutil.move(p_full, f"{dest_arch}/{d}")
                    st.rerun()
