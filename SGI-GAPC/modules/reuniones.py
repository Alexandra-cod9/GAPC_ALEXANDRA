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

def mostrar_modulo_reuniones():
    """Módulo de gestión de reuniones - El Corazón del Sistema"""
    
    # Header del módulo con botón de volver
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# 📅 Módulo de Reuniones - El Corazón del Sistema")
    with col2:
        if st.button("⬅️ Volver al Dashboard", use_container_width=True):
            st.session_state.modulo_actual = 'dashboard'
            st.rerun()
    
    st.markdown("---")
    
    # Menú de opciones
    opcion = st.radio(
        "Selecciona una acción:",
        ["➕ Nueva Reunión", "📋 Historial de Reuniones"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if opcion == "➕ Nueva Reunión":
        mostrar_nueva_reunion()
    elif opcion == "📋 Historial de Reuniones":
        mostrar_historial_reuniones()

def mostrar_nueva_reunion():
    """Interfaz para crear una nueva reunión completa"""
    st.subheader("➕ Nueva Reunión - Registro Completo")
    
    # Inicializar session_state para los movimientos temporales
    if 'prestamos_temporales' not in st.session_state:
        st.session_state.prestamos_temporales = []
    if 'aportes_temporales' not in st.session_state:
        st.session_state.aportes_temporales = []
    if 'multas_temporales' not in st.session_state:
        st.session_state.multas_temporales = []
    if 'pagos_temporales' not in st.session_state:
        st.session_state.pagos_temporales = []
    
    # PASO 1: CREAR LA REUNIÓN - Información básica
    st.subheader("📅 1. Información de la Reunión")
    
    # Obtener saldo inicial (saldo final de la última reunión)
    saldo_inicial = obtener_saldo_inicial_reunion()
    nombre_grupo = obtener_nombre_grupo()
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**🏢 Grupo:** {nombre_grupo}")
    with col2:
        st.success(f"**💰 Saldo Inicial:** ${saldo_inicial:,.2f}")
    
    with st.form("form_info_reunion"):
        col1, col2 = st.columns(2)
        with col1:
            fecha_reunion = st.date_input("📅 Fecha de la reunión *", value=datetime.now())
        with col2:
            hora_reunion = st.time_input("⏰ Hora de la reunión *", value=datetime.now().time())
        
        info_submitted = st.form_submit_button("💾 Guardar Información Básica", use_container_width=True)
    
    st.markdown("---")
    
    # PASO 2: REGISTRAR ASISTENCIA
    st.subheader("🧍 2. Registro de Asistencia")
    
    asistencias = registrar_asistencia()
    
    # Mostrar resumen de asistencia
    if asistencias:
        total_miembros = len(asistencias)
        presentes = sum(1 for asistio in asistencias.values() if asistio)
        ausentes = total_miembros - presentes
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👥 Total Miembros", total_miembros)
        with col2:
            st.metric("✅ Presentes", presentes)
        with col3:
            st.metric("❌ Ausentes", ausentes)
    
    st.markdown("---")
    
    # PASO 3: MOVIMIENTOS DE LA REUNIÓN
    st.subheader("💸 3. Movimientos de la Reunión")
    
    # 3A. REGISTRAR APORTES
    st.write("**💰 3A. Registrar Aportes**")
    with st.expander("📥 Agregar Nuevos Aportes", expanded=False):
        procesar_aportes_reunion()
    
    # 3B. REGISTRAR PRÉSTAMOS
    st.write("**📤 3B. Registrar Préstamos**")
    with st.expander("💳 Aprobar Nuevos Préstamos", expanded=False):
        procesar_prestamos_reunion(saldo_inicial)
    
    # 3C. REGISTRAR MULTAS
    st.write("**⚠️ 3C. Registrar Multas**")
    with st.expander("🎯 Aplicar Multas", expanded=False):
        procesar_multas_reunion()
    
    # 3D. REGISTRAR PAGOS
    st.write("**💵 3D. Registrar Pagos**")
    with st.expander("📋 Registrar Pagos de Préstamos/Multas", expanded=False):
        procesar_pagos_reunion()
    
    st.markdown("---")
    
    # PASO 4: RESUMEN Y CIERRE
    st.subheader("🧮 4. Resumen y Cierre")
    
    # Calcular totales
    total_aportes = sum(a['monto'] for a in st.session_state.aportes_temporales)
    total_prestamos = sum(p['monto'] for p in st.session_state.prestamos_temporales)
    total_multas = sum(m['monto'] for m in st.session_state.multas_temporales)
    total_pagos = sum(p['monto'] for p in st.session_state.pagos_temporales)
    
    # Calcular saldo final
    saldo_final = saldo_inicial + total_aportes - total_prestamos - total_multas + total_pagos
    
    # Mostrar resumen financiero
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("💰 Saldo Inicial", f"${saldo_inicial:,.2f}")
    with col2:
        st.metric("📥 Total Aportes", f"${total_aportes:,.2f}")
    with col3:
        st.metric("📤 Total Préstamos", f"-${total_prestamos:,.2f}")
    with col4:
        st.metric("⚠️ Total Multas", f"-${total_multas:,.2f}")
    with col5:
        st.metric("🧮 Saldo Final", f"${saldo_final:,.2f}")
    
    # Acuerdos y observaciones
    st.subheader("📝 Acuerdos y Observaciones")
    acuerdos = st.text_area(
        "Escribe los acuerdos, decisiones y observaciones de la reunión:",
        placeholder="Ej: Se acordó comprar materiales para...\nSe asignó tarea a Juan para...\nPróxima reunión:...",
        height=150
    )
    
    # Botón final para guardar toda la reunión
    if st.button("💾 Guardar Reunión Completa", type="primary", use_container_width=True):
        if not fecha_reunion or not hora_reunion:
            st.error("❌ Fecha y hora son obligatorios")
        elif not asistencias:
            st.error("❌ Debe registrar la asistencia de los miembros")
        else:
            guardar_reunion_completa(
                fecha_reunion, hora_reunion, asistencias,
                st.session_state.aportes_temporales,
                st.session_state.prestamos_temporales,
                st.session_state.multas_temporales,
                st.session_state.pagos_temporales,
                saldo_inicial, saldo_final, acuerdos
            )
            
            # Limpiar datos temporales
            st.session_state.prestamos_temporales = []
            st.session_state.aportes_temporales = []
            st.session_state.multas_temporales = []
            st.session_state.pagos_temporales = []
            
            st.rerun()

def obtener_saldo_inicial_reunion():
    """Obtiene el saldo inicial (saldo final de la última reunión)"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Obtener saldo final de la última reunión
            cursor.execute("""
                SELECT saldo_final 
                FROM reunion 
                WHERE id_grupo = %s 
                ORDER BY fecha DESC, hora DESC 
                LIMIT 1
            """, (id_grupo,))
            
            ultima_reunion = cursor.fetchone()
            cursor.close()
            conexion.close()
            
            if ultima_reunion and ultima_reunion['saldo_final'] is not None:
                return float(ultima_reunion['saldo_final'])
    
    except Exception as e:
        st.error(f"Error al obtener saldo inicial: {e}")
    
    return 0.0

def obtener_nombre_grupo():
    """Obtiene el nombre del grupo"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            cursor.execute("SELECT nombre_grupo FROM grupo WHERE id_grupo = %s", (id_grupo,))
            grupo = cursor.fetchone()
            cursor.close()
            conexion.close()
            
            if grupo:
                return grupo['nombre_grupo']
    
    except Exception as e:
        st.error(f"Error al obtener nombre del grupo: {e}")
    
    return "Grupo"

def registrar_asistencia():
    """Registra la asistencia de miembros y sugiere multas automáticas"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Obtener miembros del grupo
            cursor.execute("""
                SELECT m.id_miembro, m.nombre 
                FROM miembrogapc m 
                WHERE m.id_grupo = %s 
                ORDER BY m.nombre
            """, (id_grupo,))
            
            miembros = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            asistencias = {}
            st.write("**Marque ✅ los miembros que asistieron:**")
            
            for miembro in miembros:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"👤 {miembro['nombre']}")
                with col2:
                    asistio = st.checkbox("Asistió", value=True, key=f"asist_{miembro['id_miembro']}")
                    asistencias[miembro['id_miembro']] = asistio
                with col3:
                    if not asistio:
                        if st.button("⚠️ Multar", key=f"multar_{miembro['id_miembro']}"):
                            # Agregar multa automática por falta
                            monto_multa = obtener_monto_multa_ausencia()
                            multa = {
                                'id_miembro': miembro['id_miembro'],
                                'nombre': miembro['nombre'],
                                'motivo': f"Falta a reunión {datetime.now().strftime('%d/%m/%Y')}",
                                'monto': monto_multa
                            }
                            if multa not in st.session_state.multas_temporales:
                                st.session_state.multas_temporales.append(multa)
                                st.success(f"Multa de ${monto_multa} aplicada a {miembro['nombre']}")
                                st.rerun()
            
            return asistencias
            
    except Exception as e:
        st.error(f"Error al cargar miembros para asistencia: {e}")
    
    return {}

def obtener_monto_multa_ausencia():
    """Obtiene el monto de multa por ausencia del reglamento"""
    # Por defecto $5.00, podrías obtenerlo de la tabla reglamento
    return 5.00

def procesar_aportes_reunion():
    """Procesa los aportes durante la reunión"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Obtener miembros del grupo
            cursor.execute("SELECT id_miembro, nombre FROM miembrogapc WHERE id_grupo = %s ORDER BY nombre", (id_grupo,))
            miembros = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if miembros:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    miembro_aporte = st.selectbox(
                        "👤 Miembro:",
                        [f"{m['id_miembro']} - {m['nombre']}" for m in miembros],
                        key="aporte_miembro"
                    )
                
                with col2:
                    tipo_aporte = st.selectbox(
                        "📋 Tipo:",
                        ['Ahorro', 'Rifa', 'PagoPrestamo', 'PagoMulta', 'Otros'],
                        key="tipo_aporte"
                    )
                
                with col3:
                    monto_aporte = st.number_input("💵 Monto:", min_value=0.0, step=10.0, key="monto_aporte")
                
                if st.button("➕ Agregar Aporte", key="agregar_aporte"):
                    if miembro_aporte and monto_aporte > 0:
                        miembro_id = int(miembro_aporte.split(" - ")[0])
                        miembro_nombre = next(m['nombre'] for m in miembros if m['id_miembro'] == miembro_id)
                        
                        aporte = {
                            'id_miembro': miembro_id,
                            'nombre': miembro_nombre,
                            'monto': monto_aporte,
                            'tipo': tipo_aporte
                        }
                        st.session_state.aportes_temporales.append(aporte)
                        st.success(f"✅ Aporte registrado: {miembro_nombre} - ${monto_aporte:,.2f} - {tipo_aporte}")
                        st.rerun()
    
    except Exception as e:
        st.error(f"Error al procesar aportes: {e}")
    
    # Mostrar aportes registrados
    if st.session_state.aportes_temporales:
        st.write("**📋 Aportes registrados en esta reunión:**")
        for i, aporte in enumerate(st.session_state.aportes_temporales):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"- {aporte['nombre']}")
            with col2:
                st.write(f"${aporte['monto']:,.2f}")
            with col3:
                st.write(f"{aporte['tipo']}")
                if st.button("🗑️", key=f"del_aporte_{i}"):
                    st.session_state.aportes_temporales.pop(i)
                    st.rerun()

def procesar_prestamos_reunion(saldo_inicial):
    """Procesa solicitudes de préstamos durante la reunión"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Obtener miembros con su ahorro actual
            cursor.execute("""
                SELECT m.id_miembro, m.nombre, COALESCE(SUM(a.monto), 0) as ahorro
                FROM miembrogapc m
                LEFT JOIN aporte a ON m.id_miembro = a.id_miembro
                WHERE m.id_grupo = %s
                GROUP BY m.id_miembro, m.nombre
            """, (id_grupo,))
            
            miembros = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if miembros:
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    miembro_prestamo = st.selectbox(
                        "👤 Solicitante:",
                        [f"{m['id_miembro']} - {m['nombre']} (Ahorro: ${m['ahorro']:,.2f})" for m in miembros],
                        key="prestamo_miembro"
                    )
                
                with col2:
                    monto_prestamo = st.number_input("💵 Monto:", min_value=0.0, step=100.0, key="monto_prestamo")
                
                with col3:
                    plazo_meses = st.number_input("📅 Meses:", min_value=1, max_value=24, value=6, key="plazo_prestamo")
                
                with col4:
                    proposito = st.text_input("📋 Propósito:", placeholder="Motivo...", key="proposito_prestamo")
                
                if st.button("✅ Aprobar Préstamo", key="aprobar_prestamo"):
                    if miembro_prestamo and monto_prestamo > 0:
                        miembro_id = int(miembro_prestamo.split(" - ")[0])
                        miembro_nombre = next(m['nombre'] for m in miembros if m['id_miembro'] == miembro_id)
                        ahorro_miembro = next(m['ahorro'] for m in miembros if m['id_miembro'] == miembro_id)
                        
                        # Validaciones
                        if monto_prestamo > ahorro_miembro:
                            st.error(f"❌ DENEGADO: Supera el ahorro disponible (${ahorro_miembro:,.2f})")
                        elif monto_prestamo > saldo_inicial:
                            st.error(f"❌ DENEGADO: Supera el saldo del grupo (${saldo_inicial:,.2f})")
                        else:
                            prestamo = {
                                'id_miembro': miembro_id,
                                'nombre': miembro_nombre,
                                'monto': monto_prestamo,
                                'plazo_meses': plazo_meses,
                                'proposito': proposito,
                                'fecha_vencimiento': (datetime.now() + relativedelta(months=plazo_meses)).strftime("%Y-%m-%d")
                            }
                            st.session_state.prestamos_temporales.append(prestamo)
                            st.success(f"✅ Préstamo aprobado: {miembro_nombre} - ${monto_prestamo:,.2f}")
                            st.rerun()
    
    except Exception as e:
        st.error(f"Error al procesar préstamos: {e}")
    
    # Mostrar préstamos aprobados
    if st.session_state.prestamos_temporales:
        st.write("**📋 Préstamos aprobados en esta reunión:**")
        for i, prestamo in enumerate(st.session_state.prestamos_temporales):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write(f"- {prestamo['nombre']}")
            with col2:
                st.write(f"${prestamo['monto']:,.2f}")
            with col3:
                st.write(f"{prestamo['plazo_meses']} meses")
            with col4:
                if st.button("🗑️", key=f"del_prestamo_{i}"):
                    st.session_state.prestamos_temporales.pop(i)
                    st.rerun()

def procesar_multas_reunion():
    """Procesa la aplicación de multas durante la reunión"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Obtener miembros del grupo
            cursor.execute("SELECT id_miembro, nombre FROM miembrogapc WHERE id_grupo = %s ORDER BY nombre", (id_grupo,))
            miembros = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if miembros:
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    miembro_multa = st.selectbox(
                        "👤 Miembro:",
                        [f"{m['id_miembro']} - {m['nombre']}" for m in miembros],
                        key="multa_miembro"
                    )
                
                with col2:
                    monto_multa = st.number_input("💵 Monto:", min_value=0.0, step=5.0, key="monto_multa")
                
                with col3:
                    motivo = st.text_input("📋 Motivo:", placeholder="Razón de la multa...", key="motivo_multa")
                
                if st.button("⚠️ Aplicar Multa", key="aplicar_multa"):
                    if miembro_multa and monto_multa > 0 and motivo:
                        miembro_id = int(miembro_multa.split(" - ")[0])
                        miembro_nombre = next(m['nombre'] for m in miembros if m['id_miembro'] == miembro_id)
                        
                        multa = {
                            'id_miembro': miembro_id,
                            'nombre': miembro_nombre,
                            'motivo': motivo,
                            'monto': monto_multa
                        }
                        st.session_state.multas_temporales.append(multa)
                        st.success(f"✅ Multa aplicada: {miembro_nombre} - ${monto_multa:,.2f}")
                        st.rerun()
    
    except Exception as e:
        st.error(f"Error al procesar multas: {e}")
    
    # Mostrar multas aplicadas
    if st.session_state.multas_temporales:
        st.write("**📋 Multas aplicadas en esta reunión:**")
        for i, multa in enumerate(st.session_state.multas_temporales):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"- {multa['nombre']}: {multa['motivo']}")
            with col2:
                st.write(f"${multa['monto']:,.2f}")
            with col3:
                if st.button("🗑️", key=f"del_multa_{i}"):
                    st.session_state.multas_temporales.pop(i)
                    st.rerun()

def procesar_pagos_reunion():
    """Procesa los pagos de préstamos y multas durante la reunión"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Obtener miembros con préstamos pendientes
            cursor.execute("""
                SELECT DISTINCT m.id_miembro, m.nombre
                FROM miembrogapc m
                JOIN prestamo p ON m.id_miembro = p.id_miembro
                WHERE m.id_grupo = %s AND p.estado = 'aprobado'
            """, (id_grupo,))
            
            miembros_con_prestamos = cursor.fetchall()
            
            # Obtener miembros con multas pendientes
            cursor.execute("""
                SELECT DISTINCT m.id_miembro, m.nombre
                FROM miembrogapc m
                JOIN multa mt ON m.id_miembro = mt.id_miembro
                JOIN estado e ON mt.id_estado = e.id_estado
                WHERE m.id_grupo = %s AND e.nombre_estado IN ('activo', 'mora')
            """, (id_grupo,))
            
            miembros_con_multas = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            miembros_pagos = list({m['id_miembro']: m for m in miembros_con_prestamos + miembros_con_multas}.values())
            
            if miembros_pagos:
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    miembro_pago = st.selectbox(
                        "👤 Miembro:",
                        [f"{m['id_miembro']} - {m['nombre']}" for m in miembros_pagos],
                        key="pago_miembro"
                    )
                
                with col2:
                    monto_pago = st.number_input("💵 Monto:", min_value=0.0, step=10.0, key="monto_pago")
                
                with col3:
                    tipo_pago = st.selectbox(
                        "📋 Para:",
                        ['Préstamo', 'Multa'],
                        key="tipo_pago"
                    )
                
                with col4:
                    descripcion = st.text_input("📝 Descripción:", placeholder="Detalles del pago...", key="desc_pago")
                
                if st.button("💳 Registrar Pago", key="registrar_pago"):
                    if miembro_pago and monto_pago > 0:
                        miembro_id = int(miembro_pago.split(" - ")[0])
                        miembro_nombre = next(m['nombre'] for m in miembros_pagos if m['id_miembro'] == miembro_id)
                        
                        pago = {
                            'id_miembro': miembro_id,
                            'nombre': miembro_nombre,
                            'monto': monto_pago,
                            'tipo': tipo_pago,
                            'descripcion': descripcion
                        }
                        st.session_state.pagos_temporales.append(pago)
                        st.success(f"✅ Pago registrado: {miembro_nombre} - ${monto_pago:,.2f} - {tipo_pago}")
                        st.rerun()
    
    except Exception as e:
        st.error(f"Error al procesar pagos: {e}")
    
    # Mostrar pagos registrados
    if st.session_state.pagos_temporales:
        st.write("**📋 Pagos registrados en esta reunión:**")
        for i, pago in enumerate(st.session_state.pagos_temporales):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"- {pago['nombre']}: {pago['tipo']}")
            with col2:
                st.write(f"${pago['monto']:,.2f}")
            with col3:
                if st.button("🗑️", key=f"del_pago_{i}"):
                    st.session_state.pagos_temporales.pop(i)
                    st.rerun()

def guardar_reunion_completa(fecha, hora, asistencias, aportes, prestamos, multas, pagos, saldo_inicial, saldo_final, acuerdos):
    """Guarda toda la información de la reunión en la base de datos"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # 1. Insertar la reunión
            cursor.execute("""
                INSERT INTO reunion (id_grupo, fecha, hora, saldo_inicial, saldo_final, acuerdos)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (id_grupo, fecha, hora, saldo_inicial, saldo_final, acuerdos))
            
            id_reunion = cursor.lastrowid
            
            # 2. Guardar asistencias
            for id_miembro, asistio in asistencias.items():
                multa_aplicada = 0.0
                if not asistio:
                    multa_aplicada = obtener_monto_multa_ausencia()
                
                cursor.execute("""
                    INSERT INTO asistencia (id_reunion, id_miembro, estado, multa_aplicada)
                    VALUES (%s, %s, %s, %s)
                """, (id_reunion, id_miembro, 'presente' if asistio else 'ausente', multa_aplicada))
            
            # 3. Guardar aportes
            for aporte in aportes:
                cursor.execute("""
                    INSERT INTO aporte (id_reunion, id_miembro, monto, tipo)
                    VALUES (%s, %s, %s, %s)
                """, (id_reunion, aporte['id_miembro'], aporte['monto'], aporte['tipo']))
            
            # 4. Guardar préstamos
            for prestamo in prestamos:
                cursor.execute("""
                    INSERT INTO prestamo (id_miembro, id_reunion, monto_prestado, proposito, fecha_vencimiento, plazo_meses, estado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (prestamo['id_miembro'], id_reunion, prestamo['monto'], prestamo['proposito'], 
                      prestamo['fecha_vencimiento'], prestamo['plazo_meses'], 'aprobado'))
            
            # 5. Guardar multas - SOLO LAS COLUMNAS EXISTENTES
            for multa in multas:
                cursor.execute("""
                    INSERT INTO multa (id_miembro, motivo, monto)
                    VALUES (%s, %s, %s)
                """, (multa['id_miembro'], multa['motivo'], multa['monto']))
            # fecha_registro se llena automáticamente con curdate()
            
            # 6. Guardar pagos
            for pago in pagos:
                tipo_aporte = 'PagoPrestamo' if pago['tipo'] == 'Préstamo' else 'PagoMulta'
                cursor.execute("""
                    INSERT INTO aporte (id_reunion, id_miembro, monto, tipo)
                    VALUES (%s, %s, %s, %s)
                """, (id_reunion, pago['id_miembro'], pago['monto'], tipo_aporte))
            
            conexion.commit()
            cursor.close()
            conexion.close()
            
            st.success("🎉 ¡Reunión guardada exitosamente!")
            st.balloons()
            
            st.session_state.ultimo_saldo_actualizado = saldo_final
            
    except Exception as e:
        st.error(f"❌ Error al guardar la reunión: {e}")

def mostrar_historial_reuniones():
    """Muestra el historial de reuniones anteriores"""
    st.subheader("📋 Historial de Reuniones")
    
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Consulta CORREGIDA: Contar solo los presentes reales
            cursor.execute("""
                SELECT r.id_reunion, r.fecha, r.hora, r.saldo_inicial, r.saldo_final, r.acuerdos,
                       COUNT(CASE WHEN a.estado = 'presente' THEN 1 END) as total_presentes,
                       COUNT(a.id_asistencia) as total_miembros
                FROM reunion r
                LEFT JOIN asistencia a ON r.id_reunion = a.id_reunion
                WHERE r.id_grupo = %s
                GROUP BY r.id_reunion, r.fecha, r.hora, r.saldo_inicial, r.saldo_final, r.acuerdos
                ORDER BY r.fecha DESC
            """, (id_grupo,))
            
            reuniones = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if reuniones:
                for reunion in reuniones:
                    with st.expander(f"📅 Reunión del {reunion['fecha']} - {reunion['hora']}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**💰 Saldo Inicial:** ${reunion['saldo_inicial']:,.2f}")
                            st.write(f"**🧮 Saldo Final:** ${reunion['saldo_final']:,.2f}")
                            st.write(f"**✅ Presentes:** {reunion['total_presentes']} de {reunion['total_miembros']}")
                            st.write(f"**❌ Ausentes:** {reunion['total_miembros'] - reunion['total_presentes']}")
                        with col2:
                            if reunion['acuerdos']:
                                st.write("**📝 Acuerdos:**")
                                st.write(reunion['acuerdos'])
            else:
                st.info("📝 No hay reuniones registradas para este grupo.")
                
    except Exception as e:
        st.error(f"❌ Error al cargar historial: {e}")