"""Caso 2 (documento extenso): caminho HÍBRIDO.

PyMuPDF extrai texto+tabelas de forma determinística (sem LLM, custo zero);
o VLM é usado APENAS para interpretar uma figura/gráfico de uma página. Contrasta
com o caminho ingênuo (PDF inteiro no VLM), que falha/custa caro.
"""
import base64
import os
import time

from dotenv import load_dotenv

from extractor.client import OpenRouterClient
from extractor.encoding import bloco_documento
from extractor.pdf_extract import extrair_markdown, numero_paginas, renderizar_pagina

PAPER = "data/Documento 3.pdf"
MODELO_VLM = "google/gemini-2.5-flash-lite"
PAGINA_FIGURA = 6  # página (0-based) com gráficos de benchmark no paper Claude 3


def _custo(resp):
    u = getattr(resp, "usage", None)
    return (getattr(u, "model_extra", None) or {}).get("cost") if u else None


def interpretar_figura(cli, png: bytes, modelo: str):
    data_url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    msgs = [{"role": "user", "content": [
        {"type": "text", "text": "Esta é uma página de um paper acadêmico. Se houver "
         "gráfico(s) ou figura(s), descreva o que mostram e os principais valores/"
         "tendências. Se não houver, responda apenas 'sem figura'."},
        {"type": "image_url", "image_url": {"url": data_url}},
    ]}]
    t0 = time.perf_counter()
    resp = cli.client.chat.completions.create(
        model=modelo, messages=msgs, max_tokens=500,
        extra_body={"usage": {"include": True}})
    lat = time.perf_counter() - t0
    if not getattr(resp, "choices", None):
        return "(sem choices)", lat, None
    return resp.choices[0].message.content, lat, _custo(resp)


def tentar_naive(cli, modelo):
    """Caminho ingênuo: PDF inteiro no VLM. Esperado falhar ou custar caro."""
    msgs = [{"role": "user", "content": [
        {"type": "text", "text": "Extraia o conteúdo deste PDF em markdown."},
        bloco_documento(PAPER),
    ]}]
    t0 = time.perf_counter()
    try:
        resp = cli.client.chat.completions.create(
            model=modelo, messages=msgs, max_tokens=500,
            extra_body={"usage": {"include": True},
                        "plugins": [{"id": "file-parser", "pdf": {"engine": "native"}}]})
        lat = time.perf_counter() - t0
        if not getattr(resp, "choices", None):
            return "FALHOU (choices=None / erro do provedor)", lat, None
        return "OK", lat, _custo(resp)
    except Exception as e:
        return f"FALHOU: {type(e).__name__}: {str(e)[:120]}", time.perf_counter() - t0, None


def main():
    load_dotenv()
    cli = OpenRouterClient()
    n = numero_paginas(PAPER)
    t0 = time.perf_counter()
    md = extrair_markdown(PAPER)
    t_det = time.perf_counter() - t0
    png = renderizar_pagina(PAPER, min(PAGINA_FIGURA, n - 1))
    desc, lat_fig, custo_fig = interpretar_figura(cli, png, MODELO_VLM)
    naive_status, naive_lat, naive_custo = tentar_naive(cli, MODELO_VLM)

    out = [
        "# Caso 2 — Documento Extenso (paper): caminho híbrido\n",
        f"PDF: {n} páginas, {os.path.getsize(PAPER) / 1e6:.1f} MB\n",
        "## Contraste de abordagens\n",
        "| Abordagem | Resultado | Latência | Custo (US$) |",
        "|---|---|---|---|",
        f"| Ingênua — PDF inteiro no VLM | {naive_status} | {naive_lat:.1f}s | {naive_custo} |",
        f"| Híbrida — PyMuPDF (texto+tabelas, {n} págs) | OK determinístico | {t_det:.2f}s | 0 |",
        f"| Híbrida — VLM só na figura (pág {PAGINA_FIGURA + 1}) | interpretação | {lat_fig:.1f}s | {custo_fig} |",
        "\n## Interpretação da figura (VLM)\n",
        desc or "",
        "\n## Amostra do markdown determinístico (primeiros 1500 chars)\n",
        "```\n" + md[:1500] + "\n```",
    ]
    os.makedirs("benchmark/results", exist_ok=True)
    with open("benchmark/results/paper_hibrido.md", "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"OK | det {t_det:.2f}s | figura {lat_fig:.1f}s custo {custo_fig} | naive: {naive_status}")


if __name__ == "__main__":
    main()
