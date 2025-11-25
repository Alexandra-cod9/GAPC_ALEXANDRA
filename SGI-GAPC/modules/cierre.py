import streamlit as st
import pymysql
from datetime import datetime
import pandas as pd

def mostrar_modulo_cierre():
    """Módulo especializado de cierre - Proceso de liquidación del ciclo"""
    
    # Header del módulo con botón de volver
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# 📊 Módulo de Cierre")
    with col2:
        if st.button("⬅️ Volver al Dashboard", use_container_width=True):
            st.session_state.modulo_actual = 'dashboard'
            st.rerun()
    
    st.markdown("---")
    
    # Menú de opciones
    opcion = st.radio(
        "Selecciona una acción:",
        ["🔄 Nuevo Cierre", "📋 Historial de Cierres"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if opcion == "🔄 Nuevo Cierre":
        mostrar_nuevo_cierre()
    elif opcion == "📋 Historial de Cierres":
        mostrar_historial_cierres()

def mostrar_nuevo_cierre():
    """Formulario para realizar un nuevo cierre de ciclo"""
    st.subheader("🔄 Nuevo Cierre de Ciclo")
    
    st.info("""
    **💡 Información:**
    El cierre es el proceso donde se genera el acta final del ciclo y se reparten las utilidades 
    según el método elegido por el grupo (proporcional o equitativo).
    """)
    
    # Paso 1: Selección del período
    st.markdown("### 📅 Paso 1: Selecciona el Período a Cerrar")
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input(
            "Fecha de inicio del ciclo:",
            value=datetime(datetime.now().year, 1, 1),
            help="Fecha inicial del período a cerrar"
        )
    
    with col2:
        fecha_fin = st.date_input(
            "Fecha de fin del ciclo:",
            value=datetime.now(),
            help="Fecha final del período a cerrar"
        )
    
    if fecha_inicio >= fecha_fin:
        st.error("❌ La fecha de inicio debe ser anterior a la fecha de fin")
        return
    
    st.info(f"**Periodo seleccionado:** {fecha_inicio.strftime('%d/%m/%Y')} a {fecha_fin.strftime('%d/%m/%Y')}")
    
    # Botón para calcular cierre
    if st.button("🧮 Calcular Cierre", type="primary", use_container_width=True):
        calcular_cierre_periodo(fecha_inicio, fecha_fin)

def calcular_cierre_periodo(fecha_inicio, fecha_fin):
    """Calcula el cierre para el período seleccionado"""
    
    try:
        conexion = obtener_conexion()
        if not conexion:
            return
            
        with conexion.cursor() as cursor:
            
            id_grupo = st.session_state.get('usuario', {}).get('id_grupo', 1)
            
            # Obtener información del grupo
            cursor.execute("""
                SELECT nombre_grupo, metodo_reparto_utilidades, tasa_interes_mensual
                FROM grupo WHERE id_grupo = %s
            """, (id_grupo,))
            
            grupo_info = cursor.fetchone()
            
            if not grupo_info:
                st.error("❌ No se encontró información del grupo")
                return
            
            metodo_reparto = grupo_info['metodo_reparto_utilidades']
            nombre_grupo = grupo_info['nombre_grupo']
            
            st.success(f"**Grupo:** {nombre_grupo} | **Método de reparto:** {metodo_reparto}")
            
            # Paso 2: Obtener datos base para el cálculo
            st.markdown("---")
            st.markdown("### 📊 Paso 2: Datos Base del Período")
            
            # Obtener saldo final de ahorros por socia - CORREGIDO
            cursor.execute("""
                SELECT 
                    m.id_miembro,
                    m.nombre,
                    COALESCE(SUM(CASE 
                        WHEN a.tipo = 'Ahorro' THEN a.monto 
                        ELSE 0 
                    END), 0) as ahorro_total,
                    COALESCE(SUM(CASE 
                        WHEN a.tipo = 'PagoMulta' THEN a.monto 
                        ELSE 0 
                    END), 0) as multas_pagadas
                FROM miembrogapc m
                LEFT JOIN aporte a ON m.id_miembro = a.id_miembro 
                    AND EXISTS (
                        SELECT 1 FROM reunion r 
                        WHERE r.id_reunion = a.id_reunion 
                        AND r.fecha BETWEEN %s AND %s
                    )
                WHERE m.id_grupo = %s
                GROUP BY m.id_miembro, m.nombre
                HAVING ahorro_total > 0
                ORDER BY ahorro_total DESC
            """, (fecha_inicio, fecha_fin, id_grupo))
            
            socias = cursor.fetchall()
            
            if not socias:
                st.error("❌ No hay socias con ahorros en el período seleccionado")
                return
            
            # Obtener total fondo del grupo - CORREGIDO (id_gruppo → id_grupo)
            cursor.execute("""
                SELECT saldo_final 
                FROM reunion 
                WHERE id_grupo = %s AND fecha BETWEEN %s AND %s 
                ORDER BY fecha DESC 
                LIMIT 1
            """, (id_grupo, fecha_inicio, fecha_fin))
            
            ultima_reunion = cursor.fetchone()
            total_fondo_grupo = ultima_reunion['saldo_final'] if ultima_reunion else 0
            
            # Calcular total ahorro del grupo
            total_ahorro_grupo = sum(socia['ahorro_total'] for socia in socias)
            
            # Mostrar datos base
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("👥 Número de Socias", len(socias))
            with col2:
                st.metric("💰 Total Ahorro del Grupo", f"${total_ahorro_grupo:,.2f}")
            with col3:
                st.metric("🏦 Total Fondo del Grupo", f"${total_fondo_grupo:,.2f}")
            with col4:
                if total_ahorro_grupo > 0:
                    porcion_fondo = total_fondo_grupo / total_ahorro_grupo
                    st.metric("📈 Porción del Fondo", f"{porcion_fondo:.3f}")
                else:
                    porcion_fondo = 0
                    st.metric("📈 Porción del Fondo", "0.000")
            
            # Paso 3: Cálculos detallados por socia
            st.markdown("---")
            st.markdown("### 👥 Paso 3: Reparto por Socia")
            
            # Preparar datos para el cálculo
            porcion_redondeada = round(porcion_fondo, 2) if total_ahorro_grupo > 0 else 0
            
            datos_socias = []
            total_calculo = 0
            total_retiro = 0
            total_sobrante = 0
            
            for socia in socias:
                if metodo_reparto == 'proporcional':
                    calculo_proporcional = socia['ahorro_total'] * porcion_redondeada
                else:  # equitativo
                    calculo_proporcional = total_fondo_grupo / len(socias) if socias else 0
                
                retiro = socia['ahorro_total'] + calculo_proporcional
                
                # Calcular sobrante por redondeo (diferencia entre cálculo teórico y real)
                if metodo_reparto == 'proporcional':
                    calculo_teorico = socia['ahorro_total'] * porcion_fondo
                    sobrante = calculo_teorico - calculo_proporcional
                else:
                    sobrante = 0
                
                datos_socias.append({
                    'id_miembro': socia['id_miembro'],
                    'nombre': socia['nombre'],
                    'ahorro_total': socia['ahorro_total'],
                    'calculo_proporcional': calculo_proporcional,
                    'retiro': retiro,
                    'sobrante': sobrante
                })
                
                total_calculo += calculo_proporcional
                total_retiro += retiro
                total_sobrante += sobrante
            
            # Mostrar tabla de socias
            df_socias = pd.DataFrame(datos_socias)
            df_socias_display = df_socias.copy()
            df_socias_display['ahorro_total'] = df_socias_display['ahorro_total'].apply(lambda x: f"${x:,.2f}")
            df_socias_display['calculo_proporcional'] = df_socias_display['calculo_proporcional'].apply(lambda x: f"${x:,.2f}")
            df_socias_display['retiro'] = df_socias_display['retiro'].apply(lambda x: f"${x:,.2f}")
            df_socias_display['sobrante'] = df_socias_display['sobrante'].apply(lambda x: f"${x:,.4f}")
            
            # Agregar fila de totales
            totales = {
                'nombre': '**TOTALES**',
                'ahorro_total': f"**${total_ahorro_grupo:,.2f}**",
                'calculo_proporcional': f"**${total_calculo:,.2f}**",
                'retiro': f"**${total_retiro:,.2f}**",
                'sobrante': f"**${total_sobrante:,.4f}**"
            }
            
            df_totales = pd.DataFrame([totales])
            df_final = pd.concat([df_socias_display, df_totales], ignore_index=True)
            
            st.dataframe(
                df_final,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id_miembro": None,
                    "nombre": "Socia",
                    "ahorro_total": "Ahorros",
                    "calculo_proporcional": "Cálculo Reparto",
                    "retiro": "Retiro Total",
                    "sobrante": "Sobrante"
                }
            )
            
            # Paso 4: Resultados finales
            st.markdown("---")
            st.markdown("### 📋 Paso 4: Resultados Finales")
            
            saldo_cierre = total_fondo_grupo - total_calculo
            saldo_inicial_siguiente = total_sobrante
            
            # Ajustar saldo inicial a múltiplo de 50 (opcional)
            saldo_ajustado = round(saldo_inicial_siguiente / 50) * 50
            ajuste = saldo_ajustado - saldo_inicial_siguiente
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("💰 Total Sobrante", f"${total_sobrante:,.4f}")
            with col2:
                st.metric("🏦 Saldo de Cierre", f"${saldo_cierre:,.2f}")
            with col3:
                st.metric("🔄 Saldo Inicial Siguiente", f"${saldo_inicial_siguiente:,.2f}")
            with col4:
                st.metric("📐 Saldo Ajustado (x50)", f"${saldo_ajustado:,.2f}")
            
            if abs(ajuste) > 0.01:
                st.info(f"**Ajuste aplicado:** ${ajuste:,.2f} (para redondear a múltiplo de $50)")
            
            # Resumen ejecutivo
            st.markdown("---")
            st.markdown("### 📝 Resumen Ejecutivo del Cierre")
            
            st.success(f"""
            **✅ Cálculo completado para el período:**
            - **Periodo:** {fecha_inicio.strftime('%d/%m/%Y')} a {fecha_fin.strftime('%d/%m/%Y')}
            - **Total socias participantes:** {len(socias)}
            - **Método de reparto:** {metodo_reparto}
            - **Total a repartir:** ${total_calculo:,.2f}
            - **Saldo para siguiente ciclo:** ${saldo_ajustado:,.2f}
            """)
            
            # Paso 5: Confirmar y guardar cierre
            st.markdown("---")
            st.markdown("### 💾 Paso 5: Confirmar Cierre")
            
            # Mostrar resumen para confirmación
            with st.expander("📋 Ver detalles completos del cálculo", expanded=False):
                st.write("**Parámetros del cálculo:**")
                st.json({
                    "total_ahorro_grupo": total_ahorro_grupo,
                    "total_fondo_grupo": total_fondo_grupo,
                    "porcion_fondo": porcion_fondo,
                    "porcion_redondeada": porcion_redondeada,
                    "metodo_reparto": metodo_reparto,
                    "numero_socias": len(socias)
                })
            
            # Botón para confirmar cierre
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("✅ Confirmar y Guardar Cierre", type="primary", use_container_width=True):
                    guardar_cierre_completo(
                        id_grupo, 
                        fecha_inicio, 
                        fecha_fin, 
                        datos_socias, 
                        total_ahorro_grupo,
                        total_fondo_grupo,
                        porcion_fondo,
                        porcion_redondeada,
                        total_calculo,
                        total_sobrante,
                        saldo_ajustado,
                        metodo_reparto
                    )
    
    except Exception as e:
        st.error(f"❌ Error en el cálculo del cierre: {e}")

def guardar_cierre_completo(id_grupo, fecha_inicio, fecha_fin, datos_socias, 
                           total_ahorro, total_fondo, porcion_fondo, porcion_redondeada,
                           total_calculo, total_sobrante, saldo_inicial_siguiente, metodo_reparto):
    """Guarda el cierre completo en la base de datos - VERSIÓN CORREGIDA"""
    
    try:
        conexion = obtener_conexion()
        if not conexion:
            return
            
        with conexion.cursor() as cursor:
            
            # 1. Insertar en tabla cierre (estructura básica según schema)
            cursor.execute("""
                INSERT INTO cierre (
                    id_grupo, fecha_cierre, estado
                ) VALUES (%s, %s, %s)
            """, (
                id_grupo, datetime.now(), 'procesado'
            ))
            
            id_cierre = cursor.lastrowid
            
            # 2. Insertar detalles del reparto por socia
            for socia in datos_socias:
                cursor.execute("""
                    INSERT INTO repartoutilidades (
                        id_cierre, id_miembro
                    ) VALUES (%s, %s)
                """, (id_cierre, socia['id_miembro']))
            
            # 3. Generar acta de cierre (usando tabla 'acta' existente)
            cursor.execute("""
                INSERT INTO acta (
                    fecha_acta, acuerdos_detallados, id_grupo
                ) VALUES (%s, %s, %s)
            """, (
                datetime.now(),
                f"Acta de cierre del período {fecha_inicio} a {fecha_fin}. "
                f"Total repartido: ${total_calculo:,.2f}. "
                f"Método: {metodo_reparto}. "
                f"Socias participantes: {len(datos_socias)}. "
                f"Saldo siguiente ciclo: ${saldo_inicial_siguiente:,.2f}",
                id_grupo
            ))
            
            conexion.commit()
            
            st.success("🎉 ¡Cierre guardado exitosamente!")
            st.balloons()
            
            st.info(f"""
            **📋 Resumen del cierre guardado:**
            - **ID Cierre:** #{id_cierre}
            - **Periodo:** {fecha_inicio.strftime('%d/%m/%Y')} a {fecha_fin.strftime('%d/%m/%Y')}
            - **Total repartido:** ${total_calculo:,.2f}
            - **Socias beneficiadas:** {len(datos_socias)}
            - **Saldo siguiente ciclo:** ${saldo_inicial_siguiente:,.2f}
            """)
    
    except Exception as e:
        st.error(f"❌ Error al guardar el cierre: {e}")

def mostrar_historial_cierres():
    """Muestra el historial de cierres realizados"""
    st.subheader("📋 Historial de Cierres")
    
    try:
        conexion = obtener_conexion()
        if not conexion:
            return
            
        with conexion.cursor() as cursor:
            
            id_grupo = st.session_state.get('usuario', {}).get('id_grupo', 1)
            
            # Obtener historial de cierres - CORREGIDO para estructura actual
            cursor.execute("""
                SELECT 
                    c.id_cierre,
                    c.fecha_cierre,
                    c.estado,
                    COUNT(r.id_reparto) as numero_socias
                FROM cierre c
                LEFT JOIN repartoutilidades r ON c.id_cierre = r.id_cierre
                WHERE c.id_grupo = %s
                GROUP BY c.id_cierre, c.fecha_cierre, c.estado
                ORDER BY c.fecha_cierre DESC
            """, (id_grupo,))
            
            cierres = cursor.fetchall()
            
            if cierres:
                for cierre in cierres:
                    with st.expander(
                        f"📅 Cierre #{cierre['id_cierre']} | {cierre['fecha_cierre']} | "
                        f"Estado: {cierre['estado']}", 
                        expanded=False
                    ):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**📊 Estadísticas:**")
                            st.write(f"- Socias participantes: {cierre['numero_socias']}")
                        
                        with col2:
                            st.write(f"**🔒 Estado:**")
                            st.write(f"- Estado: {cierre['estado']}")
                        
                        with col3:
                            st.write(f"**📅 Fecha:**")
                            st.write(f"- Fecha: {cierre['fecha_cierre'].strftime('%d/%m/%Y')}")
                        
                        # Botón para ver detalles completos
                        if st.button("👁️ Ver Detalles Completos", key=f"detalles_{cierre['id_cierre']}"):
                            mostrar_detalles_cierre(cierre['id_cierre'])
            else:
                st.info("📝 No hay cierres registrados para este grupo.")
    
    except Exception as e:
        st.error(f"❌ Error al cargar historial de cierres: {e}")

def mostrar_detalles_cierre(id_cierre):
    """Muestra los detalles completos de un cierre específico"""
    try:
        conexion = obtener_conexion()
        if not conexion:
            return
            
        with conexion.cursor() as cursor:
            # Obtener detalles del reparto
            cursor.execute("""
                SELECT 
                    r.id_reparto,
                    m.nombre,
                    m.dui
                FROM repartoutilidades r
                JOIN miembrogapc m ON r.id_miembro = m.id_miembro
                WHERE r.id_cierre = %s
            """, (id_cierre,))
            
            detalles = cursor.fetchall()
            
            if detalles:
                st.subheader(f"👥 Socias participantes en el cierre #{id_cierre}")
                
                df_detalles = pd.DataFrame(detalles)
                st.dataframe(
                    df_detalles,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "id_reparto": "ID Reparto",
                        "nombre": "Nombre Socia",
                        "dui": "DUI"
                    }
                )
            else:
                st.info("No se encontraron detalles para este cierre.")
                
    except Exception as e:
        st.error(f"❌ Error al cargar detalles del cierre: {e}")

def obtener_conexion():
    """Función para obtener conexión a la base de datos"""
    try:
        conexion = pymysql.connect(
            host='bhzcn4gxgbe5tcxihqd1-mysql.services.clever-cloud.com',
            user='usv5pnvafxbrw5hs',
            password='WiOSztB38WxsKuXjnQgT',
            database='bhzcn4gxgbe5tcxihqd1',
            port=3306,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10
        )
        return conexion
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return None