import secrets
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from ..models import Usuario, Profesional, Administrador
from ..extensions import bcrypt
from .utils import validate_password, login_required
from flask import render_template
from flask_bcrypt import Bcrypt, check_password_hash, generate_password_hash
from ..extensions import db,mail  # Asegúrate de que extensions.py contiene "db = SQLAlchemy()"
from datetime import datetime, date, timedelta, time
from flask_mail import Mail, Message
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    """Página principal."""
    return render_template('/auth/index.html')

@auth_bp.route('/login', methods=["GET", 'POST'])
def login():
    """Maneja el inicio de sesión."""
    if request.method == "POST" and "correo" in request.form and "contrasena" in request.form:
        username = request.form['correo']
        password = request.form['contrasena']
        rol = request.form['rol']

        # Buscar usuario según el rol
        if rol == "usuario":
            user_data = Usuario.query.filter_by(correo=username, tipo_perfil=rol).first()
        elif rol == "profesional":
            user_data = Profesional.query.filter_by(correo=username).first()
        elif rol == "admin":
            user_data = Administrador.query.filter_by(correo=username).first()

        # Verificar credenciales
        if user_data and check_password_hash(user_data.contrasena, password):
            session['logged_in'] = True
            session['last_activity'] = datetime.now().isoformat()
            
            if rol == 'usuario':
                session['id_usuario'] = user_data.id_usuario
                return redirect(url_for('user.user_home'))
            elif rol == 'profesional':
                session['id_profesional'] = user_data.id_profesional
                return redirect(url_for('profesional.profesional_home'))
            elif rol == 'admin':
                session['id_administrador'] = user_data.id_administrador
                return redirect(url_for('admin.admin_home'))
        
        flash("Correo electrónico o contraseña incorrectos.", "error")
    
    return render_template('/auth/index.html')

@auth_bp.route('/signup', methods=["GET", 'POST'])
def register():
    """Maneja el registro de nuevos usuarios."""
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.form['nombre']
        tipo_documento = request.form['tipo_documento']
        numero_documento = request.form['numero_documento']
        celular = request.form['celular']
        correo = request.form['correo']
        contrasena = request.form['contrasena']

        # Validaciones
        if not validate_password(contrasena):
            flash("La contraseña no cumple con los requisitos.", "error")
            return render_template('/auth/register.html')

        if Usuario.query.filter_by(correo=correo).first():
            flash("El correo electrónico ya está registrado.", "error")
            return render_template('/auth/register.html')

        if Usuario.query.filter_by(numero_documento=numero_documento).first():
            flash("El número de documento ya está registrado.", "error")
            return render_template('/auth/register.html')

        # Crear nuevo usuario
        nuevo_usuario = Usuario(
            nombre=nombre,
            tipo_documento=tipo_documento,
            numero_documento=numero_documento,
            celular=celular,
            correo=correo,
            contrasena=generate_password_hash(contrasena).decode('utf-8')
        )

        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash("Registro exitoso. Inicia sesión con tus credenciales.", "success")
            return redirect(url_for('auth.register'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al registrar usuario: {e}", "error")
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """Cierra la sesión del usuario y muestra un mensaje flash."""
    session.clear()
    flash('Has cerrado sesión correctamente.', 'success')  # 'success' es la categoría del mensaje
    response = redirect(url_for('auth.index'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# ==============================================
# Rutas de recuperación de contraseña
# ==============================================

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Maneja el olvido de contraseña."""
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Buscar usuario en todas las tablas
        user = (Usuario.query.filter_by(correo=email).first() or 
                Profesional.query.filter_by(correo=email).first() or 
                Administrador.query.filter_by(correo=email).first())
        
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            db.session.commit()
            
            # Enviar correo con token
            msg = Message('Restablecer Contraseña', sender='tu_correo@gmail.com', recipients=[email])
            msg.body = f'Para restablecer tu contraseña, usa el siguiente token: {token}'
            mail.send(msg)
            
            flash("Se ha enviado un token a tu correo electrónico.", "success")
            return redirect(url_for('auth.reset_password'))
        else:
            flash("Correo electrónico no encontrado.", "error")
    
    return render_template('/auth/forgot_password.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Maneja el restablecimiento de contraseña."""
    if request.method == 'POST':
        token = request.form.get('token')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validaciones
        if new_password != confirm_password:
            flash("Las contraseñas no coinciden.", "error")
            return redirect(url_for('auth.reset_password'))
        
        if not validate_password(new_password):
            flash("La contraseña no cumple con los requisitos.", "error")
            return redirect(url_for('reset_password'))
        
        # Buscar usuario con el token
        user = (Usuario.query.filter_by(reset_token=token).first() or 
               Profesional.query.filter_by(reset_token=token).first() or 
               Administrador.query.filter_by(reset_token=token).first())
        
        if user and user.reset_token == token:
            user.contrasena = bcrypt.generate_password_hash(new_password).decode('utf-8')
            user.reset_token = None
            db.session.commit()
            flash("Contraseña restablecida con éxito.", "success")
            return redirect(url_for('auth.index'))
        else:
            flash("Token inválido o expirado.", "error")
    
    return render_template('/auth/reset_password.html')


@auth_bp.route('/editar_perfil', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    # Verificar si el usuario está logueado y la sesión es válida
    if 'logged_in' in session and session['logged_in']:
        # Obtener el id del usuario, profesional o administrador desde la sesión
        id_usuario = session.get('id_usuario')
        id_profesional = session.get('id_profesional')
        id_administrador = session.get('id_administrador')

        # Determinar el tipo de usuario
        if id_usuario:
            usuario = Usuario.query.get(id_usuario)
            tipo_usuario = 'usuario'
        elif id_profesional:
            usuario = Profesional.query.get(id_profesional)
            tipo_usuario = 'profesional'
        elif id_administrador:
            usuario = Administrador.query.get(id_administrador)
            tipo_usuario = 'administrador'
        else:
            flash("Usuario no encontrado.", "error")
            return redirect(url_for('auth.index'))

        # Si el método de la solicitud es POST, significa que el usuario está enviando datos para actualizar su perfil
        if request.method == 'POST':
            nombre = request.form['nombre']
            celular = request.form['celular']
            correo = request.form['correo']

            # Actualizar solo los campos permitidos
            usuario.nombre = nombre
            usuario.celular = celular
            usuario.correo = correo

            # Confirmar cambios en la base de datos
            try:
                db.session.commit()
                flash("Perfil actualizado correctamente.", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error al actualizar el perfil: {str(e)}", "error")
            
            # Redirigir a la página de configuración después de guardar cambios
            return redirect(url_for('auth.editar_perfil'))

        # Si el método es GET, obtener los datos actuales del usuario desde la base de datos
        if usuario:
            # Renderizar la plantilla de editar perfil con los datos del usuario autenticado
            return render_template('auth/editar_perfil.html', usuario=usuario, tipo_usuario=tipo_usuario)
        else:
            flash("Usuario no encontrado.", "error")
            return redirect(url_for('auth.index'))
    else:
        # Si no está logueado, redirigir al inicio de sesión
        return redirect(url_for('auth.index'))

