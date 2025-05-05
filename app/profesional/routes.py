from flask import Blueprint,redirect,flash, request,  url_for, render_template,session
from flask_login import login_required
from datetime import datetime,date
from ..models import Consulta, Usuario
from .utils import obtener_id_usuario_actual
from ..extensions import db
from ..auth.utils import login_required


profesional_bp = Blueprint('profesional', __name__)


@profesional_bp.route('/profesional_home')
@login_required

def profesional_home():
    """Página de inicio para profesionales."""
    return render_template('profesional/profesional_home.html')

@profesional_bp.route('/pacientes')
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
        return render_template('profesional/lista_pacientes.html', pacientes=pacientes)
    return redirect(url_for('auth.index'))

@profesional_bp.route('/citas_asignadas')
@login_required
def citas_asignadas():
    if 'logged_in' in session and session['logged_in']:
        id_profesional = obtener_id_usuario_actual()

        # Actualiza el estado de las citas en tiempo real
        Consulta.query.filter(
            Consulta.fecha_consulta < datetime.now().date(),
            Consulta.estado == 'Pendiente'
        ).update({'estado': 'Tomada'}, synchronize_session=False)
        db.session.commit()

        # Selecciona las citas asignadas al profesional
        citas = db.session.query(
            Consulta.id_consulta,
            Usuario.nombre.label('nombre_paciente'),
            Usuario.numero_documento,
            Usuario.correo.label('correo_paciente'),
            Consulta.fecha_consulta,
            Consulta.hora_consulta,
            Consulta.motivo,
            Consulta.estado
        ).join(Usuario, Consulta.id_usuario == Usuario.id_usuario) \
         .filter(Consulta.id_profesional == id_profesional) \
         .all()

        return render_template('/profesional/citas_asignadas.html', citas=citas)
    else:
        return redirect(url_for('auth.index'))


@profesional_bp.route('/diagnosticos_tratamientos')
@login_required
def diagnosticos_tratamientos():
    if 'logged_in' in session and session['logged_in'] and 'id_profesional' in session:
        id_profesional = session['id_profesional']

        # Consulta corregida para evitar duplicados
        consultas = db.session.query(
            Consulta.id_consulta,
            Usuario.numero_documento,
            Consulta.fecha_consulta,
            Consulta.hora_consulta,
            Consulta.motivo,
            Consulta.diagnostico,
            Consulta.tratamiento
        ).join(Usuario, Consulta.id_usuario == Usuario.id_usuario
        ).filter(
            Consulta.id_profesional == id_profesional,
            Consulta.fecha_consulta <= date.today()  # Solo citas pasadas o hoy
        ).distinct().all()  # Añade .distinct() para eliminar duplicados

        return render_template('profesional/diagnosticos_tratamientos.html', consultas=consultas)
    
    return redirect(url_for('auth.index'))

@profesional_bp.route('/editar_diagnostico_tratamiento/<int:id_consulta>', methods=['POST'])
@login_required
def editar_diagnostico_tratamiento(id_consulta):
    if 'logged_in' in session and session['logged_in']:
        try:
            # Obtener el diagnóstico y tratamiento del formulario
            diagnostico = request.form['diagnostico']
            tratamiento = request.form['tratamiento']

            # Buscar la consulta por su ID
            consulta = Consulta.query.get(id_consulta)
            if consulta:
                # Actualizar el diagnóstico y tratamiento
                consulta.diagnostico = diagnostico
                consulta.tratamiento = tratamiento
                db.session.commit()
                flash('El diagnóstico y tratamiento se han actualizado correctamente.', 'success')
            else:
                flash('Consulta no encontrada.', 'error')
        except Exception as e:
            # En caso de error, deshacer la transacción
            db.session.rollback()
            flash(f"Error al actualizar el diagnóstico y tratamiento: {str(e)}", 'error')
        
        # Redirigir a la página de diagnósticos y tratamientos
        return redirect(url_for('profesional.diagnosticos_tratamientos'))
    else:
        # Si no está logueado, redirigir al index
        return redirect(url_for('auth.index'))
    
    
