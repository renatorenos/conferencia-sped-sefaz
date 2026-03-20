"""
Lógica de conciliação entre SPED e SEFAZ.

Divergência A: Entradas no SEFAZ que NÃO constam no SPED
Divergência B: Saídas no SEFAZ que NÃO constam no SPED
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

from .parsers.sped_parser import NotaSped
from .parsers.sefaz_parser import NotaSefaz


@dataclass
class ResultadoConciliacao:
    entradas_sefaz_fora_sped: list[NotaSefaz]  # Divergência A
    saidas_sefaz_fora_sped: list[NotaSefaz]    # Divergência B

    # Totais para referência
    total_entradas_sped: int = 0
    total_saidas_sped: int = 0
    total_entradas_sefaz: int = 0
    total_saidas_sefaz: int = 0


def conciliar(
    notas_sped: Sequence[NotaSped],
    notas_sefaz: Sequence[NotaSefaz],
    incluir_canceladas: bool = False,
) -> ResultadoConciliacao:
    """
    Compara as notas do SPED com as do SEFAZ.

    incluir_canceladas: se False, ignora C100 com COD_SIT != '00' do SPED.
    """
    # --- Filtrar SPED ---
    entradas_sped: list[NotaSped] = []
    saidas_sped: list[NotaSped] = []

    for n in notas_sped:
        if not incluir_canceladas and n.cod_sit not in ("00", ""):
            continue
        if n.ind_oper == "0":
            entradas_sped.append(n)
        elif n.ind_oper == "1":
            saidas_sped.append(n)

    # --- Separar SEFAZ (apenas AUTORIZADAS) ---
    entradas_sefaz = [n for n in notas_sefaz if n.tipo == "Entrada" and n.situacao.upper() == "AUTORIZADA"]
    saidas_sefaz = [n for n in notas_sefaz if n.tipo == "Saída" and n.situacao.upper() == "AUTORIZADA"]

    # --- Construir sets de chaves ---
    chaves_entradas_sped = {n.chave for n in entradas_sped if n.chave}
    chaves_saidas_sped = {n.chave for n in saidas_sped if n.chave}

    # --- Divergências ---
    # A: entradas no SEFAZ ausentes no SPED
    div_a = [n for n in entradas_sefaz if n.chave not in chaves_entradas_sped]

    # B: saídas no SEFAZ ausentes no SPED
    div_b = [n for n in saidas_sefaz if n.chave not in chaves_saidas_sped]

    return ResultadoConciliacao(
        entradas_sefaz_fora_sped=div_a,
        saidas_sefaz_fora_sped=div_b,
        total_entradas_sped=len(entradas_sped),
        total_saidas_sped=len(saidas_sped),
        total_entradas_sefaz=len(entradas_sefaz),
        total_saidas_sefaz=len(saidas_sefaz),
    )
