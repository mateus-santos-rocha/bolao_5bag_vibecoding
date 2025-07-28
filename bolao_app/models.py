# bolao_app/models.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import func

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    apostas = db.relationship('Aposta', backref='apostador', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Time(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    liga = db.Column(db.String(50), nullable=False)

class Partida(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_partida = db.Column(db.DateTime, nullable=False)
    match_type = db.Column(db.String(10), nullable=False, default='MD1') # MD1, MD3, MD5
    resultado = db.Column(db.String(100), nullable=True) # Armazena o nome do time vencedor, agora pode ser nulo
    score_time1 = db.Column(db.Integer, nullable=True)
    score_time2 = db.Column(db.Integer, nullable=True)

    time1_id = db.Column(db.Integer, db.ForeignKey('time.id'), nullable=False)
    time2_id = db.Column(db.Integer, db.ForeignKey('time.id'), nullable=False)

    time1 = db.relationship('Time', foreign_keys=[time1_id])
    time2 = db.relationship('Time', foreign_keys=[time2_id])

class Aposta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    partida_id = db.Column(db.Integer, db.ForeignKey('partida.id'), nullable=False)
    palpite_vencedor = db.Column(db.String(100), nullable=False)
    partida = db.relationship('Partida', backref='apostas', lazy=True)

class SolicitacaoApostaTardia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    partida_id = db.Column(db.Integer, db.ForeignKey('partida.id'), nullable=False)
    palpite_vencedor = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='pendente', nullable=False) # 'pendente', 'aprovada', 'rejeitada'
    timestamp = db.Column(db.DateTime, default=func.current_timestamp(), nullable=False)

    user = db.relationship('User', backref='solicitacoes_apostas_tardias', lazy=True)
    partida = db.relationship('Partida', backref='solicitacoes_apostas_tardias', lazy=True)
