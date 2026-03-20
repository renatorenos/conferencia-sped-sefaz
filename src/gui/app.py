"""
Janela principal da aplicação Conferência SPED.
"""
from __future__ import annotations
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import customtkinter as ctk

from ..parsers.sped_parser import parse_sped, EmpresaSped
from ..parsers.sefaz_parser import parse_sefaz
from ..conciliacao import conciliar, ResultadoConciliacao
from ..exporter import exportar_xlsx
from .result_table import ResultTable

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Conferência SPED")
        self.geometry("1100x720")
        self.minsize(900, 600)

        self._sped_path = tk.StringVar(value="")
        self._sefaz_path = tk.StringVar(value="")
        self._status = tk.StringVar(value="Aguardando arquivos...")
        self._progress_val = tk.DoubleVar(value=0.0)

        self._empresa: EmpresaSped | None = None
        self._resultado: ResultadoConciliacao | None = None

        self._build_ui()

    # ------------------------------------------------------------------ #
    #  Layout                                                              #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        # --- Coluna esquerda (controles) ---
        left = ctk.CTkFrame(self, width=260, corner_radius=0)
        left.pack(side="left", fill="y", padx=0, pady=0)
        left.pack_propagate(False)

        ctk.CTkLabel(left, text="Conferência SPED", font=("Helvetica", 16, "bold")).pack(pady=(20, 4))
        ctk.CTkLabel(left, text="vs SEFAZ", font=("Helvetica", 12), text_color="gray").pack(pady=(0, 20))

        # Arquivo SPED
        ctk.CTkLabel(left, text="Arquivo SPED (.txt)", anchor="w").pack(fill="x", padx=16, pady=(8, 2))
        sped_frame = ctk.CTkFrame(left, fg_color="transparent")
        sped_frame.pack(fill="x", padx=16, pady=(0, 4))
        ctk.CTkEntry(sped_frame, textvariable=self._sped_path, state="readonly", width=170).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(sped_frame, text="📂", width=36, command=self._browse_sped).pack(side="left", padx=(4, 0))

        # Arquivo SEFAZ
        ctk.CTkLabel(left, text="Relatório SEFAZ (.xls)", anchor="w").pack(fill="x", padx=16, pady=(12, 2))
        sefaz_frame = ctk.CTkFrame(left, fg_color="transparent")
        sefaz_frame.pack(fill="x", padx=16, pady=(0, 4))
        ctk.CTkEntry(sefaz_frame, textvariable=self._sefaz_path, state="readonly", width=170).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(sefaz_frame, text="📂", width=36, command=self._browse_sefaz).pack(side="left", padx=(4, 0))

        ctk.CTkLabel(left, text="").pack()  # spacer

        self._btn_processar = ctk.CTkButton(
            left, text="▶  Processar", height=40,
            fg_color="#1a5276", hover_color="#1f618d",
            command=self._iniciar_processamento,
        )
        self._btn_processar.pack(padx=16, pady=8, fill="x")

        self._btn_exportar = ctk.CTkButton(
            left, text="💾  Exportar Relatório (.xlsx)", height=36,
            fg_color="#1e8449", hover_color="#27ae60",
            command=self._exportar,
            state="disabled",
        )
        self._btn_exportar.pack(padx=16, pady=4, fill="x")

        ctk.CTkLabel(left, text="").pack(expand=True)  # spacer push-down

        # Legenda + Contadores
        legenda_frame = ctk.CTkFrame(left, corner_radius=8)
        legenda_frame.pack(padx=12, pady=(0, 12), fill="x")

        ctk.CTkLabel(
            legenda_frame, text="Legenda",
            font=("Helvetica", 10, "bold"), text_color="gray",
        ).pack(anchor="w", padx=10, pady=(8, 4))

        # Divergência A
        row_a = ctk.CTkFrame(legenda_frame, fg_color="transparent")
        row_a.pack(fill="x", padx=10, pady=(0, 4))
        ctk.CTkLabel(row_a, text="", text_color="#1a5276", font=("Helvetica", 14), width=18).pack(side="left")
        col_a = ctk.CTkFrame(row_a, fg_color="transparent")
        col_a.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self._lbl_div_a = ctk.CTkLabel(
            col_a, text="Divergências A: —",
            font=("Helvetica", 11, "bold"), text_color="#1a5276", anchor="w",
        )
        self._lbl_div_a.pack(anchor="w")
        ctk.CTkLabel(
            col_a,
            text="Entradas no SEFAZ\nque não constam no SPED",
            font=("Helvetica", 9), text_color="gray", anchor="w", justify="left",
        ).pack(anchor="w")

        ctk.CTkFrame(legenda_frame, height=1, fg_color="gray75").pack(fill="x", padx=10, pady=4)

        # Divergência B
        row_b = ctk.CTkFrame(legenda_frame, fg_color="transparent")
        row_b.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(row_b, text="", text_color="#7b3f00", font=("Helvetica", 14), width=18).pack(side="left")
        col_b = ctk.CTkFrame(row_b, fg_color="transparent")
        col_b.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self._lbl_div_b = ctk.CTkLabel(
            col_b, text="Divergências B: —",
            font=("Helvetica", 11, "bold"), text_color="#7b3f00", anchor="w",
        )
        self._lbl_div_b.pack(anchor="w")
        ctk.CTkLabel(
            col_b,
            text="Saídas no SEFAZ\nque não constam no SPED",
            font=("Helvetica", 9), text_color="gray", anchor="w", justify="left",
        ).pack(anchor="w")

        # --- Coluna direita (resultados) ---
        right = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        right.pack(side="right", fill="both", expand=True, padx=8, pady=8)

        # Barra de status + progresso
        status_frame = ctk.CTkFrame(right, height=32, fg_color="transparent")
        status_frame.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(status_frame, textvariable=self._status, anchor="w", text_color="gray").pack(side="left", fill="x", expand=True)
        self._progress = ctk.CTkProgressBar(status_frame, variable=self._progress_val, width=160)
        self._progress.pack(side="right")
        self._progress_val.set(0)

        # Abas
        self._tabview = ctk.CTkTabview(right)
        self._tabview.pack(fill="both", expand=True)

        self._tabview.add("Entradas no SEFAZ / Fora do SPED")
        self._tabview.add("Saídas no SEFAZ / Fora do SPED")

        self._table_a = ResultTable(
            self._tabview.tab("Entradas no SEFAZ / Fora do SPED"),
            colunas=[
                ("Chave NF-e", 300),
                ("Número", 80),
                ("Série", 50),
                ("Data", 90),
                ("Emitente", 200),
                ("CNPJ Emit.", 130),
                ("Destinatário", 180),
                ("Valor Total", 110),
                ("Situação", 90),
            ],
        )
        self._table_a.pack(fill="both", expand=True)

        self._table_b = ResultTable(
            self._tabview.tab("Saídas no SEFAZ / Fora do SPED"),
            colunas=[
                ("Chave NF-e", 300),
                ("Número", 80),
                ("Série", 50),
                ("Data", 90),
                ("Emitente", 180),
                ("CNPJ Emit.", 130),
                ("Destinatário", 180),
                ("Valor Total", 110),
                ("Situação", 90),
            ],
        )
        self._table_b.pack(fill="both", expand=True)

    # ------------------------------------------------------------------ #
    #  Ações                                                               #
    # ------------------------------------------------------------------ #

    def _browse_sped(self):
        path = filedialog.askopenfilename(
            title="Selecionar arquivo SPED",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")],
        )
        if path:
            self._sped_path.set(path)

    def _browse_sefaz(self):
        path = filedialog.askopenfilename(
            title="Selecionar relatório SEFAZ",
            filetypes=[
                ("Excel 97-2003", "*.xls"),
                ("Excel", "*.xlsx"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if path:
            self._sefaz_path.set(path)

    def _iniciar_processamento(self):
        sped = self._sped_path.get().strip()
        sefaz = self._sefaz_path.get().strip()

        if not sped:
            messagebox.showerror("Arquivo faltando", "Selecione o arquivo SPED (.txt).")
            return
        if not sefaz:
            messagebox.showerror("Arquivo faltando", "Selecione o relatório SEFAZ (.xls).")
            return

        self._btn_processar.configure(state="disabled")
        self._btn_exportar.configure(state="disabled")
        self._table_a.limpar()
        self._table_b.limpar()
        self._resultado = None
        self._empresa = None
        self._lbl_div_a.configure(text="Divergências A: —")
        self._lbl_div_b.configure(text="Divergências B: —")
        self._progress_val.set(0)

        threading.Thread(target=self._processar, args=(sped, sefaz), daemon=True).start()

    def _processar(self, sped_path: str, sefaz_path: str):
        try:
            self._set_status("Lendo SPED...")

            def cb_sped(lido, total):
                self._progress_val.set(0.5 * lido / total if total else 0)
                self._set_status(f"Lendo SPED... {lido}/{total} linhas")

            empresa, notas_sped = parse_sped(sped_path, progress_cb=cb_sped)
            self._empresa = empresa

            self._set_status("Lendo relatório SEFAZ...")
            self._progress_val.set(0.6)

            notas_sefaz = parse_sefaz(sefaz_path, empresa.cnpj)

            self._set_status("Conciliando...")
            self._progress_val.set(0.8)

            resultado = conciliar(notas_sped, notas_sefaz)
            self._resultado = resultado

            self._progress_val.set(1.0)
            self._set_status(
                f"Concluído — {len(resultado.entradas_sefaz_fora_sped)} diverg. A | "
                f"{len(resultado.saidas_sefaz_fora_sped)} diverg. B"
            )

            # Atualizar UI na thread principal
            self.after(0, self._exibir_resultado)

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro no processamento", str(e)))
            self.after(0, lambda: self._set_status(f"Erro: {e}"))
            self.after(0, lambda: self._btn_processar.configure(state="normal"))

    def _exibir_resultado(self):
        r = self._resultado
        if r is None:
            return

        linhas_a = [
            (
                n.chave, n.num_doc, n.serie, n.dt_emissao,
                n.nome_emit, n.cnpj_emit,
                n.nome_dest,
                n.vl_total, n.situacao,
            )
            for n in r.entradas_sefaz_fora_sped
        ]
        self._table_a.carregar(linhas_a)

        linhas_b = [
            (
                n.chave, n.num_doc, n.serie, n.dt_emissao,
                n.nome_emit, n.cnpj_emit,
                n.nome_dest,
                n.vl_total, n.situacao,
            )
            for n in r.saidas_sefaz_fora_sped
        ]
        self._table_b.carregar(linhas_b)

        self._lbl_div_a.configure(text=f"Divergências A: {len(r.entradas_sefaz_fora_sped)}")
        self._lbl_div_b.configure(text=f"Divergências B: {len(r.saidas_sefaz_fora_sped)}")

        self._btn_processar.configure(state="normal")
        self._btn_exportar.configure(state="normal")

    def _exportar(self):
        if self._resultado is None or self._empresa is None:
            return

        e = self._empresa
        periodo = e.dt_ini.replace("/", "")[:6] if e.dt_ini else datetime.now().strftime("%Y%m")
        nome_padrao = f"conferencia_{periodo}_{e.cnpj}.xlsx"

        caminho = filedialog.asksaveasfilename(
            title="Salvar relatório",
            defaultextension=".xlsx",
            initialfile=nome_padrao,
            filetypes=[("Excel", "*.xlsx")],
        )
        if not caminho:
            return

        try:
            exportar_xlsx(caminho, self._empresa, self._resultado)
            messagebox.showinfo("Exportado", f"Relatório salvo em:\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro ao exportar", str(e))

    def _set_status(self, msg: str):
        self._status.set(msg)
