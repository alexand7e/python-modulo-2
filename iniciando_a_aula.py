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
  • Oferece sincronizar o repositório com o Git (git pull) — e, se o Git
    não estiver instalado ou o pull falhar, BAIXA o repositório como ZIP
    via HTTP (só stdlib). Funciona mesmo sem git, sem precisar clonar.
  • Pode instalar as bibliotecas do curso (pip) automaticamente.

IMPORTANTE: este arquivo usa SÓ a biblioteca padrão do Python, de
propósito — ele precisa rodar mesmo antes de você instalar qualquer coisa.
"""

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

# --------------------------------------------------------------------------
# Configuração do repositório do curso
#
# O professor define AQUI a URL do repo. Mesmo sem o Git instalado, este
# script consegue BAIXAR tudo (ZIP via HTTP) e SINCRONIZAR os arquivos do
# repositório para a máquina do aluno.优先ível de também editar em
# .repo_url (uma linha com a URL) ou via variável de ambiente AULA_REPO_URL.
# --------------------------------------------------------------------------
REPO_URL_DEFAULT = "https://github.com/alexand7e/python-modulo-2.git"
RAMO_DEFAULT = "main"

# Pastas/arquivos que NUNCA devem ser sobrescritos pelo download do ZIP,
# para não apagar o trabalho do aluno nem o ambiente virtual.
PROTEGIDOS_DOWNLOAD = {".git", ".venv", "venv", "env", "__pycache__", "saida"}


def resolver_url_repo() -> str:
    """Resolve a URL do repo: variável de ambiente > .repo_url > git remote > padrão."""
    url = os.environ.get("AULA_REPO_URL")
    if url:
        return url.strip()
    arq = Path(__file__).resolve().parent / ".repo_url"
    if arq.is_file():
        for linha in arq.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if linha and not linha.startswith("#"):
                return linha
    # tenta ler o remote via git, se existir
    git = shutil.which("git")
    if git and (Path(__file__).resolve().parent / ".git").is_dir():
        try:
            res = subprocess.run(
                [git, "remote", "get-url", "origin"],
                cwd=Path(__file__).resolve().parent,
                capture_output=True, text=True, timeout=15, check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
    return REPO_URL_DEFAULT


def url_para_zip(url_repo: str, ramo: str = RAMO_DEFAULT) -> str:
    """Converte 'https://github.com/USER/REPO.git' em URL do ZIP do ramo."""
    url = url_repo.rstrip("/").removesuffix(".git")
    # suporta github.com/USER/REPO
    if "github.com" in url:
        # -> https://codeload.github.com/USER/REPO/zip/refs/heads/RAMO
        partes = url.split("github.com/", 1)[-1]
        return f"https://codeload.github.com/{partes}/zip/refs/heads/{ramo}"
    # fallback genérico: /archive/refs/heads/RAMO.zip
    return f"{url}/archive/refs/heads/{ramo}.zip"


def baixar_e_extrair_zip(raiz: Path, ramo: str = RAMO_DEFAULT,
                          silencioso: bool = False) -> bool:
    """Baixa o repositório como ZIP (via HTTP, só stdlib) e sincroniza os
    arquivos para a pasta do curso — SÓ caminha via HTTP, sem precisar do
    Git. Não sobrescreve pastas protegidas (.git, .venv, saida, etc.).

    Retorna True em caso de sucesso.
    """
    url_zip = url_para_zip(resolver_url_repo(), ramo)
    if not silencioso:
        print(f"  Baixando ZIP do repositório:\n     {url_zip}")
    try:
        req = urllib.request.Request(
            url_zip,
            headers={"User-Agent": "iniciando_a_aula/1.0 (curso python)"},
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            dados = resp.read()
        total_kb = max(1, len(dados) // 1024)
        if not silencioso:
            print(f"  {OK} download: {total_kb} KB recebidos.")
    except Exception as e:
        print(f"  {FALTA} falha ao baixar o ZIP: {e}")
        print("       Verifique a internet ou a URL do repositório (REPO URL no")
        print("       topo do script).")
        return False

    # extrai num diretório temporário, depois copia selecionando o que passar
    with tempfile.TemporaryDirectory(prefix="aula_zip_") as tmp:
        zip_path = Path(tmp) / "repo.zip"
        zip_path.write_bytes(dados)
        try:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(tmp)
        except zipfile.BadZipFile as e:
            print(f"  {FALTA} arquivo ZIP veio corrompido: {e}")
            return False

        # O GitHub cria uma pasta raiz 'REPO-ramo/' dentro do ZIP.
        sub = [p for p in Path(tmp).iterdir() if p.is_dir()]
        raiz_zip = sub[0] if len(sub) == 1 else Path(tmp)
        if not silencioso:
            n = sum(1 for _ in raiz_zip.rglob("*") if _.is_file())
            print(f"  Copiando {n} arquivos do repositório...")

        copiados, pulados = 0, 0
        for origem in raiz_zip.rglob("*"):
            if not origem.is_file():
                continue
            rel = origem.relative_to(raiz_zip)
            # pula protegebidos (primeiro componente do caminho)
            if rel.parts and rel.parts[0] in PROTEGIDOS_DOWNLOAD:
                pulados += 1
                continue
            # também pula .git, .venv em qualquer nível
            if any(part in PROTEGIDOS_DOWNLOAD for part in rel.parts):
                pulados += 1
                continue
            destino = raiz / rel
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origem, destino)
            copiados += 1

        if not silencioso:
            print(f"  {OK} {copiados} arquivos atualizados, {pulados} protegidos"
                  " (.venv/saida/.git) preservados.")
    return True


def instalar_dependencias(raiz: Path, silencioso: bool = False) -> bool:
    """Oferece instalar as bibliotecas do curso via pip automaticamente."""
    req = raiz / "requirements.txt"
    if not req.is_file():
        print(f"  {ALERTA} requirements.txt não encontrado — nada p/ instalar.")
        return False
    cmd = [sys.executable, "-m", "pip", "install", "-r", str(req)]
    if not silencioso:
        print(f" Rodando: {' '.join(cmd)}")
    try:
        return subprocess.run(cmd, check=False).returncode == 0
    except (FileNotFoundError, OSError) as e:
        print(f"  {FALTA} não consegui rodar o pip: {e}")
        return False


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

    def sincronizar(self) -> bool:
        """Tenta `git pull`; se não der, cai no fallback de baixar o ZIP.

        Retorna True se conseguiu sincronizar de algum jeito.
        """
        if not self.tem_git():
            print(f"  {ALERTA} git não encontrado no PATH.")
            print("       Sem problema: vou baixar o repositório como ZIP "
                  "(via HTTP).")
            return self._fallback_zip("git indisponível")
        if not self.no_repositorio():
            print(f"  {ALERTA} não é um repositório Git aqui ({self.raiz}).")
            print("       Vou baixar o repositório como ZIP (via HTTP).")
            return self._fallback_zip("sem repositório local")

        print(f"  Remote detectado: {self.remote_atual() or '(nenhum)'}")
        print("Tentando sincronizar com o remote (git pull)...")
        # Tentativa 1: git pull --ff-only
        if self._tentar_comando(["pull", "--ff-only"], "pull --ff-only"):
            print(f"  {OK} repositório sincronizado (fast-forward).")
            return True
        # Tentativa 2: pull comum
        if self._tentar_comando(["pull"], "pull"):
            print(f"  {OK} repositório sincronizado.")
            return True
        # Tentativa 3: fetch --all
        if self._tentar_comando(["fetch", "--all"], "fetch --all",
                                msg_ok="busquei novidades (fetch) — "
                                       "use `git merge`/`git pull` manualmente."):
            return True

        # Tentativa 4: fallback de ZIP (não precisa de merge)
        print(f"  {ALERTA} git pull falhou. Tentando baixar o ZIP...")
        return self._fallback_zip("git pull falhou")

    def _fallback_zip(self, motivo: str) -> bool:
        """Última barreira: baixa e extrai o repositório como ZIP via HTTP."""
        print(f"  (motivo do fallback: {motivo})")
        ok = baixar_e_extrair_zip(self.raiz, RAMO_DEFAULT)
        if ok:
            print(f"  {OK} repositório sincronizado via download ZIP.")
            print("       Se você tinha mudanças locais em arquivos do repo,")
            print("       elas foram sobrescritas — pastas .venv/ e saida/ "
                  "foram preservadas.")
        else:
            print(f"  {FALTA} não foi possível sincronizar nem via Git, "
                  "nem via ZIP.")
            print("       Rode à mão, na raiz do projeto:")
            print(f"         {Cor.NEGRITO}git status{Cor.FIM}  e  "
                  f"{Cor.NEGRITO}git pull{Cor.FIM}")
            print("       Dica: para não perder seu trabalho:")
            print(f"         {Cor.NEGRITO}git stash{Cor.FIM} → git pull "
                  "→ git stash pop")
        return ok

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
    raiz = Path(__file__).resolve().parent
    titulo("0. Sincronizar / baixar arquivos do curso")
    gitsync = GitSync(raiz)
    url = resolver_url_repo()
    print("Repositório do curso:")
    print(f"   {Cor.NEGRITO}{url}{Cor.FIM}  (ramo: {RAMO_DEFAULT})")
    print("Compartilhamos scripts e bases pelo Git. Vou sincronizar de dois")
    print("jeitos, com redundância: (1) git pull, e se não der,")
    print("(2) baixar o repositório como ZIP via HTTP — funciona MESMO sem")
    print("o Git instalado.")
    if perguntar_sim("Baixar/sincronizar agora"):
        gitsync.sincronizar()
        print()
        if perguntar_sim("Já instalar as bibliotecas do curso (pip) agora"):
            if instalar_dependencias(raiz):
                print(f"  {OK} bibliotecas instaladas em "
                      f"{sys.executable}")
            else:
                print(f"  {ALERTA} a instalação via pip falhou — veja o "
                      "passo manual no final.")
    else:
        print(f"  {ALERTA} pulado. Lembre de rodar  git pull  (ou este "
              "script de novo) antes de começar a aula.")


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
            print(f"  {ALERTA} Faltam pastas/arquivos (veja o item 3).")
            print("       Rode este script de novo e aceite baixar/"
                  "sincronizar (na seção 0).")
        if faltando:
            receita_de_instalacao(faltando)

    print()


if __name__ == "__main__":
    main()