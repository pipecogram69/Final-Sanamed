from datetime import datetime
from ..models import Emocion, Consulta
from collections import Counter
from ..extensions import db  # Asegúrate de que extensions.py contiene "db = SQLAlchemy()"
from ..models import Perfil, Usuario, Profesional, Administrador, Consulta, Emocion, ProfesionalUsuario, FamiliaGratitud
from datetime import datetime, timedelta
from functools import wraps
from flask import flash, redirect, url_for, session

juegos = [
    {
        "id": 1,
        "nombre": "Meditación",
        "descripcion": "Un juego que te guía a través de una serie de ejercicios de meditación.",
        "dificultad": "Fácil",
        "duracion": "10 minutos"
    },
    {
        "id": 2,
        "nombre": "Cuestionario de Autoevaluación",
        "descripcion": "Evalúa tu estado emocional y mental con este cuestionario.",
        "dificultad": "Moderada",
        "duracion": "5 minutos"
    },
    {
        "id": 3,
        "nombre": "Desafío de Estrategia",
        "descripcion": "Desarrolla habilidades de pensamiento crítico y resolución de problemas.",
        "dificultad": "Difícil",
        "duracion": "15 minutos"
    },
    {
        "id": 4,
        "nombre": "Respiración Profunda",
        "descripcion": "Aprende técnicas de respiración para reducir la ansiedad.",
        "dificultad": "Fácil",
        "duracion": "5 minutos"
    },
    {
        "id": 5,
        "nombre": "Jardín de Gratitud",
        "descripcion": "Expresa y comparte cosas por las que estás agradecido.",
        "dificultad": "Fácil",
        "duracion": "Sin límite"
    }
]


def login_required(f):
    """Decorador para rutas que requieren autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Por favor inicie sesión para acceder a esta página', 'error')
            return redirect(url_for('auth.login'))
        
        # Verificar inactividad (opcional)
        if 'last_activity' in session:
            last_activity = datetime.fromisoformat(session['last_activity'])
            if datetime.now() - last_activity > timedelta(minutes=30):
                session.clear()
                flash('Sesión expirada por inactividad', 'error')
                return redirect(url_for('auth.login'))
        
        session['last_activity'] = datetime.now().isoformat()
        return f(*args, **kwargs)
    return decorated_function

def obtener_profesionales_disponibles():
    """Obtiene todos los profesionales disponibles."""
    return Profesional.query.with_entities(
        Profesional.id_profesional,
        Profesional.nombre,
        Profesional.especialidad
    ).all()

def obtener_nombre_profesional(id_profesional):
    """Obtiene el nombre de un profesional por su ID."""
    profesional = Profesional.query.filter_by(id_profesional=id_profesional).first()
    return profesional.nombre if profesional else None

def obtener_emociones_por_fecha(fecha):
    emociones_data = Emocion.query.filter(db.func.date(Emocion.fecha_emocion) == fecha).with_entities(
        Emocion.emocion,
        db.func.extract('hour', Emocion.fecha_emocion).label('hora'),
        db.func.extract('minute', Emocion.fecha_emocion).label('minuto')
    ).all()

    emociones = []
    horas = []
    for row in emociones_data:
        emociones.append(row.emocion)
        hora = str(int(row.hora)).zfill(2)
        minuto = str(int(row.minuto)).zfill(2)
        hora_formateada = f"{hora}:{minuto}"
        horas.append(hora_formateada)

    return emociones, horas
def obtener_consultas_por_usuario(id_usuario):
    consultas = db.session.query(
        Consulta.id_consulta,  # índice 0
        Consulta.id_profesional,  # índice 1
        Consulta.fecha_consulta,  # índice 2
        Consulta.hora_consulta,  # índice 3
        Consulta.motivo  # índice 4
    ).filter_by(id_usuario=id_usuario).all()
    return consultas

def obtener_especialidad_profesional(id_profesional):
    """Obtiene la especialidad de un profesional por su ID."""
    profesional = Profesional.query.filter_by(id_profesional=id_profesional).first()
    return profesional.especialidad if profesional else None

def obtener_conteo_emociones_por_fecha(fecha):
    """Obtiene el conteo de emociones por fecha."""
    emociones = Emocion.query.filter(db.func.date(Emocion.fecha_emocion) == fecha).with_entities(Emocion.emocion).all()
    emociones = [row.emocion for row in emociones]
    return dict(Counter(emociones))

def time_en_rango(hora, inicio, fin):
    return inicio <= hora <= fin
