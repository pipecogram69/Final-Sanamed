from ..models import Consulta
from flask import flash, redirect, url_for, session
from datetime import datetime, timedelta
from functools import wraps

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

def obtener_id_usuario_actual():
    """Obtiene el ID del usuario actualmente logueado."""
    if 'id_profesional' in session:
        return session['id_profesional']
    elif 'id_administrador' in session:
        return session['id_administrador']
    elif 'id_usuario' in session:
        return session['id_usuario']
    return None