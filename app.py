import streamlit as st
import os
import fitz  # PyMuPDF

# 1. CONFIGURACIÓN DE CARPETAS
# Creamos las rutas necesarias al iniciar la app
carpetas = ["reservas/pendientes", "reservas/firmadas", "reservas/firmas"]
for carpeta in carpetas:
    os.makedirs(carpeta, exist_ok=True)

# 2. BASE DE DATOS DE USUARIOS
usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# 3. CONTROL DE SESIÓN
if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.rol = None

# --- PANTALLA DE LOGIN ---
if not st.session_state.login:
    st.title("🔐 Acceso al Sistema")
    with st.container():
        user = st.text_input("Nombre de Usuario")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar"):
            if user in usuarios and usuarios[user]["password"] == password:
                st.session_state.login = True
                st.session_state.rol = usuarios[user]["rol"]
                st.rerun()
            else:
                st.error("⚠️ Usuario o contraseña incorrectos")

# --- PANTALLA PRINCIPAL (PARA TODOS LOS ROLES) ---
else:
    # 🚪 BARRA LATERAL: Aparece para Usuario, Ingeniero y Almacén
    with st.sidebar:
        st.header(f"👤 {st.session_state.rol.upper()}")
        st.write("---")
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state.login = False
            st.session_state.rol = None
            st.rerun()

    st.title("Sistema de Gestión de Reservas")
    rol = st.session_state.rol

    # --- FLUJO USUARIO ---
    if rol == "usuario":
        st.subheader("📤 Enviar Nueva Reserva")
        archivo = st.file_uploader("Subir archivo PDF", type=["pdf"])
        
        if st.button("Enviar al Ingeniero"):
            if archivo:
                path = f"reservas/pendientes/{archivo.name}"
                with open(path, "wb") as f:
                    f.write(archivo.getbuffer()) # buffer asegura que el archivo se guarde completo
                st.success(f"✅ ¡Éxito! El archivo '{archivo.name}' ya está en la bandeja del Ingeniero.")
            else:
                st.warning("⚠️ Selecciona un archivo PDF primero.")

    # --- FLUJO INGENIERO ---
    elif rol == "ingeniero":
        st.subheader("✍️ Bandeja de Firmas")
        pendientes = os.listdir("reservas/pendientes")
        
        if not pendientes:
            st.info("No hay documentos pendientes por ahora.")
        else:
            for arch in pendientes:
                col1, col2 = st.columns([3, 1])
                col1.write(f"📄 {arch}")
                
                if col2.button("Firmar", key=arch):
                    ruta_in = f"reservas/pendientes/{arch}"
                    ruta_out = f"reservas/firmadas/{arch}"
                    ruta_firma = "reservas/firmas/ingeniero.png"

                    if os.path.exists(ruta_firma):
                        doc = fitz.open(ruta_in)
                        pagina = doc[0]
                        # Posición de la firma (x0, y0, x1, y1)
                        rect = fitz.Rect(400, 700, 550, 800) 
                        pagina.insert_image(rect, filename=ruta_firma)
                        doc.save(ruta_out)
                        doc.close()
                        
                        os.remove(ruta_in) # Se quita de pendientes
                        st.success("✅ Documento firmado y enviado a Almacén.")
                        st.rerun() # Actualiza la lista inmediatamente
                    else:
                        st.error("❌ Error: No se encuentra la imagen 'ingeniero.png' en la carpeta 'reservas/firmas'")

    # --- FLUJO ALMACÉN ---
    elif rol == "almacen":
        st.subheader("📦 Reservas Listas para Despacho")
        firmados = os.listdir("reservas/firmadas")
        
        if not firmados:
            st.info("No hay documentos firmados todavía.")
        else:
            for arch_firmado in firmados:
                col1, col2 = st.columns([3, 1])
                col1.write(f"✅ {arch_firmado}")
                
                with open(f"reservas/firmadas/{arch_firmado}", "rb") as f:
                    col2.download_button(
                        label="Descargar",
                        data=f,
                        file_name=arch_firmado,
                        mime="application/pdf",
                        key=f"dl_{arch_firmado}"
                    )
