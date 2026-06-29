# tests/test_run.py
from extractor.client import RespostaLLM
from benchmark.run import linha_resultado, tabela_markdown

def _resp():
    return RespostaLLM(dados={}, custo_usd=0.002, tokens_in=100, tokens_out=20,
                       latencia_s=1.5, modelo="m", n_chamadas=1)

def test_linha_resultado_achata_campos():
    env = {"status": "ok", "extracted_data": {"a": "1"}}
    l = linha_resultado("cnh", "m", "single", env, _resp(), 0.83)
    assert l["doc"] == "cnh" and l["modo"] == "single"
    assert l["custo_usd"] == 0.002 and l["latencia_s"] == 1.5
    assert l["n_chamadas"] == 1 and l["acuracia_juiz"] == 0.83 and l["status"] == "ok"

def test_linha_resultado_com_acuracia_det():
    env = {"status": "ok", "extracted_data": {"a": "1"}}
    l = linha_resultado("cnh", "m", "single", env, _resp(), 0.83, acuracia_det=0.67)
    assert l["acuracia_det"] == 0.67

def test_linha_resultado_acuracia_det_none_por_default():
    env = {"status": "ok", "extracted_data": {}}
    l = linha_resultado("fatura", "m", "single", env, _resp(), 0.90)
    assert l["acuracia_det"] is None

def test_tabela_markdown_tem_cabecalho_e_linha():
    md = tabela_markdown([linha_resultado("cnh", "m", "single",
        {"status": "ok", "extracted_data": {}}, _resp(), 0.83)])
    assert "| doc " in md and "cnh" in md
    assert "acuracia_juiz" in md and "acuracia_det" in md
