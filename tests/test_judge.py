from benchmark.judge import _schema_veredito

def test_schema_veredito_e_strict():
    s = _schema_veredito(["nome", "cpf"])
    assert s["additionalProperties"] is False
    assert "acuracia" in s["properties"]
    assert s["properties"]["por_campo"]["additionalProperties"] is False
    assert set(s["properties"]["por_campo"]["properties"]) == {"nome", "cpf"}
    assert set(s["required"]) >= {"acuracia", "por_campo", "comentario"}
