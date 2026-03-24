import streamlit as st
import os
import fitz  # PyMuPDF
import json
import shutil
import io
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión de Reservas - Firma Pro", layout="wide")

# --- AUTO-CREACIÓN DE CARPETAS ---
for carpeta in [
    "reservas/pendientes",
    "reservas/firmadas",
    "reservas/firmas",
    "reservas/archivo"
]:
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

# IMPORTANTE: Verifica que los nombres de los archivos coincidan con lo que subas a GitHub
firmas_contrasena = {
    "Producción": {"archivo": "reservas/firmas/carlos_alfonso.jpeg", "password": "1234"},
}

# --- CONTROL DE SESIÓN ---
if "login" not in st.session_state:
    st.session_state.login = False

# ===========================
# SECCIÓN: LOGIN
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
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.title("📂 Menú")
        st.write(f"👤: **{st.session_state.user_name}**")
        st.write(f"🔑: **{st.session_state.rol.upper()}**")
        st.write("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.title("📋 Panel de Gestión de Reservas")
    rol = st.session_state.rol

    # ===========================
    # ROL: USUARIO (ENVÍO)
    # ===========================
    if rol == "usuario":
        st.header("📤 Enviar Nueva Reserva")
        area_u = st.selectbox("Selecciona área de destino", areas)
        arch = st.file_uploader("Subir PDF", type=["pdf"])

        if st.button("Enviar para Firma"):
            if arch:
                path_dest = f"reservas/pendientes/{area_u}"
                os.makedirs(path_dest, exist_ok=True)
                with open(f"{path_dest}/{arch.name}", "wb") as f:
                    f.write(arch.getbuffer())
                st.success(f"✅ Enviado a {area_u}")
            else:
                st.warning("Adjunta un archivo.")

    # ===========================
    # ROL: INGENIERO (FIRMA INTERACTIVA)
    # ===========================
    elif rol == "ingeniero":
        st.header("✍️ Revisión y Ubicación de Firma")
        
        area_ing = st.selectbox("Filtrar por Área", areas)
        dir_pendientes = f"reservas/pendientes/{area_ing}"
        lista_pendientes = os.listdir(dir_pendientes) if os.path.exists(dir_pendientes) else []

        if not lista_pendientes:
            st.info("No hay documentos pendientes.")

        for doc_name in lista_pendientes:
            id_u = doc_name.replace(".", "_")
            with st.expander(f"📄 Archivo: {doc_name}", expanded=True):
                path_doc = f"{dir_pendientes}/{doc_name}"
                info_f = firmas_contrasena.get(area_ing)

                if not info_f:
                    st.error("⚠️ Área sin firma configurada.")
                    continue

                # --- PROCESAMIENTO DE IMAGEN PARA EL CANVAS ---
                pdf_doc = fitz.open(path_doc)
                page = pdf_doc[0]
                # Usamos 72 DPI para que el canvas coincida exacto con las coordenadas del PDF
                pix = page.get_pixmap(dpi=72)
                img_bytes = pix.tobytes("png")
                img_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                w, h = img_pil.size

                st.markdown("👇 **Dibuja un recuadro con el mouse** donde quieras la firma:")
                
                # CANVAS - El "dibujador" interactivo
                canvas_out = st_canvas(
                    fill_color="rgba(255, 165, 0, 0.3)",
                    stroke_width=2,
                    stroke_color="#ff0000",
                    background_image=img_pil,
                    update_streamlit=True,
                    height=h,
                    width=w,
                    drawing_mode="rect",
                    key=f"canvas_{id_u}",
                )

                # VALIDACIÓN DE COORDENADAS
                rect_final = None
                if canvas_out.json_data and canvas_out.json_data["objects"]:
                    o = canvas_out.json_data["objects"][-1]
                    # Calculamos el rectángulo para PyMuPDF
                    x0, y0 = o["left"], o["top"]
                    x1, y1 = x0 + (o["width"] * o["scaleX"]), y0 + (o["height"] * o["scaleY"])
                    rect_final = fitz.Rect(x0, y0, x1, y1)
                    st.success("📍 Ubicación marcada correctamente.")

                # PROCESO DE FIRMA
                st.write("---")
                pass_ing = st.text_input("Clave para firmar", type="password", key=f"p_{id_u}")

                if st.button("🖋️ Aplicar Firma", key=f"b_{id_u}"):
                    if pass_ing == info_f["password"]:
                        if rect_final:
                            if os.path.exists(info_f["archivo"]):
                                # Estampar firma en el PDF real
                                page.insert_image(rect_final, filename=info_f["archivo"])
                                
                                # Guardar y mover
                                out_dir = f"reservas/firmadas/{area_ing}"
                                os.makedirs(out_dir, exist_ok=True)
                                pdf_doc.save(f"{out_dir}/{doc_name}")
                                pdf_doc.close()
                                
                                os.remove(path_doc)
                                st.success("✅ Firma aplicada con éxito.")
                                st.rerun()
                            else:
                                st.error(f"Archivo de firma no encontrado: {info_f['archivo']}")
                        else:
                            st.warning("Dibuja un recuadro primero.")
                    else:
                        st.error("Contraseña incorrecta.")

    # ===========================
    # ROL: ALMACÉN (DESCARGA Y ARCHIVO)
    # ===========================
    elif rol == "almacen":
        st.header("📦 Control de Salida")
        v_tipo = st.radio("Ver:", ["Nuevos Firmados", "Histórico Archivados"], horizontal=True)
        v_area = st.selectbox("Área", areas)

        path_alm = f"reservas/firmadas/{v_area}" if v_tipo == "Nuevos Firmados" else f"reservas/archivo/{v_area}"
        os.makedirs(path_alm, exist_ok=True)

        docs_alm = os.listdir(path_alm)
        for d in docs_alm:
            p_full = f"{path_alm}/{d}"
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.write(f"📄 {d}")
            
            with open(p_full, "rb") as f_bytes:
                c2.download_button("📥", f_bytes, file_name=d, key=f"d_{p_full}")

            if v_tipo == "Nuevos Firmados":
                if c3.button("📁", key=f"a_{p_full}", help="Archivar"):
                    dest_arch = f"reservas/archivo/{v_area}"
                    os.makedirs(dest_arch, exist_ok=True)
                    shutil.move(p_full, f"{dest_arch}/{d}")
                    st.rerun()
