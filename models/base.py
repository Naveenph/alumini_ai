from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth

# Share the db instance across models
db = SQLAlchemy()
mail = Mail()
oauth = OAuth()
