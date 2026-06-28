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
