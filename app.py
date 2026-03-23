import streamlit as st
import os
import fitz  # PyMuPDF
import base64

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas", layout="wide")

for carpeta in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas"]:
    os.makedirs(carpeta, exist_ok=True)

usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# --- 2. VISOR DE PDF MEJORADO ---
def mostrar_pdf(ruta_pdf):
    try:
        with open(ruta_pdf, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        # Objeto PDF incrustado con más compatibilidad
        pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf">'
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        # Opción extra por si el navegador no lo soporta
        st.info("💡 Si no ves el PDF arriba, asegúrate de permitir las cookies de terceros en tu navegador.")
    except Exception as e:
        st.error(f"Error al abrir: {e}")

# --- 3. LÓGICA DE ACCESO ---
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Acceso al Sistema")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
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
        st.write(f"👤 **{st.session_state.get('user_name', 'Usuario')}**")
        st.write(f"🔑 Rol: {st.session_state.get('rol', '').upper()}")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    # --- VISTAS POR ROL ---
    rol = st.session_state.get('rol')

    if rol == "usuario":
        st.header("📤 Enviar Reserva")
        arch = st.file_uploader("Subir PDF", type=["pdf"])
        if st.button("Enviar"):
            if arch:
                with open(f"reservas/pendientes/{arch.name}", "wb") as f:
                    f.write(arch.getbuffer())
                st.success("Enviado.")
            else: st.warning("Sube un archivo.")

    elif rol == "ingeniero":
        st.header("✍️ Bandeja de Firma")
        pendientes = os.listdir("reservas/pendientes")
        if not pendientes:
            st.info("No hay archivos.")
        for arc in pendientes:
            with st.expander(f"📄 Revisar: {arc}"):
                col1, col2 = st.columns(2)
                ruta_full = f"reservas/pendientes/{arc}"
                
                if col1.button("👁️ Visualizar", key=f"v_{arc}"):
                    mostrar_pdf(ruta_full)
                
                if col2.button("🖋️ Firmar", key=f"f_{arc}"):
                    if os.path.exists("reservas/firmas/ingeniero.png"):
                        doc = fitz.open(ruta_full)
                        pagina = doc[0]
                        pagina.insert_image(fitz.Rect(400, 700, 550, 800), filename="reservas/firmas/ingeniero.png")
                        doc.save(f"reservas/firmadas/{arc}")
                        doc.close()
                        os.remove(ruta_full)
                        st.success("Firmado.")
                        st.rerun()
                    else:
                        st.error("Falta la imagen: reservas/firmas/ingeniero.png")

    elif rol == "almacen":
        st.header("📦 Despacho")
        firmados = os.listdir("reservas/firmadas")
        for f in firmados:
            with open(f"reservas/firmadas/{f}", "rb") as file:
                st.download_button(f"Descargar {f}", file, file_name=f)
