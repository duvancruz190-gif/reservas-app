import streamlit as st
import os
import fitz  # PyMuPDF

# 1. Crear carpetas si no existen
for folder in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas"]:
    os.makedirs(folder, exist_ok=True)

# 2. Base de datos
usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# 3. Estado de la sesión
if "login" not in st.session_state:
    st.session_state.login = False

# --- PANTALLA DE LOGIN ---
if not st.session_state.login:
    st.title("Acceso al Sistema")
    user = st.text_input("Usuario")
    passw = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar"):
        if user in usuarios and usuarios[user]["password"] == passw:
            st.session_state.login = True
            st.session_state.rol = usuarios[user]["rol"]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

# --- PANTALLA PRINCIPAL ---
else:
    # ESTO ES LO QUE TE FALTA: La barra lateral para salir
    with st.sidebar:
        st.write(f"Sessión activa: **{st.session_state.rol.upper()}**")
        if st.button("Cerrar Sesión"):
            st.session_state.login = False
            st.rerun()

    st.title("Sistema de Reservas")
    rol = st.session_state.rol

    if rol == "usuario":
        st.subheader("Subir PDF")
        archivo = st.file_uploader("Archivo", type=["pdf"])
        if st.button("Enviar"):
            if archivo:
                with open(f"reservas/pendientes/{archivo.name}", "wb") as f:
                    f.write(archivo.getbuffer()) # getbuffer es clave para que el archivo no llegue vacío
                st.success("Enviado al Ingeniero")

    elif rol == "ingeniero":
        st.subheader("Documentos por Firmar")
        archivos = os.listdir("reservas/pendientes")
        if not archivos: st.info("No hay pendientes")
        for arc in archivos:
            col1, col2 = st.columns([3, 1])
            col1.write(arc)
            if col2.button("Firmar", key=arc):
                # Lógica de firma con PyMuPDF
                pdf = fitz.open(f"reservas/pendientes/{arc}")
                # ... (resto de tu lógica de firma)
                pdf.save(f"reservas/firmadas/{arc}")
                pdf.close()
                os.remove(f"reservas/pendientes/{arc}")
                st.rerun() # Esto hace que el archivo desaparezca de la lista al instante

    elif rol == "almacen":
        st.subheader("Descargar Firmados")
        firmados = os.listdir("reservas/firmadas")
        for f in firmados:
            with open(f"reservas/firmadas/{f}", "rb") as file:
                st.download_button(f"Descargar {f}", file, file_name=f)
