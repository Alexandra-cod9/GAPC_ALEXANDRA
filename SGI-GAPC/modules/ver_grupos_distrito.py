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

def mostrar_grupos_por_distrito():
    """Muestra los grupos filtrados por distrito"""
    
    st.markdown("# 📊 Grupos por Distrito")
    st.markdown("---")
    
    # Paso 1: Seleccionar distrito
    distrito_seleccionado = seleccionar_distrito()
    
    if not distrito_seleccionado:
        st.info("👆 Selecciona un distrito para ver sus grupos")
        return
    
    # Mostrar información del distrito seleccionado
    st.success(f"""
    📍 **Distrito Seleccionado:**
    - **Distrito:** {distrito_seleccionado['nombre_distrito']}
    - **Municipio:** {distrito_seleccionado['nombre_municipio']}
    - **Departamento:** {distrito_seleccionado['nombre_departamento']}
    - **Cantidad de grupos:** {distrito_seleccionado['cantidad_grupos']}
    """)
    
    st.markdown("---")
    
    # Paso 2: Obtener y mostrar grupos del distrito
    grupos = obtener_grupos_distrito(distrito_seleccionado['id_distrito'])
    
    if not grupos:
        st.warning("⚠️ No hay grupos registrados en este distrito todavía.")
        return
    
    st.subheader(f"🏘️ Grupos en {distrito_seleccionado['nombre_distrito']} ({len(grupos)} grupos)")
    
    # Mostrar grupos en tarjetas
    for i in range(0, len(grupos), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(grupos):
                grupo = grupos[i + j]
                with col:
                    mostrar_tarjeta_grupo(grupo)
    
    st.markdown("---")
    
    # Verificar si hay un grupo seleccionado
    if 'grupo_seleccionado_id' in st.session_state and st.session_state.grupo_seleccionado_id:
        mostrar_reporte_grupo(st.session_state.grupo_seleccionado_id)

def seleccionar_distrito():
    """Permite seleccionar un distrito de la lista completa"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            # Obtener todos los distritos
            cursor.execute("""
                SELECT 
                    d.id_distrito,
                    d.nombre_distrito,
                    d.cantidad_grupos,
                    m.nombre_municipio,
                    dep.nombre_departamento
                FROM distrito d
                JOIN municipio m ON d.id_municipio = m.id_municipio
                JOIN departamento dep ON m.id_departamento = dep.id_departamento
                ORDER BY dep.nombre_departamento, m.nombre_municipio, d.nombre_distrito
            """)
            
            distritos = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if distritos:
                # Crear opciones para el selectbox
                opciones = ["-- Selecciona un distrito --"] + [
                    f"{d['nombre_distrito']} - {d['nombre_municipio']}, {d['nombre_departamento']} ({d['cantidad_grupos']} grupos)"
                    for d in distritos
                ]
                
                seleccion = st.selectbox(
                    "📍 Selecciona el distrito:",
                    opciones,
                    key="distrito_seleccionado"
                )
                
                if seleccion != "-- Selecciona un distrito --":
                    # Encontrar el distrito seleccionado
                    indice = opciones.index(seleccion) - 1  # -1 porque agregamos un elemento inicial
                    return distritos[indice]
    
    except Exception as e:
        st.error(f"❌ Error al cargar distritos: {e}")
    
    return None

def obtener_grupos_distrito(id_distrito):
    """Obtiene todos los grupos de un distrito específico"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            cursor.execute("""
                SELECT 
                    g.id_grupo,
                    g.nombre_grupo,
                    g.nombre_comunidad,
                    g.fecha_formacion,
                    g.frecuencia_reuniones,
                    g.tasa_interes_mensual,
                    COUNT(DISTINCT m.id_miembro) as total_miembros
                FROM grupo g
                LEFT JOIN miembrogapc m ON g.id_grupo = m.id_grupo
                WHERE g.id_distrito = %s
                GROUP BY g.id_grupo, g.nombre_grupo, g.nombre_comunidad, 
                         g.fecha_formacion, g.frecuencia_reuniones, g.tasa_interes_mensual
                ORDER BY g.nombre_grupo
            """, (id_distrito,))
            
            grupos = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            return grupos
    
    except Exception as e:
        st.error(f"❌ Error al obtener grupos: {e}")
    
    return []

def mostrar_tarjeta_grupo(grupo):
    """Muestra una tarjeta con información básica del grupo"""
    
    # Calcular antigüedad
    fecha_formacion = grupo['fecha_formacion']
    if isinstance(fecha_formacion, str):
        fecha_formacion = datetime.strptime(fecha_formacion, '%Y-%m-%d').date()
    
    antiguedad = (datetime.now().date() - fecha_formacion).days
    anos = antiguedad // 365
    meses = (antiguedad % 365) // 30
    
    with st.container():
        st.markdown(f"""
        <div style="
            border: 2px solid #4CAF50;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: #f9f9f9;
        ">
            <h3 style="color: #4CAF50; margin-top: 0;">🏘️ {grupo['nombre_grupo']}</h3>
            <p><strong>📍 Comunidad:</strong> {grupo['nombre_comunidad']}</p>
            <p><strong>👥 Miembros:</strong> {grupo['total_miembros']}</p>
            <p><strong>📅 Formación:</strong> {fecha_formacion.strftime('%d/%m/%Y')}</p>
            <p><strong>⏰ Antigüedad:</strong> {anos} año(s) y {meses} mes(es)</p>
            <p><strong>🔄 Reuniones:</strong> {grupo['frecuencia_reuniones'].capitalize()}</p>
            <p><strong>💰 Tasa de interés:</strong> {grupo['tasa_interes_mensual']}% mensual</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(
            f"📊 Ver Reporte Detallado",
            key=f"btn_grupo_{grupo['id_grupo']}",
            use_container_width=True,
            type="primary"
        ):
            st.session_state.grupo_seleccionado_id = grupo['id_grupo']
            st.rerun()

def mostrar_reporte_grupo(id_grupo):
    """Muestra el reporte completo de un grupo específico"""
    
    st.markdown("---")
    st.markdown("# 📋 Reporte Individual del Grupo")
    
    # Obtener datos completos del grupo
    datos_grupo = obtener_datos_completos_grupo(id_grupo)
    
    if not datos_grupo:
        st.error("❌ No se pudo cargar la información del grupo")
        return
    
    # Botón para volver
    if st.button("⬅️ Volver a la lista de grupos"):
        st.session_state.grupo_seleccionado_id = None
        st.rerun()
    
    st.markdown("---")
    
    # Encabezado del grupo
    st.markdown(f"## 🏘️ {datos_grupo['info_basica']['nombre_grupo']}")
    st.markdown(f"**📍 Comunidad:** {datos_grupo['info_basica']['nombre_comunidad']}")
    
    # Métricas principales en columnas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "👥 Miembros Totales",
            datos_grupo['estadisticas']['total_miembros']
        )
    
    with col2:
        st.metric(
            "💰 Ahorro Total",
            f"${datos_grupo['estadisticas']['ahorro_total']:,.2f}"
        )
    
    with col3:
        st.metric(
            "💳 Préstamos Activos",
            datos_grupo['estadisticas']['prestamos_activos']
        )
    
    with col4:
        st.metric(
            "📅 Reuniones Realizadas",
            datos_grupo['estadisticas']['reuniones_realizadas']
        )
    
    st.markdown("---")
    
    # Tabs para organizar la información
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Información General",
        "👥 Miembros",
        "💰 Aportes y Ahorros",
        "💳 Préstamos",
        "📅 Historial de Reuniones"
    ])
    
    with tab1:
        mostrar_informacion_general(datos_grupo)
    
    with tab2:
        mostrar_miembros(datos_grupo)
    
    with tab3:
        mostrar_aportes_ahorros(id_grupo)
    
    with tab4:
        mostrar_prestamos(id_grupo)
    
    with tab5:
        mostrar_historial_reuniones(id_grupo)

def obtener_datos_completos_grupo(id_grupo):
    """Obtiene todos los datos relevantes de un grupo"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            # Información básica del grupo
            cursor.execute("""
                SELECT 
                    g.*,
                    d.nombre_distrito,
                    m.nombre_municipio,
                    dep.nombre_departamento,
                    r.texto_reglamento,
                    r.tipo_multa,
                    r.reglas_prestamo
                FROM grupo g
                LEFT JOIN distrito d ON g.id_distrito = d.id_distrito
                LEFT JOIN municipio m ON d.id_municipio = m.id_municipio
                LEFT JOIN departamento dep ON m.id_departamento = dep.id_departamento
                LEFT JOIN reglamento r ON g.id_reglamento = r.id_reglamento
                WHERE g.id_grupo = %s
            """, (id_grupo,))
            
            info_basica = cursor.fetchone()
            
            # Estadísticas del grupo
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT mg.id_miembro) as total_miembros,
                    COALESCE(SUM(CASE WHEN a.tipo = 'Ahorro' THEN a.monto ELSE 0 END), 0) as ahorro_total,
                    COUNT(DISTINCT CASE WHEN p.estado = 'aprobado' THEN p.id_prestamo END) as prestamos_activos,
                    COUNT(DISTINCT re.id_reunion) as reuniones_realizadas
                FROM grupo g
                LEFT JOIN miembrogapc mg ON g.id_grupo = mg.id_grupo
                LEFT JOIN aporte a ON mg.id_miembro = a.id_miembro
                LEFT JOIN prestamo p ON mg.id_miembro = p.id_miembro
                LEFT JOIN reunion re ON g.id_grupo = re.id_grupo
                WHERE g.id_grupo = %s
            """, (id_grupo,))
            
            estadisticas = cursor.fetchone()
            
            # Lista de miembros con roles
            cursor.execute("""
                SELECT 
                    mg.id_miembro,
                    mg.nombre,
                    mg.telefono,
                    mg.dui,
                    mg.correo,
                    r.tipo_rol,
                    COALESCE(SUM(CASE WHEN a.tipo = 'Ahorro' THEN a.monto ELSE 0 END), 0) as ahorro_individual
                FROM miembrogapc mg
                LEFT JOIN rol r ON mg.id_rol = r.id_rol
                LEFT JOIN aporte a ON mg.id_miembro = a.id_miembro
                WHERE mg.id_grupo = %s
                GROUP BY mg.id_miembro, mg.nombre, mg.telefono, mg.dui, mg.correo, r.tipo_rol
                ORDER BY r.tipo_rol, mg.nombre
            """, (id_grupo,))
            
            miembros = cursor.fetchall()
            
            cursor.close()
            conexion.close()
            
            return {
                'info_basica': info_basica,
                'estadisticas': estadisticas,
                'miembros': miembros
            }
    
    except Exception as e:
        st.error(f"❌ Error al obtener datos del grupo: {e}")
    
    return None

def mostrar_informacion_general(datos_grupo):
    """Muestra la información general del grupo"""
    info = datos_grupo['info_basica']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Datos del Grupo")
        st.write(f"**🏷️ Nombre:** {info['nombre_grupo']}")
        st.write(f"**🏘️ Comunidad:** {info['nombre_comunidad']}")
        st.write(f"**📍 Ubicación:** {info['nombre_distrito']}, {info['nombre_municipio']}, {info['nombre_departamento']}")
        st.write(f"**📅 Fecha de Formación:** {info['fecha_formacion'].strftime('%d/%m/%Y')}")
        st.write(f"**🔄 Frecuencia de Reuniones:** {info['frecuencia_reuniones'].capitalize()}")
    
    with col2:
        st.markdown("### 💰 Configuración Financiera")
        st.write(f"**💵 Tasa de Interés Mensual:** {info['tasa_interes_mensual']}%")
        st.write(f"**📊 Método de Reparto:** {info['metodo_reparto_utilidades'].capitalize()}")
        
    if info.get('meta_social'):
        st.markdown("### 🎯 Meta Social")
        st.info(info['meta_social'])
    
    # Reglamento
    if info.get('texto_reglamento') or info.get('tipo_multa') or info.get('reglas_prestamo'):
        st.markdown("---")
        st.markdown("### 📜 Reglamento")
        
        if info.get('texto_reglamento'):
            with st.expander("📋 Texto del Reglamento"):
                st.write(info['texto_reglamento'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            if info.get('tipo_multa'):
                with st.expander("⚠️ Tipos de Multas"):
                    st.write(info['tipo_multa'])
        
        with col2:
            if info.get('reglas_prestamo'):
                with st.expander("💳 Reglas de Préstamos"):
                    st.write(info['reglas_prestamo'])

def mostrar_miembros(datos_grupo):
    """Muestra la lista de miembros del grupo"""
    st.markdown("### 👥 Miembros del Grupo")
    
    miembros = datos_grupo['miembros']
    
    if not miembros:
        st.warning("⚠️ Este grupo aún no tiene miembros registrados")
        return
    
    # Tabla de miembros
    st.dataframe(
        [{
            "Nombre": m['nombre'],
            "Rol": m['tipo_rol'],
            "DUI": m['dui'],
            "Teléfono": m['telefono'],
            "Ahorro Individual": f"${m['ahorro_individual']:,.2f}",
            "Correo": m['correo'] if m['correo'] else "No registrado"
        } for m in miembros],
        use_container_width=True,
        hide_index=True
    )

def mostrar_aportes_ahorros(id_grupo):
    """Muestra el detalle de aportes y ahorros"""
    st.markdown("### 💰 Detalle de Aportes y Ahorros")
    
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            # Obtener aportes por tipo
            cursor.execute("""
                SELECT 
                    a.tipo,
                    COUNT(*) as cantidad,
                    SUM(a.monto) as total
                FROM aporte a
                JOIN miembrogapc mg ON a.id_miembro = mg.id_miembro
                WHERE mg.id_grupo = %s
                GROUP BY a.tipo
                ORDER BY total DESC
            """, (id_grupo,))
            
            aportes_tipo = cursor.fetchall()
            
            if aportes_tipo:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📊 Resumen por Tipo de Aporte")
                    for aporte in aportes_tipo:
                        st.metric(
                            f"{aporte['tipo']}",
                            f"${aporte['total']:,.2f}",
                            f"{aporte['cantidad']} aportes"
                        )
                
                with col2:
                    # Top 5 ahorradores
                    cursor.execute("""
                        SELECT 
                            mg.nombre,
                            SUM(a.monto) as total_aportado
                        FROM aporte a
                        JOIN miembrogapc mg ON a.id_miembro = mg.id_miembro
                        WHERE mg.id_grupo = %s
                        GROUP BY mg.id_miembro, mg.nombre
                        ORDER BY total_aportado DESC
                        LIMIT 5
                    """, (id_grupo,))
                    
                    top_ahorradores = cursor.fetchall()
                    
                    if top_ahorradores:
                        st.markdown("#### 🏆 Top 5 Ahorradores")
                        for i, ahorro in enumerate(top_ahorradores, 1):
                            st.write(f"{i}. **{ahorro['nombre']}** - ${ahorro['total_aportado']:,.2f}")
            else:
                st.info("📝 Aún no hay aportes registrados en este grupo")
            
            cursor.close()
            conexion.close()
    
    except Exception as e:
        st.error(f"❌ Error al cargar aportes: {e}")

def mostrar_prestamos(id_grupo):
    """Muestra el historial de préstamos"""
    st.markdown("### 💳 Historial de Préstamos")
    
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            cursor.execute("""
                SELECT 
                    mg.nombre,
                    p.fecha_solicitud,
                    p.monto_prestado,
                    p.proposito,
                    p.plazo_meses,
                    p.fecha_vencimiento,
                    p.estado
                FROM prestamo p
                JOIN miembrogapc mg ON p.id_miembro = mg.id_miembro
                WHERE mg.id_grupo = %s
                ORDER BY p.fecha_solicitud DESC
            """, (id_grupo,))
            
            prestamos = cursor.fetchall()
            
            if prestamos:
                st.dataframe(
                    [{
                        "Miembro": p['nombre'],
                        "Fecha Solicitud": p['fecha_solicitud'].strftime('%d/%m/%Y'),
                        "Monto": f"${p['monto_prestado']:,.2f}",
                        "Propósito": p['proposito'],
                        "Plazo": f"{p['plazo_meses']} meses",
                        "Vencimiento": p['fecha_vencimiento'].strftime('%d/%m/%Y'),
                        "Estado": "✅ Aprobado" if p['estado'] == 'aprobado' else "❌ Rechazado"
                    } for p in prestamos],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("📝 No hay préstamos registrados en este grupo")
            
            cursor.close()
            conexion.close()
    
    except Exception as e:
        st.error(f"❌ Error al cargar préstamos: {e}")

def mostrar_historial_reuniones(id_grupo):
    """Muestra el historial de reuniones"""
    st.markdown("### 📅 Historial de Reuniones")
    
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            cursor.execute("""
                SELECT 
                    fecha,
                    hora,
                    saldo_inicial,
                    saldo_final,
                    acuerdos,
                    observaciones
                FROM reunion
                WHERE id_grupo = %s
                ORDER BY fecha DESC, hora DESC
                LIMIT 10
            """, (id_grupo,))
            
            reuniones = cursor.fetchall()
            
            if reuniones:
                for reunion in reuniones:
                    with st.expander(f"📅 Reunión del {reunion['fecha'].strftime('%d/%m/%Y')} - {reunion['hora']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**💰 Saldo Inicial:** ${reunion['saldo_inicial']:,.2f}")
                            st.write(f"**💵 Saldo Final:** ${reunion['saldo_final']:,.2f}")
                        
                        with col2:
                            diferencia = reunion['saldo_final'] - reunion['saldo_inicial']
                            st.metric("Cambio en el Saldo", f"${diferencia:,.2f}")
                        
                        if reunion.get('acuerdos'):
                            st.markdown("**📝 Acuerdos:**")
                            st.write(reunion['acuerdos'])
                        
                        if reunion.get('observaciones'):
                            st.markdown("**💭 Observaciones:**")
                            st.write(reunion['observaciones'])
            else:
                st.info("📝 No hay reuniones registradas para este grupo")
            
            cursor.close()
            conexion.close()
    
    except Exception as e:
        st.error(f"❌ Error al cargar reuniones: {e}")