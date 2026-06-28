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


def _conteudo(resp, modelo: str) -> str:
    """Extrai o texto da resposta, falhando com mensagem clara se o provedor
    devolveu um envelope de erro (choices=None) ou conteúdo vazio/recusado."""
    if not getattr(resp, "choices", None):
        raise ValueError(f"Sem choices na resposta do modelo {modelo} (provável erro do provedor).")
    conteudo = resp.choices[0].message.content
    if not conteudo:
        raise ValueError(f"Resposta vazia ou recusada pelo modelo {modelo}.")
    return conteudo


class OpenRouterClient:
    def __init__(self, api_key: str | None = None,
                 base_url: str = "https://openrouter.ai/api/v1",
                 timeout: float = 120.0):
        chave = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not chave:
            raise ValueError("OPENROUTER_API_KEY não configurada (defina no .env ou passe api_key=).")
        # timeout evita que uma chamada (ex.: PDF gigante) trave indefinidamente.
        self.client = OpenAI(api_key=chave, base_url=base_url, timeout=timeout)

    def single_pass(self, caminho: str, layout: Layout, modelo: str,
                    max_tokens: Optional[int] = None) -> RespostaLLM:
        schema = construir_json_schema(layout)
        mensagens = [
            {"role": "system", "content": _PROMPT_EXTRACAO},
            {"role": "user", "content": [
                {"type": "text", "text": f"Layout: {layout.descricao}. Extraia os campos."},
                bloco_documento(caminho),
            ]},
        ]
        kwargs: dict = dict(
            model=modelo,
            messages=mensagens,
            response_format={"type": "json_schema", "json_schema": {
                "name": layout.layout_id, "strict": True, "schema": schema}},
            extra_body=_extra_body(caminho),
        )
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        t0 = time.perf_counter()
        resp = self.client.chat.completions.create(**kwargs)
        latencia = time.perf_counter() - t0
        dados = json.loads(_conteudo(resp, modelo))
        custo, tin, tout = _usage_custo(resp)
        return RespostaLLM(dados=dados, custo_usd=custo, tokens_in=tin,
                           tokens_out=tout, latencia_s=latencia, modelo=modelo,
                           n_chamadas=1)

    def two_step(self, caminho: str, layout: Layout, modelo: str,
                 max_tokens: Optional[int] = None) -> RespostaLLM:
        # Chamada 1: extração livre (texto), sem schema — simula o baseline.
        campos = ", ".join(c.nome for c in layout.campos)
        msg1 = [
            {"role": "system", "content": _PROMPT_EXTRACAO},
            {"role": "user", "content": [
                {"type": "text", "text": f"Extraia em texto livre estes campos: {campos}."},
                bloco_documento(caminho),
            ]},
        ]
        kw1: dict = dict(model=modelo, messages=msg1, extra_body=_extra_body(caminho))
        if max_tokens is not None:
            kw1["max_tokens"] = max_tokens
        t0 = time.perf_counter()
        r1 = self.client.chat.completions.create(**kw1)
        texto = _conteudo(r1, modelo)
        # Chamada 2: formatar o texto em JSON conforme schema.
        schema = construir_json_schema(layout)
        msg2 = [
            {"role": "system", "content": "Formate o texto a seguir no schema JSON pedido."},
            {"role": "user", "content": texto},
        ]
        kw2: dict = dict(
            model=modelo, messages=msg2,
            response_format={"type": "json_schema", "json_schema": {
                "name": layout.layout_id, "strict": True, "schema": schema}})
        if max_tokens is not None:
            kw2["max_tokens"] = max_tokens
        r2 = self.client.chat.completions.create(**kw2)
        latencia = time.perf_counter() - t0
        dados = json.loads(_conteudo(r2, modelo))
        c1, i1, o1 = _usage_custo(r1)
        c2, i2, o2 = _usage_custo(r2)
        custo = None if c1 is None and c2 is None else (c1 or 0) + (c2 or 0)
        return RespostaLLM(dados=dados, custo_usd=custo, tokens_in=i1 + i2,
                           tokens_out=o1 + o2, latencia_s=latencia, modelo=modelo,
                           n_chamadas=2)
