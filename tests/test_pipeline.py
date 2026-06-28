from extractor.models import FieldSpec, Layout
from extractor.client import RespostaLLM
from extractor.pipeline import aplicar_validators, montar_envelope, extrair

LAYOUT = Layout(layout_id="cnh", descricao="CNH", campos=[
    FieldSpec(nome="nome", tipo="text", descricao="nome"),
    FieldSpec(nome="cpf", tipo="text", descricao="cpf", validador="cpf"),
])

def test_validator_zera_cpf_invalido_e_remove_raciocinio():
    dados = {"_raciocinio": "li o doc", "nome": "Ana", "cpf": "000.000.000-00"}
    out = aplicar_validators(dados, LAYOUT)
    assert "_raciocinio" not in out
    assert out["nome"] == "Ana"
    assert out["cpf"] is None

def test_status_ok_e_partial():
    assert montar_envelope({"nome": "Ana", "cpf": "x"}, LAYOUT)["status"] == "ok"
    assert montar_envelope({"nome": "Ana", "cpf": None}, LAYOUT)["status"] == "partial"
    assert montar_envelope({}, LAYOUT)["status"] == "error"

class _FakeClient:
    def single_pass(self, caminho, layout, modelo):
        return RespostaLLM(dados={"_raciocinio": "x", "nome": "Ana",
                                  "cpf": "123.456.789-09"},
                           custo_usd=0.001, tokens_in=10, tokens_out=5,
                           latencia_s=0.5, modelo=modelo, n_chamadas=1)

def test_extrair_aplica_validators_e_monta_envelope():
    env, resp = extrair("x.jpg", LAYOUT, "m", _FakeClient(), modo="single")
    assert env["status"] == "ok"
    assert env["extracted_data"]["cpf"] == "123.456.789-09"  # CPF válido mantido
    assert "_raciocinio" not in env["extracted_data"]
    assert resp.n_chamadas == 1


class _FakeTwoStepClient:
    def two_step(self, caminho, layout, modelo):
        return RespostaLLM(dados={"_raciocinio": "x", "nome": "Bia",
                                  "cpf": "123.456.789-09"},
                           custo_usd=0.004, tokens_in=20, tokens_out=10,
                           latencia_s=1.0, modelo=modelo, n_chamadas=2)


def test_extrair_roteia_two_step():
    env, resp = extrair("x.jpg", LAYOUT, "m", _FakeTwoStepClient(), modo="two_step")
    assert resp.n_chamadas == 2
    assert env["status"] == "ok"
    assert env["extracted_data"]["nome"] == "Bia"
    assert "_raciocinio" not in env["extracted_data"]
