"""
Parser do arquivo SPED EFD-ICMS/IPI.

Extrai os registros relevantes:
  - 0000: cabeçalho (empresa, CNPJ, período)
  - 0150: participantes (fornecedores/clientes)
  - C100: documentos fiscais (NF-e)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class EmpresaSped:
    nome: str
    cnpj: str
    uf: str
    dt_ini: str
    dt_fin: str


@dataclass
class NotaSped:
    ind_oper: str        # '0'=entrada, '1'=saída
    ind_emit: str        # '0'=próprio, '1'=terceiros
    cod_part: str
    cod_mod: str
    cod_sit: str
    serie: str
    num_doc: str
    chave: str           # 44 dígitos
    dt_doc: str
    vl_doc: str
    nome_part: str = ""
    cnpj_part: str = ""

    @property
    def tipo(self) -> str:
        return "Entrada" if self.ind_oper == "0" else "Saída"


def _normaliza_cnpj(valor: str) -> str:
    return "".join(c for c in valor if c.isdigit())


def _formata_data(ddmmyyyy: str) -> str:
    if len(ddmmyyyy) == 8:
        return f"{ddmmyyyy[:2]}/{ddmmyyyy[2:4]}/{ddmmyyyy[4:]}"
    return ddmmyyyy


def parse_sped(
    caminho: str,
    progress_cb: Callable[[int, int], None] | None = None,
) -> tuple[EmpresaSped, list[NotaSped]]:
    """
    Lê o arquivo SPED e retorna (empresa, lista de C100).

    progress_cb(linhas_lidas, total_linhas) — chamada periodicamente.
    """
    with open(caminho, "r", encoding="iso-8859-1", errors="replace") as f:
        linhas = f.readlines()

    total = len(linhas)
    empresa: EmpresaSped | None = None
    participantes: dict[str, tuple[str, str]] = {}  # cod_part → (nome, cnpj)
    notas: list[NotaSped] = []

    for i, linha in enumerate(linhas):
        if progress_cb and i % 200 == 0:
            progress_cb(i, total)

        linha = linha.rstrip("\r\n")
        if not linha:
            continue

        campos = linha.split("|")
        # formato: |TIPO|...|  → campos[0]='' campos[1]=TIPO campos[2..]=dados
        if len(campos) < 2:
            continue
        tipo = campos[1]

        if tipo == "0000":
            # |0000|COD_VER|COD_FIN|DT_INI|DT_FIN|NOME|CNPJ|CPF|UF|...
            empresa = EmpresaSped(
                nome=campos[6] if len(campos) > 6 else "",
                cnpj=_normaliza_cnpj(campos[7]) if len(campos) > 7 else "",
                uf=campos[9] if len(campos) > 9 else "",
                dt_ini=_formata_data(campos[4]) if len(campos) > 4 else "",
                dt_fin=_formata_data(campos[5]) if len(campos) > 5 else "",
            )

        elif tipo == "0150":
            # |0150|COD_PART|NOME|COD_PAIS|CNPJ|CPF|IE|...
            cod_part = campos[2] if len(campos) > 2 else ""
            nome = campos[3] if len(campos) > 3 else ""
            cnpj = _normaliza_cnpj(campos[5]) if len(campos) > 5 else ""
            if not cnpj and len(campos) > 6:
                cnpj = _normaliza_cnpj(campos[6])  # CPF
            participantes[cod_part] = (nome, cnpj)

        elif tipo == "C100":
            # |C100|IND_OPER|IND_EMIT|COD_PART|COD_MOD|COD_SIT|SER|NUM_DOC|CHV_NFE|DT_DOC|DT_E_S|VL_DOC|...
            if len(campos) < 13:
                continue
            cod_part = campos[4]
            nome_part, cnpj_part = participantes.get(cod_part, ("", ""))
            nota = NotaSped(
                ind_oper=campos[2],
                ind_emit=campos[3],
                cod_part=cod_part,
                cod_mod=campos[5],
                cod_sit=campos[6],
                serie=campos[7],
                num_doc=campos[8],
                chave=campos[9].strip(),
                dt_doc=_formata_data(campos[10]),
                vl_doc=campos[12],
                nome_part=nome_part,
                cnpj_part=cnpj_part,
            )
            notas.append(nota)

    if progress_cb:
        progress_cb(total, total)

    if empresa is None:
        raise ValueError("Registro 0000 não encontrado — verifique se é um arquivo SPED válido.")

    return empresa, notas
