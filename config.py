import os

BASE_DIR = os.path.dirname(__file__)

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-mude-em-producao')
DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "composicoes.db")}')

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'logos')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Legado — mantido para eventual migração dos JSON
DATA_FILES = {
    'santaluzia':  os.path.join(BASE_DIR, 'data_santaluzia.json'),
    'sabbaeletro': os.path.join(BASE_DIR, 'data_sabbaeletro.json'),
}

DEFAULT_DATA = {"composicoes": []}
