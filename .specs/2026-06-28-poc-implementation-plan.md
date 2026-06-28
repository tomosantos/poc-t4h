# POC de Extração de Documentos — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir uma POC containerizada que extrai dados dos 3 documentos de teste via VLM single-pass + structured output (OpenRouter), expõe uma API que espelha o contrato da Tech4.ai, uma UI Streamlit, e um benchmark que quantifica o ganho de latência/custo do single-pass vs. o baseline 2-step.

**Architecture:** Núcleo Python reutilizável (`extractor/`) com cliente OpenRouter (single-pass e 2-step), construtor de JSON Schema a partir de layouts, e validators determinísticos (CPF/CNPJ) espelhando a Tech4.ai. Em cima do núcleo: uma API FastAPI (`POST /extract` → `{status, extracted_data}`), uma UI Streamlit, e um harness de benchmark (`benchmark/`) com LLM-as-judge. Tudo servido via Docker Compose.

**Tech Stack:** Python 3.11, `openai` SDK (apontando para OpenRouter), `pydantic`, `fastapi` + `uvicorn`, `streamlit`, `pytest`, Docker.

## Global Constraints

- Python 3.11; gerenciar deps via `requirements.txt`.
- Cliente LLM SEMPRE via OpenRouter: `base_url="https://openrouter.ai/api/v1"`, chave em `OPENROUTER_API_KEY` (carregada de `.env`, nunca commitada).
- Contrato de saída da extração: envelope `{"status": "ok"|"partial"|"error", "extracted_data": {<campo>: <valor>}}` (espelha a Tech4.ai).
- Structured output via `response_format={"type":"json_schema","json_schema":{"name":..., "strict": true, "schema":...}}`; todo schema de objeto usa `"additionalProperties": false` e lista todos os campos em `"required"` (exigência do modo strict).
- Validators determinísticos (CPF/CNPJ) retornam `None` quando inválidos (espelha Tech4.ai), aplicados como pós-processamento — nunca confiar no LLM para validade.
- Sem GPU local: toda inferência é por API.
- Notas/comentários de domínio em português; termos técnicos em inglês.
- TDD nos componentes determinísticos; chamadas de rede testadas por smoke test que é *skipado* sem `OPENROUTER_API_KEY`.
- Commits frequentes, um por task.

---

## File Structure

```
requirements.txt              # dependências
.env.example                  # OPENROUTER_API_KEY=...
pytest.ini                    # config de testes
extractor/
  __init__.py
  models.py                   # FieldSpec, Layout, ExtractionOutcome (dataclasses/pydantic)
  validators.py               # cpf_valido, cnpj_valido, normaliza/aplica validators
  schemas.py                  # Layout -> JSON Schema (strict)
  encoding.py                 # arquivo (img/pdf) -> blocos de conteúdo da mensagem
  client.py                   # OpenRouterClient: single_pass(), two_step()
  pipeline.py                 # extract_document() -> envelope {status, extracted_data}
benchmark/
  __init__.py
  layouts.py                  # os 3 layouts (CNH, fatura, paper) + ground truth da CNH
  judge.py                    # LLM-as-judge de fidelidade
  run.py                      # matriz modelo x documento x braço -> results.json + tabela md
api/
  __init__.py
  main.py                     # FastAPI POST /extract
ui/
  app.py                      # Streamlit: upload + imagem e JSON lado a lado
tests/
  test_validators.py
  test_schemas.py
  test_encoding.py
  test_pipeline.py
  test_client_smoke.py        # skip sem API key
Dockerfile
docker-compose.yml
README.md
```

---

### Task 0: Scaffolding do projeto

**Files:**
- Create: `requirements.txt`, `.env.example`, `pytest.ini`
- Create: `extractor/__init__.py`, `benchmark/__init__.py`, `api/__init__.py` (vazios)

**Interfaces:**
- Produces: estrutura de pacotes importável (`import extractor`), `pytest` rodável.

- [ ] **Step 1: Criar `requirements.txt`**

```
openai>=1.40.0
pydantic>=2.7.0
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
streamlit>=1.36.0
python-dotenv>=1.0.0
pytest>=8.2.0
python-multipart>=0.0.9
```

- [ ] **Step 2: Criar `.env.example`**

```
OPENROUTER_API_KEY=coloque-sua-chave-aqui
```

- [ ] **Step 3: Criar `pytest.ini`**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

- [ ] **Step 4: Criar os `__init__.py` vazios**

Crie `extractor/__init__.py`, `benchmark/__init__.py`, `api/__init__.py` como arquivos vazios.

- [ ] **Step 5: Instalar e verificar**

Run: `pip install -r requirements.txt && python -c "import extractor, openai, fastapi, streamlit; print('ok')"`
Expected: imprime `ok` sem erro.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .env.example pytest.ini extractor/__init__.py benchmark/__init__.py api/__init__.py
git commit -m "chore: scaffolding da POC (deps, pacotes, pytest)"
```

---

### Task 1: Validators determinísticos (CPF/CNPJ)

**Files:**
- Create: `extractor/validators.py`
- Test: `tests/test_validators.py`

**Interfaces:**
- Produces:
  - `so_digitos(valor: str) -> str` — remove tudo que não é dígito.
  - `cpf_valido(cpf: str) -> bool`
  - `cnpj_valido(cnpj: str) -> bool`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_validators.py
from extractor.validators import so_digitos, cpf_valido, cnpj_valido

def test_so_digitos():
    assert so_digitos("123.456.789-09") == "12345678909"

def test_cpf_valido_aceita_valido():
    assert cpf_valido("123.456.789-09") is True

def test_cpf_rejeita_digito_verificador_errado():
    assert cpf_valido("123.456.789-00") is False

def test_cpf_rejeita_todos_iguais_e_tamanho_errado():
    assert cpf_valido("111.111.111-11") is False
    assert cpf_valido("123") is False

def test_cnpj_valido_e_invalido():
    assert cnpj_valido("11.222.333/0001-81") is True
    assert cnpj_valido("11.222.333/0001-80") is False
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/test_validators.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'extractor.validators'`.

- [ ] **Step 3: Implementar**

```python
# extractor/validators.py
"""Validators determinísticos espelhando a Tech4.ai (CPF, CNPJ)."""


def so_digitos(valor: str) -> str:
    return "".join(c for c in str(valor) if c.isdigit())


def cpf_valido(cpf: str) -> bool:
    d = so_digitos(cpf)
    if len(d) != 11 or d == d[0] * 11:
        return False
    for tam in (9, 10):
        soma = sum(int(d[i]) * (tam + 1 - i) for i in range(tam))
        resto = (soma * 10) % 11
        digito = 0 if resto == 10 else resto
        if digito != int(d[tam]):
            return False
    return True


def cnpj_valido(cnpj: str) -> bool:
    d = so_digitos(cnpj)
    if len(d) != 14 or d == d[0] * 14:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    for pesos, pos in ((pesos1, 12), (pesos2, 13)):
        soma = sum(int(d[i]) * pesos[i] for i in range(pos))
        resto = soma % 11
        digito = 0 if resto < 2 else 11 - resto
        if digito != int(d[pos]):
            return False
    return True
```

- [ ] **Step 4: Rodar e ver passar**

Run: `pytest tests/test_validators.py -v`
Expected: PASS (5 testes).

- [ ] **Step 5: Commit**

```bash
git add extractor/validators.py tests/test_validators.py
git commit -m "feat: validators CPF/CNPJ determinísticos"
```

---

### Task 2: Modelos de dados e construtor de JSON Schema

**Files:**
- Create: `extractor/models.py`, `extractor/schemas.py`
- Test: `tests/test_schemas.py`

**Interfaces:**
- Produces:
  - `FieldSpec(nome: str, tipo: Literal["text","number","date"], descricao: str, validador: Optional[Literal["cpf","cnpj"]] = None)` (pydantic BaseModel).
  - `Layout(layout_id: str, descricao: str, campos: list[FieldSpec])` (pydantic BaseModel).
  - `construir_json_schema(layout: Layout) -> dict` — JSON Schema strict; todo campo `string` (datas como string), `number` para numéricos; inclui campo livre `_raciocinio: string` como PRIMEIRA propriedade (resolve o trade-off de structured output sem 2ª chamada — ver `.specs/.../design.md` §2 e `notes/02`).

- [ ] **Step 1: Escrever o teste que falha**

```python
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
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/test_schemas.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'extractor.models'`.

- [ ] **Step 3: Implementar `extractor/models.py`**

```python
# extractor/models.py
"""Modelos de dados da POC."""
from typing import Literal, Optional
from pydantic import BaseModel


class FieldSpec(BaseModel):
    nome: str
    tipo: Literal["text", "number", "date"]
    descricao: str
    validador: Optional[Literal["cpf", "cnpj"]] = None


class Layout(BaseModel):
    layout_id: str
    descricao: str
    campos: list[FieldSpec]
```

- [ ] **Step 4: Implementar `extractor/schemas.py`**

```python
# extractor/schemas.py
"""Constrói JSON Schema (strict) a partir de um Layout."""
from extractor.models import Layout

_TIPO_JSON = {"text": "string", "number": "number", "date": "string"}


def construir_json_schema(layout: Layout) -> dict:
    propriedades: dict[str, dict] = {
        "_raciocinio": {
            "type": "string",
            "description": "Raciocínio livre antes de preencher os campos (leitura do layout do documento).",
        }
    }
    for campo in layout.campos:
        descricao = campo.descricao
        if campo.tipo == "date":
            descricao += " (formato DD/MM/AAAA; string vazia se ausente)."
        propriedades[campo.nome] = {
            "type": _TIPO_JSON[campo.tipo],
            "description": descricao,
        }
    return {
        "type": "object",
        "properties": propriedades,
        "required": list(propriedades.keys()),
        "additionalProperties": False,
    }
```

- [ ] **Step 5: Rodar e ver passar**

Run: `pytest tests/test_schemas.py -v`
Expected: PASS (3 testes).

- [ ] **Step 6: Commit**

```bash
git add extractor/models.py extractor/schemas.py tests/test_schemas.py
git commit -m "feat: modelos de dados e construtor de JSON Schema strict"
```

---

### Task 3: Encoding de arquivos para blocos de mensagem

**Files:**
- Create: `extractor/encoding.py`
- Test: `tests/test_encoding.py`

**Interfaces:**
- Consumes: nada.
- Produces:
  - `bloco_documento(caminho: str) -> dict` — retorna o bloco de conteúdo OpenAI/OpenRouter: para imagem (`.jpg/.jpeg/.png/.webp`) → `{"type":"image_url","image_url":{"url":"data:<mime>;base64,<...>"}}`; para `.pdf` → `{"type":"file","file":{"filename":<nome>,"file_data":"data:application/pdf;base64,<...>"}}`.
  - `eh_pdf(caminho: str) -> bool`.

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_encoding.py
import base64
from extractor.encoding import bloco_documento, eh_pdf

def test_imagem_vira_image_url_base64(tmp_path):
    p = tmp_path / "x.jpg"
    p.write_bytes(b"\xff\xd8\xff\xe0teste")
    bloco = bloco_documento(str(p))
    assert bloco["type"] == "image_url"
    assert bloco["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert not eh_pdf(str(p))

def test_pdf_vira_file_block(tmp_path):
    p = tmp_path / "x.pdf"
    p.write_bytes(b"%PDF-1.4 teste")
    bloco = bloco_documento(str(p))
    assert bloco["type"] == "file"
    assert bloco["file"]["filename"] == "x.pdf"
    assert bloco["file"]["file_data"].startswith("data:application/pdf;base64,")
    assert eh_pdf(str(p))
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/test_encoding.py -v`
Expected: FAIL com `ModuleNotFoundError`.

- [ ] **Step 3: Implementar**

```python
# extractor/encoding.py
"""Converte arquivos locais em blocos de conteúdo para a API."""
import base64
import os

_MIME_IMG = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
             ".png": "image/png", ".webp": "image/webp"}


def eh_pdf(caminho: str) -> bool:
    return os.path.splitext(caminho)[1].lower() == ".pdf"


def bloco_documento(caminho: str) -> dict:
    with open(caminho, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    if eh_pdf(caminho):
        return {
            "type": "file",
            "file": {
                "filename": os.path.basename(caminho),
                "file_data": f"data:application/pdf;base64,{b64}",
            },
        }
    ext = os.path.splitext(caminho)[1].lower()
    mime = _MIME_IMG.get(ext, "image/jpeg")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
```

- [ ] **Step 4: Rodar e ver passar**

Run: `pytest tests/test_encoding.py -v`
Expected: PASS (2 testes).

- [ ] **Step 5: Commit**

```bash
git add extractor/encoding.py tests/test_encoding.py
git commit -m "feat: encoding de imagem/PDF para blocos de mensagem"
```

---

### Task 4: Cliente OpenRouter (single-pass e 2-step)

**Files:**
- Create: `extractor/client.py`
- Test: `tests/test_client_smoke.py`

**Interfaces:**
- Consumes: `extractor.encoding.bloco_documento`, `extractor.schemas.construir_json_schema`, `extractor.models.Layout`.
- Produces:
  - `RespostaLLM` (pydantic): `dados: dict`, `custo_usd: float | None`, `tokens_in: int`, `tokens_out: int`, `latencia_s: float`, `modelo: str`, `n_chamadas: int`.
  - `OpenRouterClient(api_key: str | None = None, base_url: str = "https://openrouter.ai/api/v1")`.
  - `OpenRouterClient.single_pass(caminho: str, layout: Layout, modelo: str) -> RespostaLLM` — 1 chamada com `response_format` json_schema strict.
  - `OpenRouterClient.two_step(caminho: str, layout: Layout, modelo: str) -> RespostaLLM` — chamada 1 (extração livre em texto) + chamada 2 (formata o texto em JSON via json_schema); `n_chamadas=2`, custo/latência/tokens somados.

- [ ] **Step 1: Escrever o smoke test (skipa sem chave)**

```python
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
```

- [ ] **Step 2: Rodar e ver skipar (ou falhar por import)**

Run: `pytest tests/test_client_smoke.py -v`
Expected: sem chave → SKIPPED; o teste importa `extractor.client`, então primeiro vai FALAR `ModuleNotFoundError` até implementarmos.

- [ ] **Step 3: Implementar**

```python
# extractor/client.py
"""Cliente OpenRouter: extração single-pass e baseline 2-step."""
import json
import os
import time
from typing import Optional

from openai import OpenAI
from pydantic import BaseModel

from extractor.encoding import bloco_documento, eh_pdf
from extractor.models import Layout
from extractor.schemas import construir_json_schema

_PROMPT_EXTRACAO = (
    "Você é um extrator de dados de documentos. Leia o documento e preencha "
    "EXATAMENTE os campos do schema. Use o campo _raciocinio para anotar a "
    "leitura do layout. Datas em DD/MM/AAAA. Se um campo não existir no "
    "documento, use string vazia. Não invente valores."
)
_PLUGIN_PDF = {"plugins": [{"id": "file-parser", "pdf": {"engine": "native"}}]}


class RespostaLLM(BaseModel):
    dados: dict
    custo_usd: Optional[float]
    tokens_in: int
    tokens_out: int
    latencia_s: float
    modelo: str
    n_chamadas: int


def _extra_body(caminho: str) -> dict:
    body = {"usage": {"include": True}}
    if eh_pdf(caminho):
        body.update(_PLUGIN_PDF)
    return body


def _usage_custo(resp) -> tuple[Optional[float], int, int]:
    u = resp.usage
    custo = None
    if u is not None:
        extra = getattr(u, "model_extra", None) or {}
        custo = extra.get("cost")
    tin = getattr(u, "prompt_tokens", 0) or 0
    tout = getattr(u, "completion_tokens", 0) or 0
    return custo, tin, tout


class OpenRouterClient:
    def __init__(self, api_key: str | None = None,
                 base_url: str = "https://openrouter.ai/api/v1"):
        self.client = OpenAI(
            api_key=api_key or os.environ["OPENROUTER_API_KEY"],
            base_url=base_url,
        )

    def single_pass(self, caminho: str, layout: Layout, modelo: str) -> RespostaLLM:
        schema = construir_json_schema(layout)
        mensagens = [
            {"role": "system", "content": _PROMPT_EXTRACAO},
            {"role": "user", "content": [
                {"type": "text", "text": f"Layout: {layout.descricao}. Extraia os campos."},
                bloco_documento(caminho),
            ]},
        ]
        t0 = time.perf_counter()
        resp = self.client.chat.completions.create(
            model=modelo,
            messages=mensagens,
            response_format={"type": "json_schema", "json_schema": {
                "name": layout.layout_id, "strict": True, "schema": schema}},
            extra_body=_extra_body(caminho),
        )
        latencia = time.perf_counter() - t0
        dados = json.loads(resp.choices[0].message.content)
        custo, tin, tout = _usage_custo(resp)
        return RespostaLLM(dados=dados, custo_usd=custo, tokens_in=tin,
                           tokens_out=tout, latencia_s=latencia, modelo=modelo,
                           n_chamadas=1)

    def two_step(self, caminho: str, layout: Layout, modelo: str) -> RespostaLLM:
        # Chamada 1: extração livre (texto), sem schema — simula o baseline.
        campos = ", ".join(c.nome for c in layout.campos)
        msg1 = [
            {"role": "system", "content": _PROMPT_EXTRACAO},
            {"role": "user", "content": [
                {"type": "text", "text": f"Extraia em texto livre estes campos: {campos}."},
                bloco_documento(caminho),
            ]},
        ]
        t0 = time.perf_counter()
        r1 = self.client.chat.completions.create(
            model=modelo, messages=msg1, extra_body=_extra_body(caminho))
        texto = r1.choices[0].message.content
        # Chamada 2: formatar o texto em JSON conforme schema.
        schema = construir_json_schema(layout)
        msg2 = [
            {"role": "system", "content": "Formate o texto a seguir no schema JSON pedido."},
            {"role": "user", "content": texto},
        ]
        r2 = self.client.chat.completions.create(
            model=modelo, messages=msg2,
            response_format={"type": "json_schema", "json_schema": {
                "name": layout.layout_id, "strict": True, "schema": schema}})
        latencia = time.perf_counter() - t0
        dados = json.loads(r2.choices[0].message.content)
        c1, i1, o1 = _usage_custo(r1)
        c2, i2, o2 = _usage_custo(r2)
        custo = None if c1 is None and c2 is None else (c1 or 0) + (c2 or 0)
        return RespostaLLM(dados=dados, custo_usd=custo, tokens_in=i1 + i2,
                           tokens_out=o1 + o2, latencia_s=latencia, modelo=modelo,
                           n_chamadas=2)
```

- [ ] **Step 4: Rodar smoke test (com chave, se disponível)**

Run: `pytest tests/test_client_smoke.py -v` (com `OPENROUTER_API_KEY` no ambiente)
Expected: PASS se houver chave; SKIPPED caso contrário. Sem erro de import.

- [ ] **Step 5: Commit**

```bash
git add extractor/client.py tests/test_client_smoke.py
git commit -m "feat: cliente OpenRouter single-pass e baseline 2-step"
```

---

### Task 5: Pipeline — envelope + validators + status

**Files:**
- Create: `extractor/pipeline.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: `extractor.models.Layout`, `extractor.client.RespostaLLM`, `extractor.validators`.
- Produces:
  - `aplicar_validators(dados: dict, layout: Layout) -> dict` — para cada campo com `validador`, zera (`None`) o valor se inválido; remove o campo `_raciocinio` do resultado final.
  - `montar_envelope(dados: dict, layout: Layout) -> dict` — retorna `{"status": ..., "extracted_data": ...}`; status `ok` se nenhum campo é vazio/None, `partial` se algum é vazio/None, `error` se `dados` vier vazio.
  - `extrair(caminho: str, layout: Layout, modelo: str, client, modo: str = "single") -> tuple[dict, RespostaLLM]` — chama `client.single_pass`/`two_step` conforme `modo` (`"single"`/`"two_step"`), aplica validators, retorna `(envelope, resposta)`.

- [ ] **Step 1: Escrever o teste que falha (client fake, sem rede)**

```python
# tests/test_pipeline.py
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
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/test_pipeline.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'extractor.pipeline'`.

- [ ] **Step 3: Implementar**

```python
# extractor/pipeline.py
"""Pós-processamento: validators, envelope {status, extracted_data}."""
from extractor.models import Layout
from extractor.validators import cpf_valido, cnpj_valido

_VALIDADORES = {"cpf": cpf_valido, "cnpj": cnpj_valido}


def aplicar_validators(dados: dict, layout: Layout) -> dict:
    out = {k: v for k, v in dados.items() if k != "_raciocinio"}
    for campo in layout.campos:
        if campo.validador and campo.nome in out:
            valor = out[campo.nome]
            if valor in (None, "") or not _VALIDADORES[campo.validador](str(valor)):
                out[campo.nome] = None
    return out


def montar_envelope(dados: dict, layout: Layout) -> dict:
    limpo = aplicar_validators(dados, layout) if "_raciocinio" in dados else dict(dados)
    if not limpo:
        return {"status": "error", "extracted_data": {}}
    vazio = any(v in (None, "") for v in limpo.values())
    return {"status": "partial" if vazio else "ok", "extracted_data": limpo}


def extrair(caminho: str, layout: Layout, modelo: str, client, modo: str = "single"):
    if modo == "two_step":
        resp = client.two_step(caminho, layout, modelo)
    else:
        resp = client.single_pass(caminho, layout, modelo)
    limpo = aplicar_validators(resp.dados, layout)
    envelope = montar_envelope(limpo, layout)
    return envelope, resp
```

> Nota: `montar_envelope` aceita dados com ou sem `_raciocinio` (idempotente); em `extrair` os validators já rodaram, então passamos o dict limpo.

- [ ] **Step 4: Rodar e ver passar**

Run: `pytest tests/test_pipeline.py -v`
Expected: PASS (3 testes).

- [ ] **Step 5: Commit**

```bash
git add extractor/pipeline.py tests/test_pipeline.py
git commit -m "feat: pipeline com validators e envelope {status, extracted_data}"
```

---

### Task 6: Layouts dos 3 documentos + ground truth da CNH

**Files:**
- Create: `benchmark/layouts.py`
- Test: `tests/test_layouts.py`

**Interfaces:**
- Consumes: `extractor.models.FieldSpec, Layout`.
- Produces:
  - `LAYOUT_CNH`, `LAYOUT_FATURA`, `LAYOUT_PAPER` (`Layout`).
  - `DOCUMENTOS: dict[str, dict]` — mapeia chave → `{"layout": Layout, "arquivo": str}` para os 3 docs de `data/`.
  - `GROUND_TRUTH_CNH: dict[str, str]` — rótulos manuais dos 6 campos da CNH (preenchidos ao inspecionar `data/Documento 1.jpeg`).

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_layouts.py
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
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/test_layouts.py -v`
Expected: FAIL com `ModuleNotFoundError`.

- [ ] **Step 3: Implementar (rótulos da CNH a confirmar inspecionando o arquivo)**

```python
# benchmark/layouts.py
"""Layouts dos 3 documentos de teste e ground truth da CNH."""
from extractor.models import FieldSpec, Layout

LAYOUT_CNH = Layout(layout_id="cnh", descricao="CNH brasileira", campos=[
    FieldSpec(nome="nome", tipo="text", descricao="Nome completo do condutor"),
    FieldSpec(nome="cpf", tipo="text", descricao="CPF do condutor", validador="cpf"),
    FieldSpec(nome="data_nascimento", tipo="date", descricao="Data de nascimento"),
    FieldSpec(nome="data_emissao", tipo="date", descricao="Data de emissão do documento"),
    FieldSpec(nome="filiacao_pai", tipo="text", descricao="Nome do pai (filiação)"),
    FieldSpec(nome="filiacao_mae", tipo="text", descricao="Nome da mãe (filiação)"),
])

LAYOUT_FATURA = Layout(layout_id="fatura", descricao="Fatura de energia CELPE", campos=[
    FieldSpec(nome="titular", tipo="text", descricao="Nome do titular da conta"),
    FieldSpec(nome="cnpj_distribuidora", tipo="text",
              descricao="CNPJ da distribuidora", validador="cnpj"),
    FieldSpec(nome="mes_referencia", tipo="text", descricao="Mês/ano de referência"),
    FieldSpec(nome="vencimento", tipo="date", descricao="Data de vencimento"),
    FieldSpec(nome="valor_total", tipo="number", descricao="Valor total a pagar em reais"),
    FieldSpec(nome="consumo_kwh", tipo="number", descricao="Consumo do mês em kWh"),
    FieldSpec(nome="numero_instalacao", tipo="text", descricao="Número da instalação/cliente"),
])

LAYOUT_PAPER = Layout(layout_id="paper", descricao="Paper acadêmico (Claude 3)", campos=[
    FieldSpec(nome="titulo", tipo="text", descricao="Título do artigo"),
    FieldSpec(nome="resumo_markdown", tipo="text",
              descricao="Conteúdo principal em Markdown preservando tabelas; "
                        "descreva gráficos/figuras em texto"),
])

DOCUMENTOS = {
    "cnh": {"layout": LAYOUT_CNH, "arquivo": "data/Documento 1.jpeg"},
    "fatura": {"layout": LAYOUT_FATURA, "arquivo": "data/Documento 2.jpg"},
    "paper": {"layout": LAYOUT_PAPER, "arquivo": "data/Documento 3.pdf"},
}

# Rótulos manuais — PREENCHER inspecionando data/Documento 1.jpeg na execução
# (mascarar/anonimizar se for documento real). Servem de calibração do juiz.
GROUND_TRUTH_CNH = {
    "nome": "",
    "cpf": "",
    "data_nascimento": "",
    "data_emissao": "",
    "filiacao_pai": "",
    "filiacao_mae": "",
}
```

- [ ] **Step 4: Rodar e ver passar**

Run: `pytest tests/test_layouts.py -v`
Expected: PASS (3 testes).

- [ ] **Step 5: Inspecionar a CNH e preencher `GROUND_TRUTH_CNH`**

Abra `data/Documento 1.jpeg` (use o tool Read para visualizar) e preencha os 6 valores reais em `GROUND_TRUTH_CNH`. Não há teste automatizado para os valores; é rótulo humano.

- [ ] **Step 6: Commit**

```bash
git add benchmark/layouts.py tests/test_layouts.py
git commit -m "feat: layouts dos 3 documentos e ground truth da CNH"
```

---

### Task 7: LLM-as-judge

**Files:**
- Create: `benchmark/judge.py`
- Test: `tests/test_judge.py`

**Interfaces:**
- Consumes: `extractor.encoding.bloco_documento`, `extractor.client.OpenRouterClient` (reusa o `.client` interno OpenAI).
- Produces:
  - `julgar(caminho: str, extracted_data: dict, client: OpenRouterClient, modelo_juiz: str = "openai/gpt-4o") -> dict` — pede ao juiz uma nota de fidelidade por campo; retorna `{"acuracia": float (0..1), "por_campo": {campo: bool}, "comentario": str}`. Usa `response_format` json_schema strict para o veredito.
  - `_schema_veredito(campos: list[str]) -> dict` — schema strict do veredito.

- [ ] **Step 1: Escrever o teste que falha (testa só o schema, sem rede)**

```python
# tests/test_judge.py
from benchmark.judge import _schema_veredito

def test_schema_veredito_e_strict():
    s = _schema_veredito(["nome", "cpf"])
    assert s["additionalProperties"] is False
    assert "acuracia" in s["properties"]
    assert s["properties"]["por_campo"]["additionalProperties"] is False
    assert set(s["properties"]["por_campo"]["properties"]) == {"nome", "cpf"}
    assert set(s["required"]) >= {"acuracia", "por_campo", "comentario"}
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/test_judge.py -v`
Expected: FAIL com `ModuleNotFoundError`.

- [ ] **Step 3: Implementar**

```python
# benchmark/judge.py
"""LLM-as-judge: avalia fidelidade da extração contra o documento-fonte."""
import json
from extractor.encoding import bloco_documento, eh_pdf
from extractor.client import OpenRouterClient

_PROMPT_JUIZ = (
    "Você é um avaliador rigoroso. Compare os dados extraídos com o documento "
    "anexado. Para cada campo, marque true se o valor extraído está fiel ao "
    "documento (ou corretamente vazio/null quando o campo não existe), e false "
    "caso contrário. 'acuracia' é a fração de campos corretos (0 a 1)."
)


def _schema_veredito(campos: list[str]) -> dict:
    por_campo = {
        "type": "object",
        "properties": {c: {"type": "boolean"} for c in campos},
        "required": list(campos),
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "acuracia": {"type": "number"},
            "por_campo": por_campo,
            "comentario": {"type": "string"},
        },
        "required": ["acuracia", "por_campo", "comentario"],
        "additionalProperties": False,
    }


def julgar(caminho: str, extracted_data: dict, client: OpenRouterClient,
           modelo_juiz: str = "openai/gpt-4o") -> dict:
    campos = list(extracted_data.keys())
    schema = _schema_veredito(campos)
    conteudo = [
        {"type": "text", "text": _PROMPT_JUIZ + "\n\nDados extraídos:\n"
         + json.dumps(extracted_data, ensure_ascii=False)},
        bloco_documento(caminho),
    ]
    extra = {"usage": {"include": True}}
    if eh_pdf(caminho):
        extra["plugins"] = [{"id": "file-parser", "pdf": {"engine": "native"}}]
    resp = client.client.chat.completions.create(
        model=modelo_juiz,
        messages=[{"role": "user", "content": conteudo}],
        response_format={"type": "json_schema", "json_schema": {
            "name": "veredito", "strict": True, "schema": schema}},
        extra_body=extra,
    )
    return json.loads(resp.choices[0].message.content)
```

- [ ] **Step 4: Rodar e ver passar**

Run: `pytest tests/test_judge.py -v`
Expected: PASS (1 teste).

- [ ] **Step 5: Commit**

```bash
git add benchmark/judge.py tests/test_judge.py
git commit -m "feat: LLM-as-judge de fidelidade com schema strict"
```

---

### Task 8: Harness de benchmark (matriz + tabela)

**Files:**
- Create: `benchmark/run.py`
- Test: `tests/test_run.py`

**Interfaces:**
- Consumes: `benchmark.layouts.DOCUMENTOS`, `extractor.pipeline.extrair`, `benchmark.judge.julgar`, `extractor.client.OpenRouterClient`.
- Produces:
  - `MODELOS: list[str]` — modelos da matriz.
  - `linha_resultado(doc_key, modelo, modo, envelope, resp, acuracia) -> dict` — uma linha achatada.
  - `tabela_markdown(linhas: list[dict]) -> str` — renderiza tabela Markdown ordenada.
  - `main()` — roda a matriz (modelos × docs × {single, two_step}), julga, salva `benchmark/results/results.json` e `benchmark/results/tabela.md`.

- [ ] **Step 1: Escrever o teste que falha (funções puras, sem rede)**

```python
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
    assert l["n_chamadas"] == 1 and l["acuracia"] == 0.83 and l["status"] == "ok"

def test_tabela_markdown_tem_cabecalho_e_linha():
    md = tabela_markdown([linha_resultado("cnh", "m", "single", 
        {"status": "ok", "extracted_data": {}}, _resp(), 0.83)])
    assert "| doc " in md and "cnh" in md
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/test_run.py -v`
Expected: FAIL com `ModuleNotFoundError`.

- [ ] **Step 3: Implementar**

```python
# benchmark/run.py
"""Roda a matriz modelo x documento x braço e gera tabela de resultados."""
import json
import os
from dotenv import load_dotenv

from benchmark.layouts import DOCUMENTOS
from benchmark.judge import julgar
from extractor.client import OpenRouterClient
from extractor.pipeline import extrair

MODELOS = [
    "google/gemini-2.5-flash-lite",
    "openai/gpt-4o-mini",
    "qwen/qwen2.5-vl-72b-instruct",
]
MODELO_JUIZ = "openai/gpt-4o"
_COLUNAS = ["doc", "modelo", "modo", "status", "n_chamadas",
            "latencia_s", "custo_usd", "acuracia"]


def linha_resultado(doc_key, modelo, modo, envelope, resp, acuracia) -> dict:
    return {
        "doc": doc_key, "modelo": modelo, "modo": modo,
        "status": envelope["status"], "n_chamadas": resp.n_chamadas,
        "latencia_s": round(resp.latencia_s, 3),
        "custo_usd": resp.custo_usd, "acuracia": acuracia,
    }


def tabela_markdown(linhas: list[dict]) -> str:
    cab = "| " + " | ".join(_COLUNAS) + " |"
    sep = "| " + " | ".join("---" for _ in _COLUNAS) + " |"
    corpo = ["| " + " | ".join(str(l.get(c, "")) for c in _COLUNAS) + " |"
             for l in linhas]
    return "\n".join([cab, sep, *corpo])


def main():
    load_dotenv()
    cli = OpenRouterClient()
    linhas = []
    for doc_key, cfg in DOCUMENTOS.items():
        for modelo in MODELOS:
            for modo in ("single", "two_step"):
                try:
                    env, resp = extrair(cfg["arquivo"], cfg["layout"], modelo,
                                        cli, modo=modo)
                    veredito = julgar(cfg["arquivo"], env["extracted_data"],
                                      cli, MODELO_JUIZ)
                    linhas.append(linha_resultado(doc_key, modelo, modo, env,
                                                  resp, veredito["acuracia"]))
                    print(f"ok: {doc_key}/{modelo}/{modo}")
                except Exception as e:  # registra falha e segue a matriz
                    print(f"FALHA: {doc_key}/{modelo}/{modo}: {e}")
    os.makedirs("benchmark/results", exist_ok=True)
    with open("benchmark/results/results.json", "w", encoding="utf-8") as f:
        json.dump(linhas, f, ensure_ascii=False, indent=2)
    with open("benchmark/results/tabela.md", "w", encoding="utf-8") as f:
        f.write(tabela_markdown(linhas))
    print(f"\n{len(linhas)} linhas salvas em benchmark/results/")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Rodar e ver passar (testes puros)**

Run: `pytest tests/test_run.py -v`
Expected: PASS (2 testes).

- [ ] **Step 5: Rodar a matriz de verdade (com chave) — gera os números do dossiê**

Run: `python -m benchmark.run` (com `OPENROUTER_API_KEY` no `.env`)
Expected: imprime progresso por célula; cria `benchmark/results/results.json` e `tabela.md`. Inspecione a tabela.

- [ ] **Step 6: Commit**

```bash
git add benchmark/run.py tests/test_run.py
git commit -m "feat: harness de benchmark (matriz, julgamento, tabela)"
```

---

### Task 9: API FastAPI espelhando o contrato Tech4.ai

**Files:**
- Create: `api/main.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: `extractor.pipeline.extrair`, `extractor.client.OpenRouterClient`, `benchmark.layouts.DOCUMENTOS`.
- Produces:
  - App FastAPI `app` com `POST /extract` recebendo `multipart/form-data`: `file` (upload) + `layout_id` (form) → `{status, extracted_data}`. `GET /health` → `{"status":"ok"}`. `GET /layouts` → lista de `layout_id` disponíveis.
  - Injeção do client via dependência sobrescrevível (para teste com fake).

- [ ] **Step 1: Escrever o teste que falha (TestClient + client fake)**

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from extractor.client import RespostaLLM
from api.main import app, get_client

class _FakeClient:
    def single_pass(self, caminho, layout, modelo):
        return RespostaLLM(dados={"_raciocinio": "x", "nome": "Ana",
                                  "cpf": "123.456.789-09", "data_nascimento": "01/01/1990",
                                  "data_emissao": "01/01/2020", "filiacao_pai": "Pai",
                                  "filiacao_mae": "Mae"},
                           custo_usd=0.001, tokens_in=1, tokens_out=1,
                           latencia_s=0.1, modelo=modelo, n_chamadas=1)

app.dependency_overrides[get_client] = lambda: _FakeClient()
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
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/test_api.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'api.main'`.

- [ ] **Step 3: Implementar**

```python
# api/main.py
"""API de extração espelhando o contrato Tech4.ai: POST /extract -> {status, extracted_data}."""
import os
import tempfile
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends

from benchmark.layouts import DOCUMENTOS
from extractor.client import OpenRouterClient
from extractor.pipeline import extrair

load_dotenv()
app = FastAPI(title="POC Extração de Documentos", version="0.1.0")
MODELO_PADRAO = os.getenv("MODELO_PADRAO", "google/gemini-2.5-flash-lite")


def get_client() -> OpenRouterClient:
    return OpenRouterClient()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/layouts")
def layouts():
    return {"layouts": list(DOCUMENTOS.keys())}


@app.post("/extract")
async def extract(layout_id: str = Form(...), file: UploadFile = File(...),
                  client=Depends(get_client)):
    if layout_id not in DOCUMENTOS:
        raise HTTPException(400, f"layout_id desconhecido: {layout_id}")
    layout = DOCUMENTOS[layout_id]["layout"]
    sufixo = os.path.splitext(file.filename or "")[1] or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=sufixo) as tmp:
        tmp.write(await file.read())
        caminho = tmp.name
    try:
        envelope, _ = extrair(caminho, layout, MODELO_PADRAO, client, modo="single")
    finally:
        os.unlink(caminho)
    return envelope
```

- [ ] **Step 4: Rodar e ver passar**

Run: `pytest tests/test_api.py -v`
Expected: PASS (2 testes).

- [ ] **Step 5: Subir a API e testar o Swagger**

Run: `uvicorn api.main:app --reload` → abrir `http://localhost:8000/docs`
Expected: Swagger UI lista `/extract`, `/health`, `/layouts`.

- [ ] **Step 6: Commit**

```bash
git add api/main.py tests/test_api.py
git commit -m "feat: API FastAPI /extract espelhando contrato Tech4.ai"
```

---

### Task 10: UI Streamlit

**Files:**
- Create: `ui/app.py`

**Interfaces:**
- Consumes: `benchmark.layouts.DOCUMENTOS`, `extractor.pipeline.extrair`, `extractor.client.OpenRouterClient`.
- Produces: app Streamlit com upload, seleção de `layout_id`, e exibição imagem ↔ JSON lado a lado. (Sem teste automatizado — UI; verificação manual.)

- [ ] **Step 1: Implementar**

```python
# ui/app.py
"""UI Streamlit: upload de documento + extração lado a lado."""
import os
import tempfile
import streamlit as st
from dotenv import load_dotenv

from benchmark.layouts import DOCUMENTOS
from extractor.client import OpenRouterClient
from extractor.pipeline import extrair

load_dotenv()
st.set_page_config(page_title="POC Extração de Documentos", layout="wide")
st.title("POC — Extração de Documentos (single-pass + structured output)")

modelo = st.sidebar.selectbox("Modelo", [
    "google/gemini-2.5-flash-lite", "openai/gpt-4o-mini",
    "qwen/qwen2.5-vl-72b-instruct"])
layout_id = st.sidebar.selectbox("Layout", list(DOCUMENTOS.keys()))
arquivo = st.file_uploader("Documento (jpg/png/pdf)",
                           type=["jpg", "jpeg", "png", "webp", "pdf"])

if arquivo and st.button("Extrair"):
    sufixo = os.path.splitext(arquivo.name)[1] or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=sufixo) as tmp:
        tmp.write(arquivo.getvalue())
        caminho = tmp.name
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Documento")
        if sufixo.lower() != ".pdf":
            st.image(arquivo.getvalue())
        else:
            st.info("PDF enviado (pré-visualização não exibida).")
    with col2:
        st.subheader("Extração")
        with st.spinner("Extraindo..."):
            try:
                envelope, resp = extrair(caminho, DOCUMENTOS[layout_id]["layout"],
                                         modelo, OpenRouterClient(), modo="single")
                st.json(envelope)
                st.caption(f"status={envelope['status']} · {resp.n_chamadas} chamada(s) "
                           f"· {resp.latencia_s:.2f}s · custo=${resp.custo_usd}")
            except Exception as e:
                st.error(f"Falha: {e}")
            finally:
                os.unlink(caminho)
```

- [ ] **Step 2: Rodar e verificar manualmente**

Run: `streamlit run ui/app.py`
Expected: abre no browser; upload de uma imagem + "Extrair" mostra imagem à esquerda e JSON `{status, extracted_data}` à direita.

- [ ] **Step 3: Commit**

```bash
git add ui/app.py
git commit -m "feat: UI Streamlit com extração lado a lado"
```

---

### Task 11: Docker + README

**Files:**
- Create: `Dockerfile`, `docker-compose.yml`, `README.md`

**Interfaces:**
- Produces: `docker compose up` sobe API (porta 8000) e UI (porta 8501).

- [ ] **Step 1: Criar `Dockerfile`**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000 8501
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Criar `docker-compose.yml`**

```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000
  ui:
    build: .
    ports: ["8501:8501"]
    env_file: .env
    command: streamlit run ui/app.py --server.address 0.0.0.0 --server.port 8501
```

- [ ] **Step 3: Criar `README.md`**

````markdown
# POC — Extração de Documentos (single-pass + structured output)

Demonstra a recomendação do dossiê: colapsar o pipeline de 2 inferências em 1
chamada (VLM + structured output via OpenRouter), espelhando o contrato da
Tech4.ai (`{status, extracted_data}`).

## Setup
```bash
cp .env.example .env   # e preencha OPENROUTER_API_KEY
pip install -r requirements.txt
pytest                 # roda os testes (chamadas de rede são skipadas sem chave)
```

## Rodar
- API:  `uvicorn api.main:app --reload`  → http://localhost:8000/docs
- UI:   `streamlit run ui/app.py`        → http://localhost:8501
- Docker: `docker compose up`            → API :8000, UI :8501
- Benchmark: `python -m benchmark.run`   → benchmark/results/{results.json,tabela.md}

## Arquitetura
`extractor/` (engine) · `api/` (FastAPI) · `ui/` (Streamlit) · `benchmark/` (experimento + LLM-as-judge).
Ver `.specs/` para spec e plano.
````

- [ ] **Step 4: Validar build e subida**

Run: `docker compose up --build`
Expected: ambos os serviços sobem; `curl http://localhost:8000/health` → `{"status":"ok"}`; UI acessível em :8501.

- [ ] **Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml README.md
git commit -m "feat: containerização (Docker Compose) e README"
```

---

## Resultado Final

Ao concluir as 12 tasks: engine testada, API espelhando a Tech4.ai, UI Streamlit,
benchmark gerando `results.json` + `tabela.md` (latência/custo/acurácia por
modelo×documento×braço), tudo containerizado. Os números do benchmark alimentam
a Seção 4 (Resultados) do dossiê.

## Próximo entregável (fora deste plano)

A redação do **Dossiê** (Entregável 1, 80%) é um plano separado, a ser iniciado
quando `benchmark/results/` existir — as 6 seções do desafio, alinhadas ao estilo
do TCP de referência (`example/`). A POC fornece a evidência empírica; o dossiê
faz a curadoria, a comparação com benchmarks de terceiros, a recomendação e a
análise de viabilidade.
