import streamlit as st
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer
import json

# --- 1. CONFIGURACIÓN ESTRUCTURAL ---
st.set_page_config(page_title="Gestión de Reservas - Digital", layout="wide")

# Crear carpetas automáticamente para evitar el error "Oh no"
carpetas = [
    "reservas/pendientes/Producción",
    "reservas/pendientes/Calidad",
    "reservas/pendientes/Mantenimiento",
    "reservas/pendientes/Logística",
    "reservas/firmadas/Producción",
    "reservas/firmadas/Calidad",
    "reservas/firmas",
    "reservas/temp"
]
for c in carpetas:
    os.makedirs(c, exist_ok=True)

# --- 2. CONFIGURACIÓN DE DATOS ---
areas = ["Producción", "Calidad", "Mantenimiento", "Logística"]

usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# Configuración de la firma (Asegúrate que el archivo esté en reservas/firmas/)
firmas_config = {
    "Producción": {
        "archivo": "reservas/firmas/carlos_alfonso.jpeg", 
        "password": "1234"
    }
}

# --- 3. FUNCIONES TÉCNICAS ---
def insertar_firma_pdf(ruta_entrada, ruta_salida, ruta_firma):
    try:
        doc = fitz.open(ruta_entrada)
        pagina = doc[0]
        # Coordenadas: x0, y0 (esquina superior izq) a x1, y1 (esquina inferior der)
        # Ajustado para que quede sobre la línea "FIRMA 1"
        rect = fitz.Rect(220, 620, 380, 710) 
        pagina.insert_image(rect, filename=ruta_firma)
        doc.save(ruta_salida)
        doc.close()
        return True
    except Exception as e:
        st.error(f"Error al estampar firma: {e}")
        return False

# --- 4. LÓGICA DE SESIÓN ---
if "login" not in st.session_state:
    st.session_state.login = False
if "prev_path" not in st.session_state:
    st.session_state.prev_path = None

# --- 5. INTERFAZ DE LOGIN ---
if not st.session_state.login:
    st.title("🔐 Acceso al Sistema de Reservas")
    col1, col2 = st.columns(2)
    with col1: u = st.text_input("Usuario")
    with col2: p = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar", use_container_width=True):
        if u in usuarios and usuarios[u]["password"] == p:
            st.session_state.login = True
            st.session_state.rol = usuarios[u]["rol"]
            st.session_state.user_name = u
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

else:
    # BARRA LATERAL
    with st.sidebar:
        st.header(f"Hola, {st.session_state.user_name}")
        if st.button("Cerrar Sesión"):
            st.session_state.login = False
            st.rerun()

    # ==========================================
    # ROL: INGENIERO (REVISIÓN Y FIRMA)
    # ==========================================
    if st.session_state.rol == "ingeniero":
        st.header("✍️ Revisión y Firma de Documentos")
        area_sel = st.selectbox("Selecciona tu Área", areas)
        ruta_pendientes = f"reservas/pendientes/{area_sel}"
        archivos = os.listdir(ruta_pendientes) if os.path.exists(ruta_pendientes) else []

        if not archivos:
            st.info("No hay documentos pendientes por ahora.")

        for arc in archivos:
            with st.expander(f"📄 Archivo: {arc}"):
                ruta_orig = f"{ruta_pendientes}/{arc}"
                
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.write("**Vista del Original:**")
                    pdf_viewer(ruta_orig, width=350)
                
                with c2:
                    st.write("**Validación de Firma:**")
                    pass_f = st.text_input("Contraseña de tu Firma", type="password", key=f"k_{arc}")
                    
                    if st.button("🔍 Ver Vista Previa", key=f"v_{arc}"):
                        if area_sel in firmas_config:
                            f_info = firmas_config[area_sel]
                            if pass_f == f_info["password"]:
                                if os.path.exists(f_info["archivo"]):
                                    tmp = f"reservas/temp/PREVIEW_{arc}"
                                    if insertar_firma_pdf(ruta_orig, tmp, f_info["archivo"]):
                                        st.session_state.prev_path = tmp
                                        st.success("Vista previa generada. Desliza hacia abajo.")
                                else:
                                    st.error(f"No se encuentra la imagen: {f_info['archivo']}")
                            else:
                                st.error("Contraseña de firma incorrecta.")
                
                # MOSTRAR VISTA PREVIA SI EXISTE
                if st.session_state.prev_path and arc in st.session_state.prev_path:
                    st.divider()
                    st.subheader("🔍 VISTA PREVIA FINAL")
                    pdf_viewer(st.session_state.prev_path, width=700)
                    
                    if st.button("🚀 CONFIRMAR Y ENVIAR ALMACÉN", key=f"send_{arc}"):
                        f_dir = f"reservas/firmadas/{area_sel}"
                        os.makedirs(f_dir, exist_ok=True)
                        os.rename(st.session_state.prev_path, f"{f_dir}/{arc}")
                        os.remove(ruta_orig) # Borra el original
                        st.session_state.prev_path = None
                        st.success("✅ Documento firmado y enviado a Almacén.")
                        st.rerun()

    # ==========================================
    # ROL: USUARIO (SUBIR)
    # ==========================================
    elif st.session_state.rol == "usuario":
        st.header("📤 Cargar Nueva Reserva")
        a_dest = st.selectbox("Área a enviar", areas)
        up = st.file_uploader("Subir PDF", type="pdf")
        if st.button("Enviar al Ingeniero") and up:
            with open(f"reservas/pendientes/{a_dest}/{up.name}", "wb") as f:
                f.write(up.getbuffer())
            st.success(f"Enviado a {a_dest}")

    # ==========================================
    # ROL: ALMACÉN (DESCARGAR)
    # ==========================================
    elif st.session_state.rol == "almacen":
        st.header("📦 Reservas Listas para Despacho")
        a_ver = st.selectbox("Filtrar por Área", areas)
        r_firm = f"reservas/firmadas/{a_ver}"
        listado = os.listdir(r_firm) if os.path.exists(r_firm) else []
        
        for f_name in listado:
            col_txt, col_btn = st.columns([3, 1])
            col_txt.write(f"📄 {f_name}")
            with open(f"{r_firm}/{f_name}", "rb") as file:
                col_btn.download_button("Descargar", file, file_name=f"FIRMADO_{f_name}", key=f"dl_{f_name}")
