"""
INICIANDO A AULA — Verificador de ambiente
Módulo 2 — Automação de Documentos: Planilhas e Word

Rode ESTE arquivo ANTES de qualquer outro. Ele NÃO instala nada e NÃO
modifica nenhum arquivo: apenas olha para a sua máquina e te diz o que
está pronto e o que falta para a aula funcionar.

    python3 iniciando_a_aula.py

Por que existe? Os slides avisam que preparar o ambiente é "o maior ponto
de atrito — reserve tempo". Este script transforma esse atrito num
checklist objetivo: versão do Python, bibliotecas do dia e arquivos da
aula. É pensamento computacional aplicado à própria preparação:
decompor o "será que está tudo certo?" em verificações pequenas e claras.

IMPORTANTE: este arquivo usa SÓ a biblioteca padrão do Python, de
propósito — ele precisa rodar mesmo antes de você instalar qualquer coisa.
"""

import importlib.util
import sys
from pathlib import Path


# --------------------------------------------------------------------------
# Pequenos enfeites de terminal. Se o seu terminal não mostrar as cores,
# não tem problema — o texto continua legível.
# --------------------------------------------------------------------------
class Cor:
    VERDE = "\033[92m"
    VERMELHO = "\033[91m"
    AMARELO = "\033[93m"
    AZUL = "\033[94m"
    NEGRITO = "\033[1m"
    FIM = "\033[0m"


OK = f"{Cor.VERDE}[OK]{Cor.FIM}"
FALTA = f"{Cor.VERMELHO}[FALTA]{Cor.FIM}"
ALERTA = f"{Cor.AMARELO}[!]{Cor.FIM}"


def titulo(texto: str) -> None:
    print()
    print(f"{Cor.NEGRITO}{Cor.AZUL}{texto}{Cor.FIM}")
    print("-" * len(texto))


# --------------------------------------------------------------------------
# 1) Versão do Python
# --------------------------------------------------------------------------
PYTHON_MINIMO = (3, 9)


def checar_python() -> bool:
    titulo("1. Versão do Python")
    v = sys.version_info
    versao_atual = f"{v.major}.{v.minor}.{v.micro}"
    if (v.major, v.minor) >= PYTHON_MINIMO:
        print(f"  {OK} Python {versao_atual} — perfeito para a aula.")
        return True
    minimo = f"{PYTHON_MINIMO[0]}.{PYTHON_MINIMO[1]}"
    print(f"  {FALTA} Python {versao_atual} — a aula pede {minimo} ou mais novo.")
    print("     Atualize o Python antes de continuar (https://python.org).")
    return False


# --------------------------------------------------------------------------
# 2) Bibliotecas do dia
#
# Cada item é (nome_para_importar, nome_no_pip, para_que_serve).
# Às vezes o nome do import é diferente do nome do pacote no pip — por isso
# os dois aparecem (ex.: importamos "docx", mas instalamos "python-docx").
# --------------------------------------------------------------------------
BIBLIOTECAS = [
    ("pandas", "pandas", "ler e limpar a planilha (Frente 0)"),
    ("openpyxl", "openpyxl", "ler/escrever Excel formatado (Frente 3)"),
    ("docx", "python-docx", "gerar os ofícios em Word (Frente 1)"),
    ("reportlab", "reportlab", "gerar os PDFs (Frente 2)"),
]


def checar_bibliotecas() -> list[str]:
    """Retorna a lista de pacotes (nome no pip) que faltam instalar."""
    titulo("2. Bibliotecas do dia")
    faltando: list[str] = []
    for nome_import, nome_pip, para_que in BIBLIOTECAS:
        if importlib.util.find_spec(nome_import) is not None:
            print(f"  {OK} {nome_pip:<14} — {para_que}")
        else:
            print(f"  {FALTA} {nome_pip:<14} — {para_que}")
            faltando.append(nome_pip)
    return faltando


# --------------------------------------------------------------------------
# 3) Arquivos e pastas da aula
# --------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent

ARQUIVOS_ESPERADOS = [
    (RAIZ / "entrada" / "servidores.xlsx", "planilha-fonte (os 30 servidores)"),
    (RAIZ / "modelo" / "oficio_modelo.docx", "modelo de ofício com {{MARCADORES}}"),
]

PASTAS_ESPERADAS = [
    (RAIZ / "entrada", "onde ficam os arquivos que LEMOS (nunca alterar)"),
    (RAIZ / "modelo", "onde fica o modelo de ofício"),
    (RAIZ / "saida", "onde GRAVAMOS o que for gerado"),
    (RAIZ / "scripts", "onde ficam os scripts de cada frente"),
]


def checar_estrutura() -> bool:
    titulo("3. Arquivos e pastas da aula")
    tudo_ok = True

    for caminho, descricao in PASTAS_ESPERADAS:
        if caminho.is_dir():
            print(f"  {OK} pasta {caminho.name + '/':<10} — {descricao}")
        else:
            print(f"  {ALERTA} pasta {caminho.name + '/':<10} — não existe ainda ({descricao})")
            print("       Crie com:  mkdir -p " + str(caminho.relative_to(RAIZ)))
            tudo_ok = False

    print()
    for caminho, descricao in ARQUIVOS_ESPERADOS:
        if caminho.is_file():
            relativo = caminho.relative_to(RAIZ)
            print(f"  {OK} {str(relativo):<28} — {descricao}")
        else:
            relativo = caminho.relative_to(RAIZ)
            print(f"  {FALTA} {str(relativo):<28} — NÃO encontrado ({descricao})")
            tudo_ok = False

    return tudo_ok


# --------------------------------------------------------------------------
# Fechamento: o que fazer agora
# --------------------------------------------------------------------------
def receita_de_instalacao(faltando: list[str]) -> None:
    titulo("Como instalar o que falta")
    print("  Passo 1 — crie um ambiente isolado (faça uma vez só):")
    print(f"    {Cor.NEGRITO}python3 -m venv .venv{Cor.FIM}")
    print(f"    {Cor.NEGRITO}source .venv/bin/activate{Cor.FIM}   "
          "(no Windows: .venv\\Scripts\\activate)")
    print()
    print("  Passo 2 — instale as bibliotecas que faltam:")
    print(f"    {Cor.NEGRITO}pip install {' '.join(faltando)}{Cor.FIM}")
    print()
    print("  Ou, de uma vez, tudo o que a aula usa:")
    print(f"    {Cor.NEGRITO}pip install -r requirements.txt{Cor.FIM}")
    print()
    print("  Depois, rode este verificador de novo para confirmar:")
    print(f"    {Cor.NEGRITO}python3 iniciando_a_aula.py{Cor.FIM}")


def main() -> None:
    print(f"{Cor.NEGRITO}╔══════════════════════════════════════════════════╗{Cor.FIM}")
    print(f"{Cor.NEGRITO}║   INICIANDO A AULA — verificação de ambiente     ║{Cor.FIM}")
    print(f"{Cor.NEGRITO}║   Módulo 2 — Automação de Documentos             ║{Cor.FIM}")
    print(f"{Cor.NEGRITO}╚══════════════════════════════════════════════════╝{Cor.FIM}")

    python_ok = checar_python()
    faltando = checar_bibliotecas()
    estrutura_ok = checar_estrutura()

    titulo("Resumo")
    if python_ok and not faltando and estrutura_ok:
        print(f"  {OK} Ambiente pronto! Pode começar pela Frente 0:")
        print(f"     {Cor.NEGRITO}python3 scripts/frente0_ler_e_limpar.py{Cor.FIM}")
    else:
        if not python_ok:
            print(f"  {FALTA} Resolva a versão do Python primeiro (item 1).")
        if faltando:
            print(f"  {FALTA} Faltam {len(faltando)} biblioteca(s): "
                  f"{', '.join(faltando)}")
        if not estrutura_ok:
            print(f"  {ALERTA} Faltam pastas/arquivos (veja o item 3).")
        if faltando:
            receita_de_instalacao(faltando)

    print()


if __name__ == "__main__":
    main()
