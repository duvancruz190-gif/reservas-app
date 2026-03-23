import streamlit as st
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer
import time

# --- 1. AJUSTES DE RUTAS ABSOLUTAS ---
ROOT = os.path.dirname(os.path.abspath(__file__))

def get_p(relative_path):
    p = os.path.join(ROOT, relative_path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p

# --- 2. CONFIGURACIÓN ---
st.set_page_config(page_title="App Reservas", layout="wide")

# Rutas críticas
FIRMA_IMG = get_p("reservas/firmas/carlos_alfonso.jpeg")
DIR_PENDIENTES = get_p("reservas/pendientes/")
DIR_FIRMADOS = get_p("reservas/firmadas/")
DIR_TEMP = get_p("reservas/temp/")

# --- 3. LÓGICA DE FIRMADO ---
def aplicar_firma(pdf_in, pdf_out, img_path):
    try:
        doc = fitz.open(pdf_in)
        # Rectángulo sobre la línea 'FIRMA 1' (ajusta si es necesario)
        rect = fitz.Rect(220, 620, 380, 710) 
        doc[0].insert_image(rect, filename=img_path)
        doc.save(pdf_out)
        doc.close()
        return True
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return False

# --- 4. INTERFAZ ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Login Ingeniería")
    if st.button("Entrar como Ingeniero (999)"):
        st.session_state.auth = True
        st.rerun()
else:
    st.sidebar.button("Cerrar Sesión", on_click=lambda: st.session_state.update({"auth": False}))
    
    st.header("📋 Gestión de Firmas")
    
    # Listar archivos PDF
    archivos = [f for f in os.listdir(DIR_PENDIENTES) if f.lower().endswith(".pdf")]
    
    if not archivos:
        st.info("No hay documentos pendientes. Sube uno para probar.")
        # Opcional: Subida rápida para pruebas
        up = st.file_uploader("Subir PDF de prueba", type="pdf")
        if up:
            with open(os.path.join(DIR_PENDIENTES, up.name), "wb") as f:
                f.write(up.getbuffer())
            st.rerun()

    for arc in archivos:
        with st.expander(f"📄 Revisar: {arc}"):
            path_orig = os.path.join(DIR_PENDIENTES, arc)
            
            # Previsualización Original (Solo si el archivo existe y es válido)
            if os.path.exists(path_orig):
                pdf_viewer(path_orig, width=500, key=f"orig_{arc}")
            
            clave = st.text_input("Clave de Firma", type="password", key=f"pw_{arc}")
            
            if st.button("🖋️ Firmar y Enviar", key=f"btn_{arc}"):
                if clave == "1234":
                    if os.path.exists(FIRMA_IMG):
                        path_final = os.path.join(DIR_FIRMADOS, arc)
                        # Firmamos directamente al destino
                        if aplicar_firma(path_orig, path_final, FIRMA_IMG):
                            os.remove(path_orig) # Borramos original
                            st.success("✅ ¡Firmado y enviado a Almacén!")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.error(f"Falta la imagen de la firma en: {FIRMA_IMG}")
                else:
                    st.error("Clave incorrecta")

    st.divider()
    st.subheader("📦 Almacén (Documentos Listos)")
    firmados = os.listdir(DIR_FIRMADOS)
    for f in firmados:
        with open(os.path.join(DIR_FIRMADOS, f), "rb") as file_data:
            st.download_button(f"📥 Descargar {f}", file_data, file_name=f"FIRMADO_{f}", key=f"dl_{f}")
