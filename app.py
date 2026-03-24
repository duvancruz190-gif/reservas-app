import streamlit as st
import os
import fitz  # PyMuPDF
# from streamlit_pdf_viewer import pdf_viewer # Ya no lo usaremos para el ingeniero, sino el Canvas
import json
import shutil

# --- LIBRERÍAS ADICIONALES PARA EL CANVAS (INSTALAR) ---
from streamlit_drawable_canvas import st_canvas
from pdf2image import convert_from_path
from PIL import Image
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas - Firma Interactiva", layout="wide")

# --- CREAR CARPETAS (Tu código original) ---
for carpeta in [
    "reservas/pendientes",
    "reservas/firmadas",
    "reservas/firmas",
    "reservas/archivo"
]:
    os.makedirs(carpeta, exist_ok=True)

# --- ÁREAS (Tu código original) ---
areas = ["Producción", "Calidad", "Mantenimiento", "Logística",
         "Recursos Humanos", "Ambiental", "Salud Ocupacional",
         "Marketing", "Financiera", "Almacén"]

# --- USUARIOS (Tu código original) ---
usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# --- FIRMAS (Tu código original, asegúrate de tener el archivo) ---
firmas_contrasena = {
    "Producción": {"archivo": "reservas/firmas/carlos_alfonso.jpeg", "password": "1234"},
}

# --- SESIÓN (Tu código original) ---
if "login" not in st.session_state:
    st.session_state.login = False

# ===========================
# LOGIN (Tu código original)
# ===========================
if not st.session_state.login:
    st.title("🔐 Acceso al Sistema")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")

    if st.button("Ingresar", use_container_width=True):
        if u in usuarios and usuarios[u]["password"] == p:
            st.session_state.login = True
            st.session_state.rol = usuarios[u]["rol"]
            st.session_state.user_name = u
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

else:
    # --- SIDEBAR (Tu código original) ---
    with st.sidebar:
        st.title("📂 Menú Principal")
        st.write(f"👤 Usuario: **{st.session_state.get('user_name')}**")
        st.write(f"🔑 Rol: **{st.session_state.get('rol').upper()}**")
        st.write("---")

        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.title("📋 Gestión de Reservas")
    rol = st.session_state.get('rol')

    # ===========================
    # USUARIO (Tu código original)
    # ===========================
    if rol == "usuario":
        st.header("📤 Enviar Nueva Reserva")
        area = st.selectbox("Selecciona el área", areas)
        arch = st.file_uploader("Subir PDF", type=["pdf"])

        if st.button("Enviar al Ingeniero"):
            if arch:
                carpeta_area = f"reservas/pendientes/{area}"
                os.makedirs(carpeta_area, exist_ok=True)

                with open(f"{carpeta_area}/{arch.name}", "wb") as f:
                    f.write(arch.getbuffer())

                st.success(f"✅ Documento enviado a {area}.")
            else:
                st.warning("Selecciona un archivo.")

    # ==============================================================================
    # INGENIERO - SECCIÓN COMPLETAMENTE REESCRITA (CANVAS INTERACTIVO)
    # ==============================================================================
    elif rol == "ingeniero":
        st.header("✍️ Revisión y Firma Interactiva con Mouse")
        st.markdown("⚠️ *Haga clic y arrastre sobre el PDF para dibujar el recuadro donde irá su firma.*")

        colA, colB = st.columns([5,1])
        with colA:
            st.subheader("📂 Documentos pendientes")
        with colB:
            if st.button("🔄 Actualizar lista"):
                st.rerun()

        area = st.selectbox("Selecciona el área", areas)
        carpeta_area = f"reservas/pendientes/{area}"
        pendientes = os.listdir(carpeta_area) if os.path.exists(carpeta_area) else []

        if not pendientes:
            st.info(f"No hay documentos pendientes en el área de {area}.")

        for arc in pendientes:
            file_id = arc.replace(".", "_") # ID único para el canvas de este archivo

            with st.expander(f"📄 Firma Interactiva: {arc}", expanded=True):
                ruta_full = f"{carpeta_area}/{arc}"

                # 1. VALIDACIONES DE FIRMA (Tu lógica original)
                if area not in firmas_contrasena:
                    st.error(f"❌ No hay firma configurada para el área {area}.")
                    continue
                info_firma = firmas_contrasena[area]
                if not os.path.exists(info_firma["archivo"]):
                    st.error(f"❌ Archivo de firma no encontrado: {info_firma['archivo']}")
                    continue

                # --- LÓGICA DEL CANVAS INTERACTIVO ---
                try:
                    # A. Convertir PDF a Imagen de fondo para el Canvas (dpi=72 coincide con puntos PDF)
                    # Ajusta 'poppler_path' si es necesario en Windows.
                    with st.spinner("Cargando vista previa del PDF..."):
                        images = convert_from_path(ruta_full, first_page=1, last_page=1, dpi=72)
                        
                        if not images:
                            st.error("No se pudo convertir el PDF a imagen.")
                            continue
                        
                        pdf_page_img = images[0]
                        width, height = pdf_page_img.size

                    st.write("#### 🖱️ Dibuja el recuadro de tu firma aquí:")

                    # B. Configuración del Canvas (Lienzo)
                    # Usamos modo "transform" para mover/redimensionar recuadros existentes, 
                    # o "rect" para dibujar uno nuevo. Usaremos "rect" por simplicidad.
                    drawing_mode = st.radio("Herramienta:", ["rect", "transform"], key=f"mode_{file_id}", horizontal=True)

                    canvas_result = st_canvas(
                        fill_color="rgba(255, 165, 0, 0.3)",  # Naranja transparente
                        stroke_width=2,
                        stroke_color="#FF0000", # Rojo
                        background_image=pdf_page_img,
                        update_streamlit=True,
                        height=height,
                        width=width,
                        drawing_mode=drawing_mode,
                        key=f"canvas_{file_id}",
                    )

                    # C. Capturar y Validar coordenadas del recuadro
                    rect_final = None
                    if canvas_result.json_data is not None:
                        objetos = canvas_result.json_data["objects"]
                        if objetos:
                            # Tomamos el último objeto dibujado/modificado
                            obj = objetos[-1] 
                            
                            if obj["type"] == "rect":
                                # Coordenadas del Canvas (píxeles a 72 dpi)
                                # left, top son la esquina superior izquierda. width, height son tamaño.
                                # scaleX, scaleY son factores si se redimensionó en modo transform.
                                l = obj["left"]
                                t = obj["top"]
                                w = obj["width"] * obj["scaleX"]
                                h = obj["height"] * obj["scaleY"]
                                
                                st.info(f"📍 Área de firma capturada: X={int(l)}, Y={int(t)} | Tamaño: {int(w)}x{int(h)}")
                                
                                # Definir el rectángulo final para PyMuPDF
                                rect_final = fitz.Rect(l, t, l + w, t + h)
                            else:
                                st.warning("Por favor, use la herramienta de rectángulo para definir el área.")
                        else:
                            st.warning("⚠️ Dibuje un recuadro sobre el PDF para ubicar su firma.")

                    st.write("---")

                    # D. Sección de Firma Final (Tu lógica original con validación del canvas)
                    contra_firma = st.text_input("Contraseña de firma", type="password", key=f"pw_{arc}")

                    if st.button("🖋️ Confirmar y Guardar PDF Firmado", key=f"btn_{arc}"):
                        if contra_firma == info_firma["password"]:
                            if rect_final is not None:
                                with st.spinner("Estampando firma en el PDF real..."):
                                    try:
                                        # Abrir PDF real con PyMuPDF
                                        doc = fitz.open(ruta_full)
                                        pagina = doc[0]

                                        # Insertar la imagen en las coordenadas EXACTAS del canvas
                                        pagina.insert_image(rect_final, filename=info_firma["archivo"])

                                        # Procesos de guardado estándar (Tu código original)
                                        carpeta_firmadas = f"reservas/firmadas/{area}"
                                        os.makedirs(carpeta_firmadas, exist_ok=True)

                                        doc.save(f"{carpeta_firmadas}/{arc}")
                                        doc.close()

                                        # Eliminar pendiente
                                        os.remove(ruta_full)

                                        st.success(f"✅ Documento '{arc}' firmado interactivamente y enviado a almacén.")
                                        st.rerun()

                                    except Exception as e:
                                        st.error(f"Error crítico al guardar el PDF: {e}")
                            else:
                                st.error("❌ Debe dibujar un recuadro sobre el PDF para ubicar la firma.")
                        else:
                            st.error("❌ Contraseña de firma incorrecta.")

                except Exception as e:
                    st.error(f"Error cargando el editor interactivo: {e}")
                    st.warning("Se intentará mostrar el PDF original como descarga.")
                    with open(ruta_full, "rb") as f:
                        st.download_button("Descargar PDF para revisar", f, file_name=arc)

    # ===========================
    # ALMACÉN (Tu código original)
    # ===========================
    elif rol == "almacen":
        st.header("📦 Gestión de Documentos")

        colA, colB = st.columns([5,1])
        with colA:
            st.subheader("📂 Archivos")
        with colB:
            if st.button("🔄 Actualizar"):
                st.rerun()

        estado_file = "reservas/firmadas/estado.json"

        if os.path.exists(estado_file):
            with open(estado_file, "r") as f:
                estados = json.load(f)
        else:
            estados = {}

        vista = st.radio("Vista", ["Firmados", "Archivados"])
        area = st.selectbox("Selecciona el área", areas)

        carpeta_area = f"reservas/firmadas/{area}" if vista == "Firmados" else f"reservas/archivo/{area}"
        os.makedirs(carpeta_area, exist_ok=True)

        archivos = os.listdir(carpeta_area)

        # 🔍 BUSCADOR
        busqueda = st.text_input("🔍 Buscar por número o nombre")

        if busqueda:
            archivos = [f for f in archivos if busqueda.lower() in f.lower()]

        st.write(f"📄 Resultados: {len(archivos)}")

        if not archivos:
            st.info("No hay documentos aquí.")

        for f_name in archivos:
            ruta = f"{carpeta_area}/{f_name}"
            icono = "💛" if estados.get(f"{area}/{f_name}", False) else "💙"

            col1, col2, col3, col4 = st.columns([3,1,1,1])
            col1.write(f"{icono} {f_name}")

            with open(ruta, "rb") as file:
                if col2.download_button("⬇️", file, file_name=f_name, key=f"down_{ruta}"): # Agregué key única
                    estados[f"{area}/{f_name}"] = True
                    with open(estado_file, "w") as ff:
                        json.dump(estados, ff)

            if vista == "Firmados":
                if col3.button("📁", key=f"arch_{ruta}"):
                    destino = f"reservas/archivo/{area}"
                    os.makedirs(destino, exist_ok=True)
                    shutil.move(ruta, f"{destino}/{f_name}")
                    st.rerun()

            if col4.button("🗑️", key=f"del_{ruta}"):
                os.remove(ruta)
                st.rerun()
