from flask import Blueprint, request, jsonify
from services.data_service import load_all, get_composicao, save_composicao, delete_composicao

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/composicoes', methods=['GET'])
def listar():
    composicoes = load_all()
    summary = [
        {
            'id': c['id'],
            'titulo': c['titulo'],
            'num_itens': len(c.get('itens', [])),
            'atualizado_em': c.get('atualizado_em', ''),
        }
        for c in composicoes
    ]
    return jsonify(summary)


@api_bp.route('/composicoes/<comp_id>', methods=['GET'])
def carregar(comp_id):
    comp = get_composicao(comp_id)
    if not comp:
        return jsonify({'error': 'Não encontrado'}), 404
    return jsonify(comp)


@api_bp.route('/composicoes/<comp_id>', methods=['DELETE'])
def deletar(comp_id):
    delete_composicao(comp_id)
    return jsonify({'status': 'ok'})


@api_bp.route('/save', methods=['POST'])
def save():
    data = request.get_json()
    saved = save_composicao(data)
    return jsonify({'status': 'ok', 'id': saved['id']})
