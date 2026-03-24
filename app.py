import streamlit as st
import os
import fitz  # PyMuPDF
import json
import shutil
import io
import numpy as np
import base64
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas v3", layout="wide")

# --- CARPETAS ---
for c in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas", "reservas/archivo"]:
    os.makedirs(c, exist_ok=True)

areas = ["Producción", "Calidad", "Mantenimiento", "Logística", "Recursos Humanos", "Ambiental", "Salud Ocupacional", "Marketing", "Financiera", "Almacén"]

usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# CONFIGURACIÓN DE FIRMAS (Asegúrate de que el archivo exista en la carpeta)
firmas_contrasena = {
    "Producción": {"archivo": "reservas/firmas/carlos_alfonso.jpeg", "password": "1234"},
}

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
            st.session_state.login, st.session_state.rol, st.session_state.user_name = True, usuarios[u]["rol"], u
            st.rerun()
        else: st.error("Error en credenciales")
else:
    with st.sidebar:
        st.write(f"👤: **{st.session_state.user_name}**")
        if st.button("Cerrar Sesión"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    rol = st.session_state.rol

    if rol == "usuario":
        st.header("📤 Enviar Reserva")
        a_u = st.selectbox("Área", areas)
        f_u = st.file_uploader("PDF", type=["pdf"])
        if st.button("Enviar"):
            if f_u:
                p_u = f"reservas/pendientes/{a_u}"
                os.makedirs(p_u, exist_ok=True)
                with open(f"{p_u}/{f_u.name}", "wb") as f: f.write(f_u.getbuffer())
                st.success("Enviado.")
            else: st.warning("Sube el archivo.")

    elif rol == "ingeniero":
        st.header("✍️ Ubicar Firma")
        a_i = st.selectbox("Área", areas)
        d_p = f"reservas/pendientes/{a_i}"
        docs = os.listdir(d_p) if os.path.exists(d_p) else []

        if not docs: st.info("Sin pendientes.")

        for d in docs:
            id_u = d.replace(".", "_")
            with st.expander(f"📄 {d}", expanded=True):
                path_d = f"{d_p}/{d}"
                info_f = firmas_contrasena.get(a_i)
                if not info_f: st.error("Área sin firma."); continue

                # --- PROCESAMIENTO ULTRA-SEGURO (FIX DEFINITIVO) ---
                doc_pdf = fitz.open(path_d)
                page = doc_pdf[0]
                pix = page.get_pixmap(dpi=72)
                img_pil = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
                
                # Convertimos la imagen a un formato "plano" para el canvas
                bg_image = Image.fromarray(np.array(img_pil))
                w, h = bg_image.size

                st.write("🖱️ **Dibuja el recuadro** para la firma:")
                
                # EL CANVAS (Ajustado para evitar AttributeError)
                canvas_out = st_canvas(
                    fill_color="rgba(255, 165, 0, 0.3)",
                    stroke_width=2,
                    stroke_color="#ff0000",
                    background_image=bg_image,
                    update_streamlit=True,
                    height=h,
                    width=w,
                    drawing_mode="rect",
                    key=f"canvas_{id_u}",
                )

                rect_f = None
                if canvas_out.json_data and canvas_out.json_data["objects"]:
                    o = canvas_out.json_data["objects"][-1]
                    x0, y0 = o["left"], o["top"]
                    x1, y1 = x0 + (o["width"] * o["scaleX"]), y0 + (o["height"] * o["scaleY"])
                    rect_f = fitz.Rect(x0, y0, x1, y1)
                    st.success("📍 Ubicación fijada.")

                pwd = st.text_input("Clave de firma", type="password", key=f"p_{id_u}")
                if st.button("🖋️ Firmar", key=f"b_{id_u}"):
                    if pwd == info_f["password"] and rect_f:
                        if os.path.exists(info_f["archivo"]):
                            page.insert_image(rect_f, filename=info_f["archivo"])
                            out_p = f"reservas/firmadas/{a_i}"
                            os.makedirs(out_p, exist_ok=True)
                            doc_pdf.save(f"{out_p}/{d}")
                            doc_pdf.close()
                            os.remove(path_d)
                            st.success("Firmado.")
                            st.rerun()
                        else: st.error("Firma no encontrada en servidor.")
                    else: st.error("Error en clave o falta recuadro.")

    elif rol == "almacen":
        st.header("📦 Almacén")
        v_t = st.radio("Ver:", ["Firmados", "Archivados"], horizontal=True)
        v_a = st.selectbox("Área", areas)
        p_a = f"reservas/firmadas/{v_a}" if v_t == "Firmados" else f"reservas/archivo/{v_a}"
        os.makedirs(p_a, exist_ok=True)
        for d in os.listdir(p_a):
            f_p = f"{p_a}/{d}"
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.write(f"📄 {d}")
            with open(f_p, "rb") as f: c2.download_button("📥", f, file_name=d, key=f"d_{f_p}")
            if v_t == "Firmados" and c3.button("📁", key=f"a_{f_p}"):
                d_a = f"reservas/archivo/{v_a}"
                os.makedirs(d_a, exist_ok=True)
                shutil.move(f_p, f"{d_a}/{d}")
                st.rerun()
