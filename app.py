if rol == "usuario":

    import pandas as pd
    from datetime import datetime

    st.header("📤 Enviar Nueva Reserva")

    area = st.selectbox("Selecciona el área", areas)

    archivos = st.file_uploader(
        "Subir PDFs",
        type=["pdf"],
        accept_multiple_files=True
    )

    if st.button("Enviar al Ingeniero"):

        if archivos:

            carpeta_area = f"reservas/pendientes/{area}"
            os.makedirs(carpeta_area, exist_ok=True)

            enviados = []
            registros = []

            for arch in archivos:
                ruta = f"{carpeta_area}/{arch.name}"

                with open(ruta, "wb") as f:
                    f.write(arch.getbuffer())

                enviados.append(arch.name)

                registros.append({
                    "usuario": st.session_state.user_name,
                    "area": area,
                    "archivo": arch.name,
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

            # --- Guardar en Excel ---
            excel_file = "reservas/historial_envios.xlsx"

            df_nuevo = pd.DataFrame(registros)

            if os.path.exists(excel_file):
                df_existente = pd.read_excel(excel_file)
                df_total = pd.concat([df_existente, df_nuevo], ignore_index=True)
            else:
                df_total = df_nuevo

            df_total.to_excel(excel_file, index=False)

            st.success(f"✅ {len(enviados)} archivos enviados con éxito")

        else:
            st.warning("Selecciona al menos un archivo")

    # ===========================
    # 📄 SIDEBAR HISTORIAL
    # ===========================

    st.sidebar.markdown("### 📄 Mis envíos")

    historial = []

    for area_loop in areas:
        carpeta = f"reservas/pendientes/{area_loop}"
        if os.path.exists(carpeta):
            for f in os.listdir(carpeta):
                historial.append((area_loop, f))

    if not historial:
        st.sidebar.info("No has enviado archivos")

    for area_h, file_h in historial:

        col1, col2 = st.sidebar.columns([3,1])
        col1.write(f"📄 {file_h} ({area_h})")

        if col2.button("🗑️", key=f"del_{area_h}_{file_h}"):
            ruta = f"reservas/pendientes/{area_h}/{file_h}"
            if os.path.exists(ruta):
                os.remove(ruta)
                st.rerun()

    # ===========================
    # ⬇️ DESCARGAR EXCEL
    # ===========================

    excel_path = "reservas/historial_envios.xlsx"

    if os.path.exists(excel_path):
        with open(excel_path, "rb") as f:
            st.sidebar.download_button(
                "⬇️ Descargar historial",
                f,
                file_name="historial_envios.xlsx"
            )
