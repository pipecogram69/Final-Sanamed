from flask import Flask
from .extensions import db, bcrypt, mail, migrate 
from .auth.routes import auth_bp
from .admin.routes import admin_bp
from .user.routes import user_bp
from .profesional.routes import profesional_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Inicializar extensiones
    db.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # Registrar blueprints
    from .auth.routes import auth_bp
    from .user.routes import user_bp
    from .profesional.routes import profesional_bp
    from .admin.routes import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(profesional_bp, url_prefix='/profesional')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    
    return app
