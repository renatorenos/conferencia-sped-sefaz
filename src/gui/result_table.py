"""
Widget de tabela de resultados usando ttk.Treeview dentro de um frame CustomTkinter.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk


class ResultTable(ctk.CTkFrame):
    def __init__(self, master, colunas: list[tuple[str, int]], **kwargs):
        """
        colunas: lista de (nome_coluna, largura_pixels)
        """
        super().__init__(master, **kwargs)

        self._ids = [c[0] for c in colunas]

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Custom.Treeview",
            rowheight=24,
            font=("Helvetica", 10),
            background="#2b2b2b",
            foreground="#ffffff",
            fieldbackground="#2b2b2b",
        )
        style.configure(
            "Custom.Treeview.Heading",
            font=("Helvetica", 10, "bold"),
            background="#1a5276",
            foreground="#ffffff",
        )
        style.map("Custom.Treeview", background=[("selected", "#1f618d")])

        self._tree = ttk.Treeview(
            self,
            columns=self._ids,
            show="headings",
            style="Custom.Treeview",
            selectmode="extended",
        )

        self._linhas: list[tuple] = []
        self._sort_col: str | None = None
        self._sort_asc: bool = True

        for nome, largura in colunas:
            self._tree.heading(
                nome, text=nome,
                command=lambda c=nome: self._ordenar(c),
            )
            self._tree.column(nome, width=largura, minwidth=60, anchor="w")

        vsb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def carregar(self, linhas: list[tuple]):
        self._linhas = list(linhas)
        self._sort_col = None
        self._sort_asc = True
        self._renderizar(self._linhas)
        # Limpa indicadores de ordenação nos cabeçalhos
        for col in self._ids:
            texto = self._tree.heading(col)["text"].rstrip(" ▲▼")
            self._tree.heading(col, text=texto)

    def limpar(self):
        self._linhas = []
        self._tree.delete(*self._tree.get_children())

    def _renderizar(self, linhas: list[tuple]):
        self._tree.delete(*self._tree.get_children())
        for i, linha in enumerate(linhas):
            tag = "par" if i % 2 == 0 else "impar"
            self._tree.insert("", "end", values=linha, tags=(tag,))
        self._tree.tag_configure("par", background="#2b2b2b")
        self._tree.tag_configure("impar", background="#242424")

    def _ordenar(self, coluna: str):
        if self._sort_col == coluna:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = coluna
            self._sort_asc = True

        idx = self._ids.index(coluna)

        def chave(linha):
            v = linha[idx] if linha[idx] is not None else ""
            # Tenta ordenar numericamente quando possível
            try:
                return (0, float(str(v).replace("R$", "").replace(".", "").replace(",", ".").strip()))
            except ValueError:
                return (1, str(v).lower())

        ordenadas = sorted(self._linhas, key=chave, reverse=not self._sort_asc)
        self._renderizar(ordenadas)

        # Atualiza indicadores nos cabeçalhos
        for col in self._ids:
            texto = self._tree.heading(col)["text"].rstrip(" ▲▼")
            if col == coluna:
                texto += " ▲" if self._sort_asc else " ▼"
            self._tree.heading(col, text=texto)
