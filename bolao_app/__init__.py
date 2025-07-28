# bolao_app/__init__.py
from flask import Flask
from flask_login import LoginManager
from .models import db, User
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'login' # O nome da rota de login
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        print(f"DEBUG: load_user chamado para user_id={user_id}")
        return User.query.get(int(user_id))

    with app.app_context():
        # Importa as rotas aqui para evitar importação circular
        from . import routes
        
        # Cria as tabelas no banco de dados se elas não existirem
        db.create_all()

        # Cria o usuário admin se ele não existir
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', is_admin=True)
            admin_user.set_password('0292')
            db.session.add(admin_user)
            db.session.commit()

    return app
