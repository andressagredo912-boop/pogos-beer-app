import streamlit as st
import base64
import os
import json

# --- CONFIGURACIÓN Y CONSTANTES ---
PATHS = {
    "db": os.path.join("data", "productos.json"),
    "config": os.path.join("data", "config.json"),
    "assets": os.path.join("assets", "wallpaper.jpg")
}
DEFAULT_CATS = ["Salchipapas", "Bebidas", "Shots y Cocteles", "Helados y Postres"]

# --- LÓGICA DE DATOS ---
@st.cache_data(show_spinner=False)
def cargar_datos():
    productos = []
    categorias = DEFAULT_CATS.copy()

    if os.path.exists(PATHS["db"]):
        with open(PATHS["db"], "r", encoding="utf-8") as f:
            try: productos = json.load(f)
            except: productos = []

    if os.path.exists(PATHS["config"]):
        with open(PATHS["config"], "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                categorias = data.get("categorias", categorias) if isinstance(data, dict) else data
            except: pass

    cats_en_prods = {p["categoria"] for p in productos if "categoria" in p}
    for c in cats_en_prods:
        if c not in categorias:
            categorias.append(c)
            
    return productos, categorias

def guardar_todo(productos, categorias):
    os.makedirs("data", exist_ok=True)
    with open(PATHS["db"], "w", encoding="utf-8") as f:
        json.dump(productos, f, indent=4, ensure_ascii=False)
    with open(PATHS["config"], "w", encoding="utf-8") as f:
        json.dump({"categorias": categorias}, f, indent=4, ensure_ascii=False)
    st.cache_data.clear()

# --- ESTILOS ---
def set_styles(image_file):
    bg_style = ""
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()
        bg_style = f"""
            .stApp {{ 
                background-image: url("data:image/png;base64,{img_base64}"); 
                background-size: cover; background-attachment: fixed; 
            }}"""

    st.markdown(f"""
        <style>
        {bg_style}
        .item-nombre {{ font-family: 'Roboto Condensed'; font-size: 30px; font-weight: 700; color: white; margin-bottom: 0; }}
        .item-precio {{ font-family: 'Bebas Neue'; color: #E6B325; font-size: 35px; text-align: right; }}
        .item-descripcion {{ color: #cccccc; font-style: italic; font-size: 16px; margin-top: -10px; line-height: 1.2; }}
        .categoria-header {{ font-family: 'Bebas Neue'; color: #E6B325; font-size: 40px; border-bottom: 2px solid #E6B325; margin: 30px 0 15px 0; }}
        .titulo-menu {{ font-family: 'Bebas Neue'; color: white; font-size: 60px; text-align: center; }}
        </style>
    """, unsafe_allow_html=True)

# --- VISTA DEL MENÚ (CLIENTE / MESERO / ADMIN) ---
def mostrar_menu(rol_usuario="cliente"):
    set_styles(PATHS["assets"])
    productos, categorias_orden = cargar_datos()
    
    st.markdown('<p class="titulo-menu">MENÚ</p>', unsafe_allow_html=True)

    # Si es ADMIN, mostramos primero la sección de GESTIÓN
    if rol_usuario == "admin":
        gestionar_inventario()
        st.divider()

    # Mostrar el cuerpo del menú para todos
    if not productos:
        st.warning("No se encontraron productos.")
        return

    for categoria in categorias_orden:
        items_cat = [p for p in productos if p.get("categoria") == categoria]
        
        # Filtro de visibilidad para el cliente
        if rol_usuario == "cliente":
            items_cat = [i for i in items_cat if i.get("disponible", True)]
        
        if not items_cat: continue

        st.markdown(f'<p class="categoria-header">{categoria}</p>', unsafe_allow_html=True)
        
        for item in items_cat:
            col_info, col_precio = st.columns([3, 1])
            with col_info:
                # Etiqueta de oculto solo visible para Mesero y Admin
                oculto_tag = " 🚫 *(Oculto)*" if not item.get("disponible", True) and rol_usuario != "cliente" else ""
                st.markdown(f'<p class="item-nombre">{item["nombre"]}{oculto_tag}</p>', unsafe_allow_html=True)
                if item.get("desc"):
                    st.markdown(f'<p class="item-descripcion">{item["desc"]}</p>', unsafe_allow_html=True)
            
            with col_precio:
                st.markdown(f'<p class="item-precio">${item["precio"]:,}</p>', unsafe_allow_html=True)

            # Mesero y Admin pueden cambiar disponibilidad
            if rol_usuario in ["mesero", "admin"]:
                current_state = item.get("disponible", True)
                if st.toggle("Disponible", value=current_state, key=f"tgl_{item['id']}") != current_state:
                    item["disponible"] = not current_state
                    guardar_todo(productos, categorias_orden)
                    st.rerun()
            
            st.markdown("<div style='margin-bottom:20px'></div>", unsafe_allow_html=True)

# --- GESTIÓN (EXCLUSIVO ADMIN) ---
def gestionar_inventario():
    # Esta función se llama dentro de mostrar_menu si el rol es admin
    productos, categorias_orden = cargar_datos()

    with st.expander("🛠️ PANEL DE ADMINISTRACIÓN (Categorías y Productos)"):
        tab1, tab2, tab3 = st.tabs(["📂 Categorías", "➕ Nuevo Producto", "🗑️ Eliminar"])

        with tab1:
            st.subheader("Configurar Categorías")
            c1, c2 = st.columns([2, 1])
            nueva_cat = c1.text_input("Nombre de la categoría")
            pos = c2.number_input("Posición", 1, len(categorias_orden)+1, len(categorias_orden)+1)
            if st.button("Añadir Categoría"):
                if nueva_cat and nueva_cat not in categorias_orden:
                    categorias_orden.insert(int(pos)-1, nueva_cat)
                    guardar_todo(productos, categorias_orden)
                    st.rerun()

            st.divider()
            for i, categoria in enumerate(categorias_orden):
                col1, col2 = st.columns([4, 1])
                col1.write(f"**{i+1}. {categoria}**")
                if col2.button("🗑️", key=f"delcat_{categoria}"):
                    if any(p["categoria"] == categoria for p in productos):
                        st.error("Error: Elimina primero los productos de esta categoría.")
                    else:
                        categorias_orden.remove(categoria)
                        guardar_todo(productos, categorias_orden)
                        st.rerun()

        with tab2:
            with st.form("nuevo_p_form", clear_on_submit=True):
                f_nom = st.text_input("Nombre del Producto")
                f_pre = st.number_input("Precio", min_value=0, step=500)
                f_des = st.text_area("Descripción")
                f_cat = st.selectbox("Categoría", categorias_orden)
                if st.form_submit_button("Guardar Producto"):
                    if f_nom:
                        nuevo_id = max([p["id"] for p in productos], default=0) + 1
                        productos.append({
                            "id": nuevo_id, "nombre": f_nom, "precio": f_pre, 
                            "desc": f_des, "categoria": f_cat, "disponible": True
                        })
                        guardar_todo(productos, categorias_orden)
                        st.rerun()

        with tab3:
            st.subheader("Eliminar Productos")
            for categoria in categorias_orden:
                items = [p for p in productos if p["categoria"] == categoria]
                if items:
                    with st.expander(f"Productos en {categoria}"):
                        for item in items:
                            cx, cy = st.columns([4, 1])
                            cx.write(f"{item['nombre']} (${item['precio']:,})")
                            if cy.button("Eliminar", key=f"delp_{item['id']}"):
                                productos = [p for p in productos if p["id"] != item["id"]]
                                guardar_todo(productos, categorias_orden)
                                st.rerun()