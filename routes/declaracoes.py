import os
import io
import traceback
import tempfile
import subprocess
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, send_file, abort, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from docxtpl import DocxTemplate
import fitz  # PyMuPDF
from models import db, Declaracao

LIBREOFFICE_PATHS = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]

def _encontrar_libreoffice():
    for p in LIBREOFFICE_PATHS:
        if os.path.exists(p):
            return p
    return None

def _docx_para_pdf_libreoffice(docx_path, output_dir):
    """Converte DOCX → PDF usando LibreOffice headless."""
    soffice = _encontrar_libreoffice()
    if not soffice:
        raise RuntimeError(
            "LibreOffice não encontrado. "
            "Instale em https://www.libreoffice.org e reinicie o servidor."
        )
    result = subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", output_dir, docx_path],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "LibreOffice não converteu o arquivo.")
    # LibreOffice gera o PDF com o mesmo nome base
    pdf_path = os.path.join(output_dir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
    if not os.path.exists(pdf_path):
        raise RuntimeError("PDF não foi gerado pelo LibreOffice.")
    return pdf_path


decl_bp = Blueprint('declaracoes', __name__, url_prefix='/declaracoes')

BASE_UPLOAD = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'declaracoes')

EXTENSOES_PERMITIDAS = {'.pdf', '.docx'}


def pasta_empresa():
    pasta = os.path.join(BASE_UPLOAD, current_user.id)
    os.makedirs(pasta, exist_ok=True)
    return pasta


def _preencher_pdf(caminho, contexto):
    """Abre o PDF, substitui os marcadores {{chave}} pelos valores e retorna BytesIO."""
    doc = fitz.open(caminho)

    for page in doc:
        # Varre todos os spans da página para coletar tamanho/cor de cada marcador
        props = {}  # marcador -> {'size': float, 'color': tuple}
        for bloco in page.get_text("dict", flags=0).get("blocks", []):
            for linha in bloco.get("lines", []):
                for span in linha.get("spans", []):
                    texto = span.get("text", "")
                    for chave in contexto:
                        marcador = f"{{{{{chave}}}}}"
                        if marcador in texto and marcador not in props:
                            size = span.get("size", 11)
                            c = span.get("color", 0)          # inteiro RGB
                            props[marcador] = {
                                "size": size,
                                "color": (
                                    ((c >> 16) & 0xFF) / 255,
                                    ((c >> 8)  & 0xFF) / 255,
                                    (c         & 0xFF) / 255,
                                ),
                            }

        # Aplica as substituições
        for chave, valor in contexto.items():
            marcador = f"{{{{{chave}}}}}"
            valor_str = str(valor) if valor else ''
            ocorrencias = page.search_for(marcador)
            if not ocorrencias:
                continue

            info = props.get(marcador, {"size": 11, "color": (0, 0, 0)})
            fontsize   = info["size"]
            text_color = info["color"]

            for rect in ocorrencias:
                page.add_redact_annot(
                    rect,
                    text=valor_str,
                    fontsize=fontsize,
                    align=fitz.TEXT_ALIGN_LEFT,
                    fill=(1, 1, 1),
                    text_color=text_color,
                )

        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

    buffer = io.BytesIO()
    doc.save(buffer, garbage=4, deflate=True)
    buffer.seek(0)
    doc.close()
    return buffer


@decl_bp.route('/')
@login_required
def index():
    decls = Declaracao.query.filter_by(empresa_id=current_user.id)\
                            .order_by(Declaracao.criado_em.desc()).all()

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

    if not arquivo:
        flash('Nenhum arquivo enviado.', 'error')
        return redirect(url_for('declaracoes.index'))

    ext = os.path.splitext(arquivo.filename.lower())[1]
    if ext not in EXTENSOES_PERMITIDAS:
        flash('Formato inválido. Envie um arquivo .pdf ou .docx.', 'error')
        return redirect(url_for('declaracoes.index'))

    decl = Declaracao(
        empresa_id   = current_user.id,
        nome         = nome or arquivo.filename,
        arquivo_nome = arquivo.filename,
    )
    db.session.add(decl)
    db.session.flush()

    filename = secure_filename(f"{decl.id}{ext}")
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

    num_pregao   = request.args.get('num_pregao',   '').strip()
    num_processo = request.args.get('num_processo', '').strip()

    contexto = {
        'nome_empresa': e.nome or '',
        'cnpj':         e.cnpj or '',
        'responsavel':  e.responsavel or '',
        'cpf':          e.documento or '',
        'rg':           e.rg or '',
        'endereco':     e.endereco or '',
        'telefone':     e.telefone or '',
        'data':         hoje.strftime('%d/%m/%Y'),
        'data_extenso': _data_extenso(hoje),
        'cidade':       _extrair_cidade(e.endereco),
        'num_pregao':   num_pregao,
        'num_processo': num_processo,
    }

    ext = os.path.splitext(decl.arquivo_path.lower())[1]

    try:
        if ext == '.pdf':
            buffer = _preencher_pdf(caminho, contexto)
        else:
            # Preenche o template DOCX e devolve o .docx preenchido
            tpl = DocxTemplate(caminho)
            tpl.render(contexto)
            buffer = io.BytesIO()
            tpl.save(buffer)
            buffer.seek(0)
    except Exception as err:
        traceback.print_exc()
        flash(f'Erro ao gerar declaração: {err}', 'error')
        return redirect(url_for('declaracoes.index'))

    decl.gerada_em = datetime.utcnow()
    db.session.commit()

    if ext == '.pdf':
        nome_download = f"{decl.nome} - preenchida.pdf"
        mimetype = 'application/pdf'
    else:
        nome_download = f"{decl.nome} - preenchida.docx"
        mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

    return send_file(
        buffer,
        as_attachment=True,
        download_name=nome_download,
        mimetype=mimetype,
    )


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
    meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
             'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
    return f"{d.day} de {meses[d.month - 1]} de {d.year}"


def _extrair_cidade(endereco):
    if not endereco:
        return ''
    return endereco
