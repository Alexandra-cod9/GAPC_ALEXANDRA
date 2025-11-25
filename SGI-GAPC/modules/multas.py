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

def mostrar_modulo_multas():
    """Módulo especializado de multas - Vista y gestión"""
    
    # Header del módulo con botón de volver
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# ⚖️ Módulo de Multas")
    with col2:
        if st.button("⬅️ Volver al Dashboard", use_container_width=True):
            st.session_state.modulo_actual = 'dashboard'
            st.rerun()
    
    st.markdown("---")
    
    # Menú de opciones
    opcion = st.radio(
        "Selecciona una acción:",
        ["📋 Ver Todas las Multas", "➕ Nueva Multa", "⏳ Multas Pendientes", "✅ Multas Pagadas"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if opcion == "📋 Ver Todas las Multas":
        mostrar_todas_multas()
    elif opcion == "➕ Nueva Multa":
        mostrar_nueva_multa()
    elif opcion == "⏳ Multas Pendientes":
        mostrar_multas_pendientes()
    elif opcion == "✅ Multas Pagadas":
        mostrar_multas_pagadas()

def mostrar_todas_multas():
    """Muestra todas las multas con filtros"""
    st.subheader("📋 Todas las Multas")
    
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Obtener todas las multas del grupo (ACTUALIZADO - sin estado)
            cursor.execute("""
                SELECT 
                    m.id_multa,
                    mb.nombre as miembro,
                    m.motivo,
                    m.monto,
                    m.fecha_registro
                FROM multa m
                JOIN miembrogapc mb ON m.id_miembro = mb.id_miembro
                WHERE mb.id_grupo = %s
                ORDER BY m.fecha_registro DESC
            """, (id_grupo,))
            
            multas = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if multas:
                # Filtros
                col1, col2 = st.columns(2)
                with col1:
                    miembros = ["Todos"] + list(set(m['miembro'] for m in multas))
                    miembro_filtro = st.selectbox("👤 Filtrar por miembro:", miembros)
                
                with col2:
                    # Filtro por rango de fechas
                    fecha_min = min(m['fecha_registro'] for m in multas)
                    fecha_max = max(m['fecha_registro'] for m in multas)
                    fecha_filtro = st.date_input(
                        "📅 Filtrar por fecha:",
                        value=(fecha_min, fecha_max),
                        min_value=fecha_min,
                        max_value=fecha_max
                    )
                
                # Aplicar filtros
                multas_filtradas = multas
                if miembro_filtro != "Todos":
                    multas_filtradas = [m for m in multas_filtradas if m['miembro'] == miembro_filtro]
                
                if isinstance(fecha_filtro, tuple) and len(fecha_filtro) == 2:
                    fecha_inicio, fecha_fin = fecha_filtro
                    multas_filtradas = [m for m in multas_filtradas if fecha_inicio <= m['fecha_registro'] <= fecha_fin]
                
                # Estadísticas
                total_multas = len(multas_filtradas)
                total_monto = sum(m['monto'] for m in multas_filtradas)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📊 Total Multas", total_multas)
                with col2:
                    st.metric("💰 Monto Total", f"${total_monto:,.2f}")
                
                st.markdown("---")
                
                # Mostrar multas
                for multa in multas_filtradas:
                    with st.expander(f"⚖️ #{multa['id_multa']} - {multa['miembro']} - ${multa['monto']:,.2f}", expanded=False):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**👤 Miembro:** {multa['miembro']}")
                            st.write(f"**💰 Monto:** ${multa['monto']:,.2f}")
                        
                        with col2:
                            st.write(f"**📋 Motivo:** {multa['motivo']}")
                            st.write(f"**📅 Fecha Registro:** {multa['fecha_registro']}")
                            
                            # Botón para eliminar multa
                            if st.button("🗑️ Eliminar Multa", key=f"eliminar_{multa['id_multa']}"):
                                eliminar_multa(multa['id_multa'])
                                st.rerun()
            else:
                st.info("📝 No hay multas registradas en este grupo.")
                
    except Exception as e:
        st.error(f"❌ Error al cargar multas: {e}")

def mostrar_nueva_multa():
    """Formulario para registrar nueva multa"""
    st.subheader("➕ Nueva Multa")
    
    st.info("""
    **💡 Información:**
    Al registrar una multa aquí, se afecta automáticamente el saldo del miembro:
    - Se crea la multa en el sistema
    - El miembro deberá pagar la multa
    - La multa afecta el estado financiero del miembro
    """)
    
    with st.form("form_nueva_multa"):
        # Buscar miembro - DEBE estar dentro del form
        miembro_seleccionado = buscar_miembro_multa()
        
        motivo_final = ""
        monto_multa = 0.0
        
        if miembro_seleccionado:
            st.markdown("---")
            
            # Mostrar información del miembro
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**👤 Miembro:** {miembro_seleccionado['nombre']}")
            with col2:
                st.info(f"📧 Teléfono: {miembro_seleccionado['telefono']}")
            
            # Datos de la multa
            st.subheader("📝 Datos de la Multa")
            
            col1, col2 = st.columns(2)
            
            with col1:
                motivo = st.selectbox(
                    "📋 Motivo de la multa:",
                    ["Falta a reunión", "Llegada tarde", "Incumplimiento de pago", "Otro"],
                    key="motivo_select"
                )
                
                if motivo == "Otro":
                    motivo_personalizado = st.text_input("📝 Especificar motivo:", key="motivo_otro")
                    motivo_final = motivo_personalizado if motivo_personalizado else "Otro"
                else:
                    motivo_final = motivo
            
            with col2:
                monto_multa = st.number_input(
                    "💰 Monto de la multa:",
                    min_value=0.0,
                    value=50.0,
                    step=10.0,
                    key="monto_multa"
                )
            
            # Resumen
            if monto_multa > 0:
                st.markdown("---")
                st.subheader("🧮 Resumen de la Multa")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("👤 Miembro", miembro_seleccionado['nombre'])
                
                with col2:
                    st.metric("💰 Monto", f"${monto_multa:,.2f}")
                
                st.info(f"""
                **📊 Detalles:**
                - **Motivo:** {motivo_final}
                - **Monto:** ${monto_multa:,.2f}
                - **Fecha registro:** Hoy
                """)
        
        # ✅ BOTÓN DE ENVÍO
        submitted = st.form_submit_button(
            "⚖️ Registrar Multa", 
            use_container_width=True,
            type="primary"
        )
        
        if submitted:
            if miembro_seleccionado and monto_multa > 0 and motivo_final:
                guardar_multa(miembro_seleccionado, motivo_final, monto_multa)
            else:
                st.error("❌ Completa todos los campos obligatorios: selecciona un miembro, ingresa un motivo y un monto válido")

def buscar_miembro_multa():
    """Busca y selecciona un miembro para multa - Versión modificada para forms"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Obtener todos los miembros del grupo
            cursor.execute("""
                SELECT 
                    id_miembro,
                    nombre,
                    telefono
                FROM miembrogapc 
                WHERE id_grupo = %s
                ORDER BY nombre
            """, (id_grupo,))
            
            miembros = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if miembros:
                # Crear lista de opciones
                opciones = ["Selecciona un miembro"] + [f"{m['id_miembro']} - {m['nombre']}" for m in miembros]
                
                miembro_seleccionado_opcion = st.selectbox(
                    "👤 Selecciona el miembro a multar:",
                    opciones,
                    key="selector_miembro_multa_form"
                )
                
                if miembro_seleccionado_opcion and miembro_seleccionado_opcion != "Selecciona un miembro":
                    # Extraer ID del miembro seleccionado
                    miembro_id = int(miembro_seleccionado_opcion.split(" - ")[0])
                    miembro_info = next((m for m in miembros if m['id_miembro'] == miembro_id), None)
                    return miembro_info
            else:
                st.warning("📝 No hay miembros en este grupo.")
                return None
                
    except Exception as e:
        st.error(f"❌ Error al cargar miembros: {e}")
    
    return None

def guardar_multa(miembro, motivo, monto):
    """Guarda una nueva multa en la base de datos (ACTUALIZADO - sin estado)"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            # Insertar multa (SOLO CAMPOS EXISTENTES - sin estado)
            cursor.execute("""
                INSERT INTO multa (
                    id_miembro, motivo, monto
                ) VALUES (%s, %s, %s)
            """, (
                miembro['id_miembro'],
                motivo,
                monto
            ))
            
            conexion.commit()
            cursor.close()
            conexion.close()
            
            st.success("🎉 ¡Multa registrada exitosamente!")
            st.balloons()
            
            # Mostrar resumen
            st.info(f"""
            **📋 Resumen de la Multa:**
            - **Miembro:** {miembro['nombre']}
            - **Motivo:** {motivo}
            - **Monto:** ${monto:,.2f}
            - **Fecha Registro:** {datetime.now().strftime('%Y-%m-%d')}
            """)
            
            # Limpiar el formulario
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error al registrar multa: {e}")

def mostrar_multas_pendientes():
    """Muestra todas las multas (ahora todas se consideran pendientes)"""
    st.subheader("⏳ Todas las Multas")
    
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Obtener todas las multas (ACTUALIZADO - sin estado)
            cursor.execute("""
                SELECT 
                    m.id_multa,
                    mb.nombre as miembro,
                    m.motivo,
                    m.monto,
                    m.fecha_registro
                FROM multa m
                JOIN miembrogapc mb ON m.id_miembro = mb.id_miembro
                WHERE mb.id_grupo = %s
                ORDER BY m.fecha_registro DESC
            """, (id_grupo,))
            
            multas = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if multas:
                # Estadísticas
                total_multas = len(multas)
                total_monto = sum(m['monto'] for m in multas)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📊 Total Multas", total_multas)
                with col2:
                    st.metric("💰 Total Pendiente", f"${total_monto:,.2f}")
                
                st.markdown("---")
                
                for multa in multas:
                    with st.expander(f"⚖️ {multa['miembro']} - ${multa['monto']:,.2f}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**👤 Miembro:** {multa['miembro']}")
                            st.write(f"**💰 Monto:** ${multa['monto']:,.2f}")
                        with col2:
                            st.write(f"**📋 Motivo:** {multa['motivo']}")
                            st.write(f"**📅 Fecha Registro:** {multa['fecha_registro']}")
                        
                        # Botón para eliminar multa
                        if st.button("🗑️ Eliminar Multa", key=f"eliminar_pend_{multa['id_multa']}"):
                            eliminar_multa(multa['id_multa'])
                            st.rerun()
            else:
                st.success("✅ No hay multas registradas en este momento.")
                
    except Exception as e:
        st.error(f"❌ Error al cargar multas: {e}")

def mostrar_multas_pagadas():
    """Como ya no hay estado, esta función muestra un mensaje informativo"""
    st.subheader("✅ Gestión de Pagos de Multas")
    
    st.info("""
    **📝 Información:**
    Con la nueva estructura de la tabla multas, todas las multas se consideran activas.
    Para registrar el pago de una multa, puedes:
    
    1. **Eliminar la multa** si ha sido pagada (desde la vista principal)
    2. **Registrar un pago** en el módulo de reuniones como "PagoMulta"
    3. **Llevar un control manual** de qué multas han sido pagadas
    
    **💡 Sugerencia:** Puedes usar el módulo de reuniones para registrar los pagos de multas.
    """)
    
    # Mostrar estadísticas generales
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Obtener estadísticas de multas
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_multas,
                    SUM(m.monto) as total_monto
                FROM multa m
                JOIN miembrogapc mb ON m.id_miembro = mb.id_miembro
                WHERE mb.id_grupo = %s
            """, (id_grupo,))
            
            stats = cursor.fetchone()
            cursor.close()
            conexion.close()
            
            if stats:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📊 Total Multas Activas", stats['total_multas'])
                with col2:
                    st.metric("💰 Monto Total", f"${stats['total_monto'] or 0:,.2f}")
                
    except Exception as e:
        st.error(f"❌ Error al cargar estadísticas: {e}")

def eliminar_multa(id_multa):
    """Elimina una multa de la base de datos"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            # Eliminar multa
            cursor.execute("DELETE FROM multa WHERE id_multa = %s", (id_multa,))
            
            conexion.commit()
            cursor.close()
            conexion.close()
            
            st.success("✅ Multa eliminada exitosamente")
            
    except Exception as e:
        st.error(f"❌ Error al eliminar multa: {e}")

# Eliminé la función marcar_multa_pagada() ya que no es necesaria con la nueva estructura