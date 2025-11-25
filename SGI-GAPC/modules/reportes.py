import streamlit as st
import pymysql
from datetime import datetime
import calendar

def mostrar_modulo_reportes():
    """Módulo de Reportes Mensuales - Vista de solo lectura"""
    
    # Header del módulo con botón de volver
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# 📊 Módulo de Reportes Mensuales")
    with col2:
        if st.button("⬅️ Volver al Dashboard", use_container_width=True):
            st.session_state.modulo_actual = 'dashboard'
            st.rerun()
    
    st.markdown("---")
    
    st.info("""
    **📈 Reportes de Solo Lectura**
    - Genera reportes consolidados mensuales
    - Visualiza toda la actividad del grupo
    - Información financiera y estadísticas
    """)
    
    # Selector de mes y año
    col1, col2 = st.columns(2)
    with col1:
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        mes_seleccionado = st.selectbox("📅 Seleccionar Mes:", meses, index=datetime.now().month-1)
    
    with col2:
        año_actual = datetime.now().year
        años = list(range(año_actual - 2, año_actual + 1))
        año_seleccionado = st.selectbox("📅 Seleccionar Año:", años, index=2)
    
    # Generar reporte
    if st.button("📈 Generar Reporte Mensual", type="primary", use_container_width=True):
        generar_reporte_mensual(mes_seleccionado, año_seleccionado)

def generar_reporte_mensual(mes_nombre, año):
    """Genera el reporte mensual completo"""
    
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # CORRECCIÓN: Mapear nombres de meses en español a números
            meses_espanol = {
                "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4,
                "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8,
                "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12
            }
            
            mes_numero = meses_espanol[mes_nombre]
            
            # Fechas del periodo
            fecha_inicio = f"{año}-{mes_numero:02d}-01"
            ultimo_dia = calendar.monthrange(año, mes_numero)[1]
            fecha_fin = f"{año}-{mes_numero:02d}-{ultimo_dia}"
            
            # Obtener información del grupo
            cursor.execute("SELECT nombre_grupo FROM grupo WHERE id_grupo = %s", (id_grupo,))
            grupo_info = cursor.fetchone()
            nombre_grupo = grupo_info['nombre_grupo'] if grupo_info else "Grupo"
            
            # ENCABEZADO
            st.markdown(f"## 📋 {nombre_grupo}")
            st.markdown(f"### 📊 Reporte Mensual: {mes_nombre} {año}")
            st.markdown(f"**Fecha de generación:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            
            # 1. REUNIONES DEL MES
            st.markdown("---")
            st.subheader("📅 Reuniones del Mes")
            
            cursor.execute("""
                SELECT id_reunion, fecha, saldo_inicial, saldo_final, acuerdos
                FROM reunion 
                WHERE id_grupo = %s AND fecha BETWEEN %s AND %s
                ORDER BY fecha
            """, (id_grupo, fecha_inicio, fecha_fin))
            
            reuniones = cursor.fetchall()
            
            if reuniones:
                st.metric("🔄 Total de Reuniones", len(reuniones))
                
                # Mostrar reuniones
                for reunion in reuniones:
                    with st.expander(f"📅 Reunión {reunion['fecha']} - Saldo: ${reunion['saldo_final']:,.2f}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Saldo inicial:** ${reunion['saldo_inicial']:,.2f}")
                            st.write(f"**Saldo final:** ${reunion['saldo_final']:,.2f}")
                        with col2:
                            if reunion['acuerdos']:
                                st.write(f"**Acuerdos:** {reunion['acuerdos']}")
            else:
                st.info("No hay reuniones registradas para este periodo.")
                return
            
            # 2. RESUMEN FINANCIERO GENERAL
            st.markdown("---")
            st.subheader("💰 Resumen Financiero")
            
            # Saldo inicial (última reunión del mes anterior)
            cursor.execute("""
                SELECT saldo_final 
                FROM reunion 
                WHERE id_grupo = %s AND fecha < %s 
                ORDER BY fecha DESC 
                LIMIT 1
            """, (id_grupo, fecha_inicio))
            
            saldo_inicial_result = cursor.fetchone()
            saldo_inicial = saldo_inicial_result['saldo_final'] if saldo_inicial_result else 0
            
            # Saldo final (última reunión del mes actual)
            saldo_final = reuniones[-1]['saldo_final'] if reuniones else saldo_inicial
            
            # Total aportes del mes
            cursor.execute("""
                SELECT SUM(a.monto) as total_aportes
                FROM aporte a
                JOIN reunion r ON a.id_reunion = r.id_reunion
                WHERE r.id_grupo = %s AND r.fecha BETWEEN %s AND %s
            """, (id_grupo, fecha_inicio, fecha_fin))
            
            total_aportes_result = cursor.fetchone()
            total_aportes = total_aportes_result['total_aportes'] or 0
            
            # Total préstamos aprobados
            cursor.execute("""
                SELECT SUM(p.monto_prestado) as total_prestamos
                FROM prestamo p
                JOIN reunion r ON p.id_reunion = r.id_reunion
                WHERE r.id_grupo = %s AND r.fecha BETWEEN %s AND %s AND p.estado = 'aprobado'
            """, (id_grupo, fecha_inicio, fecha_fin))
            
            total_prestamos_result = cursor.fetchone()
            total_prestamos = total_prestamos_result['total_prestamos'] or 0
            
            # Total multas aplicadas
            cursor.execute("""
                SELECT SUM(m.monto) as total_multas
                FROM multa m
                JOIN miembrogapc mb ON m.id_miembro = mb.id_miembro
                JOIN estado e ON m.id_estado = e.id_estado
                WHERE mb.id_grupo = %s AND m.fecha_registro BETWEEN %s AND %s
            """, (id_grupo, fecha_inicio, fecha_fin))
            
            total_multas_result = cursor.fetchone()
            total_multas = total_multas_result['total_multas'] or 0
            
            # Total pagos recibidos
            cursor.execute("""
                SELECT SUM(pg.monto_capital) as total_pagos
                FROM pago pg
                JOIN reunion r ON pg.id_reunion = r.id_reunion
                WHERE r.id_grupo = %s AND r.fecha BETWEEN %s AND %s
            """, (id_grupo, fecha_inicio, fecha_fin))
            
            total_pagos_result = cursor.fetchone()
            total_pagos = total_pagos_result['total_pagos'] or 0
            
            # Mostrar métricas financieras
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("💰 Saldo Inicial", f"${saldo_inicial:,.2f}")
                st.metric("📈 Total Aportes", f"${total_aportes:,.2f}")
            with col2:
                st.metric("🏦 Total Préstamos", f"${total_prestamos:,.2f}")
                st.metric("⚖️ Total Multas", f"${total_multas:,.2f}")
            with col3:
                st.metric("💳 Total Pagos", f"${total_pagos:,.2f}")
                st.metric("💰 Saldo Final", f"${saldo_final:,.2f}")
            with col4:
                crecimiento = saldo_final - saldo_inicial
                st.metric("📊 Crecimiento Neto", f"${crecimiento:,.2f}")
            
            # 3. DESGLOSE POR TIPO DE MOVIMIENTO
            st.markdown("---")
            st.subheader("📋 Desglose Detallado")
            
            # APORTES por tipo
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 💵 Aportes por Tipo")
                cursor.execute("""
                    SELECT a.tipo, SUM(a.monto) as total
                    FROM aporte a
                    JOIN reunion r ON a.id_reunion = r.id_reunion
                    WHERE r.id_grupo = %s AND r.fecha BETWEEN %s AND %s
                    GROUP BY a.tipo
                    ORDER BY total DESC
                """, (id_grupo, fecha_inicio, fecha_fin))
                
                aportes_por_tipo = cursor.fetchall()
                
                if aportes_por_tipo:
                    for aporte in aportes_por_tipo:
                        st.write(f"**{aporte['tipo']}:** ${aporte['total']:,.2f}")
                else:
                    st.info("No hay aportes registrados")
            
            with col2:
                st.markdown("#### 👥 Asistencia")
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_asistencias,
                        SUM(CASE WHEN a.estado = 'presente' THEN 1 ELSE 0 END) as presentes,
                        SUM(CASE WHEN a.estado = 'ausente' THEN 1 ELSE 0 END) as ausentes
                    FROM asistencia a
                    JOIN reunion r ON a.id_reunion = r.id_reunion
                    WHERE r.id_grupo = %s AND r.fecha BETWEEN %s AND %s
                """, (id_grupo, fecha_inicio, fecha_fin))
                
                asistencia_result = cursor.fetchone()
                if asistencia_result and asistencia_result['total_asistencias'] > 0:
                    porcentaje_asistencia = (asistencia_result['presentes'] / asistencia_result['total_asistencias']) * 100
                    st.metric("📊 Asistencia Promedio", f"{porcentaje_asistencia:.1f}%")
                    st.write(f"**Presentes:** {asistencia_result['presentes']}")
                    st.write(f"**Ausentes:** {asistencia_result['ausentes']}")
                else:
                    st.info("No hay datos de asistencia")
            
            # PRÉSTAMOS del mes
            st.markdown("#### 🏦 Préstamos Aprobados")
            cursor.execute("""
                SELECT p.monto_prestado, p.proposito, p.plazo_meses, p.fecha_vencimiento, m.nombre
                FROM prestamo p
                JOIN miembrogapc m ON p.id_miembro = m.id_miembro
                JOIN reunion r ON p.id_reunion = r.id_reunion
                WHERE r.id_grupo = %s AND r.fecha BETWEEN %s AND %s AND p.estado = 'aprobado'
                ORDER BY p.monto_prestado DESC
            """, (id_grupo, fecha_inicio, fecha_fin))
            
            prestamos = cursor.fetchall()
            
            if prestamos:
                st.metric("📊 Cantidad de Préstamos", len(prestamos))
                for prestamo in prestamos:
                    st.write(f"**{prestamo['nombre']}** - ${prestamo['monto_prestado']:,.2f} - {prestamo['proposito']} - {prestamo['plazo_meses']} meses")
            else:
                st.info("No hay préstamos aprobados en este periodo")
            
            # MULTAS del mes
            st.markdown("#### ⚖️ Multas Aplicadas")
            cursor.execute("""
                SELECT m.motivo, m.monto, m.fecha_registro, mb.nombre, e.nombre_estado
                FROM multa m
                JOIN miembrogapc mb ON m.id_miembro = mb.id_miembro
                JOIN estado e ON m.id_estado = e.id_estado
                WHERE mb.id_grupo = %s AND m.fecha_registro BETWEEN %s AND %s
                ORDER BY m.monto DESC
            """, (id_grupo, fecha_inicio, fecha_fin))
            
            multas = cursor.fetchall()
            
            if multas:
                st.metric("📊 Cantidad de Multas", len(multas))
                for multa in multas:
                    estado_color = "✅" if multa['nombre_estado'] == 'pagado' else "⏳"
                    st.write(f"{estado_color} **{multa['nombre']}** - ${multa['monto']:,.2f} - {multa['motivo']} - {multa['nombre_estado']}")
            else:
                st.info("No hay multas aplicadas en este periodo")
            
            # 4. ESTADO DE SOCIOS
            st.markdown("---")
            st.subheader("👥 Estado de Socios")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🏆 Top 3 Mayores Ahorradores")
                cursor.execute("""
                    SELECT m.nombre, SUM(a.monto) as total_ahorro
                    FROM aporte a
                    JOIN miembrogapc m ON a.id_miembro = m.id_miembro
                    JOIN reunion r ON a.id_reunion = r.id_reunion
                    WHERE m.id_grupo = %s AND r.fecha BETWEEN %s AND %s AND a.tipo = 'Ahorro'
                    GROUP BY m.id_miembro, m.nombre
                    ORDER BY total_ahorro DESC
                    LIMIT 3
                """, (id_grupo, fecha_inicio, fecha_fin))
                
                top_ahorradores = cursor.fetchall()
                
                if top_ahorradores:
                    for i, ahorrador in enumerate(top_ahorradores, 1):
                        st.write(f"{i}. **{ahorrador['nombre']}** - ${ahorrador['total_ahorro']:,.2f}")
                else:
                    st.info("No hay datos de ahorro")
            
            with col2:
                st.markdown("#### 📊 Socios con Multas Pendientes")
                cursor.execute("""
                    SELECT m.nombre, COUNT(*) as multas_pendientes
                    FROM multa mul
                    JOIN miembrogapc m ON mul.id_miembro = m.id_miembro
                    JOIN estado e ON mul.id_estado = e.id_estado
                    WHERE m.id_grupo = %s AND e.nombre_estado IN ('activo', 'mora')
                    GROUP BY m.id_miembro, m.nombre
                    HAVING multas_pendientes > 0
                    ORDER BY multas_pendientes DESC
                    LIMIT 5
                """, (id_grupo,))
                
                multas_pendientes = cursor.fetchall()
                
                if multas_pendientes:
                    for miembro in multas_pendientes:
                        st.write(f"**{miembro['nombre']}** - {miembro['multas_pendientes']} multas pendientes")
                else:
                    st.info("No hay multas pendientes")
            
            cursor.close()
            conexion.close()
            
            # Botón para exportar (placeholder)
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("📄 Exportar a PDF", use_container_width=True):
                    st.info("🔧 Función de exportación en desarrollo...")
            
    except Exception as e:
        st.error(f"❌ Error al generar reporte: {e}")

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