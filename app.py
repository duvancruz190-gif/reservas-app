import streamlit as st
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Eternit - Gestión de Reservas", layout="wide")

# Asegurar que las carpetas existan para evitar errores
for c in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas"]:
    os.makedirs(c, exist_ok=True)

# --- BASE DE DATOS DE USUARIOS ---
usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    
    "calidad": {
        "password": "999", 
        "rol": "ingeniero", 
        "pass_firma": "calidad123", 
        "archivo_firma": "reservas/firmas/calidad.jpeg"
    },
    
    "ambiental": {
        "password": "888", 
        "rol": "ingeniero", 
        "pass_firma": "ambiental123", 
        "archivo_firma": "reservas/firmas/ambiental .jpeg" # Mantiene el espacio detectado en tu GitHub
    },
    
    "almacen": {"password": "000", "rol": "almacen"}
}

if "login" not in st.session_state:
    st.session_state.login = False

# --- PANTALLA DE LOGIN ---
if not st.session_state.login:
    st.title("🔐 Acceso al Sistema Eternit")
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
        st.title("📂 Menú")
        st.write(f"👤 Usuario: **{st.session_state.user_name.upper()}**")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # --- VISTA PARA CALIDAD Y AMBIENTAL ---
    if st.session_state.rol == "ingeniero":
        st.header(f"✍️ Bandeja de Revisión - {st.session_state.user_name.capitalize()}")
        pends = [f for f in os.listdir("reservas/pendientes") if f.endswith(".pdf")]
        
        if not pends:
            st.info("No hay documentos pendientes de firma.")
        
        for arc in pends:
            with st.expander(f"📄 Revisar Archivo: {arc}"):
                ruta_pdf = f"reservas/pendientes/{arc}"
                
                # 1. VISOR PROFESIONAL (Soluciona el bloqueo del navegador)
                pdf_viewer(ruta_pdf, width=800)
                
                st.write("---")
                # 2. SECCIÓN DE FIRMA SEGURA CON CLAVE
                clave_f = st.text_input("Introduce tu Clave de Firma", type="password", key=f"f_{arc}")
                
                if st.button(f"Firmar y Enviar a Almacén", key=f"b_{arc}"):
                    datos = usuarios[st.session_state.user_name]
                    
                    if clave_f != datos["pass_firma"]:
                        st.error("❌ Clave de firma incorrecta.")
                    elif not os.path.exists(datos["archivo_firma"]):
                        st.error(f"❌ No se encuentra el archivo de firma: {datos['archivo_firma']}")
                    else:
                        try:
                            doc = fitz.open(ruta_pdf)
                            # Coordenadas calculadas para la línea "FIRMA 1" de Eternit
                            rect_firma = fitz.Rect(90, 650, 240, 710) 
                            doc[0].insert_image(rect_firma, filename=datos["archivo_firma"])
                            doc.save(f"reservas/firmadas/{arc}")
                            doc.close()
                            os.remove(ruta_pdf) # Borrar de pendientes
                            st.success("✅ Documento firmado con éxito.")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error técnico: {e}")
