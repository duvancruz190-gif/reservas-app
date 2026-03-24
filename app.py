import streamlit as st
import os
import fitz  # PyMuPDF
import json
import shutil
import io
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas - Firma Pro", layout="wide")

# --- AUTO-CREACIÓN DE CARPETAS ---
for carpeta in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas", "reservas/archivo"]:
    os.makedirs(carpeta, exist_ok=True)

areas = ["Producción", "Calidad", "Mantenimiento", "Logística",
         "Recursos Humanos", "Ambiental", "Salud Ocupacional",
         "Marketing", "Financiera", "Almacén"]

usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# Configuración de firmas (Asegúrate de que el archivo exista en la carpeta)
firmas_contrasena = {
    "Producción": {"archivo": "reservas/firmas/carlos_alfonso.jpeg", "password": "1234"},
}

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
    with st.sidebar:
        st.title("📂 Menú")
        st.write(f"👤: **{st.session_state.user_name}**")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    rol = st.session_state.rol

    # ===========================
    # ROL: USUARIO
    # ===========================
    if rol == "usuario":
        st.header("📤 Enviar Nueva Reserva")
        area_u = st.selectbox("Área de destino", areas)
        arch = st.file_uploader("Subir PDF", type=["pdf"])
        if st.button("Enviar para Firma"):
            if arch:
                path = f"reservas/pendientes/{area_u}"
                os.makedirs(path, exist_ok=True)
                with open(f"{path}/{arch.name}", "wb") as f: f.write(arch.getbuffer())
                st.success(f"✅ Documento enviado a {area_u}")
            else: st.warning("Sube un archivo PDF.")

    # ==============================================================================
    # ROL: INGENIERO (Aquí aplicamos el parche para el AttributeError)
    # ==============================================================================
    elif rol == "ingeniero":
        st.header("✍️ Ubicar Firma con Mouse")
        area_ing = st.selectbox("Filtrar por Área", areas)
        dir_p = f"reservas/pendientes/{area_ing}"
        docs = os.listdir(dir_p) if os.path.exists(dir_p) else []

        if not docs: st.info("No hay documentos pendientes.")

        for d in docs:
            id_u = d.replace(".", "_")
            with st.expander(f"📄 Archivo: {d}", expanded=True):
                path_d = f"{dir_p}/{d}"
                info_f = firmas_contrasena.get(area_ing)
                
                if not info_f:
                    st.error("⚠️ Área sin firma configurada."); continue

                # --- PROCESAMIENTO SEGURO DE IMAGEN (EL PARCHE) ---
                doc_pdf = fitz.open(path_d)
                page = doc_pdf[0]
                pix = page.get_pixmap(dpi=72)
                
                # Paso 1: Convertir a imagen PIL
                img_pil = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
                
                # Paso 2: Convertir a NumPy Array (esto limpia los metadatos corruptos)
                img_array = np.array(img_pil)
                
                # Paso 3: Volver a PIL. Esto garantiza que Streamlit pueda procesarla.
                bg_image_limpia = Image.fromarray(img_array)
                
                w, h = bg_image_limpia.size

                st.markdown("👇 **Dibuja un recuadro** donde quieras colocar la firma:")
                
                # CANVAS - Ya no debería dar AttributeError
                canvas_out = st_canvas(
                    fill_color="rgba(255, 165, 0, 0.3)",
                    stroke_width=2,
                    stroke_color="#ff0000",
                    background_image=bg_image_limpia,
                    update_streamlit=True,
                    height=h,
                    width=w,
                    drawing_mode="rect",
                    key=f"canvas_{id_u}",
                )

                # --- VALIDACIÓN DE COORDENADAS ---
                rect_f = None
                if canvas_out.json_data and canvas_out.json_data["objects"]:
                    o = canvas_out.json_data["objects"][-1]
                    x0, y0 = o["left"], o["top"]
                    x1, y1 = x0 + (o["width"] * o["scaleX"]), y0 + (o["height"] * o["scaleY"])
                    rect_f = fitz.Rect(x0, y0, x1, y1)
                    st.success("📍 Ubicación marcada.")

                # --- PROCESO DE FIRMA ---
                st.write("---")
                pwd = st.text_input("Clave de firma", type="password", key=f"p_{id_u}")
                if st.button("🖋️ Aplicar Firma", key=f"b_{id_u}"):
                    if pwd == info_f["password"] and rect_f:
                        if os.path.exists(info_f["archivo"]):
                            # Estampar firma
                            page.insert_image(rect_f, filename=info_f["archivo"])
                            out = f"reservas/firmadas/{area_ing}"
                            os.makedirs(out, exist_ok=True)
                            doc_pdf.save(f"{out}/{d}")
                            doc_pdf.close()
                            os.remove(path_d)
                            st.success("✅ Documento firmado con éxito.")
                            st.rerun()
                        else: st.error("❌ El archivo de imagen de la firma no existe.")
                    else: st.error("❌ Clave incorrecta o no has dibujado el recuadro.")

    # ===========================
    # ROL: ALMACÉN
    # ===========================
    elif rol == "almacen":
        st.header("📦 Control de Almacén")
        v_tipo = st.radio("Ver:", ["Nuevos Firmados", "Archivados"], horizontal=True)
        v_area = st.selectbox("Área", areas)
        path_a = f"reservas/firmadas/{v_area}" if v_tipo == "Nuevos Firmados" else f"reservas/archivo/{v_area}"
        os.makedirs(path_a, exist_ok=True)

        for d in os.listdir(path_a):
            p_f = f"{path_a}/{d}"
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.write(f"📄 {d}")
            with open(p_f, "rb") as f: c2.download_button("📥", f, file_name=d, key=f"d_{p_f}")
            if v_tipo == "Nuevos Firmados" and c3.button("📁", key=f"a_{p_f}"):
                dest = f"reservas/archivo/{v_area}"
                os.makedirs(dest, exist_ok=True)
                shutil.move(p_f, f"{dest}/{d}")
                st.rerun()
