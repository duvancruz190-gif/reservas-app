import streamlit as st
import os
import fitz
from streamlit_pdf_viewer import pdf_viewer
import json
import shutil

st.set_page_config(page_title="Gestión de Reservas", layout="wide")

# --- ESTILO ---
st.markdown("""
<style>
.stApp { background-color: #f5f7fa; }
.stButton>button {
    background-color: #005baa;
    color: white;
    border-radius: 8px;
    height: 45px;
    font-weight: bold;
}
.stButton>button:hover { background-color: #003f7d; }
section[data-testid="stSidebar"] { background-color: #002b5c; }
section[data-testid="stSidebar"] * { color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- CARPETAS ---
for carpeta in [
    "reservas/pendientes","reservas/firmadas","reservas/firmas",
    "reservas/archivo","reservas/enviados","reservas/rechazados","assets"
]:
    os.makedirs(carpeta, exist_ok=True)

areas = ["Producción","Calidad","Mantenimiento","Logística",
         "Recursos Humanos","Ambiental","Salud Ocupacional",
         "Marketing","Financiera","Almacén"]

usuarios = {
    "usuario":{"password":"123","rol":"usuario"},
    "ingeniero":{"password":"999","rol":"ingeniero"},
    "almacen":{"password":"000","rol":"almacen"}
}

firmas_contrasena = {
    "Producción":{"archivo":"reservas/firmas/Imagen1.png","password":"1234"},
    "Logística":{"archivo":"reservas/firmas/LogisticaRojas.png","password":"5678"},
}

if "login" not in st.session_state:
    st.session_state.login = False

# ================= LOGIN =================
if not st.session_state.login:

    col1, col2, col3 = st.columns([1,2,1])

    with col2:
        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png")

        st.markdown("<h2 style='text-align:center;'>Acceso al Sistema</h2>", unsafe_allow_html=True)

        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")

        if st.button("Ingresar", use_container_width=True):
            if u in usuarios and usuarios[u]["password"] == p:
                st.session_state.login = True
                st.session_state.rol = usuarios[u]["rol"]
                st.session_state.user_name = u
                st.session_state.pagina = "principal"
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

# ================= SISTEMA =================
else:

    # -------- SIDEBAR --------
    with st.sidebar:

        if os.path.exists("assets/ETERNITTTTT.png"):
            st.image("assets/ETERNITTTTT.png", width=180)

        st.markdown("### 👤 Usuario")
        st.write(f"**{st.session_state.user_name}**")
        st.write(f"Rol: {st.session_state.rol}")

        st.markdown("---")

        if st.session_state.rol == "usuario":

            if st.button("📤 Enviar"):
                st.session_state.pagina = "principal"
                st.rerun()

            if st.button("📄 Historial"):
                st.session_state.pagina = "historial"
                st.rerun()

            if st.button("📛 Rechazados"):
                st.session_state.pagina = "rechazados"
                st.rerun()

            st.markdown("---")

        if st.button("🚪 Cerrar sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    rol = st.session_state.rol
    st.title("📋 Gestión de Reservas")

    # ================= USUARIO =================
    if rol == "usuario":

        if "pagina" not in st.session_state:
            st.session_state.pagina = "principal"

        if "upload_key" not in st.session_state:
            st.session_state.upload_key = 0

        if st.session_state.pagina == "principal":

            st.header("📤 Enviar Nueva Reserva")

            area = st.selectbox("Área", areas)

            archivos = st.file_uploader(
                "Subir PDFs",
                type=["pdf"],
                accept_multiple_files=True,
                key=st.session_state.upload_key
            )

            if st.button("Enviar"):
                if archivos:
                    os.makedirs(f"reservas/pendientes/{area}", exist_ok=True)
                    os.makedirs(f"reservas/enviados/{area}", exist_ok=True)

                    for arch in archivos:
                        data = arch.getbuffer()

                        with open(f"reservas/pendientes/{area}/{arch.name}", "wb") as f:
                            f.write(data)

                        with open(f"reservas/enviados/{area}/{arch.name}", "wb") as f:
                            f.write(data)

                    st.success(f"{len(archivos)} archivos enviados")
                    st.session_state.upload_key += 1
                    st.rerun()

    # ================= INGENIERO =================
    elif rol == "ingeniero":

        st.header("✍️ Revisión y Firma")

        col1, col2 = st.columns([5,1])

        with col1:
            area = st.selectbox("Área", areas)

        with col2:
            if st.button("🔄"):
                st.rerun()

        carpeta = f"reservas/pendientes/{area}"
        archivos = os.listdir(carpeta) if os.path.exists(carpeta) else []

        for arc in archivos:

            with st.expander(arc):

                ruta = f"{carpeta}/{arc}"
                pdf_viewer(ruta)

                pw = st.text_input("Contraseña", type="password", key=arc)

                if st.button("Firmar", key=f"f{arc}"):

                    if pw == firmas_contrasena.get(area,{}).get("password"):

                        ruta_firma = firmas_contrasena[area]["archivo"]

                        if os.path.exists(ruta_firma):

                            doc = fitz.open(ruta)
                            page = doc[0]

                            # ================= FIRMA INTELIGENTE =================
                            rect_firma = None
                            coincidencias = page.search_for("FIRMA 1")

                            if coincidencias:
                                ref = coincidencias[0]
                                lineas_validas = []

                                for d in page.get_drawings():
                                    for item in d["items"]:
                                        if item[0] == "l":
                                            x1, y1 = item[1]
                                            x2, y2 = item[2]

                                            if abs(y1 - y2) < 2:
                                                if y1 < ref.y0 and abs(y1 - ref.y0) < 60:
                                                    lineas_validas.append((x1, y1, x2, y2))

                                if lineas_validas:
                                    x1, y1, x2, y2 = sorted(
                                        lineas_validas,
                                        key=lambda x: abs(x[1] - ref.y0)
                                    )[0]

                                    ancho_linea = x2 - x1

                                    if area == "Logística":
                                        alto_firma = ancho_linea * 0.18
                                    else:
                                        alto_firma = ancho_linea * 0.25

                                    rect_firma = fitz.Rect(
                                        x1,
                                        y1 - alto_firma,
                                        x2,
                                        y1 - 5
                                    )

                                else:
                                    x_centro = (ref.x0 + ref.x1) / 2
                                    rect_firma = fitz.Rect(
                                        x_centro - 120,
                                        ref.y0 - 100,
                                        x_centro + 120,
                                        ref.y0 - 20
                                    )

                            else:
                                ancho = page.rect.width
                                alto = page.rect.height
                                rect_firma = fitz.Rect(
                                    ancho * 0.55,
                                    alto * 0.65,
                                    ancho * 0.85,
                                    alto * 0.85
                                )

                            page.insert_image(rect_firma, filename=ruta_firma)

                            os.makedirs(f"reservas/firmadas/{area}", exist_ok=True)
                            doc.save(f"reservas/firmadas/{area}/{arc}")
                            doc.close()

                            os.remove(ruta)
                            st.success("✅ Documento firmado correctamente")
                            st.rerun()

                        else:
                            st.error(f"No se encontró la firma en: {ruta_firma}")
