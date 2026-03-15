import streamlit as st
from views.contabilidad import registrar_transaccion
# Importamos las funciones necesarias para persistir los cambios
from views.gestion_pedidos import cargar_pedidos_hoy, guardar_pedidos

def mostrar_interfaz_pago():
    p = st.session_state.pedido_seleccionado
    if not p:
        st.session_state.vista = "lista"
        st.rerun()

    st.markdown('<p class="main-header">💰 PROCESAR PAGO</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="categoria-header">Cliente: {p["cliente"]} | Total: ${p["total"]:,}</p>', unsafe_allow_html=True)

    if st.button("⬅️ VOLVER AL PEDIDO"):
        if "items_pendientes" in st.session_state: del st.session_state.items_pendientes
        if "persona_actual" in st.session_state: del st.session_state.persona_actual
        st.session_state.vista = "formulario"
        st.rerun()

    modo_pago = st.radio("¿Cómo se realizará el pago?", ["Cuenta Completa", "Pago Dividido"], horizontal=True)

    if modo_pago == "Cuenta Completa":
        procesar_pago_seccion(p["total"], "pago_unico", p["items"], es_final=True)
    
    else:
        num_partes = st.number_input("¿En cuántas personas se divide la cuenta?", min_value=2, max_value=20, value=2)
        
        if "items_pendientes" not in st.session_state:
            st.session_state.items_pendientes = list(p["items"])
            st.session_state.persona_actual = 1

        persona = st.session_state.persona_actual
        items_restantes = st.session_state.items_pendientes

        st.info(f"👤 Procesando pago de: **Persona {persona}** de {num_partes}")

        if persona < num_partes:
            opciones = [f"{i['nombre']} (${i['subtotal']:,})" for i in items_restantes]
            seleccion = st.multiselect(f"Selecciona los productos de Persona {persona}:", opciones)
            
            monto_a_pagar = 0
            items_a_quitar = []
            for item_txt in seleccion:
                nombre_item = item_txt.split(' ($')[0]
                for i in items_restantes:
                    if i['nombre'] == nombre_item:
                        monto_a_pagar += i['subtotal']
                        items_a_quitar.append(i)
                        break
            
            if monto_a_pagar > 0:
                procesar_pago_seccion(monto_a_pagar, f"p{persona}", items_a_quitar, es_final=False)
            else:
                st.warning("Selecciona al menos un producto para continuar.")
        
        else:
            monto_final = sum(item['subtotal'] for item in items_restantes)
            st.warning(f"La Persona {persona} pagará el resto de la cuenta.")
            for i in items_restantes:
                st.text(f"• {i['nombre']} (${i['subtotal']:,})")
            
            procesar_pago_seccion(monto_final, f"p{persona}", items_restantes, es_final=True)

def procesar_pago_seccion(monto, key_suffix, items_pago, es_final):
    st.markdown(f"### Monto a cobrar: **${monto:,}**")
    metodo = st.selectbox(f"Método de pago", ["Efectivo", "Transferencia"], key=f"metodo_{key_suffix}")

    confirmado = False
    if metodo == "Efectivo":
        recibido = st.number_input(f"Cantidad recibida", min_value=monto, step=1000, key=f"rec_{key_suffix}")
        if recibido >= monto:
            st.success(f"Cambio: **${recibido - monto:,}**")
            if st.button("CONFIRMAR PAGO", key=f"btn_{key_suffix}", use_container_width=True):
                confirmado = True
    else:
        archivo = st.file_uploader("Adjuntar comprobante", type=['png', 'jpg'], key=f"file_{key_suffix}")
        if archivo and st.button("CONFIRMAR TRANSFERENCIA", key=f"btn_{key_suffix}", use_container_width=True):
            confirmado = True

    if confirmado:
        if es_final:
            finalizar_proceso_total()
        else:
            for item in items_pago:
                if item in st.session_state.items_pendientes:
                    st.session_state.items_pendientes.remove(item)
            
            st.session_state.persona_actual += 1
            st.toast(f"Pago de Persona {st.session_state.persona_actual - 1} registrado.")
            st.rerun()

def finalizar_proceso_total():
    p = st.session_state.pedido_seleccionado
    
    # --- 1. LOGICA DE ESTADO Y PERSISTENCIA ---
    p['estado'] = 'Pagado'
    
    # Cargamos los pedidos actuales del archivo para no sobreescribir otros datos
    pedidos_hoy = cargar_pedidos_hoy()
    
    # Buscamos el pedido actual en la lista por su ID y lo actualizamos
    ids = [x['id'] for x in pedidos_hoy]
    if p['id'] in ids:
        pedidos_hoy[ids.index(p['id'])] = p
    else:
        pedidos_hoy.append(p)
    
    # Guardamos la lista actualizada en pedidos.json
    guardar_pedidos(pedidos_hoy)

    # --- 2. LOGICA DE CONTABILIDAD ---
    detalles_prod = ", ".join([f"{i['cantidad']}x {i['nombre']}" for i in p['items']])
    registrar_transaccion(
        tipo="VENTA",
        concepto=f"Venta Cliente: {p['cliente']}",
        detalle=detalles_prod,
        cantidad=len(p['items']),
        total=p['total']
    )
    
    # --- 3. FINALIZACIÓN VISUAL ---
    st.balloons()
    st.success("¡Cuenta pagada y cerrada con éxito!")

    # Limpiar estados de sesión
    if "items_pendientes" in st.session_state: del st.session_state.items_pendientes
    if "persona_actual" in st.session_state: del st.session_state.persona_actual
    
    st.session_state.vista = "lista"
    st.rerun()
