import os
import io
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, send_file, abort, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from docxtpl import DocxTemplate
from models import db, Declaracao

decl_bp = Blueprint('declaracoes', __name__, url_prefix='/declaracoes')

BASE_UPLOAD = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'declaracoes')


def pasta_empresa():
    pasta = os.path.join(BASE_UPLOAD, current_user.id)
    os.makedirs(pasta, exist_ok=True)
    return pasta


@decl_bp.route('/')
@login_required
def index():
    decls = Declaracao.query.filter_by(empresa_id=current_user.id)\
                            .order_by(Declaracao.criado_em.desc()).all()

    # avisa se dados da empresa estão incompletos
    campos_faltando = []
    e = current_user
    if not e.cnpj:        campos_faltando.append('CNPJ')
    if not e.responsavel: campos_faltando.append('Responsável')
    if not e.documento:   campos_faltando.append('CPF/RG do responsável')
    if not e.endereco:    campos_faltando.append('Endereço')

    return render_template('declaracoes.html', decls=decls,
                           campos_faltando=campos_faltando)


@decl_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    nome    = request.form.get('nome', '').strip()
    arquivo = request.files.get('arquivo')

    if not arquivo or not arquivo.filename.lower().endswith('.docx'):
        return redirect(url_for('declaracoes.index'))

    decl = Declaracao(
        empresa_id   = current_user.id,
        nome         = nome or arquivo.filename,
        arquivo_nome = arquivo.filename,
    )
    db.session.add(decl)
    db.session.flush()

    filename = secure_filename(f"{decl.id}.docx")
    arquivo.save(os.path.join(pasta_empresa(), filename))
    decl.arquivo_path = f"declaracoes/{current_user.id}/{filename}"

    db.session.commit()
    return redirect(url_for('declaracoes.index'))


@decl_bp.route('/gerar/<decl_id>')
@login_required
def gerar(decl_id):
    decl = Declaracao.query.filter_by(id=decl_id, empresa_id=current_user.id).first_or_404()
    if not decl.arquivo_path:
        abort(404)

    caminho = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', decl.arquivo_path)
    if not os.path.exists(caminho):
        abort(404)

    e = current_user
    hoje = date.today()

    num_pregao  = request.args.get('num_pregao',  '').strip()
    num_processo = request.args.get('num_processo', '').strip()

    contexto = {
        'nome_empresa':  e.nome or '',
        'cnpj':          e.cnpj or '',
        'responsavel':   e.responsavel or '',
        'cpf':           e.documento or '',
        'rg':            e.documento or '',
        'endereco':      e.endereco or '',
        'telefone':      e.telefone or '',
        'data':          hoje.strftime('%d/%m/%Y'),
        'data_extenso':  _data_extenso(hoje),
        'cidade':        _extrair_cidade(e.endereco),
        'num_pregao':    num_pregao,
        'num_processo':  num_processo,
    }

    tpl = DocxTemplate(caminho)
    tpl.render(contexto)

    buffer = io.BytesIO()
    tpl.save(buffer)
    buffer.seek(0)

    decl.gerada_em = datetime.utcnow()
    db.session.commit()

    nome_download = f"{decl.nome} - preenchida.docx"
    return send_file(buffer, as_attachment=True,
                     download_name=nome_download,
                     mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')


@decl_bp.route('/deletar/<decl_id>', methods=['POST'])
@login_required
def deletar(decl_id):
    decl = Declaracao.query.filter_by(id=decl_id, empresa_id=current_user.id).first_or_404()
    if decl.arquivo_path:
        caminho = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', decl.arquivo_path)
        if os.path.exists(caminho):
            os.remove(caminho)
    db.session.delete(decl)
    db.session.commit()
    return redirect(url_for('declaracoes.index'))


def _data_extenso(d):
    meses = ['janeiro','fevereiro','março','abril','maio','junho',
             'julho','agosto','setembro','outubro','novembro','dezembro']
    return f"{d.day} de {meses[d.month - 1]} de {d.year}"


def _extrair_cidade(endereco):
    """Tenta extrair cidade do endereço (último componente antes do estado)."""
    if not endereco:
        return ''
    partes = [p.strip() for p in endereco.replace(',', ' ').split()]
    # heurística simples: retorna o endereço completo se não conseguir separar
    return endereco
