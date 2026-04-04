import streamlit as st
import os
import fitz
from streamlit_pdf_viewer import pdf_viewer
import json
import shutil

st.set_page_config(page_title="Gestión de Reservas", layout="wide")

# --- CARPETAS ---
for carpeta in [
    "reservas/pendientes",
    "reservas/firmadas",
    "reservas/rechazados",
    "reservas/firmas",
    "reservas/archivo",
    "assets"
]:
    os.makedirs(carpeta, exist_ok=True)

# --- ÁREAS ---
areas = ["Producción", "Calidad", "Mantenimiento", "Logística",
         "Recursos Humanos", "Ambiental", "Salud Ocupacional",
         "Marketing", "Financiera", "Almacén"]

# --- USUARIOS ---
usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# --- SESIÓN ---
if "login" not in st.session_state:
    st.session_state.login = False

if "pagina" not in st.session_state:
    st.session_state.pagina = "principal"

# ================= LOGIN =================
if not st.session_state.login:

    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if u in usuarios and usuarios[u]["password"] == p:
            st.session_state.login = True
            st.session_state.rol = usuarios[u]["rol"]
            st.session_state.user_name = u
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

# ================= SISTEMA =================
else:

    # --- SIDEBAR ---
    with st.sidebar:

        st.write(f"👤 {st.session_state.user_name}")
        st.write(f"🔑 {st.session_state.rol}")

        st.markdown("---")

        if st.button("📄 Historial"):
            st.session_state.pagina = "historial"
            st.rerun()

        if st.button("🚪 Cerrar Sesión"):
            st.session_state.clear()
            st.rerun()

    rol = st.session_state.rol

    # ================= USUARIO =================
    if rol == "usuario":

        # -------- ENVIAR --------
        if st.session_state.pagina == "principal":

            st.title("📤 Enviar Reservas")

            area = st.selectbox("Área", areas)

            if "upload_key" not in st.session_state:
                st.session_state.upload_key = 0

            archivos = st.file_uploader(
                "Subir PDFs",
                type=["pdf"],
                accept_multiple_files=True,
                key=st.session_state.upload_key
            )

            if st.button("Enviar"):

                if archivos:

                    carpeta = f"reservas/pendientes/{area}"
                    os.makedirs(carpeta, exist_ok=True)

                    for arch in archivos:
                        with open(f"{carpeta}/{arch.name}", "wb") as f:
                            f.write(arch.getbuffer())

                    st.success("✅ Enviado correctamente")

                    st.session_state.upload_key += 1
                    st.rerun()

                else:
                    st.warning("Sube archivos")

            # -------- RECHAZADOS --------
            st.markdown("## 📛 Archivos Rechazados")

            encontrados = False

            for a in areas:
                carpeta = f"reservas/rechazados/{a}"
                if os.path.exists(carpeta):
                    for f in os.listdir(carpeta):
                        if f.endswith(".pdf"):
                            encontrados = True

                            ruta_json = f"{carpeta}/{f}.json"
                            motivo = "Sin motivo"

                            if os.path.exists(ruta_json):
                                with open(ruta_json) as ff:
                                    motivo = json.load(ff).get("motivo")

                            st.warning(f"📄 {f} ({a})")
                            st.write(f"📝 {motivo}")
                            st.markdown("---")

            if not encontrados:
                st.info("No hay rechazados")

        # -------- HISTORIAL (SOLO VISUAL) --------
        elif st.session_state.pagina == "historial":

            st.title("📄 Historial")

            if st.button("⬅️ Volver"):
                st.session_state.pagina = "principal"
                st.rerun()

            area_sel = st.selectbox("Área", ["Todas"] + areas)

            for a in areas:
                if area_sel != "Todas" and a != area_sel:
                    continue

                carpeta = f"reservas/pendientes/{a}"
                if os.path.exists(carpeta):

                    for f in os.listdir(carpeta):
                        st.write(f"📄 {f} ({a})")

    # ================= INGENIERO =================
    elif rol == "ingeniero":

        st.title("✍️ Revisión")

        area = st.selectbox("Área", areas)
        carpeta = f"reservas/pendientes/{area}"

        if os.path.exists(carpeta):
            archivos = os.listdir(carpeta)
        else:
            archivos = []

        for arc in archivos:

            with st.expander(f"📄 {arc}"):

                ruta = f"{carpeta}/{arc}"

                try:
                    pdf_viewer(ruta, width=800, height=600)
                except:
                    st.write("No preview")

                # --- RECHAZAR ---
                motivo = st.text_input("Motivo rechazo", key=f"mot_{arc}")

                if st.button("❌ Rechazar", key=f"rech_{arc}"):

                    if motivo.strip() == "":
                        st.warning("Escribe motivo")
                    else:

                        destino = f"reservas/rechazados/{area}"
                        os.makedirs(destino, exist_ok=True)

                        shutil.move(ruta, f"{destino}/{arc}")

                        with open(f"{destino}/{arc}.json", "w") as f:
                            json.dump({"motivo": motivo}, f)

                        st.error("Rechazado")
                        st.rerun()

                # --- FIRMAR (igual) ---
                if st.button("🖋️ Firmar", key=f"firm_{arc}"):

                    destino = f"reservas/firmadas/{area}"
                    os.makedirs(destino, exist_ok=True)

                    shutil.move(ruta, f"{destino}/{arc}")

                    st.success("Firmado")
                    st.rerun()

    # ================= ALMACÉN =================
    elif rol == "almacen":
        st.title("📦 Almacén")
