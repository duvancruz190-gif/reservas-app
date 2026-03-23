import streamlit as st
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer
import time

# --- 1. CONFIGURACIÓN DE RUTAS SEGURAS ---
st.set_page_config(page_title="Gestión de Reservas", layout="wide")

# Obtener la ruta del directorio donde está este archivo .py
DIRECTORIO_RAIZ = os.path.dirname(os.path.abspath(__file__))

def obtener_ruta(*args):
    """Crea una ruta absoluta segura"""
    return os.path.join(DIRECTORIO_RAIZ, *args)

# Crear estructura de carpetas automáticamente
AREAS = ["Producción", "Calidad", "Mantenimiento", "Logística"]
carpetas_necesarias = [
    ["reservas", "pendientes"],
    ["reservas", "firmadas"],
    ["reservas", "firmas"],
    ["reservas", "temp"]
]

for base in carpetas_necesarias:
    for area in AREAS:
        os.makedirs(obtener_ruta(*base, area), exist_ok=True)
    os.makedirs(obtener_ruta(*base), exist_ok=True)

# --- 2. CONFIGURACIÓN DE USUARIOS Y FIRMAS ---
USUARIOS = {
    "usuario": {"pw": "123", "rol": "usuario"},
    "ingeniero": {"pw": "999", "rol": "ingeniero"},
    "almacen": {"pw": "000", "rol": "almacen"}
}

# Configuración específica para tu archivo
FIRMA_CARLOS = obtener_ruta("reservas", "firmas", "carlos_alfonso.jpeg")
CLAVE_CARLOS = "1234"

# --- 3. LÓGICA DE FIRMA ---
def procesar_firma(ruta_entrada, ruta_salida, ruta_imagen):
    try:
        if not os.path.exists(ruta_imagen):
            return False, f"No se encontró la firma en {ruta_imagen}"
        
        doc = fitz.open(ruta_entrada)
        page = doc[0]
        # Coordenadas ajustadas para estar SOBRE la línea de 'FIRMA 1'
        rect = fitz.Rect(220, 620, 380, 710)
        page.insert_image(rect, filename=ruta_imagen)
        doc.save(ruta_salida)
        doc.close()
        return True, "OK"
    except Exception as e:
        return False, str(e)

# --- 4. ESTADO DE SESIÓN ---
if "auth" not in st.session_state: st.session_state.auth = False
if "prev_pdf" not in st.session_state: st.session_state.prev_pdf = None

# --- 5. INTERFAZ ---
if not st.session_state.auth:
    st.title("🔐 Acceso al Sistema")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Entrar", use_container_width=True):
        if u in USUARIOS and USUARIOS[u]["pw"] == p:
            st.session_state.auth = True
            st.session_state.rol = USUARIOS[u]["rol"]
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
else:
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user.upper()}**")
        if st.button("Cerrar Sesión"):
            st.session_state.auth = False
            st.rerun()

    # --- VISTA INGENIERO ---
    if st.session_state.rol == "ingeniero":
        st.header("✍️ Revisión y Firma de Reservas")
        area_actual = st.selectbox("Selecciona Área", AREAS)
        path_p = obtener_ruta("reservas", "pendientes", area_actual)
        
        archivos = [f for f in os.listdir(path_p) if f.lower().endswith(".pdf")]
        
        if not archivos:
            st.info(f"No hay PDFs pendientes en {area_actual}")

        for arc in archivos:
            with st.expander(f"📄 Archivo: {arc}"):
                ruta_full_orig = os.path.join(path_p, arc)
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Original:**")
                    if os.path.exists(ruta_full_orig):
                        pdf_viewer(ruta_full_orig, width=350)
                
                with col2:
                    st.write("**Validar:**")
                    clave_f = st.text_input("Clave de Firma", type="password", key=f"f_{arc}")
                    if st.button("🔍 Ver Vista Previa", key=f"v_{arc}"):
                        if clave_f == CLAVE_CARLOS:
                            tmp_path = obtener_ruta("reservas", "temp", f"PRE_{arc}")
                            exito, msg = procesar_firma(ruta_full_orig, tmp_path, FIRMA_CARLOS)
                            if exito:
                                st.session_state.prev_pdf = tmp_path
                                st.success("Vista previa generada correctamente.")
                            else:
                                st.error(f"Error: {msg}")
                        else:
                            st.error("Clave de firma incorrecta.")

                if st.session_state.prev_pdf and f"PRE_{arc}" in st.session_state.prev_pdf:
                    st.divider()
                    st.subheader("🔍 REVISIÓN DE FIRMA")
                    pdf_viewer(st.session_state.prev_pdf, width=700)
                    if st.button("🚀 CONFIRMAR Y ENVIAR", key=f"c_{arc}"):
                        ruta_final = obtener_ruta("reservas", "firmadas", area_actual, arc)
                        os.rename(st.session_state.prev_pdf, ruta_final)
                        os.remove(ruta_full_orig)
                        st.session_state.prev_pdf = None
                        st.success("¡Documento enviado!")
                        time.sleep(1)
                        st.rerun()

    # --- VISTA USUARIO (SUBIR) ---
    elif st.session_state.rol == "usuario":
        st.header("📤 Subir Nueva Reserva")
        destino = st.selectbox("Área", AREAS)
        up = st.file_uploader("PDF", type="pdf")
        if st.button("Enviar") and up:
            with open(obtener_ruta("reservas", "pendientes", destino, up.name), "wb") as f:
                f.write(up.getbuffer())
            st.success("Archivo subido.")

    # --- VISTA ALMACÉN (DESCARGAR) ---
    elif st.session_state.rol == "almacen":
        st.header("📦 Reservas Firmadas")
        area_al = st.selectbox("Área", AREAS)
        path_f = obtener_ruta("reservas", "firmadas", area_al)
        finales = [f for f in os.listdir(path_f) if f.endswith(".pdf")]
        for f in finales:
            with open(os.path.join(path_f, f), "rb") as file_data:
                st.download_button(f"Descargar {f}", file_data, file_name=f)
