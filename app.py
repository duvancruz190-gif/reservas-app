import streamlit as st
import os
import pandas as pd

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas - Usuario", layout="wide")

# --- CARPETAS ---
for carpeta in ["reservas/pendientes", "assets"]:
    os.makedirs(carpeta, exist_ok=True)

# --- ÁREAS ---
areas = ["Producción", "Calidad", "Mantenimiento", "Logística",
         "Recursos Humanos", "Ambiental", "Salud Ocupacional",
         "Marketing", "Financiera", "Almacén"]

# --- LOGIN SIMULADO ---
# Para simplificar este ejemplo, asumimos que el usuario ya está logueado
rol = "usuario"
st.session_state.user_name = "usuario_demo"

# ===========================
# USUARIO
# ===========================
if rol == "usuario":

    st.header("📤 Enviar Nueva Reserva")

    area = st.selectbox("Selecciona el área", areas)

    # --- Subir varios archivos ---
    archivos = st.file_uploader(
        "Subir PDF(s)",
        type=["pdf"],
        accept_multiple_files=True
    )

    if st.button("Enviar al Ingeniero"):
        if archivos:
            carpeta_area = f"reservas/pendientes/{area}"
            os.makedirs(carpeta_area, exist_ok=True)

            for arch in archivos:
                with open(f"{carpeta_area}/{arch.name}", "wb") as f:
                    f.write(arch.getbuffer())

            st.success(f"✅ Documento(s) enviado(s): {len(archivos)} archivo(s).")
        else:
            st.warning("Selecciona al menos un archivo.")

    # ===========================
    # Historial del usuario
    # ===========================
    st.sidebar.header("🕒 Historial de Envíos")

    area_hist = st.sidebar.selectbox("Filtrar por área", ["Todos"] + areas)

    # Cargar todos los archivos enviados
    historial = []
    base_path = "reservas/pendientes"
    for a in areas:
        carpeta_area = f"{base_path}/{a}"
        if os.path.exists(carpeta_area):
            for f_name in os.listdir(carpeta_area):
                if area_hist == "Todos" or area_hist == a:
                    historial.append({"Área": a, "Archivo": f_name, "Ruta": f"{carpeta_area}/{f_name}"})

    if historial:
        df_hist = pd.DataFrame(historial)
        for idx, row in df_hist.iterrows():
            with st.sidebar.expander(f"{row['Archivo']} ({row['Área']})"):
                col1, col2, col3 = st.columns([4,1,1])
                col1.write(row['Archivo'])
                with open(row['Ruta'], "rb") as file:
                    col2.download_button("⬇️", file, file_name=row['Archivo'])
                if col3.button("🗑️", key=f"del_{row['Ruta']}"):
                    os.remove(row['Ruta'])
                    st.experimental_rerun()  # refresca para eliminar del historial

        # Botón para descargar historial completo en Excel
        excel_df = df_hist.drop(columns=["Ruta"])
        excel_path = "historial.xlsx"
        excel_df.to_excel(excel_path, index=False)
        with open(excel_path, "rb") as f:
            st.sidebar.download_button("📥 Descargar Historial Excel", f, file_name="historial.xlsx")
    else:
        st.sidebar.info("No hay envíos registrados.")
