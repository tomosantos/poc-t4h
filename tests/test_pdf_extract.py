import fitz

from extractor.pdf_extract import extrair_markdown, numero_paginas, renderizar_pagina


def _make_pdf(path, texto="Conteudo de teste 123"):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), texto)
    doc.save(str(path))
    doc.close()


def test_numero_paginas(tmp_path):
    p = tmp_path / "x.pdf"
    _make_pdf(p)
    assert numero_paginas(str(p)) == 1


def test_extrair_markdown_pega_texto(tmp_path):
    p = tmp_path / "x.pdf"
    _make_pdf(p, "Conteudo de teste 123")
    md = extrair_markdown(str(p))
    assert "Conteudo de teste 123" in md
    assert "Página 1" in md


def test_renderizar_pagina_retorna_png(tmp_path):
    p = tmp_path / "x.pdf"
    _make_pdf(p)
    png = renderizar_pagina(str(p), 0)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
