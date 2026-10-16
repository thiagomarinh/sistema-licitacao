import uuid
import json
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Empresa(UserMixin, db.Model):
    __tablename__ = 'empresas'

    id           = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nome         = db.Column(db.String(200), nullable=False)
    email        = db.Column(db.String(200), unique=True, nullable=False)
    senha_hash   = db.Column(db.String(256), nullable=False)
    cnpj         = db.Column(db.String(20))
    responsavel  = db.Column(db.String(200))
    documento    = db.Column(db.String(30))   # CPF do responsável
    rg           = db.Column(db.String(30))   # RG do responsável
    endereco     = db.Column(db.String(300))
    telefone     = db.Column(db.String(30))
    site         = db.Column(db.String(200))
    logo_path    = db.Column(db.String(300))  # caminho relativo em static/logos/
    criado_em    = db.Column(db.DateTime, default=datetime.utcnow)

    composicoes  = db.relationship('Composicao',  backref='empresa', lazy=True, cascade='all, delete-orphan')
    documentos   = db.relationship('Documento',   backref='empresa', lazy=True, cascade='all, delete-orphan')
    declaracoes  = db.relationship('Declaracao',  backref='empresa', lazy=True, cascade='all, delete-orphan')

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


class Composicao(db.Model):
    __tablename__ = 'composicoes'

    id           = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id   = db.Column(db.String(36), db.ForeignKey('empresas.id'), nullable=False)
    titulo       = db.Column(db.String(300), default='COMPOSIÇÃO DE PREÇOS - LICITAÇÃO')
    num_pregao   = db.Column(db.String(100))
    num_processo = db.Column(db.String(100))
    config_json  = db.Column(db.Text, default='{}')
    itens_json   = db.Column(db.Text, default='[]')
    criado_em    = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em= db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_config(self):
        return json.loads(self.config_json or '{}')

    def get_itens(self):
        return json.loads(self.itens_json or '[]')

    def to_dict(self):
        return {
            'id':           self.id,
            'titulo':       self.titulo,
            'num_pregao':   self.num_pregao,
            'num_processo': self.num_processo,
            'config':       self.get_config(),
            'itens':        self.get_itens(),
            'criado_em':    self.criado_em.isoformat() if self.criado_em else '',
            'atualizado_em':self.atualizado_em.isoformat() if self.atualizado_em else '',
        }


class Declaracao(db.Model):
    __tablename__ = 'declaracoes'

    id           = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id   = db.Column(db.String(36), db.ForeignKey('empresas.id'), nullable=False)
    nome         = db.Column(db.String(300), nullable=False)
    arquivo_path = db.Column(db.String(500))   # template original .docx
    arquivo_nome = db.Column(db.String(300))
    gerada_em    = db.Column(db.DateTime)
    criado_em    = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def nunca_gerada(self):
        return self.gerada_em is None


class Documento(db.Model):
    __tablename__ = 'documentos'

    id               = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    empresa_id       = db.Column(db.String(36), db.ForeignKey('empresas.id'), nullable=False)
    nome             = db.Column(db.String(300), nullable=False)
    categoria        = db.Column(db.String(100))
    arquivo_path     = db.Column(db.String(500))
    arquivo_nome     = db.Column(db.String(300))
    data_vencimento  = db.Column(db.Date)
    criado_em        = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def status(self):
        if not self.data_vencimento:
            return 'sem_vencimento'
        hoje = date.today()
        diff = (self.data_vencimento - hoje).days
        if diff < 0:
            return 'vencido'
        elif diff <= 30:
            return 'vence_em_breve'
        return 'valido'

    @property
    def dias_para_vencer(self):
        if not self.data_vencimento:
            return None
        return (self.data_vencimento - date.today()).days
