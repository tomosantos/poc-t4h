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
