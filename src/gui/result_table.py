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

        for nome, largura in colunas:
            self._tree.heading(nome, text=nome)
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
        self._tree.delete(*self._tree.get_children())
        for i, linha in enumerate(linhas):
            tag = "par" if i % 2 == 0 else "impar"
            self._tree.insert("", "end", values=linha, tags=(tag,))
        self._tree.tag_configure("par", background="#2b2b2b")
        self._tree.tag_configure("impar", background="#242424")

    def limpar(self):
        self._tree.delete(*self._tree.get_children())
