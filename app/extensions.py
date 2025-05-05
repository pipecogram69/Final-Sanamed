from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_migrate import Migrate

# Extensiones compartidas
db = SQLAlchemy()
bcrypt = Bcrypt()
mail = Mail()
migrate = Migrate()