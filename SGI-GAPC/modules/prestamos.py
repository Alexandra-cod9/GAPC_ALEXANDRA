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
        # Buscar miembro - DEBE estar dentro del form
        miembro_seleccionado = buscar_miembro_prestamo()
        
        monto_prestamo = 0.0
        plazo_meses = 6
        proposito = ""
        fecha_solicitud = datetime.now()
        fecha_vencimiento = datetime.now()
        maximo_permitido = 0.0
        
        if miembro_seleccionado:
            st.markdown("---")
            
            # Calcular máximo permitido
            maximo_permitido = miembro_seleccionado['ahorro_actual'] * 0.8  # 80% del ahorro
            
            # Mostrar información del miembro
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**👤 Miembro:** {miembro_seleccionado['nombre']}")
            with col2:
                st.info(f"**💰 Ahorro Actual:** ${miembro_seleccionado['ahorro_actual']:,.2f}")
            with col3:
                st.info(f"**📈 Máximo Recomendado:** ${maximo_permitido:,.2f}")
            
            # Verificar si el miembro puede solicitar préstamo
            if miembro_seleccionado.get('prestamos_activos', 0) > 0:
                st.error("❌ Este miembro ya tiene un préstamo activo y no puede solicitar otro.")
            elif miembro_seleccionado['ahorro_actual'] <= 0:
                st.error("❌ Este miembro no tiene ahorro suficiente para solicitar un préstamo.")
            else:
                # Solo mostrar el formulario si el miembro es válido
                st.subheader("📝 Datos del Préstamo")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    monto_prestamo = st.number_input(
                        "💵 Monto a solicitar:",
                        min_value=0.0,
                        max_value=float(maximo_permitido),
                        value=0.0,
                        step=100.0,
                        help=f"Máximo recomendado: ${maximo_permitido:,.2f}",
                        key="monto_prestamo"
                    )
                    
                    plazo_meses = st.number_input(
                        "📅 Plazo en meses:",
                        min_value=1,
                        max_value=24,
                        value=6,
                        step=1,
                        help="Número de meses para pagar",
                        key="plazo_meses"
                    )
                
                with col2:
                    proposito = st.text_area(
                        "📋 Motivo del préstamo:",
                        placeholder="Describe para qué necesitas el préstamo...",
                        height=100,
                        key="proposito_prestamo"
                    )
                    
                    fecha_solicitud = st.date_input(
                        "📅 Fecha de solicitud:",
                        value=datetime.now(),
                        key="fecha_solicitud"
                    )
                
                # Calcular detalles si hay monto
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
        
        # ✅ BOTÓN DE ENVÍO - SIEMPRE dentro del form y SIEMPRE habilitado
        submitted = st.form_submit_button(
            "✅ Aprobar Préstamo", 
            use_container_width=True,
            type="primary"
        )
    
    # Procesar FUERA del form cuando se envía
    if submitted:
        # Validaciones
        if not miembro_seleccionado:
            st.error("❌ Debes seleccionar un miembro")
        elif miembro_seleccionado.get('prestamos_activos', 0) > 0:
            st.error("❌ Este miembro ya tiene un préstamo activo")
        elif miembro_seleccionado['ahorro_actual'] <= 0:
            st.error("❌ Este miembro no tiene ahorro suficiente")
        elif monto_prestamo <= 0:
            st.error("❌ El monto del préstamo debe ser mayor a 0")
        elif not proposito:
            st.error("❌ Debes especificar el motivo del préstamo")
        elif monto_prestamo > maximo_permitido:
            st.error(f"❌ El monto excede el máximo permitido (${maximo_permitido:,.2f})")
        else:
            # Todo validado correctamente, guardar préstamo
            fecha_vencimiento = fecha_solicitud + relativedelta(months=plazo_meses)
            guardar_prestamo_individual(
                miembro_seleccionado, 
                monto_prestamo, 
                plazo_meses, 
                proposito, 
                fecha_solicitud,
                fecha_vencimiento
            )


def buscar_miembro_prestamo():
    """Busca y selecciona un miembro para préstamo - Versión modificada para forms"""
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
                
                for miembro in miembros:
                    if miembro['prestamos_activos'] > 0:
                        opciones.append(f"{miembro['id_miembro']} - {miembro['nombre']} (Ya tiene préstamo activo)")
                    elif miembro['ahorro_actual'] <= 0:
                        opciones.append(f"{miembro['id_miembro']} - {miembro['nombre']} (Sin ahorro suficiente)")
                    else:
                        opciones.append(f"{miembro['id_miembro']} - {miembro['nombre']} (Ahorro: ${miembro['ahorro_actual']:,.2f})")
                
                miembro_seleccionado_opcion = st.selectbox(
                    "👤 Selecciona el miembro solicitante:",
                    opciones,
                    key="selector_miembro_prestamo_form"
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


def guardar_prestamo_individual(miembro, monto, plazo_meses, proposito, fecha_solicitud, fecha_vencimiento):
    """Guarda un préstamo individual fuera de reunión"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            # Insertar préstamo
            cursor.execute("""
                INSERT INTO prestamo (
                    id_miembro, id_reunion, monto_prestado, proposito,
                    fecha_solicitud, fecha_vencimiento, plazo_meses, estado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                miembro['id_miembro'],
                1,  # Usar un id_reunion por defecto
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
            
            # Limpiar el formulario
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error al guardar préstamo: {e}")
