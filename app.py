import streamlit as st
import os
import base64
from PIL import Image
from views.menu import mostrar_menu 
from views.gestion_pedidos import mostrar_gestion_pedidos
from views.compras import vista_compras
from views.contabilidad import mostrar_contabilidad

# --- 1. CONFIGURACIÓN (Debe ser la primera instrucción) ---
st.set_page_config(page_title="Pogo's Beer", page_icon="🍺", layout="centered")

# --- 2. FUNCIONES AUXILIARES ---
def get_base64_of_bin_file(bin_file):
    """Convierte una imagen local a base64 para usarla en CSS."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- 3. RUTAS Y ASSETS ---
ruta_logo = os.path.join("assets", "logo.png")
ruta_logo3 = os.path.join("assets", "logo3.png")
ruta_wallpaper = os.path.join("assets", "wallpaper.jpg")

# --- 4. ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Roboto+Condensed:wght@400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Roboto Condensed', sans-serif !important; }
    
    .main-header { 
        font-family: 'Bebas Neue', cursive !important; 
        color: #E6B325 !important; 
        font-size: 60px !important; 
        text-align: center; 
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5); 
        margin-bottom: 10px; 
    }
    
    .categoria-header, .subheader { 
        font-family: 'Bebas Neue', cursive !important; 
        color: #E6B325 !important; 
        font-size: 40px !important; 
        letter-spacing: 2px; 
        border-bottom: 2px solid rgba(230, 179, 37, 0.3); 
        margin-top: 20px; 
    }
    
    [data-testid="stSidebar"] { background-color: #111111; border-right: 1px solid #E6B32533; }
    
    .sidebar-title { 
        font-family: 'Bebas Neue', cursive !important; 
        color: #E6B325 !important; 
        font-size: 38px !important; 
        text-align: center; 
    }
    
    .stButton > button { 
        font-family: 'Bebas Neue', sans-serif !important; 
        background-color: #111111 !important; 
        color: #E6B325 !important; 
        border: 2px solid #E6B325 !important; 
        font-size: 22px !important; 
        width: 100%; 
    }
    
    .stButton > button:hover { background-color: #E6B325 !important; color: #000000 !important; }

    /* Estilo para el contenedor del login */
    .stForm {
        background-color: rgba(0, 0, 0, 0.7);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #E6B32533;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. LÓGICA DE LOGIN ---
def login():
    # Inyectar el fondo wallpaper.jpg
    if os.path.exists(ruta_wallpaper):
        bin_str = get_base64_of_bin_file(ruta_wallpaper)
        st.markdown(f"""
            <style>
            .stApp {{
                background-image: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), 
                                  url("data:image/jpg;base64,{bin_str}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            </style>
            """, unsafe_allow_html=True)

    # Logo superior
    if os.path.exists(ruta_logo3):
        st.image(Image.open(ruta_logo3), width=300)

    st.markdown("<h1 class='main-header'>🔐 ACCESO PANEL POGO'S</h1>", unsafe_allow_html=True)
    
    # Formulario centrado
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            user = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar"):
                creds = {
                    "admin": {"pass": "123456", "role": "admin"},
                    "danielam11": {"pass": "991211", "role": "mesero"}
                }
                if user in creds and creds[user]["pass"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_role = creds[user]["role"]
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

# --- 6. CONTROL DE FLUJO ---

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

es_cliente = st.query_params.get("access") == "cliente"

if es_cliente:
    # VISTA CLIENTE
    if os.path.exists(ruta_logo):
        st.image(Image.open(ruta_logo), use_container_width=True)
    mostrar_menu(rol_usuario="cliente")

elif not st.session_state.logged_in:
    # VISTA DE LOGIN
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

    # Renderizado según opción
    if "Menú" in opcion:
        mostrar_menu(rol_usuario=user_role)
    elif opcion == "Pedidos":
        mostrar_gestion_pedidos()
    elif opcion == "Compras":
        vista_compras()
    elif opcion == "Contabilidad":
        mostrar_contabilidad()
