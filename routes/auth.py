import os
import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.utils import secure_filename
from models import db, Empresa
from config import UPLOAD_FOLDER

auth_bp = Blueprint('auth', __name__)

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def _so_digitos(valor):
    return re.sub(r'\D', '', valor or '')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        empresa = Empresa.query.filter_by(email=email).first()
        if empresa and empresa.check_senha(senha):
            login_user(empresa, remember=True)
            return redirect(url_for('main.index'))
        flash('E-mail ou senha incorretos.')
    return render_template('login.html')


@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if Empresa.query.filter_by(email=email).first():
            flash('Este e-mail já está cadastrado.')
            return render_template('cadastro.html')

        empresa = Empresa(
            nome        = request.form.get('nome', '').strip(),
            email       = email,
            cnpj        = request.form.get('cnpj', '').strip(),
            responsavel = request.form.get('responsavel', '').strip(),
            documento   = request.form.get('cpf', '').strip(),
            rg          = request.form.get('rg', '').strip(),
            endereco    = request.form.get('endereco', '').strip(),
            telefone    = request.form.get('telefone', '').strip(),
            site        = request.form.get('site', '').strip(),
        )
        empresa.set_senha(request.form.get('senha', ''))

        # Upload de logo
        logo = request.files.get('logo')
        if logo and logo.filename and allowed_file(logo.filename):
            ext = logo.filename.rsplit('.', 1)[1].lower()
            filename = secure_filename(f"{empresa.id}.{ext}")
            logo.save(os.path.join(UPLOAD_FOLDER, filename))
            empresa.logo_path = f'logos/{filename}'

        db.session.add(empresa)
        db.session.commit()
        login_user(empresa, remember=True)
        return redirect(url_for('main.index'))

    return render_template('cadastro.html')


@auth_bp.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes():
    from flask_login import current_user
    empresa = current_user
    erros = {}
    sucesso = None

    if request.method == 'POST':
        acao = request.form.get('acao')

        if acao == 'dados':
            novo_email = request.form.get('email', '').strip().lower()
            if novo_email != empresa.email:
                if Empresa.query.filter_by(email=novo_email).first():
                    erros['email'] = 'Este e-mail já está em uso.'
                else:
                    empresa.email = novo_email

            empresa.nome        = request.form.get('nome', '').strip()
            empresa.cnpj        = request.form.get('cnpj', '').strip()
            empresa.responsavel = request.form.get('responsavel', '').strip()
            empresa.documento   = request.form.get('cpf', '').strip()
            empresa.rg          = request.form.get('rg', '').strip()
            empresa.endereco    = request.form.get('endereco', '').strip()
            empresa.telefone    = request.form.get('telefone', '').strip()
            empresa.site        = request.form.get('site', '').strip()

            logo = request.files.get('logo')
            if logo and logo.filename and allowed_file(logo.filename):
                ext = logo.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f"{empresa.id}.{ext}")
                logo.save(os.path.join(UPLOAD_FOLDER, filename))
                empresa.logo_path = f'logos/{filename}'

            if not erros:
                db.session.commit()
                sucesso = 'Dados atualizados com sucesso!'

        elif acao == 'senha':
            senha_atual  = request.form.get('senha_atual', '')
            senha_nova   = request.form.get('senha_nova', '')
            senha_conf   = request.form.get('senha_conf', '')

            if not empresa.check_senha(senha_atual):
                erros['senha_atual'] = 'Senha atual incorreta.'
            elif len(senha_nova) < 6:
                erros['senha_nova'] = 'A nova senha deve ter ao menos 6 caracteres.'
            elif senha_nova != senha_conf:
                erros['senha_conf'] = 'As senhas não coincidem.'
            else:
                empresa.set_senha(senha_nova)
                db.session.commit()
                sucesso = 'Senha alterada com sucesso!'

    return render_template('configuracoes.html', empresa=empresa, erros=erros, sucesso=sucesso)


@auth_bp.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    erros = {}
    sucesso = None

    if request.method == 'POST':
        email       = request.form.get('email', '').strip().lower()
        cnpj        = request.form.get('cnpj', '').strip()
        senha_nova  = request.form.get('senha_nova', '')
        senha_conf  = request.form.get('senha_conf', '')

        empresa = Empresa.query.filter_by(email=email).first()

        if not empresa or not empresa.cnpj or _so_digitos(empresa.cnpj) != _so_digitos(cnpj):
            erros['geral'] = 'E-mail ou CNPJ não encontrados ou não correspondem.'
        elif len(senha_nova) < 6:
            erros['senha_nova'] = 'A nova senha deve ter ao menos 6 caracteres.'
        elif senha_nova != senha_conf:
            erros['senha_conf'] = 'As senhas não coincidem.'
        else:
            empresa.set_senha(senha_nova)
            db.session.commit()
            sucesso = 'Senha redefinida com sucesso! Você já pode entrar.'

    return render_template('esqueci_senha.html', erros=erros, sucesso=sucesso)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
