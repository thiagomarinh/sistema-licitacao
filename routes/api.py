import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Composicao

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/composicoes', methods=['GET'])
@login_required
def listar():
    composicoes = Composicao.query.filter_by(empresa_id=current_user.id)\
                                  .order_by(Composicao.atualizado_em.desc()).all()
    return jsonify([
        {
            'id':           c.id,
            'titulo':       c.titulo,
            'num_itens':    len(c.get_itens()),
            'atualizado_em':c.atualizado_em.isoformat() if c.atualizado_em else '',
        }
        for c in composicoes
    ])


@api_bp.route('/composicoes/<comp_id>', methods=['GET'])
@login_required
def carregar(comp_id):
    c = Composicao.query.filter_by(id=comp_id, empresa_id=current_user.id).first()
    if not c:
        return jsonify({'error': 'Não encontrado'}), 404
    return jsonify(c.to_dict())


@api_bp.route('/composicoes/<comp_id>', methods=['DELETE'])
@login_required
def deletar(comp_id):
    c = Composicao.query.filter_by(id=comp_id, empresa_id=current_user.id).first()
    if c:
        db.session.delete(c)
        db.session.commit()
    return jsonify({'status': 'ok'})


@api_bp.route('/save', methods=['POST'])
@login_required
def save():
    data = request.get_json()
    comp_id = data.get('id')

    if comp_id:
        c = Composicao.query.filter_by(id=comp_id, empresa_id=current_user.id).first()
    else:
        c = None

    if not c:
        c = Composicao(empresa_id=current_user.id)
        db.session.add(c)

    c.titulo       = data.get('titulo', '')
    c.num_pregao   = data.get('num_pregao', '')
    c.num_processo = data.get('num_processo', '')
    c.config_json  = json.dumps(data.get('config', {}), ensure_ascii=False)
    c.itens_json   = json.dumps(data.get('itens', []), ensure_ascii=False)
    c.atualizado_em = datetime.utcnow()

    db.session.commit()
    return jsonify({'status': 'ok', 'id': c.id})


@api_bp.route('/produtos', methods=['GET'])
@login_required
def buscar_produtos():
    q = request.args.get('q', '').strip().lower()
    if len(q) < 2:
        return jsonify([])

    composicoes = Composicao.query.filter_by(empresa_id=current_user.id)\
                                  .order_by(Composicao.atualizado_em.desc()).all()

    vistos = {}
    for comp in composicoes:
        for item in comp.get_itens():
            desc = (item.get('descricao') or '').strip()
            if not desc:
                continue
            chave = desc.lower()
            if q in chave and chave not in vistos:
                vistos[chave] = {
                    'descricao':  desc,
                    'unidade':    item.get('unidade', ''),
                    'fornecedor': item.get('fornecedor', ''),
                    'marca':      item.get('marca', ''),
                    'custo_unit': item.get('custo_unit', ''),
                }

    resultados = sorted(vistos.values(), key=lambda x: x['descricao'].lower())
    return jsonify(resultados[:10])


@api_bp.route('/empresa/info', methods=['GET'])
@login_required
def empresa_info():
    e = current_user
    return jsonify({
        'nome':        e.nome,
        'cnpj':        e.cnpj,
        'responsavel': e.responsavel,
        'documento':   e.documento,
        'endereco':    e.endereco,
        'telefone':    e.telefone,
        'site':        e.site,
        'logo_path':   e.logo_path,
    })
