import streamlit as st
import pymysql
import pandas as pd
from datetime import datetime
import os

# Importar módulos
from utils.navegacion import mostrar_modulo

# Configuración de la página
st.set_page_config(
    page_title="Sistema GAPC",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session state
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'id_grupo' not in st.session_state:
    st.session_state.id_grupo = None

# AGREGAR ESTO - Control de navegación
if 'modulo_actual' not in st.session_state:
    st.session_state.modulo_actual = 'dashboard'  # Por defecto mostramos el dashboard

# CSS personalizado - MÁS COMPACTO
st.markdown("""
<style>
    .main-header {
        color: #6f42c1;
        text-align: center;
        margin-bottom: 0.5rem;
        font-size: 1.5rem;
    }
    .stButton button {
        background-color: #6f42c1;
        color: white;
        border: none;
        padding: 0.3rem 0.6rem;
        border-radius: 0.3rem;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .login-container {
        max-width: 300px;
        margin: 1rem auto;
        padding: 1rem;
        border: 1px solid #e0d1f9;
        border-radius: 0.5rem;
        background: #f8fafc;
    }
    .welcome-message {
        background: linear-gradient(135deg, #6f42c1, #8b5cf6);
        color: white;
        padding: 0.8rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 0.5rem 0;
        font-size: 0.8rem;
    }
    .saldo-card {
        background: linear-gradient(135deg, #059669, #10b981);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    .metric-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 0.4rem;
        padding: 0.6rem;
        text-align: center;
        margin: 0.2rem;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
    .module-button {
        background: white;
        color: #6f42c1;
        border: 1px solid #6f42c1;
        padding: 0.6rem;
        border-radius: 0.4rem;
        margin: 0.2rem;
        font-weight: bold;
        font-size: 0.75rem;
        width: 100%;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .module-button:hover {
        background: #6f42c1;
        color: white;
        transform: translateY(-1px);
    }
    .sidebar-content {
        font-size: 0.75rem;
    }
    .compact-text {
        font-size: 0.8rem;
        margin: 0.2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Función de conexión a BD - CLEVER CLOUD
def obtener_conexion():
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

# Función para obtener estadísticas reales

# FUNCIÓN PARA VERIFICAR LOGIN REAL
def verificar_login_real(correo, contrasena):
    """Verifica credenciales contra la base de datos"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            cursor.execute("""
                SELECT m.id_miembro, m.nombre, m.correo, m.contrasena, r.tipo_rol, m.id_grupo
                FROM miembrogapc m
                JOIN rol r ON m.id_rol = r.id_rol
                WHERE m.correo = %s AND m.contrasena IS NOT NULL
            """, (correo,))
            
            usuario = cursor.fetchone()
            cursor.close()
            conexion.close()
            
            if usuario:
                if usuario['contrasena'] == contrasena:
                    return {
                        'id': usuario['id_miembro'],
                        'nombre': usuario['nombre'],
                        'correo': usuario['correo'],
                        'tipo_rol': usuario['tipo_rol'],
                        'id_grupo': usuario['id_grupo']
                    }
        
        return None
        
    except Exception as e:
        st.error(f"Error al verificar login: {e}")
        return None

# FUNCIÓN DE LOGIN
def mostrar_formulario_login():
    """Muestra el formulario de login SOLO en modo real"""

    st.markdown('<div class="main-header">🏠 Sistema GAPC</div>', unsafe_allow_html=True)

    st.markdown("""
        <div class="login-container">
    """, unsafe_allow_html=True)

    st.markdown('<p class="compact-text"><strong>🔐 Iniciar Sesión</strong></p>', unsafe_allow_html=True)

    with st.form("login_form"):
        correo = st.text_input("📧 Correo Electrónico", placeholder="usuario@ejemplo.com")
        contrasena = st.text_input("🔒 Contraseña", type="password", placeholder="••••••••")

        submitted = st.form_submit_button("🚀 Ingresar al Sistema", use_container_width=True)

        if submitted:
            if correo and contrasena:
                with st.spinner("Verificando credenciales..."):
                    usuario = verificar_login_real(correo, contrasena)
                    if usuario:
                        st.session_state.usuario = usuario
                        st.success(f"¡Bienvenido/a {usuario['nombre']}! 👋")
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas o usuario no existe")
            else:
                st.warning("⚠️ Por favor completa todos los campos")

    st.markdown("</div>", unsafe_allow_html=True)


# APLICACIÓN PRINCIPAL
def main():
    if not st.session_state.usuario:
        mostrar_formulario_login()
    else:
        # Usar el sistema de navegación por módulos
        mostrar_modulo()

if __name__ == "__main__":
    main()

