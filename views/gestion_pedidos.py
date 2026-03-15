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
    st.markdown('<p style="font-family:\'Bebas Neue\'; font-size: 42px; color: #E6B325; text-align: center;">📋 GESTIÓN DE PEDIDOS</p>', unsafe_allow_html=True)
    
    # Cargar la data fresca del día
    pedidos_hoy = cargar_pedidos_hoy()
    
    # Separación lógica por estado
    pedidos_pendientes = [p for p in pedidos_hoy if p.get('estado') == 'Pendiente']
    pedidos_cerrados = [p for p in pedidos_hoy if p.get('estado') == 'Pagado']
    
    if "vista" not in st.session_state:
        st.session_state.vista = "lista"
    if "pedido_seleccionado" not in st.session_state:
        st.session_state.pedido_seleccionado = None

    if st.session_state.vista == "lista":
        # Implementación de pestañas para alternar vistas
        tab_pendientes, tab_cerrados = st.tabs(["⏳ PENDIENTES", "✅ CERRADOS"])
        
        with tab_pendientes:
            # Renderizado normal con capacidad de edición
            renderizar_lista(pedidos_pendientes, pedidos_hoy, editable=True)
            
        with tab_cerrados:
            # Renderizado solo lectura para pedidos pagados
            if not pedidos_cerrados:
                st.info("No hay pedidos cerrados hoy.")
            else:
                renderizar_lista(pedidos_cerrados, pedidos_hoy, editable=False)

    elif st.session_state.vista == "formulario":
        renderizar_formulario(pedidos_hoy)
        
    elif st.session_state.vista == "pago":
        from views.pagos import mostrar_interfaz_pago
        mostrar_interfaz_pago()


def renderizar_lista(pedidos_mostrar, todos_los_pedidos_hoy, editable=True):
    """
    Renderiza la lista de pedidos. 
    Si editable es False, oculta el botón de nuevo pedido y la edición.
    """
    col_t, col_b = st.columns([3, 1.2])
    
    with col_t:
        # Si es editable, son pendientes; si no, son cerrados
        titulo = "Pedidos Activos" if editable else "Pedidos Cerrados"
        st.markdown(f'<p class="categoria-header" style="margin-top:0;">{titulo}</p>', unsafe_allow_html=True)
    
    with col_b:
        if editable:
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

    if not pedidos_mostrar:
        msg = "No hay pedidos pendientes." if editable else "No hay pedidos cerrados hoy."
        st.info(msg)
        return

    for p in pedidos_mostrar:
        # Color: Dorado para pendientes, Verde para pagados
        color_status = "#E6B325" if editable else "#28a745"
        
        with st.container():
            st.markdown(f"""
                <div style="background: rgba(255, 255, 255, 0.05); border-left: 5px solid {color_status}; padding: 15px; border-radius: 8px; margin-bottom: 5px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-family: 'Bebas Neue'; font-size: 20px; color: {color_status};">👤 {p['cliente'].upper()}</span>
                        <span style="font-family: 'Bebas Neue'; font-size: 22px; color: white;">TOTAL: ${p['total']:,}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if editable:
                if st.button(f"DETALLES / EDITAR", key=f"edit_{p['id']}", use_container_width=True):
                    st.session_state.pedido_seleccionado = p
                    st.session_state.vista = "formulario"
                    st.rerun()
            else:
                with st.expander(f"👁️ VER DETALLE - ID: {p['id']}"):
                    for item in p.get('items', []):
                        st.write(f"• {item['cantidad']}x {item['nombre']} (${item['subtotal']:,})")

def renderizar_formulario(pedidos_hoy):
    p = st.session_state.pedido_seleccionado
    
    # Determinamos si el pedido está cerrado para bloquear la edición
    es_cerrado = p.get('estado') == 'Pagado'
    
    if st.button("⬅️ VOLVER A LA LISTA"):
        st.session_state.vista = "lista"
        st.rerun()

    titulo_seccion = "DETALLE DEL PEDIDO (SOLO LECTURA)" if es_cerrado else "DETALLE DEL PEDIDO"
    st.markdown(f'<p style="font-family:\'Bebas Neue\'; font-size: 28px; color: #E6B325; border-bottom: 2px solid rgba(230,179,37,0.3);">{titulo_seccion}</p>', unsafe_allow_html=True)
    
    # Bloqueamos el input del nombre si está cerrado
    p['cliente'] = st.text_input("NOMBRE DEL CLIENTE O MESA", value=p.get('cliente', ""), disabled=es_cerrado)

    # --- CARGA DINÁMICA DE PRODUCTOS ---
    productos_data = obtener_productos_disponibles()
    categorias_config = cargar_configuracion()
    
    productos_disponibles = [pr for pr in productos_data if pr.get('disponible', True)]
    cats_con_stock = sorted(list(set(pr['categoria'] for pr in productos_disponibles)))
    categorias = [c for c in categorias_config if c in cats_con_stock] + [c for c in cats_con_stock if c not in categorias_config]

    st.markdown('<p style="font-family:\'Bebas Neue\'; font-size: 24px; color: #E6B325; margin-top: 20px;">🛒 PRODUCTOS</p>', unsafe_allow_html=True)

    # Encabezados
    columnas_layout = [0.5, 1.5, 2.5, 1, 0.8, 1, 0.5]
    h = st.columns(columnas_layout)
    for col, txt in zip(h, ["#", "CATEGORÍA", "PRODUCTO", "PRECIO", "CANT.", "SUBTOTAL", ""]):
        col.markdown(f'<p style="font-family:\'Bebas Neue\'; font-size: 13px; color: #888;">{txt}</p>', unsafe_allow_html=True)
    
    items_actuales = p.get('items', [])
    total_acc = 0
    indices_a_eliminar = []

    for i, item in enumerate(items_actuales):
        c = st.columns(columnas_layout)
        c[0].write(f"**{i+1}**")
        
        # 1. Selección de Categoría (Deshabilitado si es_cerrado)
        cat_actual_en_item = item.get('categoria', categorias[0] if categorias else "Sin Categoría")
        cat_sel = c[1].selectbox(
            f"cat_{i}", 
            categorias, 
            index=categorias.index(cat_actual_en_item) if cat_actual_en_item in categorias else 0, 
            key=f"cat_sel_{i}", 
            label_visibility="collapsed",
            disabled=es_cerrado
        )

        if not es_cerrado and cat_sel != cat_actual_en_item:
            item['nombre'] = ""
            item['categoria'] = cat_sel
            st.rerun()
        
        # 2. Productos y 3. Selector (Deshabilitado si es_cerrado)
        ops = [pr for pr in productos_disponibles if pr['categoria'] == cat_sel]
        nombres = [pr['nombre'] for pr in ops]
        opciones_con_blanco = ["Seleccione..."] + nombres
        
        idx_p = nombres.index(item['nombre']) + 1 if item.get('nombre') in nombres else 0

        p_sel = c[2].selectbox(
            f"p_{i}", 
            opciones_con_blanco, 
            index=idx_p, 
            key=f"p_sel_{i}", 
            label_visibility="collapsed",
            disabled=es_cerrado
        )

        # 4. Procesar selección
        if p_sel != "Seleccione...":
            p_data = next((x for x in ops if x['nombre'] == p_sel), None)
            if p_data:
                precio = p_data['precio']
                if not es_cerrado:
                    item.update({'nombre': p_sel, 'precio': precio})
                
                c[3].write(f"${precio:,}")
                # Cantidad deshabilitada si es_cerrado
                cant = c[4].number_input(f"n_{i}", min_value=1, value=int(item.get('cantidad', 1)), step=1, key=f"q_{i}", label_visibility="collapsed", disabled=es_cerrado)
                item['cantidad'] = cant
                
                subtotal = precio * cant
                item['subtotal'] = subtotal
                c[5].markdown(f'<p style="color:#E6B325; font-weight:bold; font-size: 18px; padding-top:10px;">${subtotal:,}</p>', unsafe_allow_html=True)
                total_acc += subtotal
        else:
            c[3].write("$0")
            c[5].write("$0")
            item['subtotal'] = 0

        # Botón eliminar solo visible si no está cerrado
        if not es_cerrado:
            if c[6].button("🗑️", key=f"del_{i}"):
                indices_a_eliminar.append(i)

    if indices_a_eliminar:
        for index in sorted(indices_a_eliminar, reverse=True):
            items_actuales.pop(index)
        st.rerun()

    # Ocultar botón de agregar si está cerrado
    if not es_cerrado:
        if st.button("➕ AGREGAR PRODUCTO", use_container_width=True):
            if categorias:
                def_cat = categorias[0]
                productos_def = [pr for pr in productos_disponibles if pr['categoria'] == def_cat]
                if productos_def:
                    items_actuales.append({
                        "categoria": def_cat, "nombre": productos_def[0]['nombre'],
                        "precio": productos_def[0]['precio'], "cantidad": 1, "subtotal": productos_def[0]['precio']
                    })
                    st.rerun()

    st.markdown("---")
    st.markdown(f'<h2 style="text-align:right; font-family:\'Bebas Neue\'; color:#E6B325; font-size: 32px;">TOTAL: ${total_acc:,}</h2>', unsafe_allow_html=True)

    # Ocultar botones de Guardar y Pagar si el pedido ya fue pagado
    if not es_cerrado:
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
    else:
        st.success("✅ Este pedido ha sido completado y no puede ser modificado.")
def actualizar_lista_pedidos(pedidos_hoy, p_actual):
    ids = [x['id'] for x in pedidos_hoy]
    if p_actual['id'] in ids:
        pedidos_hoy[ids.index(p_actual['id'])] = p_actual
    else:
        pedidos_hoy.append(p_actual)
    guardar_pedidos(pedidos_hoy)
