from flask import Blueprint,Flask, render_template, request, session, redirect, url_for, jsonify, flash
from ..models import Usuario, Profesional, Consulta
from ..extensions import db  # Asegúrate de que extensions.py contiene "db = SQLAlchemy()"
from ..auth.utils import login_required, validate_password

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin_home')
@login_required
def admin_home():
    """Página de inicio para administradores."""
    return render_template('admin/admin_home.html')

@admin_bp.route('/profesionales')
@login_required
def listar_profesionales():
    profesionales = Profesional.query.with_entities(Profesional.id_profesional, Profesional.nombre, Profesional.especialidad).all()
    return render_template('admin/lista_profesionales.html', profesionales=profesionales)

@admin_bp.route('/agregar_profesional', methods=["GET", "POST"])
@login_required
def agregar_profesional():
    if request.method == "POST":
        nombre = request.form['nombre']
        especialidad = request.form['especialidad']
        correo = request.form['correo']
        contrasena = request.form['contrasena']

        # Validación de la contraseña
        if not validate_password(contrasena):
            error = "La contraseña debe tener al menos 8 caracteres, incluyendo letras, números y caracteres especiales."
            return render_template('admin/agregar_profesional.html', error=error)

        # Crear un nuevo profesional
        nuevo_profesional = Profesional(
            nombre=nombre,
            especialidad=especialidad,
            correo=correo,
            contrasena=contrasena
        )

        # Insertar el nuevo profesional en la base de datos
        try:
            db.session.add(nuevo_profesional)
            db.session.commit()
            flash("Profesional agregado correctamente.", "success")
            return redirect(url_for('admin.listar_profesionales'))
        except Exception as e:
            db.session.rollback()
            error = "Error al agregar profesional: " + str(e)
            return render_template('admin/agregar_profesional.html', error=error)

    return render_template('admin/agregar_profesional.html')

@admin_bp.route('/eliminar_profesional/<int:id>', methods=["POST"])
@login_required
def eliminar_profesional(id):
    try:
        # Buscar el profesional por su ID
        profesional = Profesional.query.get(id)
        if profesional:
            # Eliminar el profesional de la base de datos
            db.session.delete(profesional)
            db.session.commit()
            flash("Profesional eliminado correctamente", "success")
        else:
            flash("Profesional no encontrado", "error")
    except Exception as e:
        # En caso de error, deshacer la transacción
        db.session.rollback()
        flash(f"Error al eliminar profesional: {str(e)}", "error")
    return redirect(url_for('admin.listar_profesionales'))


@admin_bp.route('/usuarios')
@login_required
def listar_usuarios():
    usuarios = Usuario.query.with_entities(Usuario.id_usuario, Usuario.numero_documento, Usuario.correo).all()
    return render_template('admin/lista_usuarios.html', usuarios=usuarios)


@admin_bp.route('/eliminar_usuario/<int:id>', methods=["POST"])
@login_required
def eliminar_usuario(id):
    try:
        usuario = Usuario.query.get(id)
        if usuario:
            db.session.delete(usuario)
            db.session.commit()
            flash('Usuario eliminado correctamente', 'success')
        else:
            flash('Usuario no encontrado', 'error')
    except Exception as e:
        db.session.rollback()
        flash("Error al eliminar usuario: " + str(e), 'error')
    return redirect(url_for('admin.listar_usuarios'))

@admin_bp.route('/citas_agendadas')
@login_required
def listar_citas():
    citas = db.session.query(
        Usuario.numero_documento,
        Profesional.nombre.label('nombre_profesional'),
        Consulta.fecha_consulta,
        Consulta.hora_consulta,
        Consulta.motivo,
        Consulta.id_consulta
    ).join(Usuario, Consulta.id_usuario == Usuario.id_usuario) \
     .outerjoin(Profesional, Consulta.id_profesional == Profesional.id_profesional) \
     .all()
    return render_template('admin/lista_consultas.html', citas=citas)


@admin_bp.route('/eliminar_cita/<int:id>', methods=['POST'])
@login_required
def eliminar_cita(id):
    try:
        cita = Consulta.query.get(id)
        if cita:
            db.session.delete(cita)
            db.session.commit()
            flash('La cita ha sido eliminada correctamente.', 'success')
        else:
            flash('Cita no encontrada.', 'error')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar la cita: ' + str(e), 'error')
    return redirect(url_for('admin.listar_citas'))

@admin_bp.route('/pacientes')
@login_required
def pacientes():
    if 'logged_in' in session and session['logged_in'] and 'id_profesional' in session:
        id_profesional = session['id_profesional']
        
        # Consulta similar a la de citas_asignadas pero agrupando por paciente
        pacientes = db.session.query(
            Usuario.nombre,
            Usuario.numero_documento,
            Usuario.celular,
            Usuario.correo
        ).join(Consulta, Usuario.id_usuario == Consulta.id_usuario
        ).filter(
            Consulta.id_profesional == id_profesional
        ).group_by(
            Usuario.id_usuario
        ).all()

        print("DEBUG - Pacientes encontrados:", pacientes)  # Para ver en consola
        return render_template('admin/lista_pacientes.html', pacientes=pacientes)
    return redirect(url_for('login'))