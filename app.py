import streamlit as st
import os
import fitz  # PyMuPDF
import base64

# --- 1. CONFIGURACIÓN E HIGIENE DE CARPETAS ---
st.set_page_config(page_title="Gestión de Reservas", layout="wide")

# Creamos las carpetas necesarias si no existen
for carpeta in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas"]:
    os.makedirs(carpeta, exist_ok=True)

# --- 2. BASE DE DATOS DE USUARIOS ---
usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# --- 3. FUNCIONES DE APOYO ---
def mostrar_pdf(ruta_pdf):
    """Genera un visor de PDF incrustado en la página usando Base64"""
    try:
        with open(ruta_pdf, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"No se pudo visualizar el archivo: {e}")

# --- 4. LÓGICA DE SESIÓN ---
if "login" not in st.session_state:
    st.session_state.login = False

# --- PANTALLA DE LOGIN ---
if not st.session_state.login:
    st.title("🔐 Acceso al Sistema de Reservas")
    col_login, _ = st.columns([1, 2])
    with col_login:
        user_input = st.text_input("Usuario")
        pass_input = st.text_input("Contraseña", type="password")
        if st.button("Ingresar", use_container_width=True):
            if user_input in usuarios and usuarios[user_input]["password"] == pass_input:
                st.session_state.login = True
                st.session_state.rol = usuarios[user_input]["rol"]
                st.session_state.user_name = user_input
                st.rerun()
            else:
                st.error("⚠️ Credenciales incorrectas")

# --- PANTALLA PRINCIPAL (LOGUEADO) ---
else:
    # BARRA LATERAL (SIDEBAR) - Aquí está el botón de salir para TODOS
    with st.sidebar:
        st.title("Menú")
        # Usamos .get() para evitar el error de Attribute si la sesión es vieja
        nombre_usuario = st.session_state.get('user_name', 'Usuario')
        rol_usuario = st.session_state.get('rol', 'Invitado').upper()
        
        st.write(f"👤 Usuario: **{nombre_usuario}**")
        st.write(f"🔑 Rol: **{rol_usuario}**")
        st.write("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            # Limpiamos todo el estado de la sesión
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.title("📋 Sistema de Gestión de Reservas")
    rol_actual = st.session_state.get('rol')

    # --- FLUJO: USUARIO ---
    if rol_actual == "usuario":
        st.header("📤 Nueva Solicitud")
        archivo = st.file_uploader("Suba el documento de reserva (PDF)", type=["pdf"])
        if st.button("Enviar al Ingeniero"):
            if archivo:
                with open(f"reservas/pendientes/{archivo.name}", "wb") as f:
                    f.write(archivo.getbuffer())
                st.success(f"✅ Documento '{archivo.name}' enviado correctamente.")
            else:
                st.warning("⚠️ Seleccione un archivo primero.")

    # --- FLUJO: INGENIERO ---
    elif rol_actual == "ingeniero":
        st.header("✍️ Bandeja de Revisión y Firma")
        pendientes = os.listdir("reservas/pendientes")
        
        if not pendientes:
            st.info("No hay documentos pendientes de firma.")
        else:
            for arc in pendientes:
                # Usamos un expansor para organizar la visualización
                with st.expander(f"📄 Archivo: {arc}"):
                    ruta_p = f"reservas/pendientes/{arc}"
                    col_btn1, col_btn2 = st.columns(2)
                    
                    if col_btn1.button("👁️ Ver PDF", key=f"v_{arc}"):
                        mostrar_pdf(ruta_p)
                    
                    if col_btn2.button("🖋️ Firmar Documento", key=f"f_{arc}"):
                        ruta_firma = "reservas/firmas/ingeniero.png"
                        if os.path.exists(ruta_firma):
                            try:
                                doc = fitz.open(ruta_p)
                                pagina = doc[0]
                                # Rect(x0, y0, x1, y1) - Ajusta según necesites
                                rect = fitz.Rect(400, 700, 550, 800)
                                pagina.insert_image(rect, filename=ruta_firma)
                                doc.save(f"reservas/firmadas/{arc}")
                                doc.close()
                                os.remove(ruta_p)
                                st.success("✅ Firmado con éxito.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al firmar: {e}")
                        else:
                            st.error(f"⚠️ No existe la firma en 'reservas/firmas/ingeniero.png'")

    # --- FLUJO: ALMACÉN ---
    elif rol_actual == "almacen":
        st.header("📦 Reservas Listas para Despacho")
        firmados = os.listdir("reservas/firmadas")
        
        if not firmados:
            st.info("Aún no hay documentos firmados por el ingeniero.")
        else:
            for f_name in firmados:
                col_a, col_b = st.columns([3, 1])
                col_a.write(f"✅ {f_name}")
                with open(f"reservas/firmadas/{f_name}", "rb") as f:
                    col_b.download_button("Descargar", f, file_name=f_name, key=f"dl_{f_name}")
