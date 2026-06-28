from fastapi.testclient import TestClient
from extractor.client import RespostaLLM
from api.main import app, get_client

class _FakeClient:
    def single_pass(self, caminho, layout, modelo, max_tokens=None):
        return RespostaLLM(dados={"_raciocinio": "x", "nome": "Ana",
                                  "cpf": "123.456.789-09", "data_nascimento": "01/01/1990",
                                  "data_emissao": "01/01/2020", "filiacao_pai": "Pai",
                                  "filiacao_mae": "Mae"},
                           custo_usd=0.001, tokens_in=1, tokens_out=1,
                           latencia_s=0.1, modelo=modelo, n_chamadas=1)

import pytest

@pytest.fixture(autouse=True)
def _override_client():
    app.dependency_overrides[get_client] = lambda: _FakeClient()
    yield
    app.dependency_overrides.clear()

cliente = TestClient(app)

def test_health():
    assert cliente.get("/health").json()["status"] == "ok"

def test_extract_cnh_retorna_envelope():
    r = cliente.post("/extract", data={"layout_id": "cnh"},
                     files={"file": ("cnh.jpg", b"\xff\xd8\xff\xe0", "image/jpeg")})
    body = r.json()
    assert body["status"] == "ok"
    assert body["extracted_data"]["nome"] == "Ana"
    assert "_raciocinio" not in body["extracted_data"]

def test_layout_desconhecido_retorna_400():
    r = cliente.post("/extract", data={"layout_id": "nao_existe"},
                     files={"file": ("x.jpg", b"\xff\xd8\xff\xe0", "image/jpeg")})
    assert r.status_code == 400
