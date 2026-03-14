import streamlit as st
import json
import os
from datetime import datetime

# --- CONFIGURACIÓN DE RUTAS ---
DB_PEDIDOS = os.path.join("data", "pedidos.json")
DB_PRODUCTOS = os.path.join("data", "productos.json")
DB_CONFIG = os.path.join("data", "config.json")

# --- FUNCIONES DE CARGA DINÁMICA (Sin Caché para tiempo real) ---

def cargar_configuracion():
    """Carga las categorías desde config.json"""
    if os.path.exists(DB_CONFIG):
        try:
            with open(DB_CONFIG, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("categorias", [])
        except: return []
    return []

def obtener_productos_disponibles():
    """Lee productos.json y normaliza categorías"""
    if os.path.exists(DB_PRODUCTOS):
        try:
            with open(DB_PRODUCTOS, "r", encoding="utf-8") as f:
                productos = json.load(f)
                disponibles = []
                for p in productos:
                    # Normalizamos: si viene como 'cat', lo pasamos a 'categoria'
                    p['categoria'] = p.get('categoria', p.get('cat', 'Sin Categoría'))
                    disponibles.append(p)
                return disponibles
        except: return []
    return []

# --- PERSISTENCIA ---

def cargar_pedidos_hoy():
    if not os.path.exists("data"): os.makedirs("data")
    if os.path.exists(DB_PEDIDOS):
        try:
            with open(DB_PEDIDOS, "r", encoding="utf-8") as f:
                pedidos = json.load(f)
                hoy = datetime.now().strftime("%Y-%m-%d")
                return [p for p in pedidos if p.get('fecha') == hoy]
        except: return []
    return []

def guardar_pedidos(pedidos_actuales):
    todos = []
    if os.path.exists(DB_PEDIDOS):
        try:
            with open(DB_PEDIDOS, "r", encoding="utf-8") as f:
                todos = json.load(f)
        except: pass
    hoy = datetime.now().strftime("%Y-%m-%d")
    final = [p for p in todos if p.get('fecha') != hoy] + pedidos_actuales
    with open(DB_PEDIDOS, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=4, ensure_ascii=False)

# --- VISTAS ---

def mostrar_gestion_pedidos():
    st.markdown('<p class="main-header">📋 GESTIÓN DE PEDIDOS</p>', unsafe_allow_html=True)
    
    pedidos_hoy = cargar_pedidos_hoy()
    pedidos_activos = [p for p in pedidos_hoy if p.get('estado') != 'Pagado']
    
    if "vista" not in st.session_state:
        st.session_state.vista = "lista"
    if "pedido_seleccionado" not in st.session_state:
        st.session_state.pedido_seleccionado = None

    if st.session_state.vista == "lista":
        renderizar_lista(pedidos_activos, pedidos_hoy)
    elif st.session_state.vista == "formulario":
        renderizar_formulario(pedidos_hoy)
    elif st.session_state.vista == "pago":
        from views.pagos import mostrar_interfaz_pago
        mostrar_interfaz_pago()

def renderizar_lista(pedidos_activos, todos_los_pedidos_hoy):
    col_t, col_b = st.columns([3, 1.2])
    with col_t:
        st.markdown('<p class="categoria-header" style="margin-top:0;">Pedidos Activos</p>', unsafe_allow_html=True)
    with col_b:
        if st.button("➕ NUEVO PEDIDO", use_container_width=True):
            st.session_state.pedido_seleccionado = {
                "id": int(datetime.now().timestamp()),
                "cliente": "",
                "fecha": datetime.now().strftime("%Y-%m-%d"),
                "items": [],
                "total": 0,
                "estado": "Pendiente"
            }
            st.session_state.vista = "formulario"
            st.rerun()

    if not pedidos_activos:
        st.info("No hay pedidos pendientes o activos.")
        return

    for p in pedidos_activos:
        with st.container():
            st.markdown(f"""
                <div style="background: rgba(255, 255, 255, 0.05); border-left: 5px solid #E6B325; padding: 15px; border-radius: 8px; margin-bottom: 5px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-family: 'Bebas Neue'; font-size: 24px; color: #E6B325;">👤 {p['cliente']}</span>
                        <span style="font-family: 'Bebas Neue'; font-size: 26px; color: white;">TOTAL: ${p['total']:,}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"DETALLES / EDITAR", key=f"edit_{p['id']}", use_container_width=True):
                st.session_state.pedido_seleccionado = p
                st.session_state.vista = "formulario"
                st.rerun()

def renderizar_formulario(pedidos_hoy):
    p = st.session_state.pedido_seleccionado
    
    if st.button("⬅️ VOLVER A LA LISTA"):
        st.session_state.vista = "lista"
        st.rerun()

    st.markdown('<p class="categoria-header">Detalle de Comanda</p>', unsafe_allow_html=True)
    p['cliente'] = st.text_input("NOMBRE DEL CLIENTE O MESA", value=p.get('cliente', ""))

    # --- CARGA DINÁMICA DE PRODUCTOS ---
    productos_data = obtener_productos_disponibles()
    categorias_config = cargar_configuracion()
    
    # Filtrar categorías que tienen al menos un producto disponible
    productos_disponibles = [pr for pr in productos_data if pr.get('disponible', True)]
    cats_con_stock = sorted(list(set(pr['categoria'] for pr in productos_disponibles)))
    
    categorias = [c for c in categorias_config if c in cats_con_stock] + [c for c in cats_con_stock if c not in categorias_config]

    st.markdown('<p style="font-family:\'Bebas Neue\'; font-size:25px; color:#E6B325; margin-top:20px;">🛒 PRODUCTOS</p>', unsafe_allow_html=True)
    
    # Encabezados
    h = st.columns([0.5, 1.5, 2.5, 1, 0.8, 1, 0.5])
    for col, txt in zip(h, ["#", "CATEGORÍA", "PRODUCTO", "PRECIO", "CANT.", "SUBTOTAL", ""]):
        col.markdown(f'<p style="font-family:\'Bebas Neue\'; font-size:16px; color:#888;">{txt}</p>', unsafe_allow_html=True)

    items_actuales = p.get('items', [])
    total_acc = 0
    indices_a_eliminar = []

    for i, item in enumerate(items_actuales):
        c = st.columns([0.5, 1.5, 2.5, 1, 0.8, 1, 0.5])
        c[0].write(f"**{i+1}**")
        
        # 1. Selección de Categoría
        cat_actual_en_item = item.get('categoria', categorias[0] if categorias else "Sin Categoría")
        
        # Selector de Categoría con callback o detección de cambio
        cat_sel = c[1].selectbox(
            f"cat_{i}", 
            categorias, 
            index=categorias.index(cat_actual_en_item) if cat_actual_en_item in categorias else 0, 
            key=f"cat_sel_{i}", 
            label_visibility="collapsed"
        )

        # --- LÓGICA DE RESETEO ---
        # Si la categoría seleccionada es distinta a la que tenía el item, 
        # reseteamos el nombre para que obligue a elegir uno nuevo.
        if cat_sel != cat_actual_en_item:
            item['nombre'] = ""  # Forzamos blanco
            item['categoria'] = cat_sel
            st.rerun() # Recargamos para que el selector de productos se actualice
        
        # 2. Filtrar productos por la categoría seleccionada
        ops = [pr for pr in productos_disponibles if pr['categoria'] == cat_sel]
        nombres = [pr['nombre'] for pr in ops]
        
        # 3. Selector de Producto con opción en blanco si no hay selección válida
        # Añadimos un string vacío al inicio si el item no tiene nombre o no está en la lista
        opciones_con_blanco = ["Seleccione..."] + nombres
        
        # Determinar el índice actual
        if item.get('nombre') in nombres:
            idx_p = nombres.index(item['nombre']) + 1
        else:
            idx_p = 0 # Posición de "Seleccione..."

        p_sel = c[2].selectbox(
            f"p_{i}", 
            opciones_con_blanco, 
            index=idx_p, 
            key=f"p_sel_{i}", 
            label_visibility="collapsed"
        )

        # 4. Procesar selección de producto
        if p_sel != "Seleccione...":
            p_data = next((x for x in ops if x['nombre'] == p_sel), None)
            if p_data:
                precio = p_data['precio']
                item.update({'nombre': p_sel, 'precio': precio})
                
                c[3].write(f"${precio:,}")
                cant = c[4].number_input(f"n_{i}", min_value=1, value=int(item.get('cantidad', 1)), step=1, key=f"q_{i}", label_visibility="collapsed")
                item['cantidad'] = cant
                
                subtotal = precio * cant
                item['subtotal'] = subtotal
                c[5].markdown(f'<p style="color:#E6B325; font-weight:bold;">${subtotal:,}</p>', unsafe_allow_html=True)
                total_acc += subtotal
        else:
            # Si está en "Seleccione...", el subtotal es 0 o mantiene el anterior pero no suma
            c[3].write("$0")
            c[5].write("$0")
            item['subtotal'] = 0

        if c[6].button("🗑️", key=f"del_{i}"):
            indices_a_eliminar.append(i)
    if indices_a_eliminar:
        for index in sorted(indices_a_eliminar, reverse=True):
            items_actuales.pop(index)
        st.rerun()

    if st.button("➕ AGREGAR PRODUCTO", use_container_width=True):
        if categorias:
            def_cat = categorias[0]
            productos_def = [pr for pr in productos_disponibles if pr['categoria'] == def_cat]
            if productos_def:
                nueva_linea = {
                    "categoria": def_cat,
                    "nombre": productos_def[0]['nombre'],
                    "precio": productos_def[0]['precio'],
                    "cantidad": 1,
                    "subtotal": productos_def[0]['precio']
                }
                items_actuales.append(nueva_linea)
                st.rerun()

    st.markdown("---")
    st.markdown(f'<h2 style="text-align:right; font-family:\'Bebas Neue\'; color:#E6B325;">TOTAL: ${total_acc:,}</h2>', unsafe_allow_html=True)

    col_save, col_pay = st.columns(2)
    with col_save:
        if st.button("💾 GUARDAR COMANDA", use_container_width=True):
            p['items'], p['total'] = items_actuales, total_acc
            actualizar_lista_pedidos(pedidos_hoy, p)
            st.session_state.vista = "lista"
            st.rerun()
    with col_pay:
        if st.button("💳 PROCEDER AL PAGO", use_container_width=True, type="primary"):
            p['items'], p['total'] = items_actuales, total_acc
            actualizar_lista_pedidos(pedidos_hoy, p)
            st.session_state.vista = "pago"
            st.rerun()

def actualizar_lista_pedidos(pedidos_hoy, p_actual):
    ids = [x['id'] for x in pedidos_hoy]
    if p_actual['id'] in ids:
        pedidos_hoy[ids.index(p_actual['id'])] = p_actual
    else:
        pedidos_hoy.append(p_actual)
    guardar_pedidos(pedidos_hoy)