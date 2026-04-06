import json
import os
import uuid
from datetime import datetime
from config import DATA_FILES, DEFAULT_DATA


def _get_file(empresa):
    return DATA_FILES.get(empresa, DATA_FILES['santaluzia'])


def _load_raw(empresa='santaluzia'):
    data_file = _get_file(empresa)
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
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
            _save_raw(migrated, empresa)
            return migrated
        return data
    return DEFAULT_DATA.copy()


def _save_raw(data, empresa='santaluzia'):
    data_file = _get_file(empresa)
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_all(empresa='santaluzia'):
    return _load_raw(empresa)['composicoes']


def get_composicao(comp_id, empresa='santaluzia'):
    return next((c for c in load_all(empresa) if c['id'] == comp_id), None)


def save_composicao(comp_data, empresa='santaluzia'):
    data = _load_raw(empresa)
    composicoes = data['composicoes']
    now = datetime.now().isoformat()
    comp_id = comp_data.get('id')

    if comp_id:
        for i, c in enumerate(composicoes):
            if c['id'] == comp_id:
                composicoes[i] = {**comp_data, 'atualizado_em': now, 'criado_em': c.get('criado_em', now)}
                _save_raw(data, empresa)
                return composicoes[i]

    # Nova composição
    nova = {**comp_data, 'id': str(uuid.uuid4()), 'criado_em': now, 'atualizado_em': now}
    composicoes.append(nova)
    _save_raw(data, empresa)
    return nova


def delete_composicao(comp_id, empresa='santaluzia'):
    data = _load_raw(empresa)
    data['composicoes'] = [c for c in data['composicoes'] if c['id'] != comp_id]
    _save_raw(data, empresa)
