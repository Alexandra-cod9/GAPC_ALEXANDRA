import streamlit as st
from datetime import datetime
from utils.roles import es_promotora
from modules.configuracion import obtener_conexion
from modules import nuevo_grupo  # ✅ Importar el nuevo módulo
from modules import ver_grupos_distrito  # ✅ Importar el módulo de ver grupos

def obtener_distrito_promotora(usuario):
    """Obtiene el distrito asignado a la promotora a través de su grupo"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            cursor.execute("""
                SELECT 
                    d.id_distrito,
                    d.nombre_distrito,
                    m.nombre_municipio,
                    dep.nombre_departamento
                FROM miembrogapc mg
                JOIN grupo g ON mg.id_grupo = g.id_grupo
                JOIN distrito d ON g.id_distrito = d.id_distrito
                JOIN municipio m ON d.id_municipio = m.id_municipio
                JOIN departamento dep ON m.id_departamento = dep.id_departamento
                WHERE mg.id_miembro = %s
            """, (usuario.get('id_miembro'),))
            
            distrito = cursor.fetchone()
            cursor.close()
            conexion.close()
            
            return distrito
    except Exception as e:
        st.error(f"❌ Error al obtener distrito: {e}")
    
    return None

def mostrar_dashboard_principal():
    """Muestra el dashboard principal más compacto y optimizado"""
    usuario = st.session_state.usuario
    id_grupo_usuario = usuario.get('id_grupo')
  
    # ----------------- SIDEBAR -------------------
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.image("https://via.placeholder.com/100x30/6f42c1/white?text=GAPC", width=100)
        st.markdown("---")
        st.write(f"**👤 {usuario['nombre']}**")
        st.write(f"**🎭 {usuario['tipo_rol']}**")
        st.write(f"**🏢 Grupo #{id_grupo_usuario}**")
        st.write("**🔐 Modo Real**" if 'correo' in usuario else "**🧪 Modo Prueba**")
        st.markdown("---")
        
        if es_promotora(usuario):
            st.markdown("### 👩‍💼 Panel Promotora")
            distrito = obtener_distrito_promotora(usuario)
            
            if distrito:
                st.info(f"""
                📍 **Tu distrito asignado:**
                - **Distrito:** {distrito['nombre_distrito']}
                - **Municipio:** {distrito['nombre_municipio']}
                - **Departamento:** {distrito['nombre_departamento']}
                """)
            else:
                st.warning("⚠️ No se encontró distrito asignado")
            
            st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Actualizar", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("🚪 Salir", use_container_width=True):
                st.session_state.usuario = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ----------------- HEADER -------------------
    st.markdown(f"""
    <div class="welcome-message">
        <h4>¡Bienvenido/a, {usuario['nombre']}!</h4>
        <p>{usuario['tipo_rol']} - Grupo #{id_grupo_usuario}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ----------------- VERIFICAR SI MOSTRAR VER GRUPOS DISTRITO -------------------
    if st.session_state.get('mostrar_grupos_distrito', False):
        ver_grupos_distrito.mostrar_grupos_por_distrito()
        
        st.markdown("---")
        if st.button("⬅️ Volver al Dashboard Principal", use_container_width=True, type="secondary"):
            st.session_state.mostrar_grupos_distrito = False
            if 'grupo_seleccionado_id' in st.session_state:
                del st.session_state.grupo_seleccionado_id
            st.rerun()
        
        return  # Detener el resto del dashboard
    
    # ----------------- VERIFICAR SI MOSTRAR FORMULARIO NUEVO GRUPO -------------------
    if st.session_state.get('mostrar_nuevo_grupo', False):
        nuevo_grupo.mostrar_formulario_nuevo_grupo()
        
        st.markdown("---")
        if st.button("❌ Cancelar", use_container_width=True):
            st.session_state.mostrar_nuevo_grupo = False
            st.rerun()
        
        return  # Detener el resto del dashboard
    
    # ----------------- ACCIONES ESPECIALES PARA PROMOTORA -------------------
    if es_promotora(usuario):
        st.markdown("---")
        st.markdown("### 👩‍💼 Acciones de Promotora")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("➕ Crear Nuevo Grupo", use_container_width=True, type="primary"):
                st.session_state.mostrar_nuevo_grupo = True
                st.rerun()
        
        with col2:
            if st.button("📊 Ver Grupos por Distrito", use_container_width=True, type="primary"):
                st.session_state.mostrar_grupos_distrito = True
                st.rerun()
        
        with col3:
            if st.button("📈 Reporte Consolidado", use_container_width=True, type="primary"):
                st.info("🚧 Funcionalidad en desarrollo: Reporte consolidado de todos los grupos")
    
    # ----------------- MÓDULOS -------------------
    st.markdown("---")
    st.markdown("### 🚀 Módulos del Sistema")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("👥 **Miembros**\nGestión", use_container_width=True, key="miembros"):
            st.session_state.modulo_actual = 'miembros'
            st.rerun()
    with col2:
        if st.button("📅 **Reuniones**\nCalendario", use_container_width=True, key="reuniones"):
            st.session_state.modulo_actual = 'reuniones'
            st.rerun()
    with col3:
        if st.button("💰 **Aportes**\nAhorros", use_container_width=True, key="aportes"):
            st.session_state.modulo_actual = 'aportes'
            st.rerun()
    with col4:
        if st.button("💳 **Préstamos**\nGestionar", use_container_width=True, key="prestamos"):
            st.session_state.modulo_actual = 'prestamos'
            st.rerun()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("⚠️ **Multas**\nSanciones", use_container_width=True, key="multas"):
            st.session_state.modulo_actual = 'multas'
            st.rerun()
    with col2:
        if st.button("📊 **Reportes**\nEstadísticas", use_container_width=True, key="reportes"):
            st.session_state.modulo_actual = 'reportes'
            st.rerun()
    with col3:
        if st.button("🔄 **Cierre**\nPeríodo", use_container_width=True, key="cierre"):
            st.session_state.modulo_actual = 'cierre'
            st.rerun()
    with col4:
        if st.button("⚙️ **Configuración**\nAjustes", use_container_width=True, key="configuracion"):
            st.session_state.modulo_actual = 'configuracion'
            st.rerun()
    
    # ----------------- FOOTER -------------------
    st.markdown("---")
    st.markdown(
        f'<p class="compact-text">*Última actualización: {datetime.now().strftime("%d/%m/%Y %H:%M")}*</p>',
        unsafe_allow_html=True
    )