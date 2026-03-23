import streamlit as st
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer # Nuevo visor profesional

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas", layout="wide")

for carpeta in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas"]:
    os.makedirs(carpeta, exist_ok=True)

usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# --- 2. LÓGICA DE SESIÓN ---
if "login" not in st.session_state:
    st.session_state.login = False

# --- PANTALLA DE LOGIN ---
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
    # MENÚ LATERAL
    with st.sidebar:
        st.title("📂 Menú Principal")
        st.write(f"👤 Usuario: **{st.session_state.get('user_name', 'Usuario')}**")
        st.write(f"🔑 Rol: **{st.session_state.get('rol', '').upper()}**")
        st.write("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    st.title("📋 Gestión de Reservas")
    rol = st.session_state.get('rol')

    # --- VISTA: USUARIO ---
    if rol == "usuario":
        st.header("📤 Enviar Nueva Reserva")
        arch = st.file_uploader("Subir PDF", type=["pdf"])
        if st.button("Enviar al Ingeniero"):
            if arch:
                with open(f"reservas/pendientes/{arch.name}", "wb") as f:
                    f.write(arch.getbuffer())
                st.success("✅ Documento enviado.")
            else:
                st.warning("Selecciona un archivo.")

    # --- VISTA: INGENIERO ---
    elif rol == "ingeniero":
        st.header("✍️ Revisión y Firma")
        pendientes = os.listdir("reservas/pendientes")
        
        if not pendientes:
            st.info("No hay documentos pendientes.")
        
        for arc in pendientes:
            with st.expander(f"📄 Revisar Archivo: {arc}", expanded=False):
                ruta_full = f"reservas/pendientes/{arc}"
                
                # VISOR PROFESIONAL (Evita el bloqueo del navegador)
                st.write("### Previsualización:")
                try:
                    pdf_viewer(ruta_full, width=700)
                except:
                    st.error("El visor falló. Usa el botón de abajo para revisar.")
                    with open(ruta_full, "rb") as f:
                        st.download_button("📂 Descargar para revisar", f, file_name=arc)
                
                st.write("---")
                if st.button(f"🖋️ Firmar y Enviar a Almacén", key=f"f_{arc}"):
                    ruta_firma = "reservas/firmas/ingeniero.png"
                    if os.path.exists(ruta_firma):
                        doc = fitz.open(ruta_full)
                        pagina = doc[0]
                        # Colocación de firma (Ajustable)
                        pagina.insert_image(fitz.Rect(400, 700, 550, 800), filename=ruta_firma)
                        doc.save(f"reservas/firmadas/{arc}")
                        doc.close()
                        os.remove(ruta_full)
                        st.success("✅ Firmado correctamente.")
                        st.rerun()
                    else:
                        st.error("❌ No existe la firma 'ingeniero.png' en reservas/firmas/")

    # --- VISTA: ALMACÉN ---
    elif rol == "almacen":
        st.header("📦 Documentos Listos")
        firmados = os.listdir("reservas/firmadas")
        for f in firmados:
            col_a, col_b = st.columns([3, 1])
            col_a.write(f"✅ {f}")
            with open(f"reservas/firmadas/{f}", "rb") as file:
                col_b.download_button("Descargar", file, file_name=f, key=f"dl_{f}")
