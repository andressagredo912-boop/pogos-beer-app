import streamlit as st
import pandas as pd
import os
import json
import shutil
from datetime import datetime
from fpdf import FPDF

DB_CONTABILIDAD = os.path.join("data", "contabilidad.json")
DB_PEDIDOS = os.path.join("data", "pedidos.json")

# --- FUNCIONES DE CARGA Y GUARDADO ---
def cargar_contabilidad():
    if os.path.exists(DB_CONTABILIDAD):
        with open(DB_CONTABILIDAD, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"fecha_apertura": datetime.now().strftime("%Y-%m-%d %H:%M"), "registros": []}

def guardar_contabilidad(datos):
    if not os.path.exists("data"): os.makedirs("data")
    with open(DB_CONTABILIDAD, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

def ejecutar_cierre_diario(datos, df_registros):
    """Genera el PDF en memoria y devuelve un objeto de bytes puro."""
    pdf = FPDF()
    pdf.add_page()
    
    # --- 1. INSERTAR LOGO CENTRADO ---
    ruta_logo = os.path.join("assets", "logo2.png")
    ancho_logo = 33 # El ancho que definiste en mm
    
    if os.path.exists(ruta_logo):
        # Calculamos el centro: (Ancho página 210mm - Ancho logo 33mm) / 2 = 88.5mm
        x_centrado = (210 - ancho_logo) / 2
        
        # image(ruta, x, y, w)
        pdf.image(ruta_logo, x=x_centrado, y=8, w=ancho_logo) 
        pdf.set_y(45) # Baja el cursor para que el título no quede encima del logo
    else:
        # Si no hay logo, dejamos un margen superior normal
        pdf.set_y(20)

    # --- 2. TÍTULOS ---
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "REPORTE CONTABLE - POGO'S BEER", ln=True, align='C')
    
    pdf.set_font("Arial", "", 10)
    fecha_cierre = datetime.now().strftime('%Y-%m-%d %H:%M')
    pdf.cell(190, 10, f"Apertura: {datos['fecha_apertura']} | Cierre: {fecha_cierre}", ln=True, align='C')
    pdf.ln(5)

    # --- 3. TABLA DE MOVIMIENTOS ---
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(200, 200, 200)
    
    pdf.cell(20, 10, "HORA", 1, 0, 'C', True)
    pdf.cell(40, 10, "CONCEPTO", 1, 0, 'C', True)
    pdf.cell(60, 10, "DETALLE", 1, 0, 'C', True)
    pdf.cell(35, 10, "INGRESO", 1, 0, 'C', True)
    pdf.cell(35, 10, "GASTO", 1, 1, 'C', True)

    pdf.set_font("Arial", "", 8)
    for _, fila in df_registros.iterrows():
        y_start = pdf.get_y()
        
        pdf.cell(20, 10, str(fila['hora']), 1)
        pdf.cell(40, 10, str(fila['concepto'])[:20], 1)
        
        x_detalle = pdf.get_x()
        pdf.multi_cell(60, 5, str(fila['detalle']), 1) 
        y_final = pdf.get_y()
        
        pdf.set_xy(x_detalle + 60, y_start)
        
        ingreso = f"${fila['INGRESO']:,}" if fila['INGRESO'] > 0 else "-"
        gasto = f"${fila['GASTO']:,}" if fila['GASTO'] > 0 else "-"
        
        pdf.cell(35, 10, ingreso, 1, 0, 'R')
        pdf.cell(35, 10, gasto, 1, 1, 'R')
        
        if pdf.get_y() < y_final:
            pdf.set_y(y_final)

    # --- 4. TOTALES ---
    pdf.ln(5)
    total_ingresos = df_registros['INGRESO'].sum()
    total_gastos = df_registros['GASTO'].sum()
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(100, 10, "TOTAL INGRESOS:", 0)
    pdf.cell(90, 10, f"${total_ingresos:,}", ln=True, align='R')
    pdf.cell(100, 10, "TOTAL GASTOS:", 0)
    pdf.cell(90, 10, f"${total_gastos:,}", ln=True, align='R')
    
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(100, 10, "SALDO NETO EN CAJA:", 1, 0, 'L', True)
    pdf.cell(90, 10, f"${total_ingresos - total_gastos:,}", 1, 1, 'R', True)

    # Convertir a bytes para Streamlit
    return bytes(pdf.output(dest='S'))

def mostrar_contabilidad():
    st.markdown('<p class="main-header">CONTABILIDAD POGOS BEER</p>', unsafe_allow_html=True)
    
    datos = cargar_contabilidad()
    st.markdown(f"**Fecha de Apertura de Jornada:** {datos['fecha_apertura']}")
    
    if not datos["registros"]:
        st.info("No hay movimientos registrados en esta jornada.")
    else:
        df = pd.DataFrame(datos["registros"])
        
        # Cálculos de columnas
        df['INGRESO'] = df.apply(lambda x: x['total'] if x['tipo'] == 'VENTA' else 0, axis=1)
        df['GASTO'] = df.apply(lambda x: x['total'] if x['tipo'] == 'GASTO' else 0, axis=1)

        # Métricas principales
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Ventas (Ingresos)", f"${df['INGRESO'].sum():,}")
        with col2:
            st.metric("Total Gastos", f"${df['GASTO'].sum():,}")

        st.markdown("### 📝 Historial Detallado")
        
        st.dataframe(
            df[['hora', 'concepto', 'detalle', 'INGRESO', 'GASTO']],
            column_config={
                "hora": st.column_config.TextColumn("Hora", width="small"),
                "concepto": st.column_config.TextColumn("Concepto", width="medium"),
                "detalle": st.column_config.TextColumn("Detalle", width="large"),
                "INGRESO": st.column_config.NumberColumn("Ingreso", format="$%d"),
                "GASTO": st.column_config.NumberColumn("Gasto", format="$%d"),
            },
            hide_index=True,
            use_container_width=True
        )

        st.divider()
        
        # --- SECCIÓN DE CIERRE Y MANTENIMIENTO ---
        st.markdown("### 📂 Gestión de Jornada")
        col_cierre, col_reset = st.columns(2)

        with col_cierre:
            try:
                # Generar bytes del PDF
                pdf_bytes = ejecutar_cierre_diario(datos, df)
                nombre_archivo = f"Cierre_Diario_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.pdf"

                # Botón de descarga: Abre el explorador de archivos del sistema
                st.download_button(
                    label="📄 GENERAR Y GUARDAR REPORTE",
                    data=pdf_bytes,
                    file_name=nombre_archivo,
                    mime="application/pdf",
                    use_container_width=True,
                    help="Haz clic para descargar el reporte de hoy",
                    on_click=lambda: st.toast("¡Archivo preparado!")
                )
            except Exception as e:
                st.error(f"Error al generar el PDF: {e}")

        with col_reset:
            st.warning("⚠️ Acción irreversible")
            
            # Inicializamos el estado de confirmación si no existe
            if 'confirmar_reset' not in st.session_state:
                st.session_state.confirmar_reset = False

            if not st.session_state.confirmar_reset:
                # Primer botón: Activa el estado de confirmación
                if st.button("🔴 RESETEAR JORNADA", use_container_width=True):
                    st.session_state.confirmar_reset = True
                    st.rerun()
            else:
                # Interfaz de confirmación
                st.error("¿Estás seguro? Se borrarán los datos actuales.")
                col_si, col_no = st.columns(2)
                
                with col_si:
                    if st.button("SÍ, BORRAR TODO", type="primary", use_container_width=True):
                        st.session_state.confirmar_reset = False # Limpiamos el estado
                        resetear_bases_de_datos()
                
                with col_no:
                    if st.button("CANCELAR", use_container_width=True):
                        st.session_state.confirmar_reset = False
                        st.rerun()

def registrar_transaccion(tipo, concepto, detalle, cantidad, total):
    datos = cargar_contabilidad()
    nuevo = {
        "hora": datetime.now().strftime("%H:%M:%S"),
        "tipo": tipo,
        "concepto": concepto,
        "detalle": detalle,
        "cantidad": cantidad,
        "total": total
    }
    datos["registros"].append(nuevo)
    guardar_contabilidad(datos)
    
def resetear_bases_de_datos():
    fecha_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    if not os.path.exists("backups"): os.makedirs("backups")
    
    if os.path.exists(DB_PEDIDOS):
        shutil.copy(DB_PEDIDOS, f"backups/pedidos_antes_reset_{fecha_str}.json")
        os.remove(DB_PEDIDOS)
    
    if os.path.exists(DB_CONTABILIDAD):
        shutil.copy(DB_CONTABILIDAD, f"backups/contab_antes_reset_{fecha_str}.json")
        os.remove(DB_CONTABILIDAD)
    
    st.success("Bases de datos reseteadas. Listos para nueva jornada.")
    st.rerun()
