from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

# Share the db instance across models
db = SQLAlchemy()
mail = Mail()
