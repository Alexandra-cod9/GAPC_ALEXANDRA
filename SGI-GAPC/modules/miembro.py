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

def mostrar_modulo_miembros():
    """Módulo de gestión de miembros - Versión simplificada"""
    
    # Header del módulo con botón de volver
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# 👥 Módulo de Miembros")
    with col2:
        if st.button("⬅️ Volver", use_container_width=True):
            st.session_state.modulo_actual = 'dashboard'
            st.rerun()
    
    st.markdown("---")
    
    # Menú de opciones
    opcion = st.radio(
        "Selecciona una acción:",
        ["📋 Lista de Miembros", "➕ Agregar Miembro", "🔍 Buscar Miembro"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if opcion == "📋 Lista de Miembros":
        mostrar_lista_miembros()
    elif opcion == "➕ Agregar Miembro":
        mostrar_formulario_nuevo_miembro()
    elif opcion == "🔍 Buscar Miembro":
        mostrar_busqueda_miembro()

def mostrar_lista_miembros():
    """Muestra la lista simple de todos los miembros"""
    st.subheader("📋 Lista de Miembros del Grupo")
    
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Consulta simple sin cálculos financieros
            cursor.execute("""
                SELECT 
                    m.id_miembro,
                    m.nombre,
                    m.telefono,
                    m.dui,
                    m.correo,
                    r.tipo_rol
                FROM miembrogapc m
                JOIN rol r ON m.id_rol = r.id_rol
                WHERE m.id_grupo = %s
                ORDER BY 
                    CASE 
                        WHEN r.tipo_rol = 'Presidente' THEN 1
                        WHEN r.tipo_rol = 'Secretaria' THEN 2
                        WHEN r.tipo_rol = 'Tesorera' THEN 3
                        WHEN r.tipo_rol = 'Promotora' THEN 4
                        ELSE 5
                    END,
                    m.nombre
            """, (id_grupo,))
            
            miembros = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if miembros:
                # Mostrar estadísticas básicas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Miembros", len(miembros))
                with col2:
                    directiva = len([m for m in miembros if m['tipo_rol'] in ['Presidente', 'Secretaria', 'Tesorera']])
                    st.metric("Directiva", directiva)
                with col3:
                    socios = len([m for m in miembros if m['tipo_rol'] == 'socio'])
                    st.metric("Socios", socios)
                with col4:
                    otros = len([m for m in miembros if m['tipo_rol'] in ['llave', 'Institucion', 'Promotora']])
                    st.metric("Otros Roles", otros)
                
                st.markdown("---")
                
                # Mostrar tabla de miembros simple
                for miembro in miembros:
                    with st.expander(f"👤 {miembro['nombre']} - {miembro['tipo_rol']}", expanded=False):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"**📞 Teléfono:** {miembro['telefono']}")
                            st.write(f"**🆔 DUI:** {miembro['dui']}")
                            if miembro['correo']:
                                st.write(f"**📧 Correo:** {miembro['correo']}")
                        
                        with col2:
                            # Botones para ver información detallada en otros módulos
                            if st.button("💰 Aportes", key=f"aportes_{miembro['id_miembro']}", use_container_width=True):
                                st.session_state.miembro_detalle_id = miembro['id_miembro']
                                st.session_state.modulo_actual = 'aportes'
                                st.rerun()
                            
                            if st.button("💳 Préstamos", key=f"prestamos_{miembro['id_miembro']}", use_container_width=True):
                                st.session_state.miembro_detalle_id = miembro['id_miembro']
                                st.session_state.modulo_actual = 'prestamos'
                                st.rerun()
                        
                        with col3:
                            if st.button("⚠️ Multas", key=f"multas_{miembro['id_miembro']}", use_container_width=True):
                                st.session_state.miembro_detalle_id = miembro['id_miembro']
                                st.session_state.modulo_actual = 'multas'
                                st.rerun()
                            
                            # Botones de acción
                            col_edit, col_del = st.columns(2)
                            with col_edit:
                                if st.button("✏️", key=f"edit_{miembro['id_miembro']}"):
                                    st.session_state.editar_miembro_id = miembro['id_miembro']
                                    st.rerun()
                            with col_del:
                                if st.button("🗑️", key=f"del_{miembro['id_miembro']}"):
                                    st.session_state.eliminar_miembro_id = miembro['id_miembro']
                                    st.rerun()
            else:
                st.info("📝 No hay miembros registrados en este grupo. ¡Agrega el primero!")
                
    except Exception as e:
        st.error(f"❌ Error al cargar miembros: {e}")

def mostrar_formulario_nuevo_miembro():
    """Muestra el formulario para añadir nuevo miembro"""
    st.subheader("➕ Agregar Nuevo Miembro")
    
    with st.form("form_nuevo_miembro"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre = st.text_input("👤 Nombre Completo *", placeholder="Ej: Juan Pérez García")
            telefono = st.text_input("📞 Teléfono *", placeholder="Ej: 1234-5678")
            dui = st.text_input("🆔 DUI *", placeholder="Ej: 12345678-9")
        
        with col2:
            # Obtener roles disponibles
            roles = obtener_roles()
            rol_seleccionado = st.selectbox("🎭 Rol *", roles)
            
            correo = st.text_input("📧 Correo Electrónico", placeholder="usuario@ejemplo.com")
            contrasena = st.text_input("🔒 Contraseña", type="password", placeholder="••••••••")
        
        # Validaciones para roles que requieren correo y contraseña
        if rol_seleccionado in ['Secretaria', 'Presidente']:
            if not correo:
                st.warning("⚠️ Los roles de Secretaria y Presidente requieren correo electrónico")
            if not contrasena:
                st.warning("⚠️ Los roles de Secretaria y Presidente requieren contraseña")
        
        st.markdown("**\* Campos obligatorios**")
        
        submitted = st.form_submit_button("💾 Guardar Miembro", use_container_width=True)
        
        if submitted:
            if not nombre or not telefono or not dui:
                st.error("❌ Por favor completa todos los campos obligatorios")
            elif rol_seleccionado in ['Secretaria', 'Presidente'] and (not correo or not contrasena):
                st.error("❌ Los roles de Secretaria y Presidente requieren correo y contraseña")
            else:
                guardar_nuevo_miembro(nombre, telefono, dui, rol_seleccionado, correo, contrasena)

def obtener_roles():
    """Obtiene la lista de roles disponibles"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            cursor.execute("SELECT tipo_rol FROM rol ORDER BY tipo_rol")
            roles = [fila['tipo_rol'] for fila in cursor.fetchall()]
            cursor.close()
            conexion.close()
            return roles
    except Exception as e:
        st.error(f"Error al cargar roles: {e}")
    
    return ['socio', 'Presidente', 'Secretaria', 'Tesorera', 'llave', 'Institucion', 'Promotora']

def guardar_nuevo_miembro(nombre, telefono, dui, rol, correo, contrasena):
    """Guarda un nuevo miembro en la base de datos"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            # Obtener id_rol
            cursor.execute("SELECT id_rol FROM rol WHERE tipo_rol = %s", (rol,))
            rol_data = cursor.fetchone()
            
            if rol_data:
                id_rol = rol_data['id_rol']
                id_grupo = st.session_state.usuario.get('id_grupo', 1)
                
                # Insertar nuevo miembro
                cursor.execute("""
                    INSERT INTO miembrogapc 
                    (nombre, telefono, dui, correo, contrasena, id_grupo, id_rol) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (nombre, telefono, dui, correo if correo else None, contrasena if contrasena else None, id_grupo, id_rol))
                
                conexion.commit()
                cursor.close()
                conexion.close()
                
                st.success(f"✅ Miembro {nombre} agregado exitosamente!")
                st.balloons()
            else:
                st.error("❌ Error: Rol no encontrado")
                
    except pymysql.IntegrityError as e:
        if 'dui' in str(e).lower():
            st.error("❌ Error: Ya existe un miembro con este DUI")
        elif 'correo' in str(e).lower():
            st.error("❌ Error: Ya existe un miembro con este correo")
        else:
            st.error(f"❌ Error de base de datos: {e}")
    except Exception as e:
        st.error(f"❌ Error al guardar miembro: {e}")

def mostrar_busqueda_miembro():
    """Muestra la funcionalidad de búsqueda de miembros"""
    st.subheader("🔍 Buscar Miembro")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        termino_busqueda = st.text_input("🔎 Buscar por nombre, teléfono o DUI:", placeholder="Ingresa término de búsqueda...")
    
    with col2:
        st.write("")  # Espacio para alinear
        if st.button("🔍 Buscar", use_container_width=True):
            if termino_busqueda:
                buscar_miembros(termino_busqueda)
            else:
                st.warning("⚠️ Ingresa un término de búsqueda")

def buscar_miembros(termino):
    """Busca miembros según el término proporcionado"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            termino_like = f"%{termino}%"
            
            cursor.execute("""
                SELECT 
                    m.id_miembro,
                    m.nombre,
                    m.telefono,
                    m.dui,
                    m.correo,
                    r.tipo_rol
                FROM miembrogapc m
                JOIN rol r ON m.id_rol = r.id_rol
                WHERE m.id_grupo = %s AND (
                    m.nombre LIKE %s OR 
                    m.telefono LIKE %s OR 
                    m.dui LIKE %s OR
                    m.correo LIKE %s
                )
                ORDER BY m.nombre
            """, (id_grupo, termino_like, termino_like, termino_like, termino_like))
            
            resultados = cursor.fetchall()
            cursor.close()
            conexion.close()
            
            if resultados:
                st.success(f"🔍 Se encontraron {len(resultados)} resultado(s)")
                
                for miembro in resultados:
                    with st.expander(f"👤 {miembro['nombre']} - {miembro['tipo_rol']}", expanded=False):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"**📞 Teléfono:** {miembro['telefono']}")
                            st.write(f"**🆔 DUI:** {miembro['dui']}")
                            if miembro['correo']:
                                st.write(f"**📧 Correo:** {miembro['correo']}")
                        
                        with col2:
                            # Botones para ver información detallada
                            if st.button("💰 Aportes", key=f"aportes_search_{miembro['id_miembro']}", use_container_width=True):
                                st.session_state.miembro_detalle_id = miembro['id_miembro']
                                st.session_state.modulo_actual = 'aportes'
                                st.rerun()
                            
                            if st.button("💳 Préstamos", key=f"prestamos_search_{miembro['id_miembro']}", use_container_width=True):
                                st.session_state.miembro_detalle_id = miembro['id_miembro']
                                st.session_state.modulo_actual = 'prestamos'
                                st.rerun()
                        
                        with col3:
                            if st.button("⚠️ Multas", key=f"multas_search_{miembro['id_miembro']}", use_container_width=True):
                                st.session_state.miembro_detalle_id = miembro['id_miembro']
                                st.session_state.modulo_actual = 'multas'
                                st.rerun()
                            
                            # Botones de acción
                            col_edit, col_del = st.columns(2)
                            with col_edit:
                                if st.button("✏️", key=f"edit_search_{miembro['id_miembro']}"):
                                    st.session_state.editar_miembro_id = miembro['id_miembro']
                                    st.rerun()
                            with col_del:
                                if st.button("🗑️", key=f"del_search_{miembro['id_miembro']}"):
                                    st.session_state.eliminar_miembro_id = miembro['id_miembro']
                                    st.rerun()
            else:
                st.info("📝 No se encontraron miembros con ese criterio de búsqueda.")
                
    except Exception as e:
        st.error(f"❌ Error en la búsqueda: {e}")

# Funciones para editar y eliminar (las implementaremos después si es necesario)
def mostrar_formulario_edicion(miembro_id):
    """Muestra el formulario para editar un miembro"""
    st.info("🔧 Funcionalidad de edición en desarrollo...")

def mostrar_confirmacion_eliminacion(miembro_id):
    """Muestra la confirmación para eliminar un miembro"""
    st.info("🔧 Funcionalidad de eliminación en desarrollo...")
