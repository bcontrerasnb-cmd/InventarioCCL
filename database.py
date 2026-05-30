import mysql.connector
from mysql.connector import Error

def conectar():
    try:
        conexion = mysql.connector.connect(
            host='localhost',
            database='inventario_ccl',
            user='root',
            password=''
        )
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
    return None

def validar_login(username, password):
    conexion = conectar()
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            sql = "SELECT * FROM usuarios WHERE username = %s AND password = %s"
            cursor.execute(sql, (username, password))
            usuario = cursor.fetchone()
            return usuario
        except Error as e:
            print(f"Error en login: {e}")
        finally:
            cursor.close()
            conexion.close()
    return None

# =========================================
# MÓDULO DE INVENTARIO
# =========================================
def obtener_articulos(tipo_ubicacion):
    conexion = conectar()
    articulos = []
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            sql = """
                  SELECT i.id_item, i.codigo_barras, i.nombre, i.categoria, s.id_sala, s.nombre as sala, i.cantidad, i.estado
                  FROM item_inventario i
                           JOIN sala_clases s ON i.id_sala = s.id_sala
                  WHERE s.tipo_sala = %s \
                  """
            cursor.execute(sql, (tipo_ubicacion,))
            articulos = cursor.fetchall()
        except Error as e:
            print(f"Error al obtener artículos: {e}")
        finally:
            cursor.close()
            conexion.close()
    return articulos

def obtener_salas_por_tipo(tipo_sala):
    conexion = conectar()
    salas = []
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            sql = "SELECT id_sala, nombre FROM sala_clases WHERE tipo_sala = %s"
            cursor.execute(sql, (tipo_sala,))
            salas = cursor.fetchall()
        except Error as e:
            print(f"Error al obtener salas: {e}")
        finally:
            cursor.close()
            conexion.close()
    return salas

def registrar_articulo(codigo, nombre, categoria, cantidad, estado, id_sala):
    conexion = conectar()
    if conexion:
        try:
            cursor = conexion.cursor()
            sql = "INSERT INTO item_inventario (codigo_barras, nombre, categoria, cantidad, estado, id_sala) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (codigo, nombre, categoria, cantidad, estado, id_sala))
            conexion.commit()
            return True
        except Error as e:
            print(f"Error al registrar: {e}")
        finally:
            cursor.close()
            conexion.close()
    return False

def actualizar_articulo(id_item, codigo, nombre, categoria, cantidad, estado, id_sala):
    conexion = conectar()
    if conexion:
        try:
            cursor = conexion.cursor()
            sql = """UPDATE item_inventario
                     SET codigo_barras=%s, nombre=%s, categoria=%s, cantidad=%s, estado=%s, id_sala=%s
                     WHERE id_item=%s"""
            cursor.execute(sql, (codigo, nombre, categoria, cantidad, estado, id_sala, id_item))
            conexion.commit()
            return True
        except Error as e:
            print(f"Error al actualizar: {e}")
        finally:
            cursor.close()
            conexion.close()
    return False

def eliminar_articulo(id_item):
    conexion = conectar()
    if conexion:
        try:
            cursor = conexion.cursor()
            sql = "DELETE FROM item_inventario WHERE id_item=%s"
            cursor.execute(sql, (id_item,))
            conexion.commit()
            return True
        except Error as e:
            print(f"Error al eliminar: {e}")
        finally:
            cursor.close()
            conexion.close()
    return False

# =========================================
# MÓDULO DE USUARIOS
# =========================================
def obtener_usuarios():
    conexion = conectar()
    usuarios = []
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            sql = "SELECT id_usuario, username, rol, foto_perfil FROM usuarios"
            cursor.execute(sql)
            usuarios = cursor.fetchall()
        except Error as e:
            print(f"Error al obtener usuarios: {e}")
        finally:
            cursor.close()
            conexion.close()
    return usuarios

def registrar_usuario(username, password, rol, foto_perfil):
    conexion = conectar()
    if conexion:
        try:
            cursor = conexion.cursor()
            sql = "INSERT INTO usuarios (username, password, rol, foto_perfil) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (username, password, rol, foto_perfil))
            conexion.commit()
            return True
        except Error as e:
            print(f"Error al registrar usuario: {e}")
        finally:
            cursor.close()
            conexion.close()
    return False

def actualizar_usuario(id_usuario, username, password, rol, foto_perfil):
    conexion = conectar()
    if conexion:
        try:
            cursor = conexion.cursor()
            query = "UPDATE usuarios SET username=%s, rol=%s"
            params = [username, rol]

            if password:
                query += ", password=%s"
                params.append(password)
            if foto_perfil:
                query += ", foto_perfil=%s"
                params.append(foto_perfil)

            query += " WHERE id_usuario=%s"
            params.append(id_usuario)

            cursor.execute(query, tuple(params))
            conexion.commit()
            return True
        except Error as e:
            print(f"Error al actualizar usuario: {e}")
        finally:
            cursor.close()
            conexion.close()
    return False

def eliminar_usuario(id_usuario):
    conexion = conectar()
    if conexion:
        try:
            cursor = conexion.cursor()
            sql = "DELETE FROM usuarios WHERE id_usuario=%s"
            cursor.execute(sql, (id_usuario,))
            conexion.commit()
            return True
        except Error as e:
            print(f"Error al eliminar usuario: {e}")
        finally:
            cursor.close()
            conexion.close()
    return False

# =========================================
# MÓDULO DE REPORTES Y ESTADÍSTICAS
# =========================================
def obtener_estadisticas_generales():
    conexion = conectar()
    stats = {'total': 0, 'malo': 0, 'baja': 0}
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT IFNULL(SUM(cantidad), 0) as count FROM item_inventario")
            stats['total'] = cursor.fetchone()['count']

            cursor.execute("SELECT IFNULL(SUM(cantidad), 0) as count FROM item_inventario WHERE estado = 'Malo'")
            stats['malo'] = cursor.fetchone()['count']

            cursor.execute("SELECT IFNULL(SUM(cantidad), 0) as count FROM item_inventario WHERE estado = 'De baja'")
            stats['baja'] = cursor.fetchone()['count']
        except Error as e:
            print(f"Error en estadísticas: {e}")
        finally:
            cursor.close()
            conexion.close()
    return stats

def obtener_datos_graficos():
    conexion = conectar()
    datos = {}
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            # Agrupamos la suma de cantidades por tipo de sala y estado
            sql = """
                  SELECT s.tipo_sala, i.estado, SUM(i.cantidad) as total_estado
                  FROM item_inventario i
                           JOIN sala_clases s ON i.id_sala = s.id_sala
                  GROUP BY s.tipo_sala, i.estado \
                  """
            cursor.execute(sql)
            resultados = cursor.fetchall()

            # Formateamos los datos para enviarlos fácilmente a los gráficos de JavaScript
            for fila in resultados:
                tipo = fila['tipo_sala']
                estado = fila['estado']
                cantidad = int(fila['total_estado'])

                if tipo not in datos:
                    datos[tipo] = {'Bueno': 0, 'Regular': 0, 'Malo': 0, 'De baja': 0}

                # OJO: Aquí nos aseguramos de asignar la cantidad al estado correcto
                if estado in datos[tipo]:
                    datos[tipo][estado] = cantidad
                elif estado == 'De baja': # Aseguramos que 'De baja' no se confunda
                    datos[tipo]['De baja'] = cantidad

        except Error as e:
            print(f"Error en gráficos: {e}")
        finally:
            cursor.close()
            conexion.close()
    return datos

def obtener_reporte_articulos(filtro):
    conexion = conectar()
    articulos = []
    if conexion:
        try:
            cursor = conexion.cursor(dictionary=True)
            base_sql = """
                       SELECT i.codigo_barras, i.nombre, i.categoria, s.nombre as sala, s.tipo_sala, i.cantidad, i.estado
                       FROM item_inventario i
                                JOIN sala_clases s ON i.id_sala = s.id_sala \
                       """
            if filtro == 'malo':
                cursor.execute(base_sql + " WHERE i.estado = 'Malo'")
            elif filtro == 'baja':
                cursor.execute(base_sql + " WHERE i.estado = 'De baja'")
            else:
                cursor.execute(base_sql)

            articulos = cursor.fetchall()
        except Error as e:
            print(f"Error exportando reporte: {e}")
        finally:
            cursor.close()
            conexion.close()
    return articulos