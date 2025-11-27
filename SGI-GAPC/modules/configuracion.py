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

def mostrar_modulo_configuracion():
    """Módulo de configuración del sistema"""
    
    # Header del módulo con botón de volver
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# ⚙️ Módulo de Configuración")
    with col2:
        if st.button("⬅️ Volver al Dashboard", use_container_width=True):
            st.session_state.modulo_actual = 'dashboard'
            st.rerun()
    
    st.markdown("---")
    
    # Menú de opciones
    opcion = st.radio(
        "Selecciona qué configurar:",
        ["🏢 Información del Grupo", "📍 Ubicación", "📜 Reglamento", "🔧 Configuración Avanzada"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if opcion == "🏢 Información del Grupo":
        mostrar_configuracion_grupo()
    elif opcion == "📍 Ubicación":
        mostrar_configuracion_ubicacion()
    elif opcion == "📜 Reglamento":
        mostrar_configuracion_reglamento()
    elif opcion == "🔧 Configuración Avanzada":
        mostrar_configuracion_avanzada()

def mostrar_configuracion_grupo():
    """Configuración de la información básica del grupo"""
    st.subheader("🏢 Información del Grupo")
    
    # Obtener información actual del grupo
    grupo_info = obtener_informacion_grupo()
    
    with st.form("form_configuracion_grupo"):
        st.info("**Configura la información básica de tu grupo GAPC:**")
        
        # Información básica
        col1, col2 = st.columns(2)
        
        with col1:
            nombre_grupo = st.text_input(
                "🏷️ Nombre del Grupo:",
                value=grupo_info['nombre_grupo'],
                placeholder="Ej: Grupo Esperanza, Grupo Progreso...",
                help="Nombre oficial del grupo GAPC"
            )
            
            nombre_comunidad = st.text_input(
                "🏘️ Nombre de la Comunidad:",
                value=grupo_info['nombre_comunidad'],
                placeholder="Ej: Comunidad San José, Colonia Las Flores...",
                help="Nombre de la comunidad donde opera el grupo"
            )
            
            fecha_formacion = st.date_input(
                "📅 Fecha de Formación:",
                value=grupo_info['fecha_formacion'],
                help="Fecha en que se formó oficialmente el grupo"
            )
        
        with col2:
            frecuencia_reuniones = st.selectbox(
                "🔄 Frecuencia de Reuniones:",
                ["semanal", "quincenal", "mensual"],
                index=["semanal", "quincenal", "mensual"].index(grupo_info['frecuencia_reuniones']),
                help="Con qué frecuencia se reúne el grupo"
            )
            
            tasa_interes_mensual = st.number_input(
                "💰 Tasa de Interés Mensual (%):",
                min_value=0.0,
                max_value=50.0,
                value=float(grupo_info['tasa_interes_mensual']),
                step=0.1,
                help="Tasa de interés mensual para préstamos (en porcentaje)"
            )
            
            metodo_reparto_utilidades = st.selectbox(
                "📊 Método de Reparto de Utilidades:",
                ["proporcional", "equitativo"],
                index=["proporcional", "equitativo"].index(grupo_info['metodo_reparto_utilidades']),
                help="Cómo se reparten las utilidades entre miembros"
            )
        
        # Meta social
        meta_social = st.text_area(
            "🎯 Meta Social del Grupo:",
            value=grupo_info['meta_social'],
            placeholder="Describe la meta o propósito social del grupo...",
            help="Objetivo social que el grupo quiere alcanzar",
            height=100
        )
        
        if st.form_submit_button("💾 Guardar Información del Grupo", use_container_width=True):
            if nombre_grupo and nombre_comunidad:
                guardar_informacion_grupo(
                    nombre_grupo, nombre_comunidad, fecha_formacion,
                    frecuencia_reuniones, tasa_interes_mensual,
                    metodo_reparto_utilidades, meta_social
                )
            else:
                st.error("❌ El nombre del grupo y comunidad son obligatorios")

def obtener_informacion_grupo():
    """Obtiene la información actual del grupo"""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            cursor.execute("""
                SELECT 
                    nombre_grupo,
                    nombre_comunidad,
                    fecha_formacion,
                    frecuencia_reuniones,
                    tasa_interes_mensual,
                    metodo_reparto_utilidades,
                    meta_social
                FROM grupo 
                WHERE id_grupo = %s
            """, (id_grupo,))
            
            grupo = cursor.fetchone()
            
            if grupo:
                return {
                    'nombre_grupo': grupo['nombre_grupo'],
                    'nombre_comunidad': grupo['nombre_comunidad'],
                    'fecha_formacion': grupo['fecha_formacion'],
                    'frecuencia_reuniones': grupo['frecuencia_reuniones'],
                    'tasa_interes_mensual': grupo['tasa_interes_mensual'],
                    'metodo_reparto_utilidades': grupo['metodo_reparto_utilidades'],
                    'meta_social': grupo['meta_social']
                }
    
    except Exception as e:
        st.error(f"❌ Error al obtener información del grupo: {e}")
    
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()
    
    # Valores por defecto
    return {
        'nombre_grupo': "Mi Grupo GAPC",
        'nombre_comunidad': "",
        'fecha_formacion': datetime.now().date(),
        'frecuencia_reuniones': "semanal",
        'tasa_interes_mensual': 5.0,
        'metodo_reparto_utilidades': "proporcional",
        'meta_social': ""
    }

def guardar_informacion_grupo(nombre, comunidad, fecha, frecuencia, tasa_interes, metodo_reparto, meta_social):
    """Guarda la información del grupo en la base de datos"""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Actualizar grupo existente
            cursor.execute("""
                UPDATE grupo SET
                    nombre_grupo = %s,
                    nombre_comunidad = %s,
                    fecha_formacion = %s,
                    frecuencia_reuniones = %s,
                    tasa_interes_mensual = %s,
                    metodo_reparto_utilidades = %s,
                    meta_social = %s
                WHERE id_grupo = %s
            """, (nombre, comunidad, fecha, frecuencia, tasa_interes, metodo_reparto, meta_social, id_grupo))
            
            conexion.commit()
            st.success("🎉 ¡Información del grupo guardada exitosamente!")
            st.balloons()
            
    except Exception as e:
        st.error(f"❌ Error al guardar información del grupo: {e}")
    
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

def mostrar_configuracion_ubicacion():
    """Configuración de la ubicación del grupo"""
    st.subheader("📍 Ubicación del Grupo")
    
    # Obtener ubicación actual
    ubicacion_actual = obtener_ubicacion_actual()
    
    with st.form("form_configuracion_ubicacion"):
        st.info("**Selecciona la ubicación donde opera tu grupo:**")
        
        # Obtener departamentos
        departamentos = obtener_departamentos()
        
        if not departamentos:
            st.error("❌ No se pudieron cargar los departamentos")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            departamento_seleccionado = st.selectbox(
                "🏛️ Departamento:",
                options=[d['nombre_departamento'] for d in departamentos],
                index=obtener_indice_departamento(departamentos, ubicacion_actual['id_departamento']),
                help="Selecciona el departamento"
            )
        
        with col2:
            # Obtener municipios según departamento seleccionado
            id_departamento_seleccionado = next((d['id_departamento'] for d in departamentos if d['nombre_departamento'] == departamento_seleccionado), None)
            municipios = obtener_municipios(id_departamento_seleccionado) if id_departamento_seleccionado else []
            
            if municipios:
                municipio_seleccionado = st.selectbox(
                    "🏘️ Municipio:",
                    options=[m['nombre_municipio'] for m in municipios],
                    index=obtener_indice_municipio(municipios, ubicacion_actual['id_municipio']),
                    help="Selecciona el municipio"
                )
            else:
                st.warning("No hay municipios disponibles")
                municipio_seleccionado = None
        
        with col3:
            # Obtener distritos según municipio seleccionado
            if municipio_seleccionado and municipios:
                id_municipio_seleccionado = next((m['id_municipio'] for m in municipios if m['nombre_municipio'] == municipio_seleccionado), None)
                distritos = obtener_distritos(id_municipio_seleccionado) if id_municipio_seleccionado else []
                
                if distritos:
                    distrito_seleccionado = st.selectbox(
                        "🗺️ Distrito:",
                        options=[d['nombre_distrito'] for d in distritos],
                        index=obtener_indice_distrito(distritos, ubicacion_actual['id_distrito']),
                        help="Selecciona el distrito"
                    )
                else:
                    st.warning("No hay distritos disponibles")
                    distrito_seleccionado = None
            else:
                distrito_seleccionado = None
        
        if st.form_submit_button("💾 Guardar Ubicación", use_container_width=True):
            if distrito_seleccionado and distritos:
                id_distrito_seleccionado = next(d['id_distrito'] for d in distritos if d['nombre_distrito'] == distrito_seleccionado)
                guardar_ubicacion_grupo(id_distrito_seleccionado)
                st.success("🎉 ¡Ubicación guardada exitosamente!")
            else:
                st.error("❌ Debes seleccionar un distrito válido")

def obtener_ubicacion_actual():
    """Obtiene la ubicación actual del grupo"""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            cursor.execute("""
                SELECT id_distrito 
                FROM grupo 
                WHERE id_grupo = %s
            """, (id_grupo,))
            
            grupo = cursor.fetchone()
            
            if grupo and grupo['id_distrito']:
                # Obtener información completa de la ubicación
                cursor.execute("""
                    SELECT 
                        d.id_distrito,
                        d.id_municipio,
                        m.id_departamento
                    FROM distrito d
                    JOIN municipio m ON d.id_municipio = m.id_municipio
                    WHERE d.id_distrito = %s
                """, (grupo['id_distrito'],))
                
                ubicacion = cursor.fetchone()
                
                if ubicacion:
                    return {
                        'id_distrito': ubicacion['id_distrito'],
                        'id_municipio': ubicacion['id_municipio'],
                        'id_departamento': ubicacion['id_departamento']
                    }
    
    except Exception as e:
        st.error(f"❌ Error al obtener ubicación: {e}")
    
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()
    
    return {'id_departamento': None, 'id_municipio': None, 'id_distrito': None}

def obtener_departamentos():
    """Obtiene la lista de departamentos"""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            cursor.execute("SELECT id_departamento, nombre_departamento FROM departamento ORDER BY nombre_departamento")
            departamentos = cursor.fetchall()
            return departamentos
    except Exception as e:
        st.error(f"❌ Error al cargar departamentos: {e}")
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()
    
    return []

def obtener_municipios(id_departamento):
    """Obtiene municipios por departamento"""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT id_municipio, nombre_municipio 
                FROM municipio 
                WHERE id_departamento = %s 
                ORDER BY nombre_municipio
            """, (id_departamento,))
            municipios = cursor.fetchall()
            return municipios
    except Exception as e:
        st.error(f"❌ Error al cargar municipios: {e}")
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()
    
    return []

def obtener_distritos(id_municipio):
    """Obtiene distritos por municipio"""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            cursor.execute("""
                SELECT id_distrito, nombre_distrito 
                FROM distrito 
                WHERE id_municipio = %s 
                ORDER BY nombre_distrito
            """, (id_municipio,))
            distritos = cursor.fetchall()
            return distritos
    except Exception as e:
        st.error(f"❌ Error al cargar distritos: {e}")
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()
    
    return []

def obtener_indice_departamento(departamentos, id_departamento):
    """Obtiene el índice del departamento en la lista"""
    if not id_departamento:
        return 0
    for i, depto in enumerate(departamentos):
        if depto['id_departamento'] == id_departamento:
            return i
    return 0

def obtener_indice_municipio(municipios, id_municipio):
    """Obtiene el índice del municipio en la lista"""
    if not id_municipio or not municipios:
        return 0
    for i, mun in enumerate(municipios):
        if mun['id_municipio'] == id_municipio:
            return i
    return 0

def obtener_indice_distrito(distritos, id_distrito):
    """Obtiene el índice del distrito en la lista"""
    if not id_distrito or not distritos:
        return 0
    for i, dist in enumerate(distritos):
        if dist['id_distrito'] == id_distrito:
            return i
    return 0

def guardar_ubicacion_grupo(id_distrito):
    """Guarda la ubicación del grupo"""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            cursor.execute("""
                UPDATE grupo 
                SET id_distrito = %s 
                WHERE id_grupo = %s
            """, (id_distrito, id_grupo))
            
            conexion.commit()
            
    except Exception as e:
        st.error(f"❌ Error al guardar ubicación: {e}")
    
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

def mostrar_configuracion_reglamento():
    """Configuración del reglamento del grupo"""
    st.subheader("📜 Reglamento del Grupo")
    
    # Obtener reglamento actual
    reglamento_actual = obtener_reglamento_actual()
    
    with st.form("form_configuracion_reglamento"):
        st.info("**Configura las reglas y normativas de tu grupo:**")
        
        # Texto del reglamento
        texto_reglamento = st.text_area(
            "📋 Texto del Reglamento:",
            value=reglamento_actual['texto_reglamento'],
            placeholder="Escribe aquí el reglamento completo del grupo...",
            height=200,
            help="Reglas generales, derechos y obligaciones de los miembros"
        )
        
        # Tipos de multas predefinidas
        st.subheader("⚠️ Tipos de Multas Predefinidas")
        st.info("**Define los motivos y montos de multas que se aplicarán automáticamente:**")
        
        tipo_multa = st.text_area(
            "📝 Configuración de Multas:",
            value=reglamento_actual['tipo_multa'],
            placeholder="Ej: Falta a reunión: $5.00\nLlegar tarde: $2.00\nNo cumplir acuerdo: $10.00",
            height=150,
            help="Formato: Motivo: $Monto (uno por línea)"
        )
        
        # Reglas de préstamos
        st.subheader("💳 Reglas para Préstamos")
        
        reglas_prestamo = st.text_area(
            "📊 Reglas de Préstamos:",
            value=reglamento_actual['reglas_prestamo'],
            placeholder="Ej: Máximo 80% del ahorro\nPlazo máximo: 12 meses\nUn préstamo a la vez",
            height=150,
            help="Define las reglas específicas para préstamos"
        )
        
        if st.form_submit_button("💾 Guardar Reglamento", use_container_width=True):
            # Validar que no estén vacíos
            if not texto_reglamento.strip():
                st.error("❌ El texto del reglamento no puede estar vacío")
            elif not tipo_multa.strip():
                st.error("❌ Los tipos de multa no pueden estar vacíos")
            elif not reglas_prestamo.strip():
                st.error("❌ Las reglas de préstamo no pueden estar vacías")
            else:
                guardar_reglamento(texto_reglamento.strip(), tipo_multa.strip(), reglas_prestamo.strip())
                st.success("🎉 ¡Reglamento guardado exitosamente!")

def obtener_reglamento_actual():
    """Obtiene el reglamento actual del grupo"""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            # Primero obtener el id_reglamento del grupo
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            cursor.execute("SELECT id_reglamento FROM grupo WHERE id_grupo = %s", (id_grupo,))
            grupo = cursor.fetchone()
            
            if grupo and grupo['id_reglamento']:
                cursor.execute("""
                    SELECT 
                        texto_reglamento,
                        tipo_multa,
                        reglas_prestamo
                    FROM reglamento 
                    WHERE id_reglamento = %s
                """, (grupo['id_reglamento'],))
                
                reglamento = cursor.fetchone()
                
                if reglamento:
                    return {
                        'texto_reglamento': reglamento['texto_reglamento'] or "",
                        'tipo_multa': reglamento['tipo_multa'] or "",
                        'reglas_prestamo': reglamento['reglas_prestamo'] or ""
                    }
    
    except Exception as e:
        st.error(f"❌ Error al obtener reglamento: {e}")
    
    finally:
        # Cerrar recursos en el orden correcto
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()
    
    return {
        'texto_reglamento': "",
        'tipo_multa': "",
        'reglas_prestamo': ""
    }

def guardar_reglamento(texto_reglamento, tipo_multa, reglas_prestamo):
    """Guarda el reglamento en la base de datos"""
    conexion = None
    cursor = None
    try:
        conexion = obtener_conexion()
        if conexion:
            cursor = conexion.cursor()
            
            id_grupo = st.session_state.usuario.get('id_grupo', 1)
            
            # Obtener el id_reglamento del grupo
            cursor.execute("SELECT id_reglamento FROM grupo WHERE id_grupo = %s", (id_grupo,))
            grupo = cursor.fetchone()
            
            if grupo and grupo['id_reglamento']:
                # Actualizar reglamento existente
                cursor.execute("""
                    UPDATE reglamento SET
                        texto_reglamento = %s,
                        tipo_multa = %s,
                        reglas_prestamo = %s
                    WHERE id_reglamento = %s
                """, (texto_reglamento, tipo_multa, reglas_prestamo, grupo['id_reglamento']))
            else:
                # Crear nuevo reglamento y asociarlo al grupo
                cursor.execute("""
                    INSERT INTO reglamento (texto_reglamento, tipo_multa, reglas_prestamo) 
                    VALUES (%s, %s, %s)
                """, (texto_reglamento, tipo_multa, reglas_prestamo))
                
                # Obtener el ID del reglamento recién creado
                id_reglamento = cursor.lastrowid
                
                # Asociar reglamento al grupo
                cursor.execute("""
                    UPDATE grupo 
                    SET id_reglamento = %s 
                    WHERE id_grupo = %s
                """, (id_reglamento, id_grupo))
            
            conexion.commit()
            
    except Exception as e:
        st.error(f"❌ Error al guardar reglamento: {e}")
    
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()

def mostrar_configuracion_avanzada():
    """Configuración avanzada del sistema"""
    st.subheader("🔧 Configuración Avanzada")
    
    st.info("""
    **Opciones avanzadas de configuración del sistema:**
    
    Aquí puedes configurar parámetros técnicos y opciones avanzadas del sistema GAPC.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**⚙️ Configuraciones del Sistema:**")
        
        # Ejemplo de configuraciones avanzadas
        auto_multas_asistencia = st.checkbox(
            "✅ Aplicar multas automáticas por falta de asistencia",
            value=True,
            help="Aplica multas automáticamente cuando un miembro falta a una reunión"
        )
        
        limite_prestamos_simultaneos = st.number_input(
            "🔒 Límite de préstamos simultáneos:",
            min_value=1,
            max_value=5,
            value=1,
            help="Número máximo de préstamos que un miembro puede tener al mismo tiempo"
        )
    
    with col2:
        st.write("**📊 Parámetros Financieros:**")
        
        monto_multa_default = st.number_input(
            "⚠️ Monto de multa por defecto:",
            min_value=0.0,
            value=5.0,
            step=1.0,
            help="Monto predeterminado para multas no especificadas"
        )
        
        dias_gracia_prestamos = st.number_input(
            "📅 Días de gracia para préstamos:",
            min_value=0,
            max_value=30,
            value=5,
            help="Días de gracia después del vencimiento antes de aplicar recargos"
        )
    
    # Guardar configuraciones avanzadas en session_state
    if st.button("💾 Guardar Configuración Avanzada", use_container_width=True):
        if 'config_avanzada' not in st.session_state:
            st.session_state.config_avanzada = {}
        
        st.session_state.config_avanzada = {
            'auto_multas_asistencia': auto_multas_asistencia,
            'limite_prestamos_simultaneos': limite_prestamos_simultaneos,
            'monto_multa_default': monto_multa_default,
            'dias_gracia_prestamos': dias_gracia_prestamos
        }
        
        st.success("🎉 ¡Configuración avanzada guardada exitosamente!")
    
    # Mostrar configuración actual
    if 'config_avanzada' in st.session_state:
        st.markdown("---")
        st.subheader("📋 Configuración Actual")
        st.json(st.session_state.config_avanzada)
