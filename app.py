import streamlit as st
import os
import fitz  # PyMuPDF

# 1. CONFIGURACIÓN INICIAL DE CARPETAS
# Esto asegura que las carpetas existan en el servidor de Streamlit
for carpeta in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas"]:
    os.makedirs(carpeta, exist_ok=True)

# 2. BASE DE DATOS DE USUARIOS
usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# 3. GESTIÓN DE ESTADO DE SESIÓN
if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.rol = None

# --- PANTALLA DE LOGIN ---
if not st.session_state.login:
    st.title("🔐 Acceso al Sistema")
    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if user in usuarios and usuarios[user]["password"] == password:
            st.session_state.login = True
            st.session_state.rol = usuarios[user]["rol"]
            st.rerun()
        else:
            st.error("⚠️ Usuario o contraseña incorrectos")

# --- PANTALLA PRINCIPAL (LOGUEADO) ---
else:
    # 🚪 BARRA LATERAL (SIDEBAR) - AQUÍ ES DONDE APARECE EL BOTÓN DE SALIR
    with st.sidebar:
        st.header(f"👤 {st.session_state.rol.upper()}")
        st.write("---")
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state.login = False
            st.session_state.rol = None
            st.rerun()

    st.title("📋 Gestión de Reservas")
    rol = st.session_state.rol

    # --- VISTA: USUARIO ---
    if rol == "usuario":
        st.subheader("Subir Solicitud de Reserva")
        archivo = st.file_uploader("Seleccione el archivo PDF", type=["pdf"])

        if st.button("Enviar al Ingeniero"):
            if archivo:
                # Guardamos el archivo en la carpeta de pendientes
                ruta_destino = f"reservas/pendientes/{archivo.name}"
                with open(ruta_destino, "wb") as f:
                    f.write(archivo.getbuffer())
                st.success(f"✅ Archivo '{archivo.name}' enviado con éxito.")
            else:
                st.warning("⚠️ Por favor, seleccione un archivo antes de enviar.")

    # --- VISTA: INGENIERO ---
    elif rol == "ingeniero":
        st.subheader("✍️ Bandeja de Firmas")
        archivos_pendientes = os.listdir("reservas/pendientes")

        if not archivos_pendientes:
            st.info("No hay documentos pendientes de firma.")
        else:
            for nombre_archivo in archivos_pendientes:
                col1, col2 = st.columns([3, 1])
                col1.write(f"📄 {nombre_archivo}")
                
                if col2.button("Firmar", key=nombre_archivo):
                    ruta_in = f"reservas/pendientes/{nombre_archivo}"
                    ruta_out = f"reservas/firmadas/{nombre_archivo}"
                    ruta_firma = "reservas/firmas/ingeniero.png"

                    # Verificamos si existe la imagen de la firma
                    if os.path.exists(ruta_firma):
                        try:
                            doc = fitz.open(ruta_in)
                            pagina = doc[0] # Primera página
                            # Ubicación de la firma (x0, y0, x1, y1)
                            rect = fitz.Rect(400, 700, 550, 800) 
                            pagina.insert_image(rect, filename=ruta_firma)
                            doc.save(ruta_out)
                            doc.close()
                            
                            # Borramos de pendientes una vez firmado
                            os.remove(ruta_in)
                            st.success(f"✅ Documento '{nombre_archivo}' firmado.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al procesar el PDF: {e}")
                    else:
                        st.error(f"⚠️ Error: No existe el archivo '{ruta_firma}'.")
                        st.info("Sube una imagen llamada 'ingeniero.png' a la carpeta 'reservas/firmas/' en GitHub.")

    # --- VISTA: ALMACÉN ---
    elif rol == "almacen":
        st.subheader("📦 Reservas Listas para Despacho")
        archivos_firmados = os.listdir("reservas/firmadas")

        if not archivos_firmados:
            st.info("No hay documentos firmados todavía.")
        else:
            for nombre_firmado in archivos_firmados:
                col1, col2 = st.columns([3, 1])
                col1.write(f"✅ {nombre_firmado}")
                
                with open(f"reservas/firmadas/{nombre_firmado}", "rb") as f:
                    col2.download_button(
                        label="Descargar",
                        data=f,
                        file_name=nombre_firmado,
                        mime="application/pdf",
                        key=f"dl_{nombre_firmado}"
                    )
