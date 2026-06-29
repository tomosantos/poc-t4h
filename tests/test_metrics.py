from benchmark.metrics import normalizar, acuracia_deterministica


def test_normaliza_cpf_e_data_por_digitos():
    assert normalizar("cpf", "000.000.000-00") == "00000000000"
    assert normalizar("data_nascimento", "06/08/1961") == "06081961"


def test_filiacao_ignora_prefixo_e_acento():
    assert normalizar("filiacao_pai", "Pai José Antônio") == normalizar("filiacao_pai", "jose antonio")


def test_acuracia_deterministica_conta_campos():
    gt = {"nome": "Ana", "cpf": "123.456.789-09"}
    ex = {"nome": "ANA", "cpf": "11111111111"}
    ac, por = acuracia_deterministica(ex, gt)
    assert por["nome"] is True and por["cpf"] is False
    assert abs(ac - 0.5) < 1e-9
