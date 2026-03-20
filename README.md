# Conferência SPED

Aplicação desktop para conciliação entre o arquivo SPED EFD-ICMS/IPI e o relatório de NF-e exportado da SEFAZ.

## O que o programa faz

Cruza duas fontes de dados e aponta divergências:

| Divergência | Descrição |
|---|---|
| **A** | NF-e de  **entrada** presentes no SEFAZ (autorizadas) que **não foram escrituradas** no SPED |
| **B** | NF-e de  **saída** presentes no SEFAZ (autorizadas) que **não foram escrituradas** no SPED |

Notas canceladas no SEFAZ são automaticamente desconsideradas.
A chave de comparação é a **Chave de Acesso** de 44 dígitos da NF-e.

## Arquivos necessários

| Arquivo | Origem | Formato |
|---|---|---|
| SPED EFD-ICMS/IPI | Sistema de escrituração fiscal | `.txt` (pipe-delimitado, ISO-8859-1) |
| Relatório NF-e | Portal SEFAZ — Consulta Emissor/Destinatário | `.xls` |

## Instalação (primeira vez)

Requisitos: **Python 3.10+** instalado.

```bash
# 1. Clone ou copie o projeto
cd conferencia-entradas-sped

# 2. Crie o ambiente virtual
python3 -m venv .venv

# 3. Ative o ambiente
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate.bat

# 4. Instale as dependências
pip install -r requirements.txt
```

## Como usar

```bash
# Com o ambiente virtual ativado:
python main.py

# Ou diretamente (sem ativar):
.venv/bin/python main.py        # macOS/Linux
.venv\Scripts\python main.py   # Windows
```

1. Clique em **Arquivo SPED** e selecione o `.txt` do SPED
2. Clique em **Relatório SEFAZ** e selecione o `.xls` exportado da SEFAZ
3. Clique em **Processar**
4. Analise as divergências nas duas abas de resultado
5. Clique em **Exportar Relatório** para salvar um `.xlsx` com os resultados

## Exportação Excel

O arquivo gerado contém 3 abas:

- **Resumo** — empresa, período, totais e contagem de divergências
- **Entradas_Fora_SPED** — NF-e de entrada autorizadas no SEFAZ não encontradas no SPED
- **Saidas_Fora_SPED** — NF-e de saída autorizadas no SEFAZ não encontradas no SPED

## Gerar executável Windows (.exe)

Para distribuir sem precisar instalar Python, execute em uma máquina Windows:

```bat
build_windows.bat
```

O executável será gerado em `dist\ConferenciaSPED.exe`.

Alternativamente, o GitHub Actions gera o `.exe` automaticamente ao criar uma tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Estrutura do projeto

```
conferencia-entradas-sped/
├── main.py                  # Ponto de entrada
├── requirements.txt
├── conferencia_sped.spec    # Configuração do PyInstaller
├── build_windows.bat        # Script de build para Windows
├── .github/workflows/
│   └── build.yml            # GitHub Actions — build automático do .exe
└── src/
    ├── parsers/
    │   ├── sped_parser.py   # Leitura do SPED (registros 0000, 0150, C100)
    │   └── sefaz_parser.py  # Leitura do .xls da SEFAZ
    ├── conciliacao.py       # Lógica de comparação e divergências
    ├── exporter.py          # Geração do relatório .xlsx
    └── gui/
        ├── app.py           # Janela principal
        └── result_table.py  # Componente de tabela
```

## Dependências

| Pacote | Uso |
|---|---|
| `customtkinter` | Interface gráfica moderna |
| `xlrd` | Leitura de arquivos `.xls` |
| `openpyxl` | Geração do relatório `.xlsx` |
