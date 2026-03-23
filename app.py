import streamlit as st
import os
import fitz
from datetime import datetime

st.title("Sistema de Reservas")

os.makedirs("reservas/pendientes", exist_ok=True)
os.makedirs("reservas/firmadas", exist_ok=True)
os.makedirs("reservas/firmas", exist_ok=True)

usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if user in usuarios and usuarios[user]["password"] == password:
            st.session_state.login = True
            st.session_state.rol = usuarios[user]["rol"]
            st.rerun()
        else:
            st.error("Error")

if st.session_state.login:

    rol = st.session_state.rol

    if rol == "usuario":
        st.subheader("Subir PDF")
        archivo = st.file_uploader("Archivo", type=["pdf"])

        if st.button("Enviar"):
            if archivo:
                with open(f"reservas/pendientes/{archivo.name}", "wb") as f:
                    f.write(archivo.read())
                st.success("Enviado")

    if rol == "ingeniero":
        st.subheader("Firmar")

        archivos = os.listdir("reservas/pendientes")

        for archivo in archivos:
            if st.button(f"Firmar {archivo}"):

                pdf = fitz.open(f"reservas/pendientes/{archivo}")
                pagina = pdf[0]

                firma = "reservas/firmas/ingeniero.png"

                rect = fitz.Rect(300, 500, 500, 650)
                pagina.insert_image(rect, filename=firma)

                pdf.save(f"reservas/firmadas/{archivo}")
                pdf.close()

                os.remove(f"reservas/pendientes/{archivo}")

                st.success("Firmado")

    if rol == "almacen":
        st.subheader("Descargar")

        archivos = os.listdir("reservas/firmadas")

        for archivo in archivos:
            with open(f"reservas/firmadas/{archivo}", "rb") as f:
                st.download_button("Descargar", f, file_name=archivo)