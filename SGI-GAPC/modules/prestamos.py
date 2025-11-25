import streamlit as st
import pymysql
from datetime import datetime
from dateutil.relativedelta import relativedelta

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

def mostrar_modulo_prestamos():
    """Módulo especializado de préstamos - Vista y gestión"""
    
    # Header del módulo con botón de volver
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# 💳 Módulo de Préstamos")
    with col2:
        if st.button("⬅️ Volver al Dashboard", use_container_width=True):
            st.session_state.modulo_actual = 'dashboard'
            st.rerun()
    
    st.markdown("---")
    
    # Menú de opciones
    opcion = st.radio(
        "Selecciona una acción:",
        ["📋 Ver Todos los Préstamos", "➕ Nuevo Préstamo", "📊 Préstamos Activos", "✅ Préstamos Pagados"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if opcion == "📋 Ver Todos los Préstamos":
        mostrar_todos_prestamos()
    elif opcion == "➕ Nuevo Préstamo":
        mostrar_nuevo_prestamo_individual()
    elif opcion == "📊 Préstamos Activos":
        mostrar_prestamos_activos()
    elif opcion == "✅ Préstamos Pagados":
        mostrar_prestamos_pagados()

def mostrar_todos_prestamos():
    """Muestra todos los préstamos con filtros"""
    st.subheader("📋 Todos los Préstamos")
    
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Obtener todos los préstamos del grupo
            cursor.execute("""
                SELECT 
                    p.id_prestamo,
                    m.nombre as miembro,
                    p.monto_prestado,
                    p.proposito,
                    p.fecha_vencimiento,
                    p.plazo_meses,
                    p.estado,
                    p.fecha_solicitud,
                    COALESCE(SUM(pg.monto_capital), 0) as total_pagado,
                    (p.monto_prestado - COALESCE(SUM(pg.monto_capital), 0)) as saldo_pendiente,
                    DATEDIFF(p.fecha_vencimiento, CURDATE()) as dias_restantes
                FROM prestamo p
                JOIN miembrogapc m ON p.id_miembro = m.id_miembro
                LEFT JOIN pago pg ON p.id_prestamo = pg.id_prestamo
                WHERE m.id_grupo = %s
                GROUP BY p.id_prestamo, m.nombre, p.monto_prestado, p.proposito, 
                         p.fecha_vencimiento, p.plazo_meses, p.estado, p.fecha_solicitud
                ORDER BY p.estado, p.fecha_vencimiento DESC
            """, (id_grupo,))
            
            prestamos = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if prestamos:
                # Filtros
                col1, col2, col3 = st.columns(3)
                with col1:
                    estados = ["Todos"] + list(set(p['estado'] for p in prestamos))
                    estado_filtro = st.selectbox("🔍 Filtrar por estado:", estados)
                
                with col2:
                    miembros = ["Todos"] + list(set(p['miembro'] for p in prestamos))
                    miembro_filtro = st.selectbox("👤 Filtrar por miembro:", miembros)
                
                with col3:
                    situacion = ["Todas", "En tiempo", "Por vencer", "Vencidos"]
                    situacion_filtro = st.selectbox("📅 Filtrar por situación:", situacion)
                
                # Aplicar filtros
                prestamos_filtrados = prestamos
                if estado_filtro != "Todos":
                    prestamos_filtrados = [p for p in prestamos_filtrados if p['estado'] == estado_filtro]
                if miembro_filtro != "Todos":
                    prestamos_filtrados = [p for p in prestamos_filtrados if p['miembro'] == miembro_filtro]
                if situacion_filtro != "Todas":
                    if situacion_filtro == "Vencidos":
                        prestamos_filtrados = [p for p in prestamos_filtrados if p['dias_restantes'] < 0]
                    elif situacion_filtro == "Por vencer":
                        prestamos_filtrados = [p for p in prestamos_filtrados if 0 <= p['dias_restantes'] <= 30]
                    elif situacion_filtro == "En tiempo":
                        prestamos_filtrados = [p for p in prestamos_filtrados if p['dias_restantes'] > 30]
                
                # Estadísticas
                total_prestamos = len(prestamos_filtrados)
                total_pendiente = sum(p['saldo_pendiente'] for p in prestamos_filtrados)
                total_prestado = sum(p['monto_prestado'] for p in prestamos_filtrados)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📊 Total Préstamos", total_prestamos)
                with col2:
                    st.metric("💰 Total Prestado", f"${total_prestado:,.2f}")
                with col3:
                    st.metric("📉 Total Pendiente", f"${total_pendiente:,.2f}")
                with col4:
                    porcentaje_pagado = ((total_prestado - total_pendiente) / total_prestado * 100) if total_prestado > 0 else 0
                    st.metric("📈 % Pagado", f"{porcentaje_pagado:.1f}%")
                
                st.markdown("---")
                
                # Mostrar préstamos
                for prestamo in prestamos_filtrados:
                    # Determinar color según situación
                    if prestamo['dias_restantes'] < 0:
                        color = "🔴"  # Vencido
                        situacion_texto = f"VENCIDO (-{abs(prestamo['dias_restantes'])} días)"
                    elif prestamo['dias_restantes'] <= 30:
                        color = "🟡"  # Por vencer
                        situacion_texto = f"Por vencer ({prestamo['dias_restantes']} días)"
                    else:
                        color = "🟢"  # En tiempo
                        situacion_texto = f"En tiempo ({prestamo['dias_restantes']} días)"
                    
                    with st.expander(f"{color} #{prestamo['id_prestamo']} - {prestamo['miembro']} - ${prestamo['monto_prestado']:,.2f} - {prestamo['estado']}", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**👤 Miembro:** {prestamo['miembro']}")
                            st.write(f"**💵 Monto Original:** ${prestamo['monto_prestado']:,.2f}")
                            st.write(f"**📅 Fecha Solicitud:** {prestamo['fecha_solicitud']}")
                            st.write(f"**📋 Propósito:** {prestamo['proposito']}")
                        
                        with col2:
                            st.write(f"**💰 Total Pagado:** ${prestamo['total_pagado']:,.2f}")
                            st.write(f"**📉 Saldo Pendiente:** ${prestamo['saldo_pendiente']:,.2f}")
                            st.write(f"**📅 Fecha Vencimiento:** {prestamo['fecha_vencimiento']}")
                            st.write(f"**⏱️ Días Restantes:** {prestamo['dias_restantes']}")
                        
                        with col3:
                            st.write(f"**🔒 Estado:** {prestamo['estado']}")
                            st.write(f"**📊 Situación:** {situacion_texto}")
                            st.write(f"**⏳ Plazo:** {prestamo['plazo_meses']} meses")
                            
                            # Mostrar historial de pagos
                            if st.button("📋 Ver Historial de Pagos", key=f"hist_{prestamo['id_prestamo']}"):
                                mostrar_historial_pagos(prestamo['id_prestamo'])
                            
                            # Botón para registrar pago
                            if prestamo['estado'] == 'aprobado' and prestamo['saldo_pendiente'] > 0:
                                if st.button("💳 Registrar Pago", key=f"pago_{prestamo['id_prestamo']}"):
                                    st.session_state.registrar_pago_prestamo = prestamo['id_prestamo']
                                    st.rerun()
            else:
                st.info("📝 No hay préstamos registrados en este grupo.")
                
    except Exception as e:
        st.error(f"❌ Error al cargar préstamos: {e}")

def mostrar_nuevo_prestamo_individual():
    """Formulario para nuevo préstamo fuera de reunión - VERSIÓN CORREGIDA"""
    st.subheader("➕ Nuevo Préstamo")
    
    st.info("""
    **💡 Información:**
    Al registrar un préstamo aquí, se simula lo que pasaría en una reunión:
    - Se crea el préstamo con estado 'aprobado'
    - Se afecta el saldo neto del miembro automáticamente
    - El préstamo queda listo para seguimiento
    """)
    
    with st.form("form_nuevo_prestamo_individual"):
        # Buscar miembro
        miembro_seleccionado = buscar_miembro_prestamo()
        
        miembro_valido = False
        form_content_ready = False
        
        if miembro_seleccionado:
            st.markdown("---")
            
            # Mostrar información del miembro
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**👤 Miembro:** {miembro_seleccionado['nombre']}")
            with col2:
                st.info(f"**💰 Ahorro Actual:** ${miembro_seleccionado['ahorro_actual']:,.2f}")
            with col3:
                maximo_permitido = miembro_seleccionado['ahorro_actual'] * 0.8  # 80% del ahorro
                st.info(f"**📈 Máximo Recomendado:** ${maximo_permitido:,.2f}")
            
            # Verificar si el miembro puede solicitar préstamo
            if miembro_seleccionado.get('prestamos_activos', 0) > 0:
                st.error("❌ Este miembro ya tiene un préstamo activo y no puede solicitar otro.")
                miembro_valido = False
            elif miembro_seleccionado['ahorro_actual'] <= 0:
                st.error("❌ Este miembro no tiene ahorro suficiente para solicitar un préstamo.")
                miembro_valido = False
            else:
                miembro_valido = True
            
            # Solo mostrar el formulario completo si el miembro es válido
            if miembro_valido:
                # Datos del préstamo
                st.subheader("📝 Datos del Préstamo")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    monto_prestamo = st.number_input(
                        "💵 Monto a solicitar:",
                        min_value=0.0,
                        max_value=float(maximo_permitido),
                        value=0.0,
                        step=100.0,
                        help=f"Máximo recomendado: ${maximo_permitido:,.2f}"
                    )
                    
                    plazo_meses = st.number_input(
                        "📅 Plazo en meses:",
                        min_value=1,
                        max_value=24,
                        value=6,
                        step=1,
                        help="Número de meses para pagar"
                    )
                
                with col2:
                    proposito = st.text_area(
                        "📋 Motivo del préstamo:",
                        placeholder="Describe para qué necesitas el préstamo...",
                        height=100
                    )
                    
                    fecha_solicitud = st.date_input(
                        "📅 Fecha de solicitud:",
                        value=datetime.now()
                    )
                
                # Calcular detalles
                if monto_prestamo > 0:
                    st.markdown("---")
                    st.subheader("🧮 Detalles del Préstamo")
                    
                    # Calcular interés simple (ejemplo: 5% anual)
                    tasa_interes_anual = 0.05
                    interes_total = monto_prestamo * tasa_interes_anual * (plazo_meses / 12)
                    total_pagar = monto_prestamo + interes_total
                    pago_mensual = total_pagar / plazo_meses
                    fecha_vencimiento = fecha_solicitud + relativedelta(months=plazo_meses)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("💵 Monto Principal", f"${monto_prestamo:,.2f}")
                    
                    with col2:
                        st.metric("💰 Interés Total", f"${interes_total:,.2f}")
                    
                    with col3:
                        st.metric("🧮 Total a Pagar", f"${total_pagar:,.2f}")
                    
                    with col4:
                        st.metric("📅 Pago Mensual", f"${pago_mensual:,.2f}")
                    
                    st.info(f"""
                    **📊 Desglose:**
                    - **Interés total:** ${interes_total:,.2f}
                    - **Total a pagar:** ${total_pagar:,.2f}
                    - **Pago mensual:** ${pago_mensual:,.2f} x {plazo_meses} meses
                    - **Fecha de vencimiento:** {fecha_vencimiento.strftime('%d/%m/%Y')}
                    """)
                
                form_content_ready = True
        
        # ✅ SIEMPRE mostrar el botón de envío, pero deshabilitado si no hay miembro válido
        if miembro_seleccionado and miembro_valido and form_content_ready:
            submitted = st.form_submit_button(
                "✅ Aprobar Préstamo", 
                use_container_width=True,
                type="primary"
            )
        else:
            submitted = st.form_submit_button(
                "✅ Aprobar Préstamo", 
                use_container_width=True,
                type="primary",
                disabled=True  # Deshabilitar si no hay miembro válido
            )
        
        # Validar cuando se envía el formulario
        if submitted:
            if monto_prestamo > 0 and proposito:
                guardar_prestamo_individual(
                    miembro_seleccionado, 
                    monto_prestamo, 
                    plazo_meses, 
                    proposito, 
                    fecha_solicitud,
                    fecha_vencimiento
                )
            else:
                st.error("❌ Completa todos los campos obligatorios")

def buscar_miembro_prestamo():
    """Busca y valida un miembro para préstamo - VERSIÓN MEJORADA"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Obtener miembros con su ahorro y préstamos activos
            cursor.execute("""
                SELECT 
                    m.id_miembro,
                    m.nombre,
                    m.telefono,
                    COALESCE(SUM(a.monto), 0) as ahorro_actual,
                    COUNT(p.id_prestamo) as prestamos_activos
                FROM miembrogapc m
                LEFT JOIN aporte a ON m.id_miembro = a.id_miembro AND a.tipo = 'Ahorro'
                LEFT JOIN prestamo p ON m.id_miembro = p.id_miembro AND p.estado = 'aprobado'
                WHERE m.id_grupo = %s
                GROUP BY m.id_miembro, m.nombre, m.telefono
                ORDER BY m.nombre
            """, (id_grupo,))
            
            miembros = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if miembros:
                # Crear lista de opciones
                opciones = ["Selecciona un miembro"]
                miembros_info = {}
                
                for miembro in miembros:
                    if miembro['prestamos_activos'] > 0:
                        opciones.append(f"❌ {miembro['id_miembro']} - {miembro['nombre']} (Ya tiene préstamo activo)")
                        miembros_info[miembro['id_miembro']] = {**miembro, 'puede_solicitar': False}
                    elif miembro['ahorro_actual'] <= 0:
                        opciones.append(f"❌ {miembro['id_miembro']} - {miembro['nombre']} (Sin ahorro suficiente)")
                        miembros_info[miembro['id_miembro']] = {**miembro, 'puede_solicitar': False}
                    else:
                        opciones.append(f"✅ {miembro['id_miembro']} - {miembro['nombre']} (Ahorro: ${miembro['ahorro_actual']:,.2f})")
                        miembros_info[miembro['id_miembro']] = {**miembro, 'puede_solicitar': True}
                
                miembro_seleccionado_opcion = st.selectbox(
                    "👤 Selecciona el miembro solicitante:",
                    opciones,
                    key="selector_miembro_prestamo_individual"
                )
                
                if miembro_seleccionado_opcion and miembro_seleccionado_opcion != "Selecciona un miembro":
                    # Extraer ID del miembro seleccionado
                    miembro_id = int(miembro_seleccionado_opcion.split(" - ")[0].replace("✅ ", "").replace("❌ ", ""))
                    miembro_info = miembros_info.get(miembro_id)
                    
                    if miembro_info and miembro_info['puede_solicitar']:
                        return miembro_info
                    else:
                        return miembro_info  # Devuelve la info aunque no pueda solicitar
                        
            else:
                st.info("📝 No hay miembros en este grupo.")
                return None
                
    except Exception as e:
        st.error(f"❌ Error al cargar miembros: {e}")
    
    return None

def guardar_prestamo_individual(miembro, monto, plazo_meses, proposito, fecha_solicitud, fecha_vencimiento):
    """Guarda un préstamo individual fuera de reunión - VERSIÓN CORREGIDA"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            # Insertar préstamo con la nueva columna fecha_solicitud
            cursor.execute("""
                INSERT INTO prestamo (
                    id_miembro, id_reunion, monto_prestado, proposito,
                    fecha_solicitud, fecha_vencimiento, plazo_meses, estado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                miembro['id_miembro'],
                1,  # Usar un id_reunion por defecto o obtener el último
                monto,
                proposito,
                fecha_solicitud,
                fecha_vencimiento,
                plazo_meses,
                'aprobado'
            ))
            
            conexion.commit()
            cursor.close()
            conexion.close()
            
            st.success("🎉 ¡Préstamo aprobado exitosamente!")
            st.balloons()
            
            # Mostrar resumen
            st.info(f"""
            **📋 Resumen del Préstamo:**
            - **Miembro:** {miembro['nombre']}
            - **Monto:** ${monto:,.2f}
            - **Plazo:** {plazo_meses} meses
            - **Fecha Solicitud:** {fecha_solicitud.strftime('%d/%m/%Y')}
            - **Vencimiento:** {fecha_vencimiento.strftime('%d/%m/%Y')}
            - **Estado:** Aprobado
            """)
            
    except Exception as e:
        st.error(f"❌ Error al guardar préstamo: {e}")

def mostrar_prestamos_activos():
    """Muestra solo los préstamos activos"""
    st.subheader("📊 Préstamos Activos")
    
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Obtener préstamos activos
            cursor.execute("""
                SELECT 
                    p.id_prestamo,
                    m.nombre as miembro,
                    p.monto_prestado,
                    p.proposito,
                    p.fecha_vencimiento,
                    p.plazo_meses,
                    COALESCE(SUM(pg.monto_capital), 0) as total_pagado,
                    (p.monto_prestado - COALESCE(SUM(pg.monto_capital), 0)) as saldo_pendiente,
                    DATEDIFF(p.fecha_vencimiento, CURDATE()) as dias_restantes
                FROM prestamo p
                JOIN miembrogapc m ON p.id_miembro = m.id_miembro
                LEFT JOIN pago pg ON p.id_prestamo = pg.id_prestamo
                WHERE m.id_grupo = %s AND p.estado = 'aprobado'
                GROUP BY p.id_prestamo, m.nombre, p.monto_prestado, p.proposito, 
                         p.fecha_vencimiento, p.plazo_meses
                HAVING saldo_pendiente > 0
                ORDER BY p.fecha_vencimiento ASC
            """, (id_grupo,))
            
            prestamos_activos = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if prestamos_activos:
                # Estadísticas
                total_activos = len(prestamos_activos)
                total_pendiente = sum(p['saldo_pendiente'] for p in prestamos_activos)
                total_prestado = sum(p['monto_prestado'] for p in prestamos_activos)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📊 Préstamos Activos", total_activos)
                with col2:
                    st.metric("💰 Total Prestado", f"${total_prestado:,.2f}")
                with col3:
                    st.metric("📉 Total Pendiente", f"${total_pendiente:,.2f}")
                with col4:
                    vencidos = len([p for p in prestamos_activos if p['dias_restantes'] < 0])
                    st.metric("⚠️ Préstamos Vencidos", vencidos)
                
                st.markdown("---")
                
                for prestamo in prestamos_activos:
                    # Determinar color según días restantes
                    if prestamo['dias_restantes'] < 0:
                        color = "🔴"  # Vencido
                        estado = f"VENCIDO (-{abs(prestamo['dias_restantes'])} días)"
                    elif prestamo['dias_restantes'] <= 30:
                        color = "🟡"  # Por vencer
                        estado = f"Por vencer ({prestamo['dias_restantes']} días)"
                    else:
                        color = "🟢"  # En tiempo
                        estado = f"En tiempo ({prestamo['dias_restantes']} días)"
                    
                    with st.expander(f"{color} {prestamo['miembro']} - ${prestamo['monto_prestado']:,.2f} - {estado}", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**💵 Monto Original:** ${prestamo['monto_prestado']:,.2f}")
                            st.write(f"**💰 Total Pagado:** ${prestamo['total_pagado']:,.2f}")
                            st.write(f"**📋 Propósito:** {prestamo['proposito']}")
                        with col2:
                            st.write(f"**📉 Saldo Pendiente:** ${prestamo['saldo_pendiente']:,.2f}")
                            st.write(f"**📅 Fecha Vencimiento:** {prestamo['fecha_vencimiento']}")
                            st.write(f"**⏱️ Días Restantes:** {prestamo['dias_restantes']}")
                        with col3:
                            st.write(f"**⏳ Plazo:** {prestamo['plazo_meses']} meses")
                            
                            # Botón para registrar pago
                            if st.button("💳 Registrar Pago", key=f"pago_act_{prestamo['id_prestamo']}"):
                                registrar_pago_prestamo(prestamo['id_prestamo'])
            else:
                st.success("✅ No hay préstamos activos en este momento.")
                
    except Exception as e:
        st.error(f"❌ Error al cargar préstamos activos: {e}")

def mostrar_prestamos_pagados():
    """Muestra los préstamos que han sido pagados completamente"""
    st.subheader("✅ Préstamos Pagados")
    
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Obtener préstamos pagados
            cursor.execute("""
                SELECT 
                    p.id_prestamo,
                    m.nombre as miembro,
                    p.monto_prestado,
                    p.proposito,
                    p.fecha_solicitud,
                    p.fecha_vencimiento,
                    p.plazo_meses,
                    COALESCE(SUM(pg.monto_capital), 0) as total_pagado,
                    MAX(pg.fecha_pago) as fecha_ultimo_pago
                FROM prestamo p
                JOIN miembrogapc m ON p.id_miembro = m.id_miembro
                LEFT JOIN pago pg ON p.id_prestamo = pg.id_prestamo
                WHERE m.id_grupo = %s AND p.estado = 'aprobado'
                GROUP BY p.id_prestamo, m.nombre, p.monto_prestado, p.proposito, 
                         p.fecha_solicitud, p.fecha_vencimiento, p.plazo_meses
                HAVING total_pagado >= p.monto_prestado
                ORDER BY fecha_ultimo_pago DESC
            """, (id_grupo,))
            
            prestamos_pagados = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if prestamos_pagados:
                st.info(f"📊 Se encontraron {len(prestamos_pagados)} préstamos completamente pagados")
                
                for prestamo in prestamos_pagados:
                    with st.expander(f"✅ #{prestamo['id_prestamo']} - {prestamo['miembro']} - ${prestamo['monto_prestado']:,.2f}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**👤 Miembro:** {prestamo['miembro']}")
                            st.write(f"**💵 Monto Original:** ${prestamo['monto_prestado']:,.2f}")
                            st.write(f"**💰 Total Pagado:** ${prestamo['total_pagado']:,.2f}")
                            st.write(f"**📅 Fecha Solicitud:** {prestamo['fecha_solicitud']}")
                        with col2:
                            st.write(f"**📋 Propósito:** {prestamo['proposito']}")
                            st.write(f"**📅 Fecha Vencimiento:** {prestamo['fecha_vencimiento']}")
                            st.write(f"**📅 Último Pago:** {prestamo['fecha_ultimo_pago']}")
                            st.write(f"**⏳ Plazo:** {prestamo['plazo_meses']} meses")
            else:
                st.info("📝 No hay préstamos completamente pagados.")
                
    except Exception as e:
        st.error(f"❌ Error al cargar préstamos pagados: {e}")

def mostrar_historial_pagos(id_prestamo):
    """Muestra el historial de pagos de un préstamo"""
    st.info("🔧 Función de historial de pagos en desarrollo...")

def registrar_pago_prestamo(id_prestamo):
    """Registra un pago para un préstamo"""
    st.info("🔧 Función de registro de pago en desarrollo...")