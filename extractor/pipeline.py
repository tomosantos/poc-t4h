"""Pós-processamento: validators, envelope {status, extracted_data}."""
from extractor.models import Layout
from extractor.validators import cpf_valido, cnpj_valido

_VALIDADORES = {"cpf": cpf_valido, "cnpj": cnpj_valido}


def aplicar_validators(dados: dict, layout: Layout) -> dict:
    out = {k: v for k, v in dados.items() if k != "_raciocinio"}
    for campo in layout.campos:
        if campo.validador and campo.nome in out:
            fn = _VALIDADORES.get(campo.validador)
            valor = out[campo.nome]
            if fn and (valor in (None, "") or not fn(str(valor))):
                out[campo.nome] = None
    return out


def montar_envelope(dados: dict) -> dict:
    limpo = {k: v for k, v in dados.items() if k != "_raciocinio"}
    if not limpo:
        return {"status": "error", "extracted_data": {}}
    vazio = any(v in (None, "") for v in limpo.values())
    return {"status": "partial" if vazio else "ok", "extracted_data": limpo}


def extrair(caminho: str, layout: Layout, modelo: str, client, modo: str = "single",
            **kwargs):
    if modo == "two_step":
        resp = client.two_step(caminho, layout, modelo, **kwargs)
    elif modo == "hybrid":
        resp = client.hybrid_pass(caminho, layout, modelo, **kwargs)
    else:
        resp = client.single_pass(caminho, layout, modelo, **kwargs)
    limpo = aplicar_validators(resp.dados, layout)
    envelope = montar_envelope(limpo)
    return envelope, resp
