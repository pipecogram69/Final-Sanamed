from flask import Blueprint,Flask, render_template, request, session, redirect, url_for, jsonify, flash
from flask_login import login_required
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_bcrypt import Bcrypt, check_password_hash, generate_password_hash
from flask_migrate import Migrate
from datetime import datetime, date, timedelta, time
from ..extensions import db  # Asegúrate de que extensions.py contiene "db = SQLAlchemy()"
from .utils import juegos, obtener_conteo_emociones_por_fecha, obtener_emociones_por_fecha, obtener_profesionales_disponibles, obtener_especialidad_profesional, obtener_nombre_profesional
from ..models import Emocion, Consulta, FamiliaGratitud
from ..auth.utils import login_required


user_bp = Blueprint('user', __name__)


@user_bp.route('/home')
@login_required
def user_home():
    """Página de inicio para usuarios."""
    return render_template('user/user_home.html')

@user_bp.route('/configuracion')
@login_required
def configuracion():
    """Página de configuración del usuario."""
    return render_template('user/configuracion.html')
@user_bp.route('/sobre_nosotros')
@login_required
def sobre_nosotros():
    """Página sobre nosotros."""
    return render_template('user/sobre_nosotros.html')

@user_bp.route('/preguntas_frecuentes')
@login_required
def preguntas_frecuentes():
    """Página de preguntas frecuentes."""
    return render_template('user/preguntas_frecuentes.html')


@user_bp.route('/registro_emocion', methods=['POST'])
@login_required
def registro_emocion():
    """Registra una nueva emoción para el usuario."""
    if 'id_usuario' not in session:
        flash("Debes iniciar sesión como usuario.", "error")
        return redirect(url_for('auth.login'))

    emocion = request.form.get('emocion')
    if not emocion:
        flash("No se recibió ninguna emoción", "error")
        return redirect(url_for('user.user_home'))

    try:
        nueva_emocion = Emocion(
            id_usuario=session['id_usuario'],
            emocion=emocion,
            fecha_emocion=datetime.now()
        )
        db.session.add(nueva_emocion)
        db.session.commit()
        flash("Emoción registrada correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error al registrar la emoción.", "error")
    
    return redirect(url_for('user.user_home'))  # Mejor que render_template para evitar duplicados


@user_bp.route('/games')
@login_required
def games():
    return render_template('user/games.html')

@user_bp.route('/api/juegos', methods=['GET'])
def obtener_juegos():
    return jsonify({"juegos": juegos}), 200

@user_bp.route('/rompecabezas')
def rompecabezas():
    return render_template('rompecabezas.html')


@user_bp.route('/laberinto')
def laberinto():
    return render_template('laberinto.html')


def time_en_rango(hora, inicio, fin):
    return inicio <= hora <= fin



@user_bp.route('/agregar_gratitud', methods=['POST'])
@login_required
def agregar_gratitud():
    if 'id_usuario' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    data = request.get_json()
    gratitud = data.get('gratitud', '').strip()
    
    if not gratitud:
        return jsonify({'error': 'El texto de gratitud no puede estar vacío'}), 400

    try:
        nueva_gratitud = FamiliaGratitud(
            gratitud=gratitud,
            id_usuario=session['id_usuario']
        )
        db.session.add(nueva_gratitud)
        db.session.commit()
        return jsonify({
            'message': 'Gratitud agregada',
            'id_gratitud': nueva_gratitud.id_gratitud
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/eliminar_gratitud/<int:id_gratitud>', methods=['DELETE'])
@login_required
def eliminar_gratitud(id_gratitud):
    if 'id_usuario' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    gratitud = FamiliaGratitud.query.filter_by(
        id_gratitud=id_gratitud,
        id_usuario=session['id_usuario']
    ).first()

    if not gratitud:
        return jsonify({'error': 'Gratitud no encontrada'}), 404

    try:
        db.session.delete(gratitud)
        db.session.commit()
        return jsonify({'message': 'Gratitud eliminada'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/cargar_gratitudes', methods=['GET'])
@login_required
def cargar_gratitudes():
    if 'id_usuario' not in session:
        return jsonify({'error': 'No autenticado'}), 401

    gratitudes = FamiliaGratitud.query.filter_by(
        id_usuario=session['id_usuario']
    ).order_by(FamiliaGratitud.fecha.desc()).all()

    return jsonify({
        'gratitudes': [{
            'id': g.id_gratitud,
            'texto': g.gratitud,
            'fecha': g.fecha.isoformat()
        } for g in gratitudes]
    }), 200
    
    
    
@user_bp.route('/agendar_cita', methods=["GET", "POST"])
@login_required
def agendar_cita():
    if 'logged_in' in session and session['logged_in']:
        profesionales = obtener_profesionales_disponibles()
        
        if request.method == "POST":
            fecha = request.form['fecha']
            hora = request.form['hora']
            motivo = request.form['motivo']
            id_usuario = session['id_usuario']
            id_profesional = request.form['profesional']

            # Convertir formatos de fecha y hora
            fecha_consulta = datetime.strptime(fecha, '%Y-%m-%d').date()
            hora_24 = datetime.strptime(hora, '%I:%M %p').time()
            fecha_actual = date.today()

            # Validación 1: Fecha no puede ser anterior a hoy
            if fecha_consulta < fecha_actual:
                flash("No puedes programar una cita en una fecha pasada.", "error")
                return render_template('user/agendar_cita.html', profesionales=profesionales)

            # Validación 2: Horario laboral (8:00 - 17:00)
            if hora_24 < time(8, 0) or hora_24 > time(17, 0):
                flash("La hora debe estar entre 8:00 AM y 5:00 PM.", "error")
                return render_template('user/agendar_cita.html', profesionales=profesionales)

            # Validación 3: No permitir que el usuario tenga más de 3 citas el mismo día (puedes ajustar este número)
            citas_usuario_mismo_dia = Consulta.query.filter(
                Consulta.id_usuario == id_usuario,
                Consulta.fecha_consulta == fecha_consulta
            ).count()
            
            if citas_usuario_mismo_dia >= 3:  # Límite de 3 citas por día
                flash("Has alcanzado el límite de citas para este día (máximo 3).", "error")
                return render_template('user/agendar_cita.html', profesionales=profesionales)

            # Validación 4: Profesional no debe tener cita a la misma hora
            cita_profesional_misma_hora = Consulta.query.filter(
                Consulta.id_profesional == id_profesional,
                Consulta.fecha_consulta == fecha_consulta,
                Consulta.hora_consulta == hora_24
            ).first()
            
            if cita_profesional_misma_hora:
                flash("El profesional ya tiene una cita programada para esta hora.", "error")
                return render_template('user/agendar_cita.html', profesionales=profesionales)

            # Si pasa todas las validaciones, crear la cita
            nueva_cita = Consulta(
                id_usuario=id_usuario,
                id_profesional=id_profesional,
                fecha_consulta=fecha_consulta,
                hora_consulta=hora_24,
                motivo=motivo,
                estado='Pendiente'
            )

            try:
                db.session.add(nueva_cita)
                db.session.commit()
                flash("Cita agendada exitosamente!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error al agendar cita: {str(e)}", "error")

        return render_template('user/agendar_cita.html', profesionales=profesionales)
    else:
        return redirect(url_for('auth.index'))
# Nueva ruta para obtener horarios disponibles
@user_bp.route('/obtener_horarios_disponibles', methods=['POST'])
@login_required
def obtener_horarios_disponibles():
    data = request.get_json()
    fecha = data.get('fecha')
    id_profesional = data.get('profesional')
    
    if not fecha or not id_profesional:
        return jsonify({'error': 'Datos incompletos'}), 400
    
    try:
        fecha_consulta = datetime.strptime(fecha, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    # Obtener todas las horas posibles
    horas_posibles = [
        '08:00 AM', '09:00 AM', '10:00 AM', '11:00 AM', '12:00 PM',
        '01:00 PM', '02:00 PM', '03:00 PM', '04:00 PM', '05:00 PM'
    ]
    
    # Obtener citas ya agendadas para ese profesional en esa fecha
    citas_agendadas = Consulta.query.filter(
        Consulta.id_profesional == id_profesional,
        Consulta.fecha_consulta == fecha_consulta
    ).all()
    
    # Convertir horas agendadas al formato de 12 horas
    horas_ocupadas = []
    for cita in citas_agendadas:
        hora_24 = cita.hora_consulta.strftime('%H:%M')
        hora_12 = datetime.strptime(hora_24, '%H:%M').strftime('%I:%M %p')
        horas_ocupadas.append(hora_12)
    
    # Filtrar horas disponibles
    horas_disponibles = [hora for hora in horas_posibles if hora not in horas_ocupadas]
    
    return jsonify({'horas_disponibles': horas_disponibles})
    
@user_bp.route('/calendario')
@login_required
def mostrar_calendario():
    # Aquí debes implementar la lógica para mostrar el calendario
    return render_template('user/calendario.html')


@user_bp.route('/seleccionar_dia', methods=['GET'])
@login_required
def seleccionar_dia():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('index'))
    
    fecha = request.args.get('fecha')  # Usar args para GET en lugar de form
    
    if not fecha:
        return redirect(url_for('user.mostrar_calendario'))
    
    # Convertir la fecha de string a objeto date
    try:
        fecha_seleccionada = datetime.strptime(fecha, '%Y-%m-%d').date()
    except ValueError:
        flash("Formato de fecha inválido", "error")
        return redirect(url_for('user.mostrar_calendario'))
    
    # Obtener emociones del usuario para esa fecha
    emociones = Emocion.query.filter(
        Emocion.id_usuario == session['id_usuario'],
        db.func.date(Emocion.fecha_emocion) == fecha_seleccionada
    ).all()
    
    if not emociones:
        flash(f"No hay emociones registradas para el {fecha_seleccionada.strftime('%d/%m/%Y')}", "info")
        return redirect(url_for('mostrar_calendario'))
    
    return render_template('user/emociones.html', 
                         emociones=emociones,
                         fecha_seleccionada=fecha_seleccionada)
    
@user_bp.route('/ver_grafica/<fecha>')
@login_required
def ver_grafica(fecha):
    conteo_emociones = obtener_conteo_emociones_por_fecha(fecha)
    
    if not conteo_emociones:
        mensaje = "No hay emociones registradas para este día."
        return render_template('user/calendario.html', mensaje=mensaje)
    
    # Extraer etiquetas (emociones) y valores (conteo de cada emoción)
    emociones = list(conteo_emociones.keys())
    cantidades = list(conteo_emociones.values())
    
    return render_template(
        'user/grafica_emociones.html', 
        fecha_seleccionada=fecha, 
        emociones=emociones, 
        cantidades=cantidades
    )

@user_bp.route('/consultas_dia')
@login_required
def consultas_dia():
    if 'logged_in' not in session or not session['logged_in'] or 'id_usuario' not in session:
        flash('Debes iniciar sesión para ver tus citas', 'error')
        return redirect(url_for('auth.login'))

    consultas = db.session.query(
        Consulta.id_consulta,        # índice 0 (para eliminar)
        Consulta.id_profesional,     # índice 1
        Consulta.fecha_consulta,     # índice 2
        Consulta.hora_consulta,      # índice 3
        Consulta.motivo              # índice 4
    ).filter_by(id_usuario=session['id_usuario']).all()

    return render_template('user/consultas.html', consultas=consultas, obtener_nombre_profesional=obtener_nombre_profesional, obtener_especialidad_profesional=obtener_especialidad_profesional
    )


@user_bp.route('/eliminar_consulta/<int:id>', methods=['POST'])
@login_required
def eliminar_consulta(id):
    if 'logged_in' not in session or not session['logged_in']:
        flash('Debes iniciar sesión para realizar esta acción', 'error')
        return redirect(url_for('auth.login'))

    try:
        # Buscar la consulta a eliminar
        consulta = Consulta.query.get(id)
        
        if consulta:
            # Verificar que el usuario es el dueño de la consulta
            if 'id_usuario' in session and consulta.id_usuario == session['id_usuario']:
                db.session.delete(consulta)
                db.session.commit()
                flash('La cita ha sido eliminada correctamente', 'success')
            else:
                flash('No tienes permiso para eliminar esta cita', 'error')
        else:
            flash('La cita no existe o ya fue eliminada', 'error')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la cita: {str(e)}', 'error')
    
    return redirect(url_for('user.consultas_dia'))