import streamlit as st 
import os
import json
import time
from datetime import datetime
import pandas as pd
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reservas", layout="wide")

# --- ARCHIVO HISTORIAL ---
HISTORIAL_FILE = "reservas/historial.json"

def cargar_historial():
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, "r") as f:
            return json.load(f)
    return []

def guardar_historial(data):
    with open(HISTORIAL_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- ESTADOS ---
if "login" not in st.session_state:
    st.session_state.login = False
if "rol" not in st.session_state:
    st.session_state.rol = ""
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "historial" not in st.session_state:
    st.session_state.historial = cargar_historial()
if "refresh" not in st.session_state:
    st.session_state.refresh = 0
if "mensaje_envio" not in st.session_state:
    st.session_state.mensaje_envio = ""

# --- USUARIOS ---
usuarios = {
    "usuario": {"password": "123", "rol": "usuario"},
    "ingeniero": {"password": "999", "rol": "ingeniero"},
    "almacen": {"password": "000", "rol": "almacen"}
}

# --- ESTILO LOGIN UNIFICADO PROFESIONAL ---
st.markdown("""
<style>
/* FONDO GENERAL */
.stApp {
    background-color: #ffffff;
    color: #333;
}

/* CENTRAR TODO EL LOGIN */
.css-18e3th9 {
    justify-content: center;
    align-items: center;
}

/* INPUTS */
div.stTextInput>div>div>input {
    height: 45px;
    border-radius: 6px;
    border: 1px solid #ccc;
    padding-left: 10px;
}

/* BOTÓN */
.stButton>button {
    background-color: #005baa !important;  /* Azul corporativo */
    color: white !important;
    border-radius: 6px;
    height: 45px;
    font-weight: bold;
    border: none;
}

.stButton>button:hover {
    background-color: #004080 !important;
}

/* LOGO */
img {
    max-width: 300px;
    height: auto;
    object-fit: contain;
    margin-bottom: 20px;
}

/* TEXTOS */
h2, .css-10trblm {
    color: #333;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# --- LOGIN UNIFICADO ---
if not st.session_state.login:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        # Logo limpio Eternit
        if os.path.exists("assets/ETERNIT_LOGO_LIMPIO.png"):
            st.image("assets/ETERNIT_LOGO_LIMPIO.png")

        st.markdown("<h2>Acceso al Sistema</h2>", unsafe_allow_html=True)
        st.caption("Gestión de Reservas - Eternit Colombiana")

        usuario_input = st.text_input("Usuario")
        contrasena_input = st.text_input("Contraseña", type="password")

        if st.button("Ingresar", use_container_width=True):
            if usuario_input in usuarios and usuarios[usuario_input]["password"] == contrasena_input:
                st.session_state.login = True
                st.session_state.rol = usuarios[usuario_input]["rol"]
                st.session_state.user_name = usuario_input
                st.experimental_rerun()
            else:
                st.error("Credenciales incorrectas")

# --- SISTEMA ---
else:
    st.sidebar.write(f"👤 {st.session_state.user_name}")
    st.sidebar.write(f"🔑 {st.session_state.rol}")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.clear()
        st.experimental_rerun()
    
    st.title("📋 Gestión de Reservas")
    if st.session_state.rol == "usuario":
        st.header("📤 Enviar Nueva Reserva")
        st.write("Aquí va la sección de usuario con botones rojos profesionales.")
