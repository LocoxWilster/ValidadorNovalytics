import streamlit as st
import random
import math
import os
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Novalytics - Validador de Prompts", page_icon="🎯", layout="centered")

ARCHIVO_LOGS = "registro_validaciones.csv"

# Función para guardar el historial de auditorías
def guardar_log(prompt_name, analista, total_llamadas, muestra_max, revisadas, errores, resultado):
    nuevo_registro = {
        "Fecha e Hora": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "Nombre del Prompt": [prompt_name],
        "Analista": [analista],
        "Tamaño del Lote": [total_llamadas],
        "Muestra Máxima": [muestra_max],
        "Llamadas Auditadas": [revisadas],
        "Errores Detectados": [errores],
        "Tasa de Error (%)": [round((errores / revisadas) * 100, 2) if revisadas > 0 else 0],
        "Resultado Final": [resultado]
    }
    df_nuevo = pd.DataFrame(nuevo_registro)
    if os.path.exists(ARCHIVO_LOGS):
        df_existente = pd.read_csv(ARCHIVO_LOGS)
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
    else:
        df_final = df_nuevo
    df_final.to_csv(ARCHIVO_LOGS, index=False)

# Inicializar las variables de estado de la aplicación web
if 'validación_activa' not in st.session_state:
    st.session_state.validación_activa = False
    st.session_state.llamadas_disponibles = []
    st.session_state.errores_encontrados = 0
    st.session_state.auditorias_realizadas = 0
    st.session_state.llamada_actual = None
    st.session_state.muestra_maxima = 0
    st.session_state.max_errores_permitidos = 0
    st.session_state.datos_iniciales = {}

st.title("🎯 Novalytics - Validador de Prompts")
st.subheader("Muestreo de Aceptación Estadístico para Control de Calidad")
st.write("---")

# PANTALLA 1: Formulario Inicial de Configuración
if not st.session_state.validación_activa:
    st.write("### 📝 Configuración de la Auditoría")
    prompt_name = st.text_input("Nombre del Prompt a validar", placeholder="ej: Sabor Producto V1")
    analista = st.text_input("Nombre del Analista de Calidad", placeholder="ej: Juan Pérez")
    total_llamadas = st.number_input("Tamaño del lote (Total de llamadas procesadas por la IA)", min_value=1, step=1, value=120)
    
    if st.button("🚀 Iniciar Proceso de Validación", use_container_width=True):
        if not prompt_name.strip():
            st.error("⚠️ El nombre del prompt es obligatorio.")
        elif not analista.strip():
            st.error("⚠️ Por favor, ingrese el nombre del analista.")
        else:
            # Cálculos Estadísticos (95% confianza, 5% error)
            Z = 1.96
            p = 0.05
            e = 0.05
            num = (Z**2) * p * (1-p) * total_llamadas
            den = (e**2) * (total_llamadas - 1) + (Z**2) * p * (1-p)
            muestra_maxima = math.ceil(num / den)
            max_errores_permitidos = max(1, math.floor(muestra_maxima * 0.10))
            
            # Crear y mezclar el lote de llamadas al azar
            llamadas = list(range(1, total_llamadas + 1))
            random.shuffle(llamadas)
            
            # Guardar todo en el estado de la sesión
            st.session_state.muestra_maxima = muestra_maxima
            st.session_state.max_errores_permitidos = max_errores_permitidos
            st.session_state.llamadas_disponibles = llamadas
            st.session_state.errores_encontrados = 0
            st.session_state.auditorias_realizadas = 1
            st.session_state.llamada_actual = llamadas.pop()
            st.session_state.datos_iniciales = {
                "prompt": prompt_name,
                "analista": analista,
                "lote": total_llamadas
            }
            st.session_state.validación_activa = True
            st.rerun()

# PANTALLA 2: Interfaz Interactiva de Auditoría
else:
    info = st.session_state.datos_iniciales
    
    # Barra de información superior
    st.info(f"📋 **Prompt:** {info['prompt']} | 👤 **Analista:** {info['analista']} | 📦 **Lote Total:** {info['lote']} llamadas")
    
    # Panel de métricas estadísticas en tiempo real
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Progreso de Muestra", f"{st.session_state.auditorias_realizadas} / {st.session_state.muestra_maxima}")
    with col2:
        st.metric("Errores Detectados", f"{st.session_state.errores_encontrados} / {st.session_state.max_errores_permitidos + 1}")
    with col3:
        st.metric("Margen Tolerable", f"Máx {st.session_state.max_errores_permitidos} errores")
        
    st.write("---")
    
    # Bloque de acción central para el analista
    st.write("### 🎧 Instrucción para el Auditor:")
    st.success(f"### Por favor, escucha y valida la llamada con **ID: {st.session_state.llamada_actual}**")
    st.write("¿La clasificación hecha por la Inteligencia Artificial fue correcta?")
    
    btn_col1, btn_col2 = st.columns(2)
    
    # Caso 1: El analista dice que la IA acertó (SÍ)
    if btn_col1.button("✅ SÍ, es Correcto", use_container_width=True, type="primary"):
        evaluar_paso(error=False)
        
    # Caso 2: El analista dice que la IA falló (NO)
    if btn_col2.button("❌ NO, es Incorrecto (Error)", use_container_width=True):
        evaluar_paso(error=True)

    if st.button("⏹️ Cancelar y salir", type="secondary"):
        st.session_state.validación_activa = False
        st.rerun()

# Función interna para evaluar cada clic y aplicar los criterios estadísticos de parada
def evaluar_paso(error):
    info = st.session_state.datos_iniciales
    
    if error:
        st.session_state.errores_encontrados += 1
        
    # 1. Comprobar criterio de PARADA TEMPRANA POR RECHAZO
    if st.session_state.errores_encontrados > st.session_state.max_errores_permitidos:
        guardar_log(info['prompt'], info['analista'], info['lote'], st.session_state.muestra_maxima, st.session_state.auditorias_realizadas, st.session_state.errores_encontrados, "RECHAZADO")
        st.session_state.validación_activa = False
        st.error(f"🚨 **PROMPT RECHAZADO**: Se detectaron {st.session_state.errores_encontrados} errores. El prompt no cumple con la confianza estadística requerida.")
        st.toast("Log guardado en el archivo CSV")
        return

    # 2. Comprobar criterio de PARADA TEMPRANA POR ÉXITO (50% de la muestra sin fallas)
    mitad_muestra = max(5, math.ceil(st.session_state.muestra_maxima * 0.5))
    if st.session_state.auditorias_realizadas >= mitad_muestra and st.session_state.errores_encontrados == 0:
        guardar_log(info['prompt'], info['analista'], info['lote'], st.session_state.muestra_maxima, st.session_state.auditorias_realizadas, st.session_state.errores_encontrados, "APROBADO TEMPRANAMENTE")
        st.session_state.validación_activa = False
        st.success(f"🎉 **PROMPT APROBADO TEMPRANAMENTE**: Excelente nivel de acierto. Tras {st.session_state.auditorias_realizadas} revisiones perfectas al azar, el prompt es altamente confiable.")
        st.toast("Log guardado en el archivo CSV")
        return

    # 3. Comprobar si completamos la muestra máxima de llamadas
    if st.session_state.auditorias_realizadas >= st.session_state.muestra_maxima or not st.session_state.llamadas_disponibles:
        guardar_log(info['prompt'], info['analista'], info['lote'], st.session_state.muestra_maxima, st.session_state.auditorias_realizadas, st.session_state.errores_encontrados, "APROBADO")
        st.session_state.validación_activa = False
        st.success(f"🏆 **PROMPT APROBADO**: Se completaron las {st.session_state.auditorias_realizadas} auditorías reglamentarias tolerando solo {st.session_state.errores_encontrados} errores.")
        st.toast("Log guardado en el archivo CSV")
        return

    # Avanzar a la siguiente llamada aleatoria si no se cumplió ninguna condición de parada
    st.session_state.auditorias_realizadas += 1
    st.session_state.llamada_actual = st.session_state.llamadas_disponibles.pop()
    st.rerun()

# SECCIÓN DE LOGS HISTÓRICOS (Se despliega abajo en la interfaz)
st.write("---")
st.write("### 📊 Historial de Validaciones Registradas")
if os.path.exists(ARCHIVO_LOGS):
    df_logs = pd.read_csv(ARCHIVO_LOGS)
    st.dataframe(df_logs.iloc[::-1], use_container_width=True) # Muestra los registros más nuevos arriba
    
    # Botón nativo para que el analista descargue el reporte directo a Excel/CSV desde la web
    csv_data = df_logs.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Reporte Histórico Completo (CSV)",
        data=csv_data,
        file_name=f"reporte_calidad_novalytics_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )
else:
    st.info("Aún no hay validaciones registradas en esta sesión. Los logs aparecerán aquí cuando finalice la primera auditoría.")
