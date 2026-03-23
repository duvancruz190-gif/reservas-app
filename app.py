import streamlit as st
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer
import time
import json

# --- 1. CONFIGURACIÓN ESTRUCTURAL ---
st.set_page_config(page_title="Gestión de Reservas Digital", layout="wide")

# Rutas Base (Uso de rutas absolutas para evitar el "Oh no")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_PENDIENTES = os.path.join(BASE_DIR, "reservas", "pendientes")
PATH_FIRMADOS = os.path.join(BASE_DIR, "reservas", "firmadas")
PATH_FIRMAS = os.path.join(BASE_DIR, "reservas", "firmas")
PATH_TEMP = os.path.join(BASE_DIR, "reservas", "temp")

# Áreas del sistema
AREAS = ["Producción", "Calidad", "Mantenimiento", "Logística", "Almacén"]

# Crear carpetas si no existen
for area in AREAS:
    os.makedirs(os.path.join(PATH_PENDIENTES, area), exist_ok=True)
    os.makedirs(os.path.join(PATH_FIRMADOS, area), exist_ok=True)
os.makedirs(PATH_FIRMAS, exist_ok=True)
os.makedirs(PATH_TEMP, exist_ok=True)

# --- 2. CONFIGURACIÓN DE FIRMAS Y USUARIOS ---
USUARIOS = {
    "usuario": {"pw": "123", "rol": "usuario"},
    "ingeniero": {"pw": "999", "rol": "ingeniero"},
    "almacen": {"pw": "000", "rol": "almacen"}
}

FIRMAS_DB = {
    "Producción": {
        "archivo": os.path.join(PATH_FIRMAS, "carlos_alfonso.jpeg"),
        "clave": "1234"
    }
}

# --- 3. FUNCIONES TÉCNICAS ---
def firmar_documento(ruta_in, ruta_out, ruta_img):
    try:
        doc = fitz.open(ruta_in)
        page = doc[0] # Primera página
        # Rectángulo: (x0, y0, x1, y1) -> Ajustado para estar sobre la línea FIRMA 1
        # x: 220-380 (Centro), y: 620-710 (Sobre la línea)
        rect = fitz.Rect(220, 620, 380, 710)
        page.insert_image(rect, filename=ruta_img)
        doc.save(ruta_out)
        doc.close()
        return True
    except Exception as e:
        st.error(f"Error técnico al estampar firma: {e}")
        return False

# --- 4. GESTIÓN DE SESIÓN ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if "rol" not in st.session_state: st.session_state.rol = None
if "preview_file" not in st.session_state: st.session_state.preview_file = None

# --- 5. INTERFAZ DE LOGIN ---
if not st.session_state.autenticado:
    st.title("🔐 Acceso al Sistema")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar", use_container_width=True):
        if u in USUARIOS and USUARIOS[u]["pw"] == p:
            st.session_state.autenticado = True
            st.session_state.rol = USUARIOS[u]["rol"]
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

else:
    # MENÚ LATERAL
    with st.sidebar:
        st.write(f"👤 Usuario: **{st.session_state.user}**")
        if st.button("Cerrar Sesión"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    # ==========================================
    # VISTA USUARIO: SUBIR DOCUMENTOS
    # ==========================================
    if st.session_state.rol == "usuario":
        st.header("📤 Enviar Reserva para Firma")
        area_dest = st.selectbox("Área de destino", AREAS)
        file = st.file_uploader("Subir archivo PDF", type="pdf")
        if st.button("Enviar al Ingeniero") and file:
            dest = os.path.join(PATH_PENDIENTES, area_dest, file.name)
            with open(dest, "wb") as f:
                f.write(file.getbuffer())
            st.success(f"✅ Enviado a {area_dest}")

    # ==========================================
    # VISTA INGENIERO: VISTA PREVIA Y FIRMA
    # ==========================================
    elif st.session_state.rol == "ingeniero":
        st.header("✍️ Revisión y Firma (Ingeniería)")
        area_ing = st.selectbox("Área a revisar", AREAS)
        ruta_p = os.path.join(PATH_PENDIENTES, area_ing)
        pendientes = [f for f in os.listdir(ruta_p) if f.endswith(".pdf")]

        if not pendientes:
            st.info(f"No hay pendientes en {area_ing}")

        for arc in pendientes:
            with st.expander(f"📄 Reserva: {arc}"):
                full_orig = os.path.join(ruta_p, arc)
                c1, c2 = st.columns(2)
                
                with c1:
                    st.write("**Documento Original:**")
                    if os.path.exists(full_orig):
                        pdf_viewer(full_orig, width=400)
                
                with c2:
                    st.write("**Validar Firma:**")
                    pass_f = st.text_input("Clave de Firma", type="password", key=f"pw_{arc}")
                    if st.button("🔍 Generar Vista Previa", key=f"btn_v_{arc}"):
                        if area_ing in FIRMAS_DB:
                            f_info = FIRMAS_DB[area_ing]
                            if pass_f == f_info["clave"]:
                                if os.path.exists(f_info["archivo"]):
                                    tmp_path = os.path.join(PATH_TEMP, f"PRE_{arc}")
                                    if firmar_documento(full_orig, tmp_path, f_info["archivo"]):
                                        st.session_state.preview_file = tmp_path
                                        st.success("Vista previa lista abajo")
                                else: st.error(f"Firma no encontrada en: {f_info['archivo']}")
                            else: st.error("Clave de firma incorrecta")
                        else: st.error("Área sin firma configurada")

                # Mostrar Previsualización si se generó para este archivo
                if st.session_state.preview_file and f"PRE_{arc}" in st.session_state.preview_file:
                    st.divider()
                    st.subheader("🔍 REVISIÓN DE POSICIÓN DE FIRMA")
                    pdf_viewer(st.session_state.preview_file, width=700)
                    if st.button("🚀 CONFIRMAR Y ENVIAR ALMACÉN", key=f"conf_{arc}"):
                        final_path = os.path.join(PATH_FIRMADOS, area_ing, arc)
                        os.rename(st.session_state.preview_file, final_path)
                        os.remove(full_orig)
                        st.session_state.preview_file = None
                        st.success("¡Documento enviado exitosamente!")
                        time.sleep(1)
                        st.rerun()

    # ==========================================
    # VISTA ALMACÉN: DESCARGA
    # ==========================================
    elif st.session_state.rol == "almacen":
        st.header("📦 Reservas Listas (Almacén)")
        area_al = st.selectbox("Área", AREAS)
        ruta_f = os.path.join(PATH_FIRMADOS, area_al)
        firmados = [f for f in os.listdir(ruta_f) if f.endswith(".pdf")]
        
        for f in firmados:
            col_t, col_b = st.columns([3, 1])
            col_t.write(f"📄 {f}")
            with open(os.path.join(ruta_f, f), "rb") as file_data:
                col_b.download_button("Descargar", file_data, file_name=f"FIRMADO_{f}", key=f"dl_{f}")
