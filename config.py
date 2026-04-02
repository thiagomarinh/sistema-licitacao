import os

BASE_DIR = os.path.dirname(__file__)

DATA_FILES = {
    'santaluzia':  os.path.join(BASE_DIR, 'data_santaluzia.json'),
    'sabbaeletro': os.path.join(BASE_DIR, 'data_sabbaeletro.json'),
}

DEFAULT_DATA = {
    "composicoes": []
}
