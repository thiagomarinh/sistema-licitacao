import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Documento

docs_bp = Blueprint('documentos', __name__, url_prefix='/documentos')

ALLOWED_EXT = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx'}
BASE_UPLOAD = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'documentos')

CATEGORIAS = [
    'Certidão Negativa Federal',
    'Certidão Negativa Estadual',
    'Certidão Negativa Municipal',
    'Certidão FGTS',
    'Certidão Trabalhista',
    'Alvará de Funcionamento',
    'Contrato Social',
    'Procuração',
    'Outros',
]


def pasta_empresa():
    pasta = os.path.join(BASE_UPLOAD, current_user.id)
    os.makedirs(pasta, exist_ok=True)
    return pasta


def allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


@docs_bp.route('/')
@login_required
def index():
    filtro = request.args.get('filtro', 'todos')
    docs = Documento.query.filter_by(empresa_id=current_user.id)\
                          .order_by(Documento.data_vencimento.asc()).all()

    if filtro == 'vencido':
        docs = [d for d in docs if d.status == 'vencido']
    elif filtro == 'vence_em_breve':
        docs = [d for d in docs if d.status == 'vence_em_breve']
    elif filtro == 'valido':
        docs = [d for d in docs if d.status == 'valido']

    contagem = {
        'todos':         Documento.query.filter_by(empresa_id=current_user.id).count(),
        'vencido':       sum(1 for d in Documento.query.filter_by(empresa_id=current_user.id) if d.status == 'vencido'),
        'vence_em_breve':sum(1 for d in Documento.query.filter_by(empresa_id=current_user.id) if d.status == 'vence_em_breve'),
        'valido':        sum(1 for d in Documento.query.filter_by(empresa_id=current_user.id) if d.status == 'valido'),
    }

    return render_template('documentos.html', docs=docs, filtro=filtro,
                           contagem=contagem, categorias=CATEGORIAS)


@docs_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    nome      = request.form.get('nome', '').strip()
    categoria = request.form.get('categoria', '').strip()
    venc_str  = request.form.get('data_vencimento', '').strip()
    arquivo   = request.files.get('arquivo')

    data_venc = None
    if venc_str:
        try:
            data_venc = datetime.strptime(venc_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    doc = Documento(
        empresa_id      = current_user.id,
        nome            = nome or (arquivo.filename if arquivo else 'Documento'),
        categoria       = categoria,
        data_vencimento = data_venc,
    )

    if arquivo and arquivo.filename and allowed(arquivo.filename):
        db.session.add(doc)
        db.session.flush()  # gera o id antes de salvar o arquivo
        ext = arquivo.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"{doc.id}.{ext}")
        arquivo.save(os.path.join(pasta_empresa(), filename))
        doc.arquivo_path = f"documentos/{current_user.id}/{filename}"
        doc.arquivo_nome = arquivo.filename

    db.session.add(doc)
    db.session.commit()
    return redirect(url_for('documentos.index'))


@docs_bp.route('/download/<doc_id>')
@login_required
def download(doc_id):
    doc = Documento.query.filter_by(id=doc_id, empresa_id=current_user.id).first_or_404()
    if not doc.arquivo_path:
        abort(404)
    caminho = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', doc.arquivo_path)
    return send_file(caminho, as_attachment=True, download_name=doc.arquivo_nome or 'documento')


@docs_bp.route('/deletar/<doc_id>', methods=['POST'])
@login_required
def deletar(doc_id):
    doc = Documento.query.filter_by(id=doc_id, empresa_id=current_user.id).first_or_404()
    if doc.arquivo_path:
        caminho = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', doc.arquivo_path)
        if os.path.exists(caminho):
            os.remove(caminho)
    db.session.delete(doc)
    db.session.commit()
    return redirect(url_for('documentos.index'))
