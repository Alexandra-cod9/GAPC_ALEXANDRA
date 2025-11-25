import streamlit as st
from modules.configuracion import obtener_conexion

def es_promotora(usuario):
    """Verifica si el usuario tiene rol de promotora"""
    return usuario.get("tipo_rol", "").lower() == "promotora"

def obtener_distrito_usuario(usuario):
    """
    Obtiene el distrito del usuario a través de su grupo.
    Retorna el ID del distrito o None si no se encuentra.
    """
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            # Obtener el distrito a través del grupo del usuario
            cursor.execute("""
                SELECT g.id_distrito
                FROM miembrogapc m
                JOIN grupo g ON m.id_grupo = g.id_grupo
                WHERE m.id_miembro = %s
            """, (usuario.get('id_miembro'),))
            
            resultado = cursor.fetchone()
            cursor.close()
            conexion.close()
            
            if resultado:
                return resultado['id_distrito']
    except Exception as e:
        st.error(f"❌ Error al obtener distrito del usuario: {e}")
    
    return None

def obtener_distrito_por_id(id_distrito):
    """Obtiene la información de un distrito específico por su ID"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            cursor.execute("""
                SELECT 
                    d.id_distrito,
                    d.nombre_distrito,
                    d.cantidad_grupos,
                    d.id_municipio,
                    m.nombre_municipio,
                    m.id_departamento,
                    dep.nombre_departamento
                FROM distrito d
                JOIN municipio m ON d.id_municipio = m.id_municipio
                JOIN departamento dep ON m.id_departamento = dep.id_departamento
                WHERE d.id_distrito = %s
            """, (id_distrito,))
            
            distrito = cursor.fetchone()
            cursor.close()
            conexion.close()
            
            return distrito
    except Exception as e:
        st.error(f"❌ Error al obtener distrito: {e}")
    
    return None

def obtener_todos_distritos():
    """Obtiene todos los distritos disponibles"""
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
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
            
            return distritos
    except Exception as e:
        st.error(f"❌ Error al obtener distritos: {e}")
    
    return []

def distritos_para_usuario(usuario):
    """
    Retorna los distritos según el rol del usuario.
    - Si es promotora: retorna solo su distrito asignado
    - Si es otro rol: retorna todos los distritos
    """
    if es_promotora(usuario):
        # Obtener el distrito a través del grupo
        id_distrito = obtener_distrito_usuario(usuario)
        if id_distrito:
            distrito = obtener_distrito_por_id(id_distrito)
            return [distrito] if distrito else []
        return []
    else:
        # Usuarios normales pueden ver todos los distritos
        return obtener_todos_distritos()