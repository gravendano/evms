import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Pronóstico EVM Monte Carlo", layout="wide")

st.title("Simulación de Pronóstico de Valor Ganado 📈")

# 1. Explicación teórica
with st.expander("📚 1. Definiciones Clave y Fórmulas EVM (Método Ricardo Vargas)", expanded=False):
    st.markdown("""
    * **BAC (Presupuesto a la Conclusión):** Presupuesto total original del proyecto.
    * **BCWS (Costo Presupuestado del Trabajo Programado):** Valor planificado ($PV$).
    * **BCWP (Costo Presupuestado del Trabajo Realizado):** Valor ganado ($EV$).
    * **ACWP (Costo Real del Trabajo Realizado):** Costo real incurrido ($AC$).
    * **CPI (Índice de Desempeño del Costo):** $CPI = \\frac{BCWP}{ACWP}$
    * **SPI (Índice de Desempeño del Cronograma):** $SPI = \\frac{BCWP}{BCWS}$
    
    **Tres Puntos para Estimación de Costo a la Finalización (EAC):**
    1. **EAC Optimista:** $EAC_1 = ACWP + (BAC - BCWP)$
    2. **EAC Realista (CPI):** $EAC_{CPI} = \\frac{BAC}{CPI}$
    3. **EAC Pesimista (SCI):** $EAC_{SCI} = ACWP + \\frac{BAC - BCWP}{CPI \\times SPI}$
    """)

# 2. Datos Iniciales
initial_data = [
    {"Tarea": "Diseñar requerimientos", "BAC": 4000.0, "BCWP": 4000.0, "ACWP": 5000.0, "SPI": 1.0},
    {"Tarea": "Preparar datos", "BAC": 4000.0, "BCWP": 2000.0, "ACWP": 5000.0, "SPI": 0.67},
    {"Tarea": "Obtener herramientas", "BAC": 6000.0, "BCWP": 1500.0, "ACWP": 3000.0, "SPI": 0.25},
    {"Tarea": "Diseñar solución", "BAC": 12000.0, "BCWP": 12000.0, "ACWP": 10000.0, "SPI": 1.0},
    {"Tarea": "Comprar equipos de prueba", "BAC": 15000.0, "BCWP": 15000.0, "ACWP": 13500.0, "SPI": 1.0},
    {"Tarea": "Construir ambiente de pruebas", "BAC": 6000.0, "BCWP": 600.0, "ACWP": 900.0, "SPI": 0.50},
    {"Tarea": "Probar", "BAC": 3000.0, "BCWP": 0.0, "ACWP": 0.0, "SPI": 1.0}
]

# 3. Editor de Datos Interactivo
st.subheader("2. Simulación Interactiva del Proyecto")
st.caption("Modifica **BCWP** y **ACWP** directamente en la tabla:")

df_input = pd.DataFrame(initial_data)

edited_df = st.data_editor(
    df_input,
    column_config={
        "Tarea": st.column_config.TextColumn("Tarea", disabled=True),
        "BAC": st.column_config.NumberColumn("Presupuesto (BAC)", format="$%.2f", disabled=True),
        "BCWP": st.column_config.NumberColumn("Valor Ganado (BCWP)", format="$%.2f", min_value=0.0),
        "ACWP": st.column_config.NumberColumn("Costo Real (ACWP)", format="$%.2f", min_value=0.0),
        "SPI": st.column_config.NumberColumn("SPI", format="%.2f", disabled=True),
    },
    use_container_width=True,
    num_rows="fixed"
)

# 4. Cálculo de Totales del Proyecto
tot_bac = edited_df['BAC'].sum()
tot_bcwp = edited_df['BCWP'].sum()
tot_acwp = edited_df['ACWP'].sum()

tot_bcws = (edited_df['BCWP'] / edited_df['SPI'].replace(0, 1)).sum()
tot_spi = tot_bcwp / tot_bcws if tot_bcws > 0 else 0.0
tot_cpi = tot_bcwp / tot_acwp if tot_acwp > 0 else 0.0

tot_eac_opt = tot_acwp + (tot_bac - tot_bcwp)
tot_eac_real = tot_bac / tot_cpi if tot_cpi > 0 else tot_eac_opt
tot_sci = tot_cpi * tot_spi
tot_eac_pess = (tot_acwp + (tot_bac - tot_bcwp) / tot_sci) if tot_sci > 0 else (tot_eac_real if tot_cpi > 0 else tot_eac_opt)

# Métricas Principales
st.markdown("**Resumen de Totales e Indicadores**")
m1, m2, m3, m4 = st.columns(4)
m1.metric("BAC Total", f"${tot_bac:,.2f}")
m2.metric("BCWP Total", f"${tot_bcwp:,.2f}")
m3.metric("ACWP Total", f"${tot_acwp:,.2f}")
m4.metric("CPI Total", f"{tot_cpi:.2f}")

e1, e2, e3 = st.columns(3)
e1.metric("EAC Optimista", f"${tot_eac_opt:,.2f}")
e2.metric("EAC Realista", f"${tot_eac_real:,.2f}")
e3.metric("EAC Pesimista", f"${tot_eac_pess:,.2f}")

st.divider()

# 5. Monte Carlo
st.subheader("3. Ejecución de Simulación Monte Carlo")
iterations = st.slider("Número de Iteraciones", min_value=10000, max_value=100000, value=50000, step=10000)

if st.button("🚀 Correr Simulación Monte Carlo", type="primary"):
    if not (tot_eac_opt <= tot_eac_real <= tot_eac_pess) or (tot_eac_opt == tot_eac_pess):
        st.error("Error: Los valores de EAC no son válidos para una distribución triangular (Optimista <= Realista <= Pesimista).")
    else:
        # Generar distribución triangular
        results = np.random.triangular(left=tot_eac_opt, mode=tot_eac_real, right=tot_eac_pess, size=iterations)
        
        mean = np.mean(results)
        p05 = np.percentile(results, 5)
        p95 = np.percentile(results, 95)
        
        c_res, c_chart = st.columns([1, 2])
        
        with c_res:
            st.markdown("### Resultados del Pronóstico")
            st.info(f"**Costo Final Promedio (Media):**\n### ${mean:,.2f}")
            st.success(f"**Intervalo de Confianza del 90%:**\n### ${p05:,.2f} - ${p95:,.2f}")
            st.caption("Existe un 90% de probabilidad de que el costo final se mantenga dentro de este rango.")
            
        with c_chart:
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=results,
                nbinsx=40,
                name="EAC",
                marker_color='rgba(66, 165, 245, 0.7)',
                marker_line=dict(color='rgba(13, 71, 161, 1)', width=1)
            ))
            
            fig.add_vline(x=mean, line_width=3, line_dash="dash", line_color="red",
                          annotation_text=f"Media: ${mean:,.2f}", annotation_position="top left")
            fig.add_vline(x=p05, line_width=2, line_dash="dot", line_color="green",
                          annotation_text=f"P5: ${p05:,.2f}", annotation_position="bottom left")
            fig.add_vline(x=p95, line_width=2, line_dash="dot", line_color="orange",
                          annotation_text=f"P95: ${p95:,.2f}", annotation_position="bottom right")
            
            fig.update_layout(
                title="Histograma de Resultados de la Simulación",
                xaxis_title="Costo Final Estimado (EAC)",
                yaxis_title="Frecuencia",
                template="plotly_white",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)