"""Captura os prints reais da aplicação e das evidências de execução.

O script sobe o Streamlit em uma porta local, abre cada perfil de `exemplos/`
no modo demonstração (`?perfil=...`), tira as capturas e também gera a imagem da saída real do pytest.

Uso:
    python tools/capturar_prints.py
    python tools/capturar_prints.py --porta 8790 --sem-terminal

Requisitos (uma vez):
    python -m pip install playwright
    python -m playwright install chromium
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PRINTS = RAIZ / "docs" / "prints"
EVIDENCIAS = RAIZ / "docs" / "evidencias"

# (arquivo de exemplo, nome do print, título para o documento)
PERFIS = [
    ("perfil_analitico", "persona-analitico", "Perfil analítico — matemática e dados"),
    ("perfil_frontend", "persona-frontend", "Perfil visual — design e interface"),
    ("perfil_backend", "persona-backend", "Perfil back-end — lógica e código"),
    ("perfil_devops", "persona-devops", "Perfil infraestrutura — Linux e automação"),
    ("perfil_seguranca", "persona-seguranca", "Perfil segurança — redes e defesa"),
    ("perfil_produto", "persona-produto", "Perfil negócios — produto e comunicação"),
    ("perfil_neutro", "caso-limite-neutro", "Caso-limite — perfil neutro"),
    ("perfil_conflitante", "caso-limite-conflitante", "Caso-limite — perfil contraditório"),
    ("perfil_ideal_mobile", "perfil-ideal-mobile", "Perfil ideal — Desenvolvimento Mobile"),
    ("perfil_ideal_cloud", "perfil-ideal-cloud", "Perfil ideal — Arquitetura em Nuvem"),
    ("perfil_ideal_eng_dados", "perfil-ideal-eng-dados", "Perfil ideal — Engenharia de Dados"),
]

ABAS = [
    ("Panorama", "04-resultado-panorama"),
    ("Justificativas", "05-resultado-justificativas"),
    ("Lacunas", "06-resultado-lacunas"),
    ("Roadmap", "07-resultado-roadmap"),
    ("Exportar", "08-resultado-exportar"),
]


def _esperar_servidor(url: str, tentativas: int = 90) -> None:
    for _ in range(tentativas):
        try:
            with urllib.request.urlopen(f"{url}/_stcore/health", timeout=2) as resposta:
                if resposta.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            pass
        time.sleep(1)
    raise RuntimeError("O servidor Streamlit não respondeu a tempo")


def _html_terminal(titulo: str, comando: str, saida: str) -> str:
    saida_escapada = (
        saida.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    total_linhas = len(saida.splitlines())
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>{titulo}</title>
<style>
  body {{ margin: 0; padding: 32px; background: #0b1120; color: #e2e8f0;
         font-family: "Cascadia Mono", Consolas, "Courier New", monospace; }}
  .janela {{ background: #0f172a; border: 1px solid #1e293b; border-radius: 10px; overflow: hidden; }}
  .barra {{ display: flex; align-items: center; gap: 8px; padding: 10px 14px;
            background: #111c33; border-bottom: 1px solid #1e293b; }}
  .bola {{ width: 11px; height: 11px; border-radius: 50%; }}
  .titulo {{ margin-left: 10px; color: #94a3b8; font-size: 13px; }}
  pre {{ margin: 0; padding: 18px 20px; font-size: 13.5px; line-height: 1.55; white-space: pre-wrap; }}
  .prompt {{ color: #38bdf8; }}
  .ok {{ color: #4ade80; }}
  .info {{ color: #cbd5e1; }}
</style></head>
<body>
  <div class="janela">
    <div class="barra">
      <span class="bola" style="background:#f87171"></span>
      <span class="bola" style="background:#fbbf24"></span>
      <span class="bola" style="background:#4ade80"></span>
      <span class="titulo">{titulo}</span>
    </div>
    <pre><span class="prompt">PS C:\\consultor-carreiras-ti&gt;</span> {comando}

{saida_escapada}
<span class="ok">— fim da saída ({total_linhas} linhas) —</span></pre>
  </div>
</body></html>
"""


def _altura_do_conteudo(pagina) -> int:
    """Altura real do bloco principal (o Streamlit rola dentro de um container)."""
    return int(
        pagina.evaluate(
            """() => {
                const candidatos = [
                    document.querySelector('[data-testid="stMainBlockContainer"]'),
                    document.querySelector('[data-testid="stMain"]'),
                    document.querySelector('[data-testid="stAppViewContainer"]'),
                    document.body,
                ].filter(Boolean);
                return Math.max(...candidatos.map((el) => el.scrollHeight || 0), 950);
            }"""
        )
    )


def _ajustar_altura(pagina, margem: int = 90, maximo: int = 7000) -> None:
    altura = min(_altura_do_conteudo(pagina) + margem, maximo)
    largura = pagina.viewport_size["width"]
    pagina.set_viewport_size({"width": largura, "height": altura})
    pagina.wait_for_timeout(700)


def _recortar_rodape(caminho: Path, margem: int = 36) -> None:
    """Remove a faixa uniforme no fim da imagem (o Streamlit reserva altura extra)."""
    from PIL import Image

    imagem = Image.open(caminho).convert("RGB")
    largura, altura = imagem.size
    fundo_direita = imagem.getpixel((largura - 3, altura - 3))
    fundo_esquerda = imagem.getpixel((20, altura - 3))
    inicio = int(largura * 0.30)  # divisa entre a barra lateral e o conteúdo

    def tem_conteudo(y: int) -> bool:
        direita = [imagem.getpixel((x, y)) for x in range(inicio, largura - 8, 6)]
        esquerda = [imagem.getpixel((x, y)) for x in range(0, inicio - 20, 6)]
        if any(sum(abs(c - a) for c, a in zip(pixel, fundo_direita)) > 14 for pixel in direita):
            return True
        return any(sum(abs(c - a) for c, a in zip(pixel, fundo_esquerda)) > 14 for pixel in esquerda)

    limite = altura
    for y in range(altura - 1, 0, -1):
        if tem_conteudo(y):
            limite = min(altura, y + margem)
            break
    if limite < altura:
        imagem.crop((0, 0, largura, limite)).save(caminho)


def _rodar(comando: list[str]) -> str:
    processo = subprocess.run(
        comando, cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    saida = (processo.stdout or "") + (processo.stderr or "")
    return saida.strip()


def capturar(url_base: str, com_terminal: bool) -> list[tuple[str, str]]:
    from playwright.sync_api import sync_playwright

    PRINTS.mkdir(parents=True, exist_ok=True)
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    capturados: list[tuple[str, str]] = []

    def tirar(page, destino: Path, inteira: bool = True, ajustar: bool = True) -> None:
        if ajustar:
            _ajustar_altura(page)
        page.screenshot(path=str(destino), full_page=inteira)
        _recortar_rodape(destino)
        capturados.append((destino.name, destino.stat().st_size and "ok"))

    with sync_playwright() as play:
        navegador = play.chromium.launch()

        # --- trio do wizard -------------------------------------------------
        contexto = navegador.new_context(viewport={"width": 1440, "height": 950}, locale="pt-BR")
        pagina = contexto.new_page()
        pagina.set_default_timeout(45_000)
        pagina.goto(url_base, wait_until="domcontentloaded")
        pagina.get_by_text("Passo 1 · Perfil pessoal").wait_for()
        pagina.wait_for_timeout(1200)
        tirar(pagina, PRINTS / "01-passo-1-perfil.png")

        pagina.get_by_role("button", name=re.compile("Continuar para as afinidades")).click()
        pagina.get_by_text("Passo 2 · Afinidades técnicas").wait_for()
        pagina.wait_for_timeout(1200)
        tirar(pagina, PRINTS / "02-passo-2-afinidades.png")

        pagina.get_by_role("button", name=re.compile("Continuar para os objetivos")).click()
        pagina.get_by_text("Passo 3 · Objetivos e conhecimentos").wait_for()
        pagina.wait_for_timeout(1200)
        tirar(pagina, PRINTS / "03-passo-3-objetivos.png")
        contexto.close()

        # --- resultado de cada perfil ---------------------------------------
        for exemplo, arquivo, _titulo in PERFIS:
            contexto = navegador.new_context(viewport={"width": 1440, "height": 950}, locale="pt-BR")
            pagina = contexto.new_page()
            pagina.set_default_timeout(45_000)
            pagina.goto(f"{url_base}/?perfil={exemplo}", wait_until="domcontentloaded")
            pagina.get_by_text("Resultado da análise", exact=True).first.wait_for()
            pagina.get_by_text("Perfil de demonstração carregado", exact=False).first.wait_for()
            pagina.wait_for_timeout(2500)
            tirar(pagina, PRINTS / f"{arquivo}.png")
            contexto.close()

        # --- abas do resultado (perfil de infraestrutura) --------------------
        contexto = navegador.new_context(viewport={"width": 1440, "height": 950}, locale="pt-BR")
        pagina = contexto.new_page()
        pagina.set_default_timeout(45_000)
        pagina.goto(f"{url_base}/?perfil=perfil_devops", wait_until="domcontentloaded")
        pagina.get_by_text("Resultado da análise", exact=True).first.wait_for()
        pagina.wait_for_timeout(2500)
        for rotulo, arquivo in ABAS:
            pagina.get_by_role("tab", name=re.compile(rotulo)).click()
            pagina.wait_for_timeout(1500)
            tirar(pagina, PRINTS / f"{arquivo}.png", inteira=(rotulo != "Exportar"), ajustar=(rotulo != "Exportar"))
        contexto.close()

        # --- evidências de terminal -----------------------------------------
        if com_terminal:
            saida_pytest = _rodar([sys.executable, "-m", "pytest", "-v", "--no-header"])
            html = EVIDENCIAS / "saida-pytest.html"
            html.write_text(
                _html_terminal("pytest — suíte completa", "python -m pytest -v", saida_pytest),
                encoding="utf-8",
            )
            contexto = navegador.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
            pagina = contexto.new_page()
            pagina.goto(html.as_uri())
            pagina.wait_for_timeout(600)
            tirar(pagina, PRINTS / "09-evidencia-pytest.png")
            contexto.close()


        navegador.close()
    return capturados


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Captura prints da aplicação para a documentação.")
    parser.add_argument("--porta", type=int, default=8765)
    parser.add_argument("--sem-terminal", action="store_true", help="Não gera o print do pytest")
    args = parser.parse_args(argv)

    url = f"http://localhost:{args.porta}"
    servidor = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless", "true",
            "--server.port", str(args.porta),
            "--browser.gatherUsageStats", "false",
        ],
        cwd=RAIZ,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _esperar_servidor(url)
        capturados = capturar(url, not args.sem_terminal)
    finally:
        servidor.terminate()
        try:
            servidor.wait(timeout=10)
        except subprocess.TimeoutExpired:  # pragma: no cover
            servidor.kill()

    print(f"{len(capturados)} prints salvos em {PRINTS}:")
    for nome, _ in capturados:
        print(f"  - {nome}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
