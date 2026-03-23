import streamlit as st
import os
import fitz  # PyMuPDF
from streamlit_pdf_viewer import pdf_viewer
import json

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema de Gestión de Reservas", layout="wide")

# Creación de carpetas necesarias
for carpeta in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas", "reservas/temp"]:
    os.makedirs(carpeta, exist_ok=True)

# --- CONFIGURACIÓN DE DATOS ---
areas = ["Producción", "Calidad", "Mantenimiento", "Logística", "Almacén"]

usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# Configuración de firmas (Ajustado a tu archivo exacto)
firmas_config = {
    "Producción": {
        "archivo": "reservas/firmas/carlos_alfonso.jpeg", 
        "password": "1234",
        "nombre": "Ing. Carlos Alfonso"
    },
    # Puedes agregar más aquí:
    # "Calidad": {"archivo": "reservas/firmas/firma_calidad.jpeg", "password": "5678", "nombre": "Ing. Calidad"}
}

# --- FUNCIONES TÉCNICAS ---

def insertar_firma_pdf(ruta_entrada, ruta_salida, ruta_firma):
    """Inserta la firma en la posición sobre la línea 'FIRMA 1'"""
    try:
        doc = fitz.open(ruta_entrada)
        pagina = doc[0] # Primera página
        
        # COORDENADAS (x0, y0, x1, y1) 
        # Ajustadas para quedar SOBRE la línea inferior (FIRMA 1)
        # x: 220 a 380 (centrado aprox), y: 620 a 710 (sobre la línea)
        rectangulo_firma = fitz.Rect(220, 620, 380, 710)
        
        pagina.insert_image(rectangulo_firma, filename=ruta_firma)
        doc.save(ruta_salida)
        doc.close()
        return True
    except Exception as e:
        st.error(f"Error técnico al firmar: {e}")
        return False

# --- GESTIÓN DE SESIÓN ---
if "login" not in st.session_state:
    st.session_state.login = False
if "pdf_previsualizado" not in st.session_state:
    st.session_state.pdf_previsualizado = None

# --- INTERFAZ DE LOGIN ---
if not st.session_state.login:
    st.title("🔐 Acceso al Sistema de Reservas")
    col1, col2 = st.columns(2)
    with col1:
        u = st.text_input("Usuario")
    with col2:
        p = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar Sistema", use_container_width=True):
        if u in usuarios and usuarios[u]["password"] == p:
            st.session_state.login = True
            st.session_state.rol = usuarios[u]["rol"]
            st.session_state.user_name = u
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

else:
    # BARRA LATERAL
    with st.sidebar:
        st.header(f"Bienvenido, {st.session_state.user_name}")
        st.write(f"Rol: **{st.session_state.rol.upper()}**")
        if st.button("Cerrar Sesión"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    st.title("📋 Panel de Gestión de Reservas")

    # ==========================================
    # VISTA USUARIO: SUBIR DOCUMENTOS
    # ==========================================
    if st.session_state.rol == "usuario":
        st.subheader("📤 Enviar Nueva Reserva para Firma")
        area_destino = st.selectbox("¿A qué área pertenece la reserva?", areas)
        archivo_subido = st.file_uploader("Selecciona el documento PDF", type=["pdf"])
        
        if st.button("Enviar al Ingeniero"):
            if archivo_subido:
                ruta_dest = f"reservas/pendientes/{area_destino}"
                os.makedirs(ruta_dest, exist_ok=True)
                with open(f"{ruta_dest}/{archivo_subido.name}", "wb") as f:
                    f.write(archivo_subido.getbuffer())
                st.success(f"✅ Documento enviado correctamente a {area_destino}.")
            else:
                st.warning("Por favor sube un archivo primero.")

    # ==========================================
    # VISTA INGENIERO: PREVISUALIZAR Y FIRMAR
    # ==========================================
    elif st.session_state.rol == "ingeniero":
        st.subheader("✍️ Revisión y Firma de Documentos")
        area_ing = st.selectbox("Ver pendientes de:", areas)
        carpeta_p = f"reservas/pendientes/{area_ing}"
        archivos = os.listdir(carpeta_p) if os.path.exists(carpeta_p) else []

        if not archivos:
            st.info(f"No hay pendientes para el área de {area_ing}")
        
        for arc in archivos:
            with st.expander(f"📄 Documento: {arc}"):
                ruta_orig = f"{carpeta_p}/{arc}"
                
                col_izq, col_der = st.columns([1, 1])
                
                with col_izq:
                    st.write("**1. Revisar Contenido Original**")
                    pdf_viewer(ruta_orig, width=400)

                with col_der:
                    st.write("**2. Proceso de Firma**")
                    clave = st.text_input("Contraseña de Firma", type="password", key=f"p_{arc}")
                    
                    if st.button("🔍 Ver Vista Previa", key=f"btn_pre_{arc}"):
                        if area_ing in firmas_config:
                            conf = firmas_config[area_ing]
                            if clave == conf["password"]:
                                if os.path.exists(conf["archivo"]):
                                    ruta_temp = f"reservas/temp/PREVIEW_{arc}"
                                    if insertar_firma_pdf(ruta_orig, ruta_temp, conf["archivo"]):
                                        st.session_state.pdf_previsualizado = ruta_temp
                                        st.success("Vista previa generada abajo 👇")
                                else:
                                    st.error(f"No se encontró el archivo de firma en {conf['archivo']}")
                            else:
                                st.error("Contraseña de firma incorrecta")
                        else:
                            st.error("No hay una firma configurada para esta área.")

                # Mostrar vista previa si fue generada
                if st.session_state.pdf_previsualizado and f"PREVIEW_{arc}" in st.session_state.pdf_previsualizado:
                    st.write("---")
                    st.warning("⚠️ Revisa si la firma quedó correctamente sobre la línea 'FIRMA 1'")
                    pdf_viewer(st.session_state.pdf_previsualizado, width=700)
                    
                    if st.button("🚀 CONFIRMAR Y ENVIAR A ALMACÉN", key=f"btn_confirm_{arc}"):
                        ruta_final_dir = f"reservas/firmadas/{area_ing}"
                        os.makedirs(ruta_final_dir, exist_ok=True)
                        ruta_final = f"{ruta_final_dir}/{arc}"
                        
                        # Mover de temp a carpeta final
                        os.rename(st.session_state.pdf_previsualizado, ruta_final)
                        # Borrar el original de pendientes
                        os.remove(ruta_orig)
                        
                        st.session_state.pdf_previsualizado = None
                        st.success("✅ Documento firmado y enviado exitosamente.")
                        st.rerun()

    # ==========================================
    # VISTA ALMACÉN: DESCARGAR FIRMADOS
    # ==========================================
    elif st.session_state.rol == "almacen":
        st.subheader("📦 Almacén: Descarga de Reservas Firmadas")
        
        # Cargar historial de descargas
        historial_path = "reservas/firmadas/historial.json"
        if os.path.exists(historial_path):
            with open(historial_path, "r") as f: historial = json.load(f)
        else: historial = {}

        area_sel = st.selectbox("Seleccionar área para despacho", areas)
        ruta_firmados = f"reservas/firmadas/{area_sel}"
        listado = os.listdir(ruta_firmados) if os.path.exists(ruta_firmados) else []

        if not listado:
            st.info("No hay documentos listos en esta área.")

        for f_name in listado:
            id_doc = f"{area_sel}/{f_name}"
            descargado = historial.get(id_doc, False)
            
            col_doc, col_btn = st.columns([3, 1])
            icon = "✅" if descargado else "🆕"
            col_doc.write(f"{icon} {f_name}")
            
            with open(f"{ruta_firmados}/{f_name}", "rb") as file:
                if col_btn.download_button("Descargar PDF", file, file_name=f"FIRMADO_{f_name}", key=f"dl_{f_name}"):
                    historial[id_doc] = True
                    with open(historial_path, "w") as f: json.dump(historial, f)
                    st.rerun()
