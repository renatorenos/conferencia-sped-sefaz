# Padrões de Projeto — Conferência SPED/SEFAZ

Referência técnica para manter consistência em futuros projetos desktop Python que sigam os padrões estabelecidos nesta aplicação.

---

## 1. Stack e Dependências

| Camada | Tecnologia | Versão mínima |
|---|---|---|
| GUI principal | `customtkinter` | >= 5.2.0 |
| Tabelas de dados | `ttk.Treeview` (nativo Python) | — |
| Leitura XLS legado | `xlrd` | >= 2.0.1 |
| Geração XLSX | `openpyxl` | >= 3.1.0 |
| Distribuição Windows | PyInstaller + `.spec` customizado | — |
| CI/CD | GitHub Actions (trigger: tag `v*`) | — |

**Regra:** manter o `requirements.txt` com versões mínimas (`>=`), nunca fixadas (`==`), exceto quando há incompatibilidade conhecida.

---

## 2. Estrutura de Arquivos

```
main.py                  ← ponto de entrada, apenas instancia e chama App().mainloop()
src/
  __init__.py
  conciliacao.py         ← lógica de negócio pura
  exporter.py            ← geração de relatórios (output layer)
  parsers/
    __init__.py
    sped_parser.py       ← leitura e transformação de dados SPED
    sefaz_parser.py      ← leitura e transformação de dados SEFAZ
  gui/
    __init__.py
    app.py               ← janela principal (View + Controller)
    result_table.py      ← componente reutilizável de tabela
docs/                    ← documentação do projeto
```

**Regra:** cada camada vive em seu próprio módulo. A camada `gui/` é o único ponto que conhece as demais — parsers, conciliação e exporter **nunca** importam de `gui/`.

---

## 3. Arquitetura em Camadas

```
gui/app.py  (View + Controller)
    │
    ├── parsers/  (Data Layer — I/O e transformação)
    ├── conciliacao.py  (Business Logic — pura, sem I/O)
    └── exporter.py  (Output Layer — pura, sem GUI)
```

- **Parsers:** retornam dataclasses tipadas. Sem efeito colateral além da leitura do arquivo.
- **Conciliação:** recebe sequências tipadas, retorna dataclass de resultado. Sem I/O.
- **Exporter:** recebe dados de domínio, escreve arquivo. Sem dependência de GUI.
- **GUI:** orquestra os módulos acima. Toda lógica de apresentação fica aqui.

---

## 4. Janela Principal — Classe `App`

### Herança
```python
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
```

Herança direta de `ctk.CTk`. Sem classes intermediárias de janela base.

### Configuração de tema (nível de módulo)
```python
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")
```

Definido **antes** da instanciação de `App`, fora da classe.

### Layout macro (`pack` lateral)
```python
left  = ctk.CTkFrame(self, width=260, corner_radius=0)
right = ctk.CTkFrame(self, corner_radius=0)

left.pack(side="left",  fill="y")
right.pack(side="right", fill="both", expand=True)
```

- **Sidebar esquerda:** largura fixa (260 px), apenas `fill="y"`.
- **Área direita:** expansível com `fill="both", expand=True`.

### Padrão de método construtor de UI
```python
def __init__(self):
    super().__init__()
    self._build_ui()

def _build_ui(self):
    # todo o código de construção de widgets fica aqui
```

Separa a inicialização da construção visual. O `__init__` só chama `_build_ui()`.

---

## 5. Componente Reutilizável — `ResultTable`

Único componente extraído em classe própria. Herdade `ctk.CTkFrame` e encapsula um `ttk.Treeview`.

```python
class ResultTable(ctk.CTkFrame):
    def __init__(self, master, colunas: list[str], **kwargs):
        super().__init__(master, **kwargs)
        self._build()

    def carregar(self, linhas: list[tuple]) -> None: ...
    def limpar(self) -> None: ...
```

### Interface pública mínima
- `carregar(linhas)` — popula a tabela.
- `limpar()` — remove todos os itens.

### Layout interno (sempre `grid`)
```python
self._tree.grid(row=0, column=0, sticky="nsew")
vsb.grid(row=0, column=1, sticky="ns")
hsb.grid(row=1, column=0, sticky="ew")
self.grid_rowconfigure(0, weight=1)
self.grid_columnconfigure(0, weight=1)
```

`grid` é preferido dentro de componentes com scrollbars em duas direções.

### Ordenação bidirecional por coluna
```python
self._tree.heading(
    nome, text=nome,
    command=lambda c=nome: self._ordenar(c),  # c=nome evita late binding
)
```

O `c=nome` no lambda é **obrigatório** para capturar o valor atual da variável de loop, não a referência.

### Zebragem de linhas
```python
self._tree.tag_configure("par",   background="#2b2b2b")
self._tree.tag_configure("impar", background="#242424")
```

Aplicado na inserção: `tags=("par" if i % 2 == 0 else "impar",)`.

### Ordenação numérica inteligente
```python
def _chave(v):
    try:    return (0, float(v))
    except: return (1, v)
```

Tenta `float` primeiro; se falhar, usa comparação de string. Garante que `"10" > "9"`.

---

## 6. Padrões de Layout

| Contexto | Gerenciador | Regra |
|---|---|---|
| Layout macro da janela | `pack` | sidebar fixa à esquerda, área de conteúdo expansível à direita |
| Widgets dentro da sidebar | `pack` vertical | empilhamento top-down |
| Par Entry + Button de arquivo | `pack` horizontal dentro de Frame | Entry expande, Button tem largura fixa (36 px) |
| Spacer para empurrar rodapé | `CTkLabel(text="").pack(expand=True)` | empurra elementos para a parte de baixo |
| Interior de componentes com scrollbar | `grid` | posicionamento preciso de scrollbars |
| Abas de resultado | `ctk.CTkTabview` | — |
| Separador visual horizontal | `CTkFrame(height=1, fg_color="gray75")` | — |

**Regra:** não misturar `pack` e `grid` no mesmo master widget. Definir qual gerenciador é o padrão de cada contexto e mantê-lo.

---

## 7. Paleta de Cores

### Interface (customtkinter)

| Elemento | Hex | Uso |
|---|---|---|
| `#1a5276` | Azul escuro | Botão primário (Processar), labels de divergência A |
| `#1f618d` | Azul médio | Hover do botão primário, seleção no Treeview |
| `#1e8449` | Verde escuro | Botão de ação secundária (Exportar) |
| `#27ae60` | Verde médio | Hover do botão Exportar |
| `#7b3f00` | Marrom/laranja | Labels de divergência B |
| `#2b2b2b` | Cinza escuro | Background linha par do Treeview |
| `#242424` | Cinza mais escuro | Background linha ímpar do Treeview |
| `gray75` | Sistema | Separadores, textos de status |

### Relatório Excel (openpyxl)

| Constante | Hex | Uso |
|---|---|---|
| `_AZUL_HEADER` | `1F4E79` | Cabeçalho aba Entradas |
| `_AZUL_CLARO` | `D6E4F0` | Linhas pares aba Entradas |
| `_LARANJA_HEADER` | `7B3F00` | Cabeçalho aba Saídas |
| `_LARANJA_CLARO` | `FAE5D3` | Linhas pares aba Saídas |
| `_CINZA_CLARO` | `F2F2F2` | Linhas ímpares (ambas as abas) |

**Regra:** cores do Excel são constantes privadas de módulo (`_NOME_UPPER_CASE`). Manter coerência visual entre a GUI e o relatório exportado (mesma identidade de cores por categoria).

---

## 8. Tipografia

Fonte única em toda a aplicação: **`"Helvetica"`** (sem importar fontes externas).

| Elemento | Especificação |
|---|---|
| Título da sidebar | `("Helvetica", 16, "bold")` |
| Subtítulo | `("Helvetica", 12)` |
| Labels de contador | `("Helvetica", 11, "bold")` |
| Descrição de legenda | `("Helvetica", 9)` |
| Corpo do Treeview | `("Helvetica", 10)` |
| Cabeçalho do Treeview | `("Helvetica", 10, "bold")` |

**Regra:** usar apenas fontes disponíveis no sistema alvo (Windows: `"Helvetica"`, `"Arial"`, `"Segoe UI"`). Evitar dependências de fontes externas.

---

## 9. Estilo do Treeview (ttk.Style)

O Treeview usa tema `"clam"` para garantir controle total dos estilos:

```python
style = ttk.Style()
style.theme_use("clam")
style.configure(
    "Custom.Treeview",
    background="#2b2b2b",
    foreground="white",
    fieldbackground="#2b2b2b",
    rowheight=24,
    font=("Helvetica", 10),
)
style.configure(
    "Custom.Treeview.Heading",
    background="#1a5276",
    foreground="white",
    font=("Helvetica", 10, "bold"),
)
style.map(
    "Custom.Treeview",
    background=[("selected", "#1f618d")],
)
```

**Regra:** sempre aplicar `style.theme_use("clam")` antes de configurar estilos customizados no Treeview. O tema padrão do Windows ignora muitas configurações de estilo.

---

## 10. Threading e Thread-Safety

**Regra fundamental:** qualquer operação de I/O ou processamento pesado deve rodar em thread separada. A UI só é atualizada na thread principal.

### Padrão de disparo
```python
def _iniciar_processamento(self):
    t = threading.Thread(target=self._processar, daemon=True)
    t.start()
```

`daemon=True` garante que a thread encerra quando a janela fecha, sem precisar de join explícito.

### Retorno para a thread principal
```python
# dentro da thread:
self.after(0, self._exibir_resultado)

# para erros:
self.after(0, lambda: messagebox.showerror("Erro", str(e)))
```

`self.after(0, callback)` faz o marshaling correto de volta para o loop de eventos do tkinter. **Nunca** atualizar widgets diretamente de dentro de uma thread.

### Callback de progresso (inversão de controle)
```python
# No parser:
def parse_sped(caminho: str, progress_cb=None) -> tuple[...]:
    for i, linha in enumerate(linhas):
        if progress_cb:
            progress_cb(i, total)

# Na GUI:
def cb_sped(lido, total):
    self._progress_val.set(0.5 * lido / total if total else 0)
    self._set_status(f"Lendo SPED... {lido}/{total} linhas")

empresa, notas = parse_sped(caminho, progress_cb=cb_sped)
```

O parser não conhece a GUI — apenas aceita um callable opcional. A GUI define o comportamento de progresso.

---

## 11. Gerenciamento de Estado

Estado gerenciado como atributos de instância de `App`. Sem framework externo.

### `tk.StringVar` / `tk.DoubleVar` para binding automático com widgets
```python
self._sped_path    = tk.StringVar(value="")
self._sefaz_path   = tk.StringVar(value="")
self._status       = tk.StringVar(value="Aguardando...")
self._progress_val = tk.DoubleVar(value=0.0)
```

### Objetos de domínio como atributos simples
```python
self._empresa:   EmpresaSped | None = None
self._resultado: ResultadoConciliacao | None = None
```

**Regra:** `tk.StringVar`/`tk.DoubleVar` para dados que precisam de binding automático com widgets. Objetos de domínio como atributos simples — atualizados sincronamente em `_exibir_resultado()`.

---

## 12. Dataclasses como DTOs

Todos os dados trafegam entre camadas via dataclasses tipadas:

```python
@dataclass
class EmpresaSped:
    cnpj: str
    nome: str

@dataclass
class NotaSped:
    chave: str
    tipo: str  # ou @property derivado de outro campo

@dataclass
class NotaSefaz:
    chave: str
    numero: str
    data: str
    valor: float
    situacao: str

@dataclass
class ResultadoConciliacao:
    entradas_divergentes_a: list[NotaSefaz]
    entradas_divergentes_b: list[NotaSped]
    saidas_divergentes_a: list[NotaSefaz]
    saidas_divergentes_b: list[NotaSped]
    total_entradas_sefaz: int
    total_saidas_sefaz: int
```

**Regra:** uma dataclass por entidade de domínio. Nunca passar dicionários genéricos entre camadas.

---

## 13. Convenções de Nomenclatura

**Idioma:** português para todo o vocabulário do domínio. Inglês apenas para termos técnicos universais (`parse`, `export`, `build`, `callback`).

### Classes
`PascalCase` — `App`, `ResultTable`, `EmpresaSped`, `NotaSped`, `NotaSefaz`, `ResultadoConciliacao`

### Métodos privados de instância
Prefixo `_` + verbo descritivo:
- `_build_ui()` — construção de widgets
- `_browse_sped()` / `_browse_sefaz()` — abertura de diálogo de arquivo
- `_iniciar_processamento()` — disparo da thread
- `_processar()` — lógica na thread
- `_exibir_resultado()` — atualização da UI pós-processamento
- `_exportar()` — escrita do relatório
- `_set_status()` — helper de atualização de status

### Funções privadas de módulo
Prefixo `_` + verbo:
- `_normaliza_cnpj()`, `_formata_data()`, `_cell_str()` (parsers)
- `_header_style()`, `_ajustar_colunas()`, `_aba_resumo()` (exporter)

### Atributos de instância
Prefixo `_` + substantivo:
- `_sped_path`, `_sefaz_path` — `StringVar` de caminhos
- `_btn_processar`, `_btn_exportar` — widgets que precisam de referência posterior
- `_table_a`, `_table_b` — componentes de tabela
- `_empresa`, `_resultado` — objetos de domínio

### Constantes de módulo
`UPPER_CASE` para constantes públicas; `_UPPER_CASE` para constantes privadas de módulo.

### Lambdas com closures em loop
```python
command=lambda c=nome: self._ordenar(c)  # sempre usar argumento padrão
```

---

## 14. Padrões do Exporter (openpyxl)

- Uma função pública: `exportar(resultado, empresa, caminho)`.
- Funções privadas por responsabilidade: `_aba_resumo()`, `_aba_entradas()`, `_aba_saidas()`, `_header_style()`, `_ajustar_colunas()`.
- Estilo de cabeçalho definido em helper reutilizável `_header_style(ws, colunas, cor_hex)`.
- `_ajustar_colunas(ws)` itera todas as colunas e define largura baseada no conteúdo máximo.
- Zebragem via `PatternFill` nas linhas de dados (par/ímpar com cores distintas por aba).
- Constantes de cor definidas no topo do módulo como `_NOME_HEX = "RRGGBB"` (sem `#`).

---

## 15. Distribuição (PyInstaller)

### `.spec` essencial
```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name='ConferenciaSPEDSEFAZ',
    console=False,          # sem janela de console
    icon='icon.ico',        # ícone do executável
)
```

### Ícone na janela
```python
def _aplicar_icone(self):
    if sys.platform == "win32":
        self.iconbitmap("icon.ico")
```

Aplica o ícone apenas no Windows. No macOS, o ícone é definido via `.app bundle`.

### CI/CD (GitHub Actions)
- Trigger: push de tag `v*` (ex: `v1.2.0`).
- Runner: `windows-latest`.
- Comando: `pyinstaller conferencia_sped.spec`.
- Artefato: upload do `.exe` gerado como asset da release.

---

## 16. Checklist para Novos Projetos

- [ ] Estrutura de módulos em camadas (`parsers/`, `gui/`, módulos de negócio e output separados)
- [ ] `main.py` com apenas `App().mainloop()`
- [ ] Tema definido no nível de módulo antes de instanciar a janela
- [ ] `_build_ui()` separado do `__init__`
- [ ] Threading com `daemon=True` para processamento pesado
- [ ] Marshaling de volta para UI via `self.after(0, callback)`
- [ ] Callbacks de progresso por inversão de controle (parser aceita `progress_cb=None`)
- [ ] Dataclasses como DTOs entre camadas
- [ ] `ttk.Style` com tema `"clam"` para Treeview customizado
- [ ] Lambda com argumento padrão em loops (`lambda c=nome: ...`)
- [ ] Zebragem de linhas no Treeview com tags `"par"` / `"impar"`
- [ ] Ordenação bidirecional com chave numérica inteligente (`try float`)
- [ ] Paleta de cores consistente entre GUI e relatório exportado
- [ ] Constantes de cor no topo dos módulos (`_NOME_HEX`)
- [ ] Nomenclatura em português para o domínio da aplicação
- [ ] `.spec` PyInstaller com `console=False` e ícone configurado
- [ ] CI/CD via GitHub Actions com trigger em tag `v*`
