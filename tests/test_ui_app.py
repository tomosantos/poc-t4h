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

    # Verifica que os achados antigos não aparecem em alerts (prova que a
    # implementação antiga com st.info/st.warning/st.success foi removida).
    # Procura cada título nos valores dos alerts coletados.
    all_alerts = [elem.value for elem in list(at.info) + list(at.warning) + list(at.success)]
    alert_text = "\n".join(all_alerts)
    for label in labels_esperados:
        assert label not in alert_text


def test_secao_demo_explica_single_pass_e_limite_two_step():
    at = _run_app()
    # Encontra o parágrafo Task 4 que contém "lado a lado" (é o único).
    task4_elem = next(m.value for m in at.markdown if "lado a lado" in m.value)
    # Assegura que os conceitos "single-pass" e "two_step/two-step" aparecem
    # NESTE parágrafo específico, não apenas em algum lugar da página.
    assert "single-pass" in task4_elem
    assert "two_step" in task4_elem or "two-step" in task4_elem
    assert "lado a lado" in task4_elem
