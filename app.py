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

    with st.sidebar:
        st.markdown("### 👤 Usuario")
        st.write(st.session_state.user_name)
        st.write(st.session_state.rol)

        if st.button("🚪 Cerrar sesión"):
            st.session_state.clear()
            st.rerun()

    rol = st.session_state.rol
    st.title("📋 Gestión de Reservas")

# ================= INGENIERO =================
    if rol == "ingeniero":

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

                            rect_firma = None
                            pagina_objetivo = None

                            # 🔍 BUSCAR EN TODAS LAS HOJAS
                            for i in range(len(doc)):
                                page = doc[i]
                                coincidencias = page.search_for("FIRMA 1")

                                if coincidencias:
                                    ref = coincidencias[0]
                                    pagina_objetivo = page

                                    lineas_validas = []

                                    for d in page.get_drawings():
                                        for item in d["items"]:
                                            if item[0] == "l":
                                                p1, p2 = item[1], item[2]
                                                x1, y1, x2, y2 = p1.x, p1.y, p2.x, p2.y

                                                if abs(y1 - y2) < 2:
                                                    if y1 < ref.y0 and abs(y1 - ref.y0) < 60:
                                                        lineas_validas.append((x1, y1, x2, y2))

                                    ancho_firma = 120
                                    alto_firma = 50

                                    if lineas_validas:
                                        x1, y1, x2, y2 = sorted(lineas_validas, key=lambda l: abs(l[1] - ref.y0))[0]

                                        ancho_linea = x2 - x1

                                        x_centro = x1 + (ancho_linea / 2)
                                        x_inicio = x_centro - (ancho_firma / 2)

                                        # 🔥 ARRIBA SI CABE
                                        y_arriba_top = y1 - alto_firma - 5

                                        if y_arriba_top > 0:
                                            rect_firma = fitz.Rect(
                                                x_inicio,
                                                y_arriba_top,
                                                x_inicio + ancho_firma,
                                                y1 - 5
                                            )
                                        else:
                                            rect_firma = fitz.Rect(
                                                x_inicio,
                                                y1 + 10,
                                                x_inicio + ancho_firma,
                                                y1 + 10 + alto_firma
                                            )
                                    else:
                                        rect_firma = fitz.Rect(
                                            ref.x0,
                                            ref.y1 + 10,
                                            ref.x0 + ancho_firma,
                                            ref.y1 + 10 + alto_firma
                                        )

                                    break

                            # fallback
                            if rect_firma is None:
                                page = doc[0]
                                pagina_objetivo = page

                                rect_firma = fitz.Rect(
                                    page.rect.width * 0.6,
                                    page.rect.height * 0.7,
                                    page.rect.width * 0.85,
                                    page.rect.height * 0.9
                                )

                            pagina_objetivo.insert_image(rect_firma, filename=ruta_firma)

                            os.makedirs(f"reservas/firmadas/{area}", exist_ok=True)
                            doc.save(f"reservas/firmadas/{area}/{arc}")
                            doc.close()

                            os.remove(ruta)
                            st.success("✅ Documento firmado")
                            st.rerun()

                motivo = st.text_input("Motivo", key=f"m{arc}")

                if st.button("Rechazar", key=f"r{arc}"):

                    if motivo:
                        os.makedirs(f"reservas/rechazados/{area}", exist_ok=True)
                        shutil.move(ruta, f"reservas/rechazados/{area}/{arc}")

                        with open(f"reservas/rechazados/{area}/{arc}.json","w") as f:
                            json.dump({"motivo":motivo},f)

                        st.rerun()

# ================= ALMACEN =================
    elif rol == "almacen":

        st.header("📦 Gestión de Documentos")

        col1, col2 = st.columns([5,1])

        with col1:
            area = st.selectbox("Área", areas)

        with col2:
            if st.button("🔄"):
                st.rerun()

        carpeta = f"reservas/firmadas/{area}"
        os.makedirs(carpeta, exist_ok=True)

        archivos = os.listdir(carpeta)

        for f in archivos:

            ruta = f"{carpeta}/{f}"

            col1,col2,col3 = st.columns([5,1,1])

            col1.write(f)

            with open(ruta,"rb") as file:
                col2.download_button("⬇️", file, file_name=f)

            if col3.button("📁", key=f):
                os.makedirs(f"reservas/archivo/{area}", exist_ok=True)
                shutil.move(ruta, f"reservas/archivo/{area}/{f}")
                st.rerun()
