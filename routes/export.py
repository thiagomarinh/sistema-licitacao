import os
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from services.excel_service import gerar_excel

export_bp = Blueprint('export', __name__, url_prefix='/api/export')


@export_bp.route('/excel', methods=['POST'])
@login_required
def export_excel():
    try:
        data = request.get_json()

        empresa_info = {
            'nome':        current_user.nome,
            'cnpj':        current_user.cnpj or '',
            'endereco':    current_user.endereco or '',
            'telefone':    current_user.telefone or '',
            'site':        current_user.site or '',
            'responsavel': current_user.responsavel or '',
            'logo_path':   None,
        }

        if current_user.logo_path:
            # logo_path já contém o prefixo "logos/" (ex: "logos/arquivo.png")
            logo_abs = os.path.join(current_app.root_path, 'static', current_user.logo_path)
            if os.path.isfile(logo_abs):
                empresa_info['logo_path'] = logo_abs

        output = gerar_excel(data, empresa_info)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='composicao_precos.xlsx'
        )
    except ImportError as e:
        return jsonify({'error': str(e)}), 500
