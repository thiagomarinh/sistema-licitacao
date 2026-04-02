from flask import Flask
from flask_login import LoginManager
from models import db, Empresa
from config import SECRET_KEY, DATABASE_URI

from routes.main import main_bp
from routes.api import api_bp
from routes.export import export_bp
from routes.auth import auth_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Faça login para acessar o sistema.'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Empresa, user_id)

app.register_blueprint(main_bp)
app.register_blueprint(api_bp)
app.register_blueprint(export_bp)
app.register_blueprint(auth_bp)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
