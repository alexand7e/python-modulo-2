# Módulo 2 — Automação de Documentos 🧑‍💻

Bem-vindo(a)! Aqui você vai transformar **uma planilha de 30 servidores** em
**ofícios Word, PDFs e um Excel formatado** — sem fazer nada à mão. E vai
fazer isso **dirigindo a IA**, não decorando código.

## 🚦 Comece por aqui (3 passos)

**1. Veja se sua máquina está pronta:**

```bash
python3 iniciando_a_aula.py
```

Esse script não muda nada — ele só te diz a versão do Python, quais
bibliotecas faltam e quais arquivos da aula já existem. Se faltar algo, ele
explica como instalar.

**2. Instale as bibliotecas (uma vez só):**

```bash
python3 -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**3. Rode a aula, na ordem:**

```bash
python3 scripts/frente0_ler_e_limpar.py     # limpa a planilha → saida/servidores_limpo.xlsx
python3 scripts/frente1_oficios_word.py     # 28 ofícios .docx  → saida/oficios/
python3 scripts/frente2_pdf_reportlab.py    # 28 PDFs           → saida/pdfs/
python3 scripts/frente3_excel_formatado.py  # Excel bonito      → saida/servidores_formatado.xlsx
python3 scripts/complemento_organizar_arquivos.py   # renomear (modo seguro)
```

> A **Frente 0 vem sempre primeiro**: ela gera a planilha limpa que todas as
> outras leem.

## 🧠 A regra da casa

```
Pense o problema  →  dirija a IA  →  confira o resultado.
```

E o **esqueleto** que se repete o tempo todo:

```
ler a planilha  →  para cada linha  →  gerar a saída  →  salvar
```

## ✍️ Sua vez (o que está em aberto)

A base já funciona, mas **de propósito** alguns pedaços ficaram para você.
Procure por `EXERCÍCIO` e `TODO(aluno)` nos scripts — cada um traz um
**prompt pronto para a IA** e uma dica:

- **Frente 0:** as datas ainda estão bagunçadas (`12-11-2010`, `05/07/2018`…).
  Faça `limpar_datas` deixar tudo em `dd/mm/aaaa`.
- **Frente 2:** o PDF está cru. Dê a ele um layout institucional (cabeçalho,
  cores, rodapé).
- **Complemento:** mova cada ofício para a subpasta da sua secretaria.

E o mais importante: **invente tarefas novas** que você acha úteis. Validar
o CPF? Uma aba por secretaria? Coluna "anos de casa"? Vá em frente — é assim
que se aprende.

## 📁 Onde fica cada coisa

| Pasta        | Para quê                                            |
|--------------|-----------------------------------------------------|
| `entrada/`   | a planilha original — **nunca altere**              |
| `modelo/`    | o modelo de ofício com `{{MARCADORES}}`             |
| `scripts/`   | um arquivo por frente da aula                       |
| `saida/`     | tudo o que é gerado — pode apagar e rodar de novo   |

## ⚠️ Regra de ouro (operações em lote)

Antes de renomear ou mover arquivos **em massa**, rode em modo de simulação e
**confira o resultado na tela**. Em lote, o erro é irreversível. Por isso o
script de renomear só mexe nos arquivos quando você passa `--aplicar`.
