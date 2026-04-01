import json
import os
import uuid
from datetime import datetime
from config import DATA_FILE, DEFAULT_DATA


def _load_raw():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Migração: formato antigo não tinha 'composicoes'
        if 'composicoes' not in data:
            comp = {
                'id': str(uuid.uuid4()),
                'titulo': data.get('titulo', 'COMPOSIÇÃO DE PREÇOS - LICITAÇÃO'),
                'config': data.get('config', {'taxa': 7.0, 'lucro_liq': 9.0, 'dasn': 3.0}),
                'itens': data.get('itens', []),
                'criado_em': datetime.now().isoformat(),
                'atualizado_em': datetime.now().isoformat(),
            }
            migrated = {'composicoes': [comp] if comp['itens'] else []}
            _save_raw(migrated)
            return migrated
        return data
    return DEFAULT_DATA.copy()


def _save_raw(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_all():
    return _load_raw()['composicoes']


def get_composicao(comp_id):
    return next((c for c in load_all() if c['id'] == comp_id), None)


def save_composicao(comp_data):
    data = _load_raw()
    composicoes = data['composicoes']
    now = datetime.now().isoformat()
    comp_id = comp_data.get('id')

    if comp_id:
        for i, c in enumerate(composicoes):
            if c['id'] == comp_id:
                composicoes[i] = {**comp_data, 'atualizado_em': now, 'criado_em': c.get('criado_em', now)}
                _save_raw(data)
                return composicoes[i]

    # Nova composição
    nova = {**comp_data, 'id': str(uuid.uuid4()), 'criado_em': now, 'atualizado_em': now}
    composicoes.append(nova)
    _save_raw(data)
    return nova


def delete_composicao(comp_id):
    data = _load_raw()
    data['composicoes'] = [c for c in data['composicoes'] if c['id'] != comp_id]
    _save_raw(data)
