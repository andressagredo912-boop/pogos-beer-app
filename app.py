import streamlit as st
import os
from PIL import Image
from views.menu import mostrar_menu 
from views.gestion_pedidos import mostrar_gestion_pedidos
from views.compras import vista_compras
from views.contabilidad import mostrar_contabilidad

# --- 1. CONFIGURACIÓN (Siempre debe ser la primera instrucción de Streamlit) ---
st.set_page_config(page_title="Pogo's Beer", page_icon="🍺", layout="centered")

# --- 2. RUTAS Y ASSETS ---
ruta_logo = os.path.join("assets", "logo.png")

# --- 3. ESTILOS PERSONALIZADOS (Se mantiene tu CSS original) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Roboto+Condensed:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto Condensed', sans-serif !important; }
    .main-header { font-family: 'Bebas Neue', cursive !important; color: #E6B325 !important; font-size: 60px !important; text-align: center; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); margin-bottom: 10px; }
    .categoria-header, .subheader { font-family: 'Bebas Neue', cursive !important; color: #E6B325 !important; font-size: 40px !important; letter-spacing: 2px; border-bottom: 2px solid rgba(230, 179, 37, 0.3); margin-top: 20px; }
    [data-testid="stSidebar"] { background-color: #111111; border-right: 1px solid #E6B32533; }
    .sidebar-title { font-family: 'Bebas Neue', cursive !important; color: #E6B325 !important; font-size: 38px !important; text-align: center; }
    .stButton > button { font-family: 'Bebas Neue', sans-serif !important; background-color: #111111 !important; color: #E6B325 !important; border: 2px solid #E6B325 !important; font-size: 22px !important; width: 100%; }
    .stButton > button:hover { background-color: #E6B325 !important; color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. LÓGICA DE LOGIN ---
def login():
    st.markdown("<h1 class='main-header'>🔐 ACCESO PANEL</h1>", unsafe_allow_html=True)
    with st.form("login_form"):
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            creds = {
                "admin": {"pass": "123", "role": "admin"},
                "Pepito Perez": {"pass": "cerveza123", "role": "mesero"}
            }
            if user in creds and creds[user]["pass"] == password:
                st.session_state.logged_in = True
                st.session_state.user_role = creds[user]["role"]
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

# --- 5. CONTROL DE FLUJO ---

# Inicializar estado de sesión
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# DETECTAR CLIENTE: Si la URL tiene ?access=cliente, entra directo al menú
es_cliente = st.query_params.get("access") == "cliente"

if es_cliente:
    # VISTA LIMPIA PARA CLIENTE (Sin Login, Sin Sidebar)
    if os.path.exists(ruta_logo):
        st.image(Image.open(ruta_logo), use_container_width=True)
    mostrar_menu(rol_usuario="cliente")

elif not st.session_state.logged_in:
    # VISTA DE LOGIN PARA PERSONAL
    login()

else:
    # VISTA PERSONAL AUTENTICADO
    user_role = st.session_state.user_role
    
    with st.sidebar:
        if os.path.exists(ruta_logo):
            st.image(ruta_logo, width=150)
        
        st.markdown(f'<p class="sidebar-title">PANEL {user_role.upper()}</p>', unsafe_allow_html=True)
        
        if user_role == "admin":
            opciones = ["Menú (Gestionar)", "Pedidos", "Compras", "Contabilidad"]
        else:
            opciones = ["Menú (Disponibilidad)", "Pedidos"]

        opcion = st.radio("Navegación", opciones)
        
        st.divider()
        if st.button("Cerrar Sesión"):
            st.session_state.logged_in = False
            st.rerun()

    # Renderizado de vistas según opción
    if "Menú" in opcion:
        mostrar_menu(rol_usuario=user_role)
    elif opcion == "Pedidos":
        mostrar_gestion_pedidos()
    elif opcion == "Compras":
        vista_compras()
    elif opcion == "Contabilidad":
        mostrar_contabilidad()