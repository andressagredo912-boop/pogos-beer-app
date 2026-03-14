import streamlit as st
# Importamos la función necesaria de contabilidad
from views.contabilidad import registrar_transaccion 

def vista_compras():
    st.title("Registro de Compras (Gastos)")
    
    with st.form("form_gastos"):
        concepto = st.text_input("Concepto (Ej: Reposición Pola, Hielo)")
        detalle = st.text_area("Detalles")
        valor = st.number_input("Valor Total", min_value=0)
        cantidad = st.number_input("Cantidad", min_value=1)
        
        if st.form_submit_button("Registrar Gasto"):
            if concepto and valor > 0:
                # Se llama a la función para que impacte en contabilidad.json
                registrar_transaccion(
                    tipo='GASTO', 
                    concepto=concepto, 
                    detalle=detalle, 
                    cantidad=cantidad, 
                    total=valor
                )
                st.success(f"Gasto '{concepto}' registrado y enviado a contabilidad.")
            else:
                st.error("Por favor, completa el concepto y el valor.")