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


def test_secao_conceitos_abordados_tem_4_expanders():
    at = _run_app()
    headers = [h.value for h in at.header]
    assert "Conceitos Abordados" in headers
    assert headers.index("Abordagem Utilizada") < headers.index("Conceitos Abordados")
    assert headers.index("Conceitos Abordados") < headers.index("Resultados do Benchmark")

    labels_esperados = {
        "Single-pass vs. two-step",
        "VLM (Vision-Language Model)",
        "Structured output / constrained decoding",
        "LLM-as-judge vs. métrica determinística",
    }
    labels_encontrados = {e.label for e in at.expander}
    assert labels_esperados.issubset(labels_encontrados)
