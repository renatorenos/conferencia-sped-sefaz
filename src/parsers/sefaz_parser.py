"""
Parser do relatório de NF-e exportado da SEFAZ (formato .xls).

Estrutura do arquivo:
  Linha 0: "SECRETARIA DE ESTADO DE FAZENDA..."
  Linha 1: "RELATÓRIO DE INFORMAÇÕES DA NF-e"
  Linha 2: "GERADO EM DD/MM/YYYY - HH:MM:SS"
  Linha 3: "CONSULTA EMISSOR/DESTINATÁRIO"
  Linha 4: (vazia)
  Linha 5: (agrupador de colunas: DADOS EMISSOR / DADOS DESTINATÁRIO)
  Linha 6: cabeçalho das colunas
  Linha 7+: dados

Colunas (0-indexado):
  0  DATA EMISSÃO
  1  SÉRIE
  2  NUMERO NOTA FISCAL
  3  CHAVE DE ACESSO
  4  NATUREZA DE OPERAÇÃO
  5  TIPO DE EMISSÃO
  6  NUMR DE PROTOCOLO
  7  DATA AUTORIZAÇÃO
  8  SITUAÇÃO
  9  CNPJ/CPF (emitente)
  10 NOME/RAZÃO SOCIAL (emitente)
  11 IE (emitente)
  12 NOME FANTASIA (emitente)
  13 UF (emitente)
  14 CNPJ/CPF (destinatário)
  15 IE (destinatário)
  16 NOME/RAZÃO SOCIAL (destinatário)
  17 UF (destinatário)
  18 VALR TOTAL BASE DE CÁLCULO
  ...
  24 VALR TOTAL NOTA FISCAL

Lógica de entrada/saída:
  - Se CNPJ empresa == CNPJ destinatário (col 14) → ENTRADA
  - Se CNPJ empresa == CNPJ emitente   (col 9)  → SAÍDA
"""
from __future__ import annotations
from dataclasses import dataclass
import xlrd


@dataclass
class NotaSefaz:
    chave: str
    tipo: str           # 'Entrada' ou 'Saída'
    serie: str
    num_doc: str
    dt_emissao: str
    situacao: str
    cnpj_emit: str
    nome_emit: str
    cnpj_dest: str
    nome_dest: str
    vl_total: str


def _normaliza_cnpj(valor: str) -> str:
    return "".join(c for c in str(valor) if c.isdigit())


def _cell_str(cell) -> str:
    if cell.ctype == xlrd.XL_CELL_NUMBER:
        v = int(cell.value)
        return str(v)
    return str(cell.value).strip()


HEADER_ROW = 6   # linha do cabeçalho (0-indexado)
DATA_START = 7   # primeira linha de dados


def parse_sefaz(caminho: str, cnpj_empresa: str) -> list[NotaSefaz]:
    """
    Lê o .xls da SEFAZ e retorna lista de NotaSefaz.

    cnpj_empresa: CNPJ da empresa (só dígitos) — usado para detectar entrada/saída.
    """
    cnpj_empresa = _normaliza_cnpj(cnpj_empresa)

    try:
        wb = xlrd.open_workbook(caminho)
    except Exception as e:
        raise ValueError(f"Não foi possível abrir o arquivo SEFAZ: {e}")

    ws = wb.sheet_by_index(0)

    if ws.nrows <= DATA_START:
        raise ValueError("Arquivo SEFAZ sem linhas de dados.")

    notas: list[NotaSefaz] = []
    skipped = 0

    for r in range(DATA_START, ws.nrows):
        row = ws.row(r)

        # Ignorar linhas de rodapé / totais (primeira célula vazia ou texto)
        chave_raw = _cell_str(row[3]).replace(" ", "").replace("-", "")
        if len(chave_raw) != 44 or not chave_raw.isdigit():
            skipped += 1
            continue

        cnpj_emit = _normaliza_cnpj(_cell_str(row[9]))
        cnpj_dest = _normaliza_cnpj(_cell_str(row[14]))

        if cnpj_dest == cnpj_empresa:
            tipo = "Entrada"
        elif cnpj_emit == cnpj_empresa:
            tipo = "Saída"
        else:
            # NF onde a empresa não é nem emitente nem destinatário — ignorar
            skipped += 1
            continue

        serie_raw = row[1].value
        serie = str(int(serie_raw)) if isinstance(serie_raw, float) else str(serie_raw).strip()

        num_raw = row[2].value
        num_doc = str(int(num_raw)) if isinstance(num_raw, float) else str(num_raw).strip()

        notas.append(NotaSefaz(
            chave=chave_raw,
            tipo=tipo,
            serie=serie,
            num_doc=num_doc,
            dt_emissao=_cell_str(row[0]),
            situacao=_cell_str(row[8]),
            cnpj_emit=cnpj_emit,
            nome_emit=_cell_str(row[10]),
            cnpj_dest=cnpj_dest,
            nome_dest=_cell_str(row[16]),
            vl_total=_cell_str(row[24]),
        ))

    return notas
