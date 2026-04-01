from flask import Blueprint, request, jsonify, send_file
from services.excel_service import gerar_excel

export_bp = Blueprint('export', __name__, url_prefix='/api/export')


@export_bp.route('/excel', methods=['POST'])
def export_excel():
    try:
        data = request.get_json()
        output = gerar_excel(data)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='composicao_precos.xlsx'
        )
    except ImportError as e:
        return jsonify({'error': str(e)}), 500
