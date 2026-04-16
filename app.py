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

        elif st.session_state.pagina == "historial":

            st.header("📄 Historial")

            area_sel = st.selectbox("Filtrar por área", ["Todas"] + areas)

            archivos_totales = []

            if area_sel == "Todas":
                for a in areas:
                    ruta = f"reservas/enviados/{a}"
                    if os.path.exists(ruta):
                        for f in os.listdir(ruta):
                            archivos_totales.append((a,f))
            else:
                ruta = f"reservas/enviados/{area_sel}"
                if os.path.exists(ruta):
                    for f in os.listdir(ruta):
                        archivos_totales.append((area_sel,f))

            if not archivos_totales:
                st.info("No hay archivos")
            else:

                st.write(f"📄 Total: {len(archivos_totales)}")

                if st.button("🧹 Borrar todo"):
                    for a,f in archivos_totales:
                        os.remove(f"reservas/enviados/{a}/{f}")
                    st.rerun()

                for a,f in archivos_totales:
                    col1,col2 = st.columns([6,1])
                    col1.write(f"{f} ({a})")

                    if col2.button("🗑️", key=f"hist_{a}_{f}"):
                        os.remove(f"reservas/enviados/{a}/{f}")
                        st.rerun()

        elif st.session_state.pagina == "rechazados":

            st.header("📛 Archivos Rechazados")

            area_sel = st.selectbox("Filtrar por área", ["Todas"] + areas)

            rechazados = []

            if area_sel == "Todas":
                for a in areas:
                    ruta = f"reservas/rechazados/{a}"
                    if os.path.exists(ruta):
                        for f in os.listdir(ruta):
                            if f.endswith(".pdf"):
                                rechazados.append((a,f))
            else:
                ruta = f"reservas/rechazados/{area_sel}"
                if os.path.exists(ruta):
                    for f in os.listdir(ruta):
                        if f.endswith(".pdf"):
                            rechazados.append((area_sel,f))

            if not rechazados:
                st.info("No hay rechazados")
            else:

                st.write(f"📄 Total: {len(rechazados)}")

                if st.button("🧹 Borrar todos"):
                    for a,f in rechazados:
                        os.remove(f"reservas/rechazados/{a}/{f}")
                        json_path = f"reservas/rechazados/{a}/{f}.json"
                        if os.path.exists(json_path):
                            os.remove(json_path)
                    st.rerun()

                for a,f in rechazados:

                    motivo = "Sin motivo"
                    ruta_json = f"reservas/rechazados/{a}/{f}.json"

                    if os.path.exists(ruta_json):
                        with open(ruta_json) as ff:
                            motivo = json.load(ff)["motivo"]

                    col1,col2 = st.columns([6,1])
                    col1.warning(f"{f} ({a})")
                    col1.write(f"Motivo: {motivo}")

                    if col2.button("🗑️", key=f"rech_{a}_{f}"):
                        os.remove(f"reservas/rechazados/{a}/{f}")
                        if os.path.exists(ruta_json):
                            os.remove(ruta_json)
                        st.rerun()

    # ================= INGENIERO =================
    elif rol == "ingeniero":

        st.header("✍️ Revisión y Firma")

        col1, col2 = st.columns([5,1])
        with col1:
            area = st.selectbox("Área", ["Todas"] + areas)
        with col2:
            if st.button("🔄"):
                st.rerun()

        archivos = []

        if area == "Todas":
            for a in areas:
                carpeta = f"reservas/pendientes/{a}"
                if os.path.exists(carpeta):
                    for f in os.listdir(carpeta):
                        archivos.append((a, f))
        else:
            carpeta = f"reservas/pendientes/{area}"
            if os.path.exists(carpeta):
                for f in os.listdir(carpeta):
                    archivos.append((area, f))

        for a, arc in archivos:

            with st.expander(f"{arc} ({a})"):

                ruta = f"reservas/pendientes/{a}/{arc}"
                pdf_viewer(ruta)

                pw = st.text_input("Contraseña", type="password", key=arc)

                if st.button("Firmar", key=f"f{arc}"):

                    datos_firma = firmas_contrasena.get(a)

                    if datos_firma and pw == datos_firma.get("password"):

                        ruta_firma = datos_firma["archivo"]

                        if os.path.exists(ruta_firma):

                            doc = fitz.open(ruta)
                            rect_firma = None
                            pagina_objetivo = None

                            for page in doc:
                                coincidencias = page.search_for("FIRMA 1")

                                if coincidencias:
                                    ref = coincidencias[0]
                                    pagina_objetivo = page

                                    ancho_firma = 120
                                    alto_firma = 50
                                    x_centro = (ref.x0 + ref.x1) / 2

                                    def hay_contenido(page, rect):
                                        texto = page.get_text("text", clip=rect)
                                        if texto.strip():
                                            return True
                                        for d in page.get_drawings():
                                            for item in d["items"]:
                                                if item[0] == "l":
                                                    p1, p2 = item[1], item[2]
                                                    if rect.intersects(fitz.Rect(p1, p2)):
                                                        return True
                                        return False

                                    y_base_arriba = ref.y0 - 10

                                    for i in range(8):
                                        rect_intento = fitz.Rect(
                                            x_centro - ancho_firma/2,
                                            y_base_arriba - alto_firma,
                                            x_centro + ancho_firma/2,
                                            y_base_arriba
                                        )

                                        if not hay_contenido(page, rect_intento):
                                            rect_firma = rect_intento
                                            break

                                        y_base_arriba -= 10
                                    else:
                                        y_base_abajo = ref.y1 + 15

                                        for i in range(12):
                                            rect_intento = fitz.Rect(
                                                x_centro - ancho_firma/2,
                                                y_base_abajo,
                                                x_centro + ancho_firma/2,
                                                y_base_abajo + alto_firma
                                            )

                                            if not hay_contenido(page, rect_intento):
                                                rect_firma = rect_intento
                                                break

                                            y_base_abajo += 12
                                        else:
                                            rect_firma = fitz.Rect(
                                                x_centro - ancho_firma/2,
                                                ref.y1 + 40,
                                                x_centro + ancho_firma/2,
                                                ref.y1 + 40 + alto_firma
                                            )

                                    break

                            if not pagina_objetivo:
                                pagina_objetivo = doc[-1]
                                ancho = pagina_objetivo.rect.width
                                alto = pagina_objetivo.rect.height
                                rect_firma = fitz.Rect(
                                    ancho * 0.55,
                                    alto * 0.65,
                                    ancho * 0.85,
                                    alto * 0.85
                                )

                            pagina_objetivo.insert_image(rect_firma, filename=ruta_firma)

                            os.makedirs(f"reservas/firmadas/{a}", exist_ok=True)
                            doc.save(f"reservas/firmadas/{a}/{arc}")
                            doc.close()

                            os.remove(ruta)
                            st.success("✅ Documento firmado correctamente")
                            st.rerun()

                motivo = st.text_input("Motivo", key=f"m{arc}")

                if st.button("Rechazar", key=f"r{arc}"):

                    if motivo:
                        os.makedirs(f"reservas/rechazados/{a}", exist_ok=True)
                        shutil.move(ruta, f"reservas/rechazados/{a}/{arc}")

                        with open(f"reservas/rechazados/{a}/{arc}.json","w") as f:
                            json.dump({"motivo":motivo},f)

                        st.rerun()

# ================= ALMACÉN =================
elif rol == "almacen":

    st.header("📦 Gestión de Documentos")

    col1, col2 = st.columns([5,1])
    with col1:
        area = st.selectbox("Área", ["Todas"] + areas)
    with col2:
        if st.button("🔄", key="refresh_almacen"):
            st.rerun()

    vista = st.radio("Vista", ["Firmados","Archivados"])

    archivos = []

    if area == "Todas":
        for a in areas:
            carpeta = f"reservas/firmadas/{a}" if vista=="Firmados" else f"reservas/archivo/{a}"
            if os.path.exists(carpeta):
                for f in os.listdir(carpeta):
                    archivos.append((a, f))
    else:
        carpeta = f"reservas/firmadas/{area}" if vista=="Firmados" else f"reservas/archivo/{area}"
        os.makedirs(carpeta, exist_ok=True)
        for f in os.listdir(carpeta):
            archivos.append((area, f))

    # 🧹 BORRADO MASIVO EN ARCHIVADOS
    if vista == "Archivados" and archivos:
        if st.button("🧹 Borrar todos los archivados"):
            for a, f in archivos:
                ruta_del = f"reservas/archivo/{a}/{f}"
                if os.path.exists(ruta_del):
                    os.remove(ruta_del)
            st.success("Archivados eliminados")
            st.rerun()

    for a, f in archivos:

        ruta = f"reservas/firmadas/{a}/{f}" if vista=="Firmados" else f"reservas/archivo/{a}/{f}"

        col1,col2,col3,col4 = st.columns([4,1,1,1])
        col1.write(f"{f} ({a})")

        # ⬇️ DESCARGAR Y MOVER AUTOMÁTICAMENTE A ARCHIVO
        with open(ruta,"rb") as file:
            if col2.download_button("⬇️", file, file_name=f, key=f"down_{a}_{f}"):

                if vista == "Firmados":
                    os.makedirs(f"reservas/archivo/{a}", exist_ok=True)
                    shutil.move(ruta, f"reservas/archivo/{a}/{f}")
                    st.success(f"{f} movido a archivo")
                    st.rerun()

        if vista == "Firmados":

            if col3.button("📁", key=f"a{f}"):
                os.makedirs(f"reservas/archivo/{a}", exist_ok=True)
                shutil.move(ruta, f"reservas/archivo/{a}/{f}")
                st.rerun()

            if col4.button("🗑️", key=f"del_f{f}"):
                os.remove(ruta)
                st.rerun()

        else:

            if col3.button("🗑️", key=f"del_a{f}"):
                os.remove(ruta)
                st.rerun()
