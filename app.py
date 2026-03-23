import streamlit as st
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Eternit - Gestión de Reservas", layout="wide")

# Asegurar que las carpetas existan en el servidor de Streamlit
for c in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas"]:
    os.makedirs(c, exist_ok=True)

# --- BASE DE DATOS DE USUARIOS ---
# Nota: Los nombres de usuario aquí deben estar en MINÚSCULAS
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
        # Se mantiene el espacio detectado en tu archivo de GitHub
        "archivo_firma": "reservas/firmas/ambiental .jpeg" 
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
        # PROTECCIÓN: Limpiamos espacios y pasamos a minúsculas para evitar el KeyError
        u_limpio = u.strip().lower()
        
        if u_limpio in usuarios and usuarios[u_limpio]["password"] == p:
            st.session_state.login = True
            st.session_state.rol = usuarios[u_limpio]["rol"]
            st.session_state.user_name = u_limpio
            st.rerun()
        else:
            st.error("❌ Credenciales incorrectas o usuario no registrado.")

else:
    # MENÚ LATERAL
    with st.sidebar:
        st.title("📂 Menú")
        st.write(f"👤 Usuario: **{st.session_state.user_name.upper()}**")
        st.write(f"🔑 Rol: **{st.session_state.rol.upper()}**")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # --- VISTA PARA INGENIEROS (CALIDAD / AMBIENTAL) ---
    if st.session_state.rol == "ingeniero":
        st.header(f"✍️ Bandeja de Revisión y Firma")
        
        # Listar archivos PDF en la carpeta pendientes
        if os.path.exists("reservas/pendientes"):
            pends = [f for f in os.listdir("reservas/pendientes") if f.endswith(".pdf")]
        else:
            pends = []
        
        if not pends:
            st.info("No hay documentos pendientes de firma en este momento.")
        
        for arc in pends:
            with st.expander(f"📄 Revisar Archivo: {arc}", expanded=True):
                ruta_pdf = f"reservas/pendientes/{arc}"
                
                # Visualización del PDF para revisión
                st.subheader("Previsualización:")
                pdf_viewer(ruta_pdf, width=800)
                
                st.write("---")
                # Sección de firma
                col1, col2 = st.columns([2, 1])
                with col1:
                    clave_f = st.text_input("Introduce tu Clave de Firma", type="password", key=f"f_{arc}")
                
                with col2:
                    st.write("##") # Espaciador
                    btn_firmar = st.button(f"🖋️ Firmar {arc}", key=f"b_{arc}", use_container_width=True)
                
                if btn_firmar:
                    # Obtenemos los datos del usuario actual de forma segura
                    datos = usuarios.get(st.session_state.user_name)
                    
                    if not datos:
                        st.error("Error de sesión: Usuario no encontrado.")
                    elif clave_f != datos["pass_firma"]:
                        st.error("❌ Clave de firma incorrecta.")
                    elif not os.path.exists(datos["archivo_firma"]):
                        st.error(f"❌ No se encuentra la imagen de tu firma en: {datos['archivo_firma']}")
                    else:
                        try:
                            # Proceso de estampado de firma con PyMuPDF
                            doc = fitz.open(ruta_pdf)
                            # Coordenadas rect(x0, y0, x1, y1) ajustadas para la línea "FIRMA 1"
                            rect_firma = fitz.Rect(90, 650, 240, 710) 
                            
                            doc[0].insert_image(rect_firma, filename=datos["archivo_firma"])
                            
                            # Guardar en carpeta de firmadas y mover el original
                            doc.save(f"reservas/firmadas/{arc}")
                            doc.close()
                            os.remove(ruta_pdf) 
                            
                            st.success(f"✅ Documento '{arc}' firmado y enviado a Almacén.")
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al procesar el PDF: {e}")

    # --- VISTA PARA USUARIO (CREAR RESERVAS) ---
    elif st.session_state.rol == "usuario":
        st.header("📤 Cargar Nueva Reserva")
        archivo_subido = st.file_uploader("Sube el PDF de la reserva (Eternit)", type="pdf")
        if archivo_subido is not None:
            if st.button("Enviar a Revisión"):
                with open(f"reservas/pendientes/{archivo_subido.name}", "wb") as f:
                    f.write(archivo_subido.getbuffer())
                st.success("Archivo enviado correctamente a los ingenieros.")

    # --- VISTA PARA ALMACÉN (DESCARGAR FIRMADOS) ---
    elif st.session_state.rol == "almacen":
        st.header("📦 Reservas Autorizadas")
        firmados = [f for f in os.listdir("reservas/firmadas") if f.endswith(".pdf")]
        if not firmados:
            st.info("Aún no hay documentos firmados.")
        for f in firmados:
            with open(f"reservas/firmadas/{f}", "rb") as file:
                st.download_button(label=f"⬇️ Descargar {f}", data=file, file_name=f)
