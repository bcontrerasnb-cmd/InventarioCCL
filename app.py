from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
import database
import io
import csv
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'clave_secreta_ccl_2026'

app.config['UPLOAD_FOLDER'] = 'static/img/perfiles'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    usuario = database.validar_login(username, password)

    if usuario:
        session['usuario_id'] = usuario['id_usuario']
        session['username'] = usuario['username']
        session['rol'] = usuario['rol']
        session['foto'] = usuario.get('foto_perfil') or 'default.png'
        return redirect(url_for('dashboard'))
    else:
        flash('Usuario o contraseña incorrectos', 'error')
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))

    modulos_disponibles = [
        {"titulo": "Salas de Clase", "icono": "📚", "ruta": "Sala", "roles": ["Admin", "Docente"]},
        {"titulo": "Laboratorios", "icono": "🔬", "ruta": "Laboratorio", "roles": ["Admin", "Docente"]},
        {"titulo": "Oficinas", "icono": "🏢", "ruta": "Oficina", "roles": ["Admin", "Administrativo"]},
        {"titulo": "Gimnasios", "icono": "🏀", "ruta": "Gimnasio", "roles": ["Admin", "Administrativo"]},
        {"titulo": "Bodegas", "icono": "📦", "ruta": "Bodega", "roles": ["Admin", "Administrativo"]},
        {"titulo": "Baños", "icono": "🚻", "ruta": "Baño", "roles": ["Admin", "Administrativo"]},
        {"titulo": "Usuarios", "icono": "👥", "ruta": "Usuarios", "roles": ["Admin"]},
        {"titulo": "Estadísticas", "icono": "📊", "ruta": "Reportes", "roles": ["Admin"]}
    ]
    return render_template('dashboard.html', modulos=modulos_disponibles)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# =========================================
# RUTAS DEL INVENTARIO
# =========================================
@app.route('/inventario/<tipo_modulo>')
def inventario(tipo_modulo):
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    articulos = database.obtener_articulos(tipo_modulo)
    salas_reales = database.obtener_salas_por_tipo(tipo_modulo)
    return render_template('inventario.html', tipo_modulo=tipo_modulo, articulos=articulos, salas=salas_reales)

@app.route('/inventario/<tipo_modulo>/procesar', methods=['POST'])
def procesar_articulo(tipo_modulo):
    if 'usuario_id' not in session:
        return redirect(url_for('index'))

    accion = request.form.get('accion')
    id_item = request.form.get('id_item')
    codigo = request.form.get('codigo')
    nombre = request.form.get('nombre')
    categoria = request.form.get('categoria')
    cantidad = request.form.get('cantidad')
    estado = request.form.get('estado')
    id_sala = request.form.get('id_sala')

    if accion == 'guardar':
        if database.registrar_articulo(codigo, nombre, categoria, cantidad, estado, id_sala):
            flash('Artículo registrado correctamente.', 'success')
        else:
            flash('Error al registrar el artículo.', 'error')

    elif accion == 'actualizar':
        if database.actualizar_articulo(id_item, codigo, nombre, categoria, cantidad, estado, id_sala):
            flash('Artículo actualizado correctamente.', 'success')
        else:
            flash('Error al actualizar.', 'error')

    elif accion == 'eliminar':
        if database.eliminar_articulo(id_item):
            flash('Artículo eliminado correctamente.', 'success')
        else:
            flash('Error al eliminar.', 'error')

    return redirect(url_for('inventario', tipo_modulo=tipo_modulo))

@app.route('/inventario/<tipo_modulo>/exportar')
def exportar_excel(tipo_modulo):
    if 'usuario_id' not in session:
        return redirect(url_for('index'))

    articulos = database.obtener_articulos(tipo_modulo)
    output = io.StringIO()
    output.write(u'\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Código de Barras', 'Artículo', 'Categoría', 'Ubicación', 'Cantidad', 'Estado'])

    for art in articulos:
        writer.writerow([art['codigo_barras'], art['nombre'], art['categoria'], art['sala'], art['cantidad'], art['estado']])

    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers["Content-Disposition"] = f"attachment; filename=Inventario_{tipo_modulo}.csv"
    return response

# =========================================
# RUTAS DE USUARIOS
# =========================================
@app.route('/usuarios')
def usuarios():
    if 'usuario_id' not in session or session.get('rol') != 'Admin':
        flash('Acceso denegado.', 'error')
        return redirect(url_for('dashboard'))

    lista_usuarios = database.obtener_usuarios()
    return render_template('usuarios.html', usuarios=lista_usuarios)

@app.route('/usuarios/procesar', methods=['POST'])
def procesar_usuario():
    if 'usuario_id' not in session or session.get('rol') != 'Admin':
        return redirect(url_for('dashboard'))

    accion = request.form.get('accion')
    id_usuario = request.form.get('id_usuario')
    username = request.form.get('username')
    password = request.form.get('password')
    rol = request.form.get('rol')

    foto = request.files.get('foto')
    nombre_foto = None
    if foto and foto.filename != '':
        nombre_foto = secure_filename(foto.filename)
        foto.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_foto))
        if str(id_usuario) == str(session.get('usuario_id')):
            session['foto'] = nombre_foto

    if accion == 'guardar':
        if not password:
            flash('Debes ingresar una contraseña.', 'error')
        else:
            foto_final = nombre_foto if nombre_foto else 'default.png'
            if database.registrar_usuario(username, password, rol, foto_final):
                flash('Usuario creado correctamente.', 'success')
            else:
                flash('Error al crear el usuario.', 'error')

    elif accion == 'actualizar':
        if database.actualizar_usuario(id_usuario, username, password, rol, nombre_foto):
            flash('Usuario actualizado correctamente.', 'success')
        else:
            flash('Error al actualizar el usuario.', 'error')

    elif accion == 'eliminar':
        if str(id_usuario) == str(session['usuario_id']):
            flash('No puedes eliminar tu propia cuenta.', 'error')
        else:
            if database.eliminar_usuario(id_usuario):
                flash('Usuario eliminado.', 'success')

    return redirect(url_for('usuarios'))

# =========================================
# RUTAS DE REPORTES
# =========================================
@app.route('/reportes')
def reportes():
    if 'usuario_id' not in session or session.get('rol') != 'Admin':
        return redirect(url_for('dashboard'))

    stats = database.obtener_estadisticas_generales()
    datos_graficos = database.obtener_datos_graficos()
    return render_template('reportes.html', stats=stats, graficos=datos_graficos)

@app.route('/reportes/exportar/<filtro>')
def exportar_reporte(filtro):
    if 'usuario_id' not in session or session.get('rol') != 'Admin':
        return redirect(url_for('dashboard'))

    articulos = database.obtener_reporte_articulos(filtro)
    output = io.StringIO()
    output.write(u'\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Código de Barras', 'Artículo', 'Categoría', 'Ubicación Exacta', 'Tipo de Área', 'Cantidad', 'Estado'])

    for art in articulos:
        writer.writerow([art['codigo_barras'], art['nombre'], art['categoria'], art['sala'], art['tipo_sala'], art['cantidad'], art['estado']])

    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers["Content-Disposition"] = f"attachment; filename=Reporte_Inventario_{filtro.upper()}.csv"
    return response

if __name__ == '__main__':
    app.run(debug=True, port=5000)