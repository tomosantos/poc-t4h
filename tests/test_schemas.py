# tests/test_schemas.py
from extractor.models import FieldSpec, Layout
from extractor.schemas import construir_json_schema

def _layout():
    return Layout(layout_id="cnh", descricao="CNH", campos=[
        FieldSpec(nome="nome", tipo="text", descricao="Nome completo"),
        FieldSpec(nome="cpf", tipo="text", descricao="CPF", validador="cpf"),
        FieldSpec(nome="data_nascimento", tipo="date", descricao="Data de nascimento"),
    ])

def test_schema_e_strict_e_fecha_objeto():
    s = construir_json_schema(_layout())
    assert s["type"] == "object"
    assert s["additionalProperties"] is False
    # todos os campos + _raciocinio são required
    assert set(s["required"]) == {"_raciocinio", "nome", "cpf", "data_nascimento"}

def test_raciocinio_vem_primeiro():
    s = construir_json_schema(_layout())
    assert list(s["properties"].keys())[0] == "_raciocinio"

def test_tipos_mapeados():
    s = construir_json_schema(_layout())
    assert s["properties"]["nome"]["type"] == "string"
    assert s["properties"]["data_nascimento"]["type"] == "string"
