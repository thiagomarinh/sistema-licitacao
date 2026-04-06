import io


def gerar_excel(data):
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise ImportError('Instale openpyxl: pip install openpyxl')

    config = data.get('config', {'taxa': 7, 'lucro_liq': 9, 'dasn': 3})
    itens = data.get('itens', [])
    titulo = data.get('titulo', 'COMPOSIÇÃO DE PREÇOS')

    taxa = config['taxa'] / 100
    lucro_liq = config['lucro_liq'] / 100
    dasn = config['dasn'] / 100
    divisor = 1 - taxa - lucro_liq - dasn

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Composição de Preços"

    # Estilos
    header_fill = PatternFill("solid", fgColor="1F4E79")
    total_fill = PatternFill("solid", fgColor="D6E4F7")
    header_font = Font(bold=True, color="FFFFFF", size=9)
    bold_font = Font(bold=True, size=9)
    normal_font = Font(size=9)
    center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    right = Alignment(horizontal='right', vertical='center')
    thin = Side(style='thin', color='AAAAAA')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # Título
    ws.merge_cells('A1:S1')
    ws['A1'] = titulo
    ws['A1'].font = Font(bold=True, size=14, color="1F4E79")
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 30

    # Config linha
    ws.merge_cells('A2:S2')
    ws['A2'] = (
        f"Taxa: {config['taxa']}%   |   Lucro Líquido: {config['lucro_liq']}%"
        f"   |   DASN: {config['dasn']}%   |   Desconto Total: {config['taxa'] + config['lucro_liq'] + config['dasn']}%"
    )
    ws['A2'].font = Font(italic=True, size=9, color="555555")
    ws['A2'].alignment = Alignment(horizontal='center', vertical='center')

    # Cabeçalhos
    headers = [
        '#', 'DESCRIÇÃO', 'UND', 'QUANT', 'FORNECEDOR', 'MARCA SELECIONADA',
        'CUSTO UNIT.\nAQUISIÇÃO', 'CUSTO TOTAL\nAQUISIÇÃO',
        f'PREÇO VENDA\nUNIT. ({100 - round((1 - divisor) * 100)}%)',
        'PREÇO TOTAL\nVENDA', 'LUCRO\nBRUTO %',
        'NOVO\nLANCE', 'NOVO\nTOTAL', 'NOVO\nLUCRO %',
        'NOVO\nLUCRO R$', f'LUCRO LÍQ.\nR$ ({config["lucro_liq"]}%)',
        f'DASN\nR$ ({config["dasn"]}%)', 'CUSTO\nOPERACIONAL'
    ]

    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center
        cell.border = border

    ws.row_dimensions[3].height = 40

    # Dados
    totais = {
        'custo_total': 0, 'preco_total': 0, 'novo_total': 0,
        'novo_lucro_rs': 0, 'lucro_liq_rs': 0, 'dasn_rs': 0, 'custo_op': 0
    }

    for i, item in enumerate(itens):
        row = i + 4
        qtd = float(item.get('quantidade', 0) or 0)
        custo_unit = float(item.get('custo_unit', 0) or 0)
        novo_lance = float(item.get('novo_lance', 0) or 0)

        custo_total = qtd * custo_unit
        preco_venda_unit = (custo_unit / divisor) if divisor > 0 else 0
        preco_total = qtd * preco_venda_unit
        lucro_bruto_pct = ((preco_venda_unit - custo_unit) / custo_unit * 100) if custo_unit > 0 else 0
        novo_total = qtd * novo_lance
        novo_lucro_pct = (((novo_lance - custo_unit) / novo_lance) - dasn - lucro_liq) * 100 if novo_lance > 0 else 0
        novo_lucro_rs = novo_total * (novo_lucro_pct / 100)
        lucro_liq_rs = novo_total * lucro_liq
        dasn_rs = novo_total * dasn
        custo_op = novo_total * taxa

        totais['custo_total'] += custo_total
        totais['preco_total'] += preco_total
        totais['novo_total'] += novo_total
        totais['novo_lucro_rs'] += novo_lucro_rs
        totais['lucro_liq_rs'] += lucro_liq_rs
        totais['dasn_rs'] += dasn_rs
        totais['custo_op'] += custo_op

        values = [
            i + 1, item.get('descricao', ''), item.get('unidade', ''), qtd,
            item.get('fornecedor', ''), item.get('marca', ''),
            custo_unit, custo_total, preco_venda_unit, preco_total,
            lucro_bruto_pct / 100, novo_lance, novo_total,
            novo_lucro_pct / 100, novo_lucro_rs, lucro_liq_rs, dasn_rs, custo_op
        ]

        fill = PatternFill("solid", fgColor="EBF3FB") if i % 2 == 1 else None

        for col, val in enumerate(values, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.font = normal_font
            cell.border = border
            if fill:
                cell.fill = fill
            if col in [1, 3]:
                cell.alignment = center
            elif col in [7, 8, 9, 10, 12, 13, 15, 16, 17, 18]:
                cell.number_format = 'R$ #,##0.00'
                cell.alignment = right
            elif col in [11, 14]:
                cell.number_format = '0.00%'
                cell.alignment = center
            elif col == 4:
                cell.number_format = '#,##0.00'
                cell.alignment = center

    # Totais
    total_row = len(itens) + 4
    ws.cell(row=total_row, column=1, value='TOTAIS').font = bold_font
    ws.merge_cells(f'A{total_row}:F{total_row}')
    ws.cell(row=total_row, column=1).alignment = center

    novo_lucro_pct_total = (totais['novo_lucro_rs'] / totais['novo_total'] * 100) if totais['novo_total'] > 0 else 0

    total_values = {
        8: totais['custo_total'], 10: totais['preco_total'],
        13: totais['novo_total'], 14: novo_lucro_pct_total / 100,
        15: totais['novo_lucro_rs'], 16: totais['lucro_liq_rs'],
        17: totais['dasn_rs'], 18: totais['custo_op']
    }

    for col in range(1, 19):
        cell = ws.cell(row=total_row, column=col)
        if col in total_values:
            cell.value = total_values[col]
        cell.fill = total_fill
        cell.font = bold_font
        cell.border = border
        if col in [8, 10, 13, 15, 16, 17, 18]:
            cell.number_format = 'R$ #,##0.00'
            cell.alignment = right
        elif col == 14:
            cell.number_format = '0.00%'
            cell.alignment = center

    # Larguras das colunas
    col_widths = [4, 35, 6, 7, 18, 20, 12, 12, 12, 12, 10, 12, 12, 10, 12, 12, 10, 12]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.freeze_panes = 'A4'

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output
