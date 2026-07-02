from streamlit.testing.v1 import AppTest


def _run_app():
    at = AppTest.from_file("ui/app.py")
    at.run(timeout=30)
    assert not at.exception
    return at


def test_header_tagline_sem_linha_de_abordagem():
    at = _run_app()
    tagline = at.markdown[0].value
    assert "Abordagem:" not in tagline
    assert "Documentos:" in tagline


def test_secao_abordagem_utilizada_existe():
    at = _run_app()
    headers = [h.value for h in at.header]
    assert "Abordagem Utilizada" in headers
    assert headers.index("Abordagem Utilizada") < headers.index("Resultados do Benchmark")
    corpo = "\n".join(m.value for m in at.markdown)
    assert "single-pass" in corpo
    assert "duas chamadas" in corpo
