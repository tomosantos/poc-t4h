# tests/test_client_smoke.py
import os
import pytest
from extractor.client import OpenRouterClient
from extractor.models import FieldSpec, Layout

pytestmark = pytest.mark.skipif(
    not os.getenv("OPENROUTER_API_KEY"),
    reason="precisa de OPENROUTER_API_KEY para smoke test de rede",
)

LAYOUT = Layout(layout_id="t", descricao="teste", campos=[
    FieldSpec(nome="titulo", tipo="text", descricao="título principal do documento"),
])

def test_single_pass_retorna_estrutura(tmp_path):
    # imagem branca mínima 1x1 PNG
    import base64
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    p = tmp_path / "branco.png"; p.write_bytes(png)
    cli = OpenRouterClient()
    r = cli.single_pass(str(p), LAYOUT, "google/gemini-2.5-flash-lite")
    assert "titulo" in r.dados
    assert r.n_chamadas == 1
    assert r.latencia_s > 0
