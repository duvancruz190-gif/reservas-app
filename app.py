import streamlit as st
import os
import fitz
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema de Reservas", layout="centered")

# Crear carpetas necesarias
for carpeta in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas"]:
    os.makedirs(carpeta, exist_ok=True)

# Usuarios
usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# --- LÓGICA DE SESIÓN ---
if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.rol = None

# Función para salir
def salir():
    st.session_state.login = False
    st.session_state.rol = None
    st.rerun()

# --- PANTALLA DE LOGIN ---
if not st.session_state.login:
    st.title("🔑 Ingreso al Sistema")
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
    # 🚪 EL BOTÓN DE SALIR (En la barra lateral)
    with st.sidebar:
        st.write(f"Conectado como: **{st.session_state.rol.upper()}**")
        if st.button("Cerrar Sesión"):
            salir()

    st.title("📋 Sistema de Reservas")
    rol = st.session_state.rol

    # ROL: USUARIO
    if rol == "usuario":
        st.subheader("Subir PDF")
        archivo = st.file_uploader("Seleccione el archivo de reserva", type=["pdf"])

        if st.button("Enviar"):
            if archivo:
                # Usamos getbuffer() para asegurar que se guarde bien
                with open(f"reservas/pendientes/{archivo.name}", "wb") as f:
                    f.write(archivo.getbuffer())
                st.success("✅ Enviado correctamente al ingeniero.")
            else:
                st.warning("Por favor, sube un archivo primero.")

    # ROL: INGENIERO
    elif rol == "ingeniero":
        st.subheader("✍️ Panel de Firma (Ingeniero)")
        archivos = os.listdir("reservas/pendientes")

        if not archivos:
            st.info("No hay archivos pendientes.")
        
        for arch in archivos:
            col1, col2 = st.columns([3, 1])
            col1.write(arch)
            if col2.button("Firmar", key=arch):
                # Proceso de firma
                pdf = fitz.open(f"reservas/pendientes/{arch}")
                pagina = pdf[0]
                firma = "reservas/firmas/ingeniero.png"
                
                if os.path.exists(firma):
                    rect = fitz.Rect(300, 500, 500, 650)
                    pagina.insert_image(rect, filename=firma)
                    pdf.save(f"reservas/firmadas/{arch}")
                    pdf.close()
                    os.remove(f"reservas/pendientes/{arch}")
                    st.success(f"Firmado: {arch}")
                    st.rerun() # Esto actualiza la lista automáticamente
                else:
                    st.error("Falta el archivo de firma en 'reservas/firmas/ingeniero.png'")

    # ROL: ALMACEN
    elif rol == "almacen":
        st.subheader("📦 Descargar Firmados")
        archivos_firmados = os.listdir("reservas/firmadas")

        if not archivos_firmados:
            st.info("No hay archivos listos.")

        for arch in archivos_firmados:
            with open(f"reservas/firmadas/{arch}", "rb") as f:
                st.download_button(f"Descargar {arch}", f, file_name=arch)
