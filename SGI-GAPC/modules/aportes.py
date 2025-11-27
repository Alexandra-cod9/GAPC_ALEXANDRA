import streamlit as st
import pymysql
from datetime import datetime

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

def mostrar_modulo_aportes():
    """Módulo de gestión de aportes - Cartera Personal"""
    
    # Header del módulo con botón de volver
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# 💰 Cartera Personal - Estado Financiero")
    with col2:
        if st.button("⬅️ Volver al Dashboard", use_container_width=True):
            st.session_state.modulo_actual = 'dashboard'
            st.rerun()
    
    st.markdown("---")
    
    # Verificar si venimos de la búsqueda específica de un miembro
    miembro_especifico_id = st.session_state.get('miembro_detalle_id')
    
    if miembro_especifico_id:
        # Mostrar directamente la información del miembro específico
        miembro_info = obtener_miembro_por_id(miembro_especifico_id)
        if miembro_info:
            st.info(f"🔍 Mostrando estado financiero de: **{miembro_info['nombre']}**")
            mostrar_estado_financiero_completo(miembro_info)
            
            # Limpiar el estado después de mostrar
            st.session_state.miembro_detalle_id = None
        else:
            st.error("❌ No se encontró el miembro especificado")
            mostrar_busqueda_normal()
    else:
        # Mostrar búsqueda normal
        mostrar_busqueda_normal()

def obtener_miembro_por_id(miembro_id):
    """Obtiene un miembro por su ID"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            cursor.execute("""
                SELECT 
                    m.id_miembro,
                    m.nombre,
                    m.telefono,
                    m.dui,
                    m.correo
                FROM miembrogapc m
                WHERE m.id_miembro = %s
            """, (miembro_id,))
            
            miembro = cursor.fetchone()
            cursor.close()
            conexion.close()
            
            return miembro
    except Exception as e:
        st.error(f"❌ Error al obtener miembro: {e}")
    
    return None

def mostrar_busqueda_normal():
    """Muestra la búsqueda normal de aportes"""
    st.subheader("🔍 Buscar Miembro para Ver Estado Financiero")
    
    # Buscar miembro
    miembro_seleccionado = buscar_miembro_aportes()
    
    if miembro_seleccionado:
        mostrar_estado_financiero_completo(miembro_seleccionado)

def buscar_miembro_aportes():
    """Busca y selecciona un miembro para ver su estado financiero"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Obtener miembros del grupo con información básica de ahorro
            cursor.execute("""
                SELECT 
                    m.id_miembro,
                    m.nombre,
                    m.telefono,
                    m.dui,
                    COALESCE(SUM(
                        CASE WHEN a.tipo = 'Ahorro' THEN a.monto ELSE 0 END
                    ), 0) as ahorro_total
                FROM miembrogapc m
                LEFT JOIN aporte a ON m.id_miembro = a.id_miembro
                WHERE m.id_grupo = %s
                GROUP BY m.id_miembro, m.nombre, m.telefono, m.dui
                ORDER BY m.nombre
            """, (id_grupo,))
            
            miembros = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if miembros:
                # Crear lista de opciones
                opciones_miembros = [f"{m['id_miembro']} - {m['nombre']} (Ahorro: ${m['ahorro_total']:,.2f})" for m in miembros]
                
                # Selector de miembro
                miembro_seleccionado = st.selectbox(
                    "👤 Selecciona un miembro:",
                    opciones_miembros,
                    key="selector_miembro_aportes"
                )
                
                if miembro_seleccionado:
                    # Extraer ID del miembro seleccionado
                    miembro_id = int(miembro_seleccionado.split(" - ")[0])
                    miembro_info = next(m for m in miembros if m['id_miembro'] == miembro_id)
                    return miembro_info
            else:
                st.info("📝 No hay miembros en este grupo.")
                return None
                
    except Exception as e:
        st.error(f"❌ Error al cargar miembros: {e}")
    
    return None

def mostrar_estado_financiero_completo(miembro):
    """Muestra el estado financiero completo de un miembro"""
    
    st.markdown("---")
    
    # Obtener todos los datos financieros del miembro
    datos_financieros = obtener_datos_financieros_completos(miembro['id_miembro'])
    
    # Header con información del miembro
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**👤 Miembro:** {miembro['nombre']}")
    with col2:
        st.info(f"**📞 Teléfono:** {miembro['telefono']}")
    with col3:
        st.info(f"**🆔 DUI:** {miembro['dui']}")
    
    st.markdown("---")
    
    # SECCIÓN 1: ENTRADAS (APORTES)
    st.subheader("💵 ENTRADAS - Total Aportado")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "💰 Ahorro Total", 
            f"${datos_financieros['total_ahorro']:,.2f}",
            help="Suma de todos los aportes de tipo 'Ahorro'"
        )
    
    with col2:
        st.metric(
            "🎯 Rifas", 
            f"${datos_financieros['total_rifa']:,.2f}",
            help="Suma de todos los aportes de tipo 'Rifa'"
        )
    
    with col3:
        st.metric(
            "🔧 Otros", 
            f"${datos_financieros['total_otros']:,.2f}",
            help="Suma de todos los aportes de tipo 'Otros'"
        )
    
    with col4:
        st.metric(
            "📤 Pago Préstamos", 
            f"${datos_financieros['total_pago_prestamo']:,.2f}",
            help="Suma de todos los aportes de tipo 'PagoPrestamo'"
        )
    
    with col5:
        st.metric(
            "⚠️ Pago Multas", 
            f"${datos_financieros['total_pago_multa']:,.2f}",
            help="Suma de todos los aportes de tipo 'PagoMulta'"
        )
    
    # Total de entradas
    total_entradas = (datos_financieros['total_ahorro'] + 
                     datos_financieros['total_rifa'] + 
                     datos_financieros['total_otros'] +
                     datos_financieros['total_pago_prestamo'] +
                     datos_financieros['total_pago_multa'])
    
    st.success(f"**📈 TOTAL ENTRADAS: ${total_entradas:,.2f}**")
    
    st.markdown("---")
    
    # SECCIÓN 2: SALIDAS (DEDUCCIONES)
    st.subheader("📉 SALIDAS - Obligaciones Pendientes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "💳 Préstamos Pendientes", 
            f"${datos_financieros['prestamos_pendientes']:,.2f}",
            delta=f"-${datos_financieros['prestamos_pendientes']:,.2f}",
            delta_color="inverse",
            help="Capital pendiente de todos los préstamos no pagados"
        )
    
    with col2:
        st.metric(
            "⚠️ Multas Pendientes", 
            f"${datos_financieros['multas_pendientes']:,.2f}",
            delta=f"-${datos_financieros['multas_pendientes']:,.2f}",
            delta_color="inverse",
            help="Suma de todas las multas registradas"
        )
    
    # Total de salidas
    total_salidas = datos_financieros['prestamos_pendientes'] + datos_financieros['multas_pendientes']
    
    st.error(f"**📊 TOTAL SALIDAS: ${total_salidas:,.2f}**")
    
    st.markdown("---")
    
    # SECCIÓN 3: SALDO NETO (CÁLCULO AUTOMÁTICO)
    st.subheader("🧮 SALDO NETO - Estado Actual")
    
    saldo_neto = total_entradas - total_salidas
    
    # Mostrar saldo neto con color según el resultado
    if saldo_neto >= 0:
        st.success(f"## ✅ SALDO NETO DISPONIBLE: ${saldo_neto:,.2f}")
        st.balloons()
    else:
        st.error(f"## ❌ SALDO NEGATIVO: ${saldo_neto:,.2f}")
        st.warning("El miembro tiene más obligaciones que aportes")
    
    # Fórmula desglosada
    with st.expander("📋 Ver desglose de la fórmula", expanded=False):
        st.write(f"""
        **Fórmula del Saldo Neto:**
        
        ```
        Saldo Neto = (Ahorro Total + Rifas + Otros + Pago Préstamos + Pago Multas) - (Préstamos Pendientes + Multas Pendientes)
        ```
        
        **Cálculo:**
        - **Entradas:** ${total_entradas:,.2f}
        - **Salidas:** ${total_salidas:,.2f}
        - **Resultado:** ${saldo_neto:,.2f}
        """)
    
    st.markdown("---")
    
    # SECCIÓN 4: DETALLES ADICIONALES
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Detalle de Préstamos")
        if datos_financieros['detalle_prestamos']:
            for prestamo in datos_financieros['detalle_prestamos']:
                st.write(f"**#{prestamo['id_prestamo']}** - ${prestamo['monto_prestado']:,.2f}")
                st.write(f"  📅 Vence: {prestamo['fecha_vencimiento']}")
                st.write(f"  💰 Pagado: ${prestamo['monto_pagado']:,.2f}")
                st.write(f"  📉 Pendiente: ${prestamo['monto_restante']:,.2f}")
                st.write("---")
        else:
            st.info("✅ No tiene préstamos pendientes")
    
    with col2:
        st.subheader("⚠️ Detalle de Multas")
        if datos_financieros['detalle_multas']:
            for multa in datos_financieros['detalle_multas']:
                st.write(f"**#{multa['id_multa']}** - ${multa['monto']:,.2f}")
                st.write(f"  📝 {multa['motivo']}")
                st.write(f"  📅 Registrada: {multa['fecha_registro']}")
                st.write("---")
        else:
            st.info("✅ No tiene multas registradas")
    
    # SECCIÓN 5: DEBUG - Mostrar datos brutos (temporal para diagnóstico)
    with st.expander("🔍 Ver datos de debug (para diagnóstico)", expanded=False):
        st.write("**Datos financieros obtenidos:**")
        st.json(datos_financieros)

def obtener_datos_financieros_completos(id_miembro):
    """Obtiene todos los datos financieros de un miembro"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            # DEBUG: Verificar que estamos buscando el miembro correcto
            st.write(f"🔍 DEBUG: Buscando datos para id_miembro: {id_miembro}")
            
            # 1. Obtener totales por tipo de aporte
            cursor.execute("""
                SELECT 
                    tipo,
                    COALESCE(SUM(monto), 0) as total,
                    COUNT(*) as cantidad
                FROM aporte 
                WHERE id_miembro = %s
                GROUP BY tipo
            """, (id_miembro,))
            
            resultados_aportes = cursor.fetchall()
            
            # DEBUG: Mostrar aportes encontrados
            st.write(f"📊 DEBUG: Aportes encontrados: {len(resultados_aportes)}")
            for ap in resultados_aportes:
                st.write(f"  - {ap['tipo']}: ${ap['total']} ({ap['cantidad']} registros)")
            
            # Inicializar totales
            totales_aportes = {
                'Ahorro': 0,
                'Rifa': 0,
                'PagoPrestamo': 0,
                'PagoMulta': 0,
                'Otros': 0
            }
            
            # Llenar totales con datos reales
            for resultado in resultados_aportes:
                tipo = resultado['tipo']
                if tipo in totales_aportes:
                    totales_aportes[tipo] = float(resultado['total'])
            
            # 2. Obtener préstamos pendientes
            cursor.execute("""
                SELECT 
                    p.id_prestamo,
                    p.monto_prestado,
                    p.fecha_vencimiento,
                    p.estado,
                    COALESCE(SUM(pg.monto_capital), 0) as monto_pagado,
                    (p.monto_prestado - COALESCE(SUM(pg.monto_capital), 0)) as monto_restante
                FROM prestamo p
                LEFT JOIN pago pg ON p.id_prestamo = pg.id_prestamo
                WHERE p.id_miembro = %s AND p.estado = 'aprobado'
                GROUP BY p.id_prestamo, p.monto_prestado, p.fecha_vencimiento, p.estado
                HAVING monto_restante > 0
            """, (id_miembro,))
            
            prestamos_pendientes = cursor.fetchall()
            total_prestamos_pendientes = sum(float(p['monto_restante']) for p in prestamos_pendientes)
            
            # DEBUG: Mostrar préstamos
            st.write(f"💳 DEBUG: Préstamos pendientes: {len(prestamos_pendientes)}")
            
            # 3. Obtener multas pendientes (CORREGIDO - SIN JOIN a tabla estado)
            cursor.execute("""
                SELECT 
                    mt.id_multa,
                    mt.motivo,
                    mt.monto,
                    mt.fecha_registro
                FROM multa mt
                WHERE mt.id_miembro = %s
            """, (id_miembro,))
            
            multas_pendientes = cursor.fetchall()
            total_multas_pendientes = sum(float(m['monto']) for m in multas_pendientes)
            
            # DEBUG: Mostrar multas
            st.write(f"⚠️ DEBUG: Multas pendientes: {len(multas_pendientes)}")
            
            cursor.close()
            conexion.close()
            
            return {
                # Entradas (Aportes)
                'total_ahorro': totales_aportes['Ahorro'],
                'total_rifa': totales_aportes['Rifa'],
                'total_otros': totales_aportes['Otros'],
                'total_pago_prestamo': totales_aportes['PagoPrestamo'],
                'total_pago_multa': totales_aportes['PagoMulta'],
                
                # Salidas (Obligaciones)
                'prestamos_pendientes': total_prestamos_pendientes,
                'multas_pendientes': total_multas_pendientes,
                
                # Detalles
                'detalle_prestamos': prestamos_pendientes,
                'detalle_multas': multas_pendientes
            }
            
    except Exception as e:
        st.error(f"❌ Error al obtener datos financieros: {e}")
        import traceback
        st.code(traceback.format_exc())
    
    # Retorno por defecto en caso de error
    return {
        'total_ahorro': 0,
        'total_rifa': 0,
        'total_otros': 0,
        'total_pago_prestamo': 0,
        'total_pago_multa': 0,
        'prestamos_pendientes': 0,
        'multas_pendientes': 0,
        'detalle_prestamos': [],
        'detalle_multas': []
    }
