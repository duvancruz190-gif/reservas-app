import streamlit as st
import os
import fitz  # PyMuPDF
from datetime import datetime

st.set_page_config(page_title="Sistema de Reservas", layout="centered")
st.title("Sistema de Reservas")

# Crear carpetas si no existen
os.makedirs("reservas/pendientes", exist_ok=True)
os.makedirs("reservas/firmadas", exist_ok=True)
os.makedirs("reservas/firmas", exist_ok=True)

# Base de datos de usuarios
usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# Inicializar sesión
if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.rol = None

# --- LÓGICA DE CERRAR SESIÓN ---
def cerrar_sesion():
    st.session_state.login = False
    st.session_state.rol = None
    st.rerun()

# --- PANTALLA DE LOGIN ---
if not st.session_state.login:
    with st.container():
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")

        if st.button("Ingresar"):
            if user in usuarios and usuarios[user]["password"] == password:
                st.session_state.login = True
                st.session_state.rol = usuarios[user]["rol"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

# --- PANTALLA PRINCIPAL (LOGUEADO) ---
else:
    # BOTÓN DE SALIR SIEMPRE VISIBLE EN LA BARRA LATERAL
    st.sidebar.write(f"Sesión: **{st.session_state.rol.upper()}**")
    if st.sidebar.button("Cerrar Sesión"):
        cerrar_sesion()

    rol = st.session_state.rol

    # --- VISTA USUARIO ---
    if rol == "usuario":
        st.subheader("Subir nueva reserva (PDF)")
        archivo = st.file_uploader("Seleccione el archivo", type=["pdf"])

        if st.button("Enviar al Ingeniero"):
            if archivo is not None:
                path = os.path.join("reservas/pendientes", archivo.name)
                with open(path, "wb") as f:
                    f.write(archivo.getbuffer())
                st.success(f"Archivo '{archivo.name}' enviado correctamente.")
            else:
                st.warning("Por favor seleccione un archivo primero.")

    # --- VISTA INGENIERO ---
    elif rol == "ingeniero":
        st.subheader("Documentos pendientes de firma")
        
        # Listar archivos en la carpeta de pendientes
        archivos = os.listdir("reservas/pendientes")
        
        if len(archivos) == 0:
            st.info("No hay archivos pendientes de firma.")
        else:
            for nombre_archivo in archivos:
                col1, col2 = st.columns([3, 1])
                col1.write(f"📄 {nombre_archivo}")
                
                # Usamos una clave (key) única para cada botón
                if col2.button("Firmar", key=nombre_archivo):
                    ruta_entrada = f"reservas/pendientes/{nombre_archivo}"
                    ruta_salida = f"reservas/firmadas/{nombre_archivo}"
                    firma_path = "reservas/firmas/ingeniero.png"

                    if os.path.exists(firma_path):
                        doc = fitz.open(ruta_entrada)
                        pagina = doc[0]
                        # Coordenadas donde se pondrá la firma
                        rect = fitz.Rect(400, 700, 550, 800) 
                        pagina.insert_image(rect, filename=firma_path)
                        doc.save(ruta_salida)
                        doc.close()
                        
                        os.remove(ruta_entrada)
                        st.success(f"Firmado: {nombre_archivo}")
                        st.rerun() # Recargar para que desaparezca de la lista
                    else:
                        st.error("No se encontró el archivo de firma en 'reservas/firmas/ingeniero.png'")

    # --- VISTA ALMACEN ---
    elif rol == "almacen":
        st.subheader("Descargar reservas firmadas")
        archivos_firmados = os.listdir("reservas/firmadas")

        if len(archivos_firmados) == 0:
            st.info("No hay archivos listos para descargar.")
        else:
            for archivo in archivos_firmados:
                with open(f"reservas/firmadas/{archivo}", "rb") as f:
                    st.download_button(label=f"Descargar {archivo}", data=f, file_name=archivo)
