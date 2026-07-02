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


def test_secao_achados_chave_tem_5_expanders():
    at = _run_app()
    labels_esperados = [
        "Prompt ancorado supera escalação de modelo",
        "Juiz LLM é leniente — métrica dupla é necessária",
        "CPF: gargalo de legibilidade intrínseca",
        "Single-pass funciona para fatura e paper",
        "Modelos testados são mid-tier 2024/2025 — abordagem é model-agnostic",
    ]
    labels_encontrados = [e.label for e in at.expander]
    for label in labels_esperados:
        assert label in labels_encontrados

    # Não deve sobrar nenhum st.info/st.warning/st.success da versão antiga
    # (a seção de Conceitos usa só st.markdown dentro de expander, então
    # qualquer alert restante pertence à implementação antiga de Achados).
    assert len(at.info) == 0
    assert len(at.warning) == 0
    assert len(at.success) == 0


def test_secao_demo_explica_single_pass_e_limite_two_step():
    at = _run_app()
    corpo = "\n".join(m.value for m in at.markdown)
    assert "single-pass" in corpo
    assert "two_step" in corpo or "two-step" in corpo
    assert "lado a lado" in corpo
