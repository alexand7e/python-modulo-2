"""
INICIANDO A AULA — Verificador de ambiente
Módulo 2 — Automação de Documentos: Planilhas e Word
Módulo 3 — Análise de Dados

Rode ESTE arquivo ANTES de qualquer outro. Ele NÃO instala nada e NÃO
modifica nenhum arquivo de dados: apenas olha para a sua máquina e te diz o
que está pronto e o que falta para a aula funcionar.

    python3 iniciando_a_aula.py

Por que existe? Os slides avisam que preparar o ambiente é "o maior ponto
de atrito — reserve tempo". Este script transforma esse atrito num
checklist objetivo. É pensamento computacional aplicado à própria
preparação: decompor o "será que está tudo certo?" em verificações pequenas
e claras.

Novo na versão com Módulo 3:
  • Verifica bibliotecas e arquivos dos DOIS módulos.
  • Oferece sincronizar o repositório com o Git (git pull) para que novos
    arquivos compartilhados pelo professor cheguem à máquina de cada aluno
    — sem precisar clonar de novo.

IMPORTANTE: este arquivo usa SÓ a biblioteca padrão do Python, de
propósito — ele precisa rodar mesmo antes de você instalar qualquer coisa.
"""

import importlib.util
import shutil
import subprocess
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
# 0) Sincronizar com o Git (pegar arquivos novos compartilhados pelo prof)
# --------------------------------------------------------------------------
class GitSync:
    """Utilities para sincronizar o repositório com o remote (git pull).

    O objetivo é REDUNDÂNCIA e FUNCIONAMENTO: tentamos vários caminhos e
    mostramos o que deu errado, sem quebrar o resto da checagem.
    """

    def __init__(self, raiz: Path):
        self.raiz = raiz
        self.git = shutil.which("git")

    def no_repositorio(self) -> bool:
        """True se estamos dentro de um repo git (existe .git)."""
        return (self.raiz / ".git").is_dir()

    def tem_git(self) -> bool:
        return self.git is not None

    def remote_atual(self) -> str | None:
        """Retorna o nome do remote configurado ('origin') ou None."""
        if not self.tem_git():
            return None
        try:
            res = subprocess.run(
                [self.git, "remote", "get-url", "origin"],
                cwd=self.raiz, capture_output=True, text=True,
                timeout=15, check=False,
            )
            return res.stdout.strip() if res.returncode == 0 else None
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return None

    def sincronizar(self) -> None:
        """Tenta `git pull` no repositório. Múltiplas tentativas com fallback."""
        print(f"  Remote detectado: {self.remote_atual() or '(nenhum)'}")
        if not self.tem_git():
            print(f"  {ALERTA} git não encontrado no PATH — pulando sincronização.")
            print("       Instale o Git (https://git-scm.com) e rode novamente.")
            return
        if not self.no_repositorio():
            print(f"  {ALERTA} não é um repositório Git aqui ({self.raiz}).")
            print("       Para baixar o curso do zero, use:")
            print(f"         {Cor.NEGRITO}git clone <url-do-professor>"
                  f"{Cor.FIM}")
            return

        print("Tentando sincronizar com o remote (git pull)...")
        # Tentativa 1: git pull (abraça fetch + merge/rebase)
        ok = self._tentar_comando(["pull", "--ff-only"], "pull --ff-only")
        if ok:
            print(f"  {OK} repositório sincronizado (fast-forward).")
            return

        # Tentativa 2: um pull comum (pode criar merge)
        ok = self._tentar_comando(["pull"], "pull")
        if ok:
            print(f"  {OK} repositório sincronizado.")
            return

        # Tentativa 3: apenas fetch, sem mexer na cópia de trabalho
        ok = self._tentar_comando(["fetch", "--all"], "fetch --all",
                                  msg_ok="busquei novidades (fetch) — "
                                         "rode `git merge`/`git pull` manual"
                                  " se houver mudanças.")
        if ok:
            return

        # Tentativa 4: fallback — mostrar status para o aluno decidir
        print(f"  {ALERTA} não consegui sincronizar automaticamente.")
        print("       Possíveis causas:")
        print("         • mudanças locais não commitadas (Salve antes e rode "
              "`git stash` ou faça um commit.)")
        print("         • sem internet ou remote incorreto.")
        print("         • histórico divergente que exige merge manual.")
        print("       Rode à mão, na raiz do projeto:")
        print(f"         {Cor.NEGRITO}git status{Cor.FIM}    e    "
              f"{Cor.NEGRITO}git pull{Cor.FIM}")
        print("       Dica: para não perder seu trabalho, antes de tudo:")
        print(f"         {Cor.NEGRITO}git stash{Cor.FIM}   (guarda mudanças à "
              "parte) → git pull → git stash pop")

    def _tentar_comando(self, args, nome, msg_ok=None) -> bool:
        """Roda um subcomando git; retorna True em caso de sucesso."""
        try:
            res = subprocess.run(
                [self.git, *args],
                cwd=self.raiz, capture_output=True, text=True,
                timeout=60, check=False,
            )
        except subprocess.TimeoutExpired:
            print(f"  {ALERTA} '{' '.join(args)}' demorou demais (>60s) "
                  "— internet lenta ou bloqueada?")
            return False
        except (FileNotFoundError, OSError) as e:
            print(f"  {ALERTA} '{' '.join(args)}' falhou ao rodar: {e}")
            return False
        if res.returncode == 0:
            saida = (res.stdout or "").strip()
            if saida:
                for linha in saida.splitlines()[:6]:
                    print(f"      git│ {linha}")
            if msg_ok:
                print(f"  {OK} {msg_ok}")
            return True
        # erro: mostra as duas primeiras linhas
        err = (res.stderr or res.stdout or "").strip().splitlines()
        for linha in err[:4]:
            print(f"      git│ {linha}")
        return False


def perguntar_sim(pergunta: str) -> bool:
    """Pergunta S/N no terminal. Retorna True para sim."""
    try:
        rsp = input(f"{Cor.NEGRITO}{pergunta} (s/N)? {Cor.FIM}").strip().lower()
        return rsp in ("s", "sim", "y", "yes")
    except EOFError:
        return False


def sec_sincronizacao_git() -> None:
    titulo("0. Sincronizar com o Git (pegar arquivos novos)")
    gitsync = GitSync(Path(__file__).resolve().parent)
    print("Com o Módulo 3 vimos arquivos novos compartilhados no repositório.")
    print("Sincroniza-los agora garante que você tem os scripts e as bases.")
    if gitsync.no_repositorio() and gitsync.tem_git():
        if perguntar_sim("Sincronizar agora (git pull)"):
            gitsync.sincronizar()
        else:
            print(f"  {ALERTA} pulado. Lembre: rode  git pull  antes de "
                  "começar a aula.")
    else:
        gitsync.sincronizar()  # mostra as mensagens explicativas


# --------------------------------------------------------------------------
# 1) Versão do Python
# --------------------------------------------------------------------------
PYTHON_MINIMO = (3, 9)


def checar_python() -> bool:
    titulo("1. Versão do Python")
    v = sys.version_info
    versao_atual = f"{v.major}.{v.minor}.{v.micro}"
    if (v.major, v.minor) >= PYTHON_MINIMO:
        print(f"  {OK} Python {versao_atual} — perfeito para os módulos.")
        return True
    minimo = f"{PYTHON_MINIMO[0]}.{PYTHON_MINIMO[1]}"
    print(f"  {FALTA} Python {versao_atual} — a aula pede {minimo} ou mais novo.")
    print("     Atualize o Python antes de continuar (https://python.org).")
    return False


# --------------------------------------------------------------------------
# 2) Bibliotecas do dia (dois módulos agora)
# --------------------------------------------------------------------------
BIBLIOTECAS = [
    # Módulo 2
    ("pandas", "pandas", "ler e limpar a planilha (Módulo 2 · Frente 0)"),
    ("openpyxl", "openpyxl", "ler/escrever Excel formatado (Módulo 2 · Frente 3)"),
    ("docx", "python-docx", "gerar os ofícios em Word (Módulo 2 · Frente 1)"),
    ("reportlab", "reportlab", "gerar os PDFs (Módulo 2 · Frente 2)"),
    # Módulo 3
    ("matplotlib", "matplotlib", "gráficos de barras/linhas/pizza (Módulo 3 · notebook)"),
    ("streamlit", "streamlit", "dashboard interativo (Módulo 3 · dashboard)"),
    ("jupyterlab", "jupyterlab", "abrir/rodar o notebook ETL (Módulo 3)"),
]


def checar_bibliotecas() -> list[str]:
    """Retorna a lista de pacotes (nome no pip) que faltam instalar."""
    titulo("2. Bibliotecas (Módulos 2 e 3)")
    faltando: list[str] = []
    modulo = None
    for nome_import, nome_pip, para_que in BIBLIOTECAS:
        eh_m3 = "Módulo 3" in para_que
        if eh_m3 != modulo:
            modulo = eh_m3
            print(f"   {Cor.NEGRITO}{'— Módulo 3 —' if eh_m3 else '— Módulo 2 —'}"
                  f"{Cor.FIM}")
        if importlib.util.find_spec(nome_import) is not None:
            print(f"  {OK} {nome_pip:<14} — {para_que}")
        else:
            print(f"  {FALTA} {nome_pip:<14} — {para_que}")
            faltando.append(nome_pip)
    return faltando


# --------------------------------------------------------------------------
# 3) Arquivos e pastas da aula (dois módulos agora)
# --------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent

ARQUIVOS_ESPERADOS = [
    # Módulo 2
    (RAIZ / "entrada" / "modulo2" / "servidores.xlsx",
     "planilha-fonte Módulo 2 (30 servidores)"),
    (RAIZ / "modelo" / "oficio_modelo.docx",
     "modelo de ofício com {{MARCADORES}}"),
    # Módulo 3
    (RAIZ / "entrada" / "modulo3" / "municipios_piaui_suja.xlsx",
     "base 1 do Módulo 3 (municípios + lat/long)"),
    (RAIZ / "entrada" / "modulo3" / "escolas_piaui_suja.xlsx",
     "base 2 do Módulo 3 (escolas)"),
    (RAIZ / "entrada" / "modulo3" / "servidores_piaui_suja.xlsx",
     "base 3 do Módulo 3 (servidores)"),
    (RAIZ / "entrada" / "modulo3" / "escolas_piaui_v1.xlsx",
     "versão 'antes' p/ diff do Módulo 3"),
    (RAIZ / "entrada" / "modulo3" / "escolas_piaui_v2.xlsx",
     "versão 'depois' p/ diff do Módulo 3"),
    (RAIZ / "scripts" / "modulo3" / "notebook_etl.ipynb",
     "notebook central do Módulo 3"),
]

PASTAS_ESPERADAS = [
    (RAIZ / "entrada" / "modulo2", "dados de ENTRADA do Módulo 2 (não alterar)"),
    (RAIZ / "entrada" / "modulo3", "dados de ENTRADA do Módulo 3 (não alterar)"),
    (RAIZ / "modelo", "onde fica o modelo de ofício"),
    (RAIZ / "saida" / "modulo2", "SAÍDA gerada pelo Módulo 2"),
    (RAIZ / "saida" / "modulo3", "SAÍDA gerada pelo Módulo 3"),
    (RAIZ / "scripts" / "modulo2", "scripts das frentes do Módulo 2"),
    (RAIZ / "scripts" / "modulo3", "scripts do Módulo 3"),
]


def checar_estrutura() -> bool:
    titulo("3. Arquivos e pastas (Módulos 2 e 3)")
    tudo_ok = True

    for caminho, descricao in PASTAS_ESPERADAS:
        if caminho.is_dir():
            rel = str(caminho.relative_to(RAIZ))
            print(f"  {OK} pasta {rel:<32} — {descricao}")
        else:
            rel = str(caminho.relative_to(RAIZ))
            print(f"  {ALERTA} pasta {rel:<32} — não existe ({descricao})")
            print("       Se faltar, rode:  git pull   (professor compartilhou?)")
            print("       Ou crie com:  mkdir -p " + rel)
            tudo_ok = False

    print()
    for caminho, descricao in ARQUIVOS_ESPERADOS:
        if caminho.is_file():
            relativo = caminho.relative_to(RAIZ)
            print(f"  {OK} {str(relativo):<40} — {descricao}")
        else:
            relativo = caminho.relative_to(RAIZ)
            print(f"  {FALTA} {str(relativo):<40} — NÃO encontrado "
                  f"({descricao})")
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
    print("  Ou, de uma vez, tudo o que os módulos usam:")
    print(f"    {Cor.NEGRITO}pip install -r requirements.txt{Cor.FIM}")
    print()
    print("  Depois, rode este verificador de novo para confirmar:")
    print(f"    {Cor.NEGRITO}python3 iniciando_a_aula.py{Cor.FIM}")


def main() -> None:
    print(f"{Cor.NEGRITO}╔══════════════════════════════════════════════════╗{Cor.FIM}")
    print(f"{Cor.NEGRITO}║   INICIANDO A AULA — verificação de ambiente     ║{Cor.FIM}")
    print(f"{Cor.NEGRITO}║   Módulo 2 — Automação de Documentos            ║{Cor.FIM}")
    print(f"{Cor.NEGRITO}║   Módulo 3 — Análise de Dados                   ║{Cor.FIM}")
    print(f"{Cor.NEGRITO}╚══════════════════════════════════════════════════╝{Cor.FIM}")

    sec_sincronizacao_git()
    python_ok = checar_python()
    faltando = checar_bibliotecas()
    estrutura_ok = checar_estrutura()

    titulo("Resumo")
    if python_ok and not faltando and estrutura_ok:
        print(f"  {OK} Ambiente pronto! Comece pelo inicio de cada módulo:")
        print(f"     Módulo 2:  {Cor.NEGRITO}"
              f"python3 scripts/modulo2/frente0_ler_e_limpar.py{Cor.FIM}")
        print(f"     Módulo 3:  {Cor.NEGRITO}"
              f"jupyter lab scripts/modulo3/notebook_etl.ipynb{Cor.FIM}")
        print(f"     Dashboard: {Cor.NEGRITO}"
              f"streamlit run scripts/modulo3/m3_dashboard_streamlit.py{Cor.FIM}")
    else:
        if not python_ok:
            print(f"  {FALTA} Resolva a versão do Python primeiro (item 1).")
        if faltando:
            print(f"  {FALTA} Faltam {len(faltando)} biblioteca(s): "
                  f"{', '.join(faltando)}")
        if not estrutura_ok:
            print(f"  {ALERTA} Faltam pastas/arquivos (veja o item 3). "
                  "Tente:  git pull")
        if faltando:
            receita_de_instalacao(faltando)

    print()


if __name__ == "__main__":
    main()