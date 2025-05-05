
from flask import session
def obtener_id_usuario_actual():
    """Obtiene el ID del usuario actualmente logueado."""
    if 'id_profesional' in session:
        return session['id_profesional']
    elif 'id_administrador' in session:
        return session['id_administrador']
    elif 'id_usuario' in session:
        return session['id_usuario']
    return None