import streamlit as st
import os
import fitz  # PyMuPDF

# 1. Crear carpetas
for folder in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas"]:
    os.makedirs(folder, exist_ok=True)

# 2. Base de datos
usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

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
    # BARRA LATERAL (Esto es lo que te permite salir)
    with st.sidebar:
        st.header(f"Rol: {st.session_state.rol.upper()}")
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
                    f.write(archivo.getbuffer())
                st.success("Enviado al Ingeniero")

    elif rol == "ingeniero":
        st.subheader("Documentos por Firmar")
        archivos = os.listdir("reservas/pendientes")
        if not archivos:
            st.info("No hay documentos pendientes")
        for arc in archivos:
            col1, col2 = st.columns([3, 1])
            col1.write(arc)
            if col2.button("Firmar", key=arc):
                ruta_in = f"reservas/pendientes/{arc}"
                ruta_out = f"reservas/firmadas/{arc}"
                ruta_firma = "reservas/firmas/ingeniero.png"
                if os.path.exists(ruta_firma):
                    pdf = fitz.open(ruta_in)
                    pagina = pdf[0]
                    rect = fitz.Rect(300, 500, 500, 650)
                    pagina.insert_image(rect, filename=ruta_firma)
                    pdf.save(ruta_out)
                    pdf.close()
                    os.remove(ruta_in)
                    st.success("Firmado")
                    st.rerun()
                else:
                    st.error("Sube la firma 'ingeniero.png' a la carpeta reservas/firmas")

    elif rol == "almacen":
        st.subheader("Descargar Firmados")
        firmados = os.listdir("reservas/firmadas")
        for f in firmados:
            with open(f"reservas/firmadas/{f}", "rb") as file:
                st.download_button(f"Descargar {f}", file, file_name=f)
