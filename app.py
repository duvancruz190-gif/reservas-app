import streamlit as st
import os
import fitz  # PyMuPDF
import base64

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión de Reservas", layout="wide")

# Crear carpetas si no existen
for carpeta in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas"]:
    os.makedirs(carpeta, exist_ok=True)

# Base de datos de usuarios
usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# --- 2. EL VISOR "TODO TERRENO" ---
def visor_pdf_en_pagina(ruta_pdf):
    try:
        with open(ruta_pdf, "rb") as f:
            datos_pdf = f.read()
            base64_pdf = base64.b64encode(datos_pdf).decode('utf-8')
        
        # Combinación de OBJECT y EMBED para máxima compatibilidad en la misma página
        pdf_html = f'''
            <div style="border: 2px solid #f0f2f6; border-radius: 10px; overflow: hidden;">
                <object data="data:application/pdf;base64,{base64_pdf}" type="application/pdf" width="100%" height="600px">
                    <embed src="data:application/pdf;base64,{base64_pdf}" type="application/pdf" width="100%" height="600px" />
                    <div style="padding: 20px; text-align: center;">
                        <p>⚠️ Tu navegador limita la visualización directa.</p>
                        <a href="data:application/pdf;base64,{base64_pdf}" download="archivo_reserva.pdf" 
                           style="background-color: #ff4b4b; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                           Descargar para Revisar
                        </a>
                    </div>
                </object>
            </div>
        '''
        st.markdown(pdf_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error al cargar el visor: {e}")

# --- 3. LÓGICA DE ACCESO ---
if "login" not in st.session_state:
    st.session_state.login = False

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
    # --- BARRA LATERAL (MENÚ) ---
    with st.sidebar:
        st.title("📂 Menú Principal")
        st.write(f"👤 Usuario: **{st.session_state.get('user_name', 'Usuario')}**")
        st.write(f"🔑 Rol: **{st.session_state.get('rol', '').upper()}**")
        st.write("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
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
                st.success("✅ Documento enviado con éxito.")
            else:
                st.warning("Selecciona un archivo PDF.")

    # --- VISTA: INGENIERO ---
    elif rol == "ingeniero":
        st.header("✍️ Revisión y Firma")
        pendientes = os.listdir("reservas/pendientes")
        
        if not pendientes:
            st.info("No hay documentos pendientes por ahora.")
        
        for arc in pendientes:
            with st.expander(f"📄 Archivo: {arc}", expanded=False):
                ruta_full = f"reservas/pendientes/{arc}"
                
                # Botones de control
                col_v, col_f = st.columns(2)
                
                # El visor aparece solo si se despliega el expander
                st.write("### Vista Previa:")
                visor_pdf_en_pagina(ruta_full)
                
                st.write("---")
                if st.button(f"🖋️ Firmar y Enviar {arc}", key=f"btn_{arc}"):
                    ruta_firma = "reservas/firmas/ingeniero.png"
                    if os.path.exists(ruta_firma):
                        doc = fitz.open(ruta_full)
                        pagina = doc[0]
                        # Ubicación de la firma
                        pagina.insert_image(fitz.Rect(400, 700, 550, 800), filename=ruta_firma)
                        doc.save(f"reservas/firmadas/{arc}")
                        doc.close()
                        os.remove(ruta_full)
                        st.success("✅ Documento firmado.")
                        st.rerun()
                    else:
                        st.error("❌ Falta la imagen 'ingeniero.png' en reservas/firmas/")

    # --- VISTA: ALMACÉN ---
    elif rol == "almacen":
        st.header("📦 Documentos para Despacho")
        firmados = os.listdir("reservas/firmadas")
        if not firmados:
            st.info("No hay reservas firmadas todavía.")
        for f in firmados:
            col_a, col_b = st.columns([3, 1])
            col_a.write(f"✅ {f}")
            with open(f"reservas/firmadas/{f}", "rb") as file:
                col_b.download_button("Descargar", file, file_name=f, key=f"dl_{f}")
