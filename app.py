# ===========================
# USUARIO
# ===========================
if rol == "usuario":

    st.markdown("""
    <style>
        /* Fondo de la sección */
        .stApp section[data-testid="stSidebar"] {
            background-color: #0b1f3f;  /* Azul corporativo oscuro */
            color: #ffffff;
        }

        .stApp section[data-testid="stSidebar"] * {
            color: white !important;
        }

        /* Botones principales */
        .stButton>button {
            background-color: #005baa;
            color: white;
            font-weight: bold;
            border-radius: 6px;
            height: 45px;
        }

        .stButton>button:hover {
            background-color: #003f7d;
            color: white;
        }

        /* Inputs */
        .stTextInput>div>div>input {
            border-radius: 6px;
            border: 1px solid #005baa;
            padding: 6px;
        }

        /* Sidebar expander */
        .st-expander {
            background-color: #0f2a50;
            border-radius: 6px;
            padding: 5px;
        }

        .st-expander header {
            font-weight: bold;
            color: #ffd966;
        }

        .stDownloadButton>button {
            background-color: #0072c6;
            color: white;
            border-radius: 6px;
        }

        .stDownloadButton>button:hover {
            background-color: #004a8f;
        }
    </style>
    """, unsafe_allow_html=True)

    st.header("📤 Enviar Nueva Reserva")

    area = st.selectbox("Selecciona el área", areas)

    # --- Subir varios archivos ---
    archivos = st.file_uploader(
        "Subir PDF(s)",
        type=["pdf"],
        accept_multiple_files=True
    )

    if st.button("Enviar al Ingeniero", use_container_width=True):
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

                # Descargar PDF
                with open(row['Ruta'], "rb") as file:
                    col2.download_button(
                        "⬇️",
                        file,
                        file_name=row['Archivo'],
                        key=f"dl_{row['Ruta']}"
                    )

                # Botón de borrar visible
                if col3.button(
                    "🗑️ Borrar",
                    key=f"del_{row['Ruta']}",
                    help="Eliminar este archivo",
                    use_container_width=True
                ):
                    os.remove(row['Ruta'])
                    st.experimental_rerun()  # refresca el historial al borrar

        # Descargar historial completo en Excel
        excel_df = df_hist.drop(columns=["Ruta"])
        excel_path = "historial.xlsx"
        excel_df.to_excel(excel_path, index=False)
        with open(excel_path, "rb") as f:
            st.sidebar.download_button(
                "📥 Descargar Historial Excel",
                f,
                file_name="historial.xlsx"
            )

    else:
        st.sidebar.info("No hay envíos registrados.")
