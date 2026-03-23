import streamlit as st
import os
import fitz  # PyMuPDF
import base64

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas", layout="wide")

# Crear carpetas si no existen
for carpeta in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas"]:
    os.makedirs(carpeta, exist_ok=True)

usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# --- 2. FUNCIÓN PARA ABRIR PDF (LA MÁS COMPATIBLE) ---
def visor_pdf_compatible(ruta_pdf):
    try:
        with open(ruta_pdf, "rb") as f:
            datos_pdf = f.read()
            base64_pdf = base64.b64encode(datos_pdf).decode('utf-8')
        
        # Intentar mostrar visor
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        # BOTÓN DE RESPALDO (Esto nunca falla)
        st.download_button(
            label="📂 Ver PDF en pantalla completa / Descargar para revisar",
            data=datos_pdf,
            file_name="revision_reserva.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Error al cargar archivo: {e}")

# --- 3. LOGICA DE SESION ---
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
    # BARRA LATERAL (SIDEBAR)
    with st.sidebar:
        st.title("📂 Menú")
        st.write(f"👤 **{st.session_state.get('user_name', 'Usuario')}**")
        st.write(f"🔑 Rol: {st.session_state.get('rol', '').upper()}")
        st.write("---")
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
                st.success("✅ Documento enviado al Ingeniero.")
            else: st.warning("Por favor, sube un archivo.")

    elif rol == "ingeniero":
        st.header("✍️ Bandeja de Revisión y Firma")
        pendientes = os.listdir("reservas/pendientes")
        
        if not pendientes:
            st.info("No hay documentos pendientes.")
        
        for arc in pendientes:
            with st.expander(f"📄 Documento: {arc}"):
                ruta_full = f"reservas/pendientes/{arc}"
                
                # VISOR Y REVISIÓN
                visor_pdf_compatible(ruta_full)
                
                st.write("---")
                if st.button("🖋️ Aplicar Firma y Enviar a Almacén", key=f"f_{arc}"):
                    ruta_firma = "reservas/firmas/ingeniero.png"
                    if os.path.exists(ruta_firma):
                        doc = fitz.open(ruta_full)
                        pagina = doc[0]
                        # Insertar firma en la esquina inferior
                        pagina.insert_image(fitz.Rect(400, 700, 550, 800), filename=ruta_firma)
                        doc.save(f"reservas/firmadas/{arc}")
                        doc.close()
                        os.remove(ruta_full)
                        st.success("✅ Firmado correctamente.")
                        st.rerun()
                    else:
                        st.error("❌ No se encontró la firma en: 'reservas/firmas/ingeniero.png'")

    elif rol == "almacen":
        st.header("📦 Reservas para Despacho")
        firmados = os.listdir("reservas/firmadas")
        if not firmados:
            st.info("No hay archivos firmados.")
        for f in firmados:
            col_a, col_b = st.columns([3, 1])
            col_a.write(f"✅ {f}")
            with open(f"reservas/firmadas/{f}", "rb") as file:
                col_b.download_button("Descargar", file, file_name=f, key=f"dl_{f}")
