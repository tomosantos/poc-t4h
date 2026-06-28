from benchmark.layouts import DOCUMENTOS, GROUND_TRUTH_CNH, LAYOUT_CNH

def test_tres_documentos_mapeados():
    assert set(DOCUMENTOS) == {"cnh", "fatura", "paper"}
    for d in DOCUMENTOS.values():
        assert "layout" in d and "arquivo" in d

def test_cnh_tem_seis_campos():
    nomes = {c.nome for c in LAYOUT_CNH.campos}
    assert nomes == {"nome", "cpf", "data_nascimento", "data_emissao",
                     "filiacao_pai", "filiacao_mae"}

def test_ground_truth_cobre_os_campos_da_cnh():
    assert set(GROUND_TRUTH_CNH) == {c.nome for c in LAYOUT_CNH.campos}
