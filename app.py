import streamlit as st
import os
import fitz  # PyMuPDF

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
st.set_page_config(page_title="Gestión de Reservas PRO", layout="wide")

areas = ["Producción", "Calidad", "Mantenimiento", "Logística",
         "Recursos Humanos", "Ambiental", "Salud Ocupacional",
         "Marketing", "Financiera", "Almacén"]

for carpeta in ["reservas/pendientes", "reservas/firmadas", "reservas/firmas"]:
    os.makedirs(carpeta, exist_ok=True)
for area in areas:
    os.makedirs(f"reservas/pendientes/{area}", exist_ok=True)
    os.makedirs(f"reservas/firmadas/{area}", exist_ok=True)

usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

firma_path = "reservas/firmas/carlos_alfonso.jpeg"
firma_password = "1234"

# -----------------------------
# FUNCIÓN PRO DE FIRMA
# -----------------------------
def insertar_firma_auto(page, texto_buscar, firma_path):
    coincidencias = page.search_for(texto_buscar)

    for inst in coincidencias:
        x0 = inst.x0
        x1 = inst.x1
        y_texto = inst.y0

        # 🔍 Buscar línea arriba del texto
        drawings = page.get_drawings()
        linea_y = None

        for d in drawings:
            for item in d["items"]:
                if item[0] == "l":  # línea
                    x_start, y_start, x_end, y_end = item[1]

                    # Línea horizontal cercana al texto
                    if abs(y_start - y_end) < 2 and (y_start < y_texto):
                        if abs(y_texto - y_start) < 80:
                            linea_y = y_start
                            break

            if linea_y:
                break

        # Si encuentra línea → usarla
        if linea_y:
            y_firma = linea_y - 5
        else:
            # fallback si no encuentra línea
            y_firma = y_texto - 80

        # 📏 Ajuste automático de tamaño
        ancho = (x1 - x0) * 1.5
        alto = ancho * 0.4

        rect = fitz.Rect(
            x0,
            y_firma - alto,
            x0 + ancho,
            y_firma
        )

        page.insert_image(rect, filename=firma_path)

# -----------------------------
# SESIÓN
# -----------------------------
if "login" not in st.session_state:
    st.session_state.login = False

# -----------------------------
# LOGIN
# -----------------------------
if not st.session_state.login:
    st.title("🔐 Acceso")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if u in usuarios and usuarios[u]["password"] == p:
            st.session_state.login = True
            st.session_state.rol = usuarios[u]["rol"]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

# -----------------------------
# APP
# -----------------------------
else:
    rol = st.session_state.rol

    # ===========================
    # USUARIO
    # ===========================
    if rol == "usuario":
        st.header("📤 Subir PDF")
        area = st.selectbox("Área", areas)
        archivo = st.file_uploader("PDF", type=["pdf"])

        if st.button("Enviar"):
            if archivo:
                with open(f"reservas/pendientes/{area}/{archivo.name}", "wb") as f:
                    f.write(archivo.getbuffer())
                st.success("✅ Enviado")

    # ===========================
    # INGENIERO
    # ===========================
    elif rol == "ingeniero":
        st.header("✍️ Firma Automática PRO")

        area = st.selectbox("Área", areas)
        carpeta = f"reservas/pendientes/{area}"
        archivos = os.listdir(carpeta)

        if not archivos:
            st.info("Sin documentos")

        for archivo in archivos:
            with st.expander(f"📄 {archivo}"):

                ruta = f"{carpeta}/{archivo}"

                # Ver PDF
                with open(ruta, "rb") as f:
                    st.download_button("Ver PDF", f, file_name=archivo)

                pw = st.text_input("Contraseña firma", type="password", key=archivo)

                if pw == firma_password:

                    if st.button("🖋️ Firmar automáticamente", key=f"btn_{archivo}"):

                        doc = fitz.open(ruta)

                        for page in doc:
                            insertar_firma_auto(page, "FIRMA 1", firma_path)

                        destino = f"reservas/firmadas/{area}/{archivo}"
                        doc.save(destino)
                        doc.close()

                        os.remove(ruta)

                        st.success("✅ Firma colocada correctamente sobre la línea")
                        st.rerun()

                elif pw:
                    st.error("❌ Contraseña incorrecta")

    # ===========================
    # ALMACÉN
    # ===========================
    elif rol == "almacen":
        st.header("📦 Documentos Firmados")

        area = st.selectbox("Área", areas)
        carpeta = f"reservas/firmadas/{area}"
        archivos = os.listdir(carpeta)

        for archivo in archivos:
            with open(f"{carpeta}/{archivo}", "rb") as f:
                st.download_button(f"Descargar {archivo}", f)
