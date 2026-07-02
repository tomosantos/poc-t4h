"""Extração determinística de PDFs com PyMuPDF (texto + tabelas + render de página).

Para o "documento extenso" (Caso 2 do desafio), texto e tabelas saem DAQUI —
sem LLM, sem custo de token, sem latência de rede. O VLM fica reservado apenas
para interpretar gráficos/figuras (ver `benchmark/paper_hibrido.py`). Esse é o
cerne do argumento: não usar o motor caro onde um parser determinístico resolve.
"""
from typing import Optional

import fitz  # PyMuPDF


def numero_paginas(caminho: str) -> int:
    with fitz.open(caminho) as doc:
        return doc.page_count


def extrair_markdown(caminho: str, max_paginas: Optional[int] = None) -> str:
    """Extrai texto + tabelas do PDF em Markdown, página a página.

    Tabelas detectadas pelo PyMuPDF viram Markdown (| ... |); o restante vira
    texto corrido. 100% determinístico e local — nenhuma chamada de modelo.
    """
    partes: list[str] = []
    with fitz.open(caminho) as doc:
        total = doc.page_count if max_paginas is None else min(max_paginas, doc.page_count)
        for i in range(total):
            page = doc[i]
            partes.append(f"\n\n## Página {i + 1}\n")
            try:
                tabelas = page.find_tables()
                for t in tabelas.tables:
                    partes.append("\n" + t.to_markdown() + "\n")
            except Exception:
                pass  # detecção de tabela é best-effort; texto abaixo é o fallback
            partes.append(page.get_text("text"))
    return "".join(partes).strip()


def paginas_com_imagem(caminho: str, max_paginas: int = 3) -> list[int]:
    """Índices (0-based) de páginas com imagem raster embutida — heurística
    determinística (PyMuPDF, sem VLM) para achar candidatas a figura/gráfico
    sem precisar rodar o modelo em todas as páginas do PDF."""
    encontradas: list[int] = []
    with fitz.open(caminho) as doc:
        for i in range(doc.page_count):
            if doc[i].get_images(full=True):
                encontradas.append(i)
            if len(encontradas) >= max_paginas:
                break
    return encontradas


def renderizar_pagina(caminho: str, indice: int, zoom: float = 2.0) -> bytes:
    """Renderiza uma página (0-based) como PNG em bytes — para enviar a um VLM
    interpretar gráficos/figuras daquela página específica (sem mandar o PDF inteiro)."""
    with fitz.open(caminho) as doc:
        page = doc[indice]
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        return pix.tobytes("png")
