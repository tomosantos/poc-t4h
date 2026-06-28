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
    if not extracted_data:
        raise ValueError("extracted_data vazio: nada para julgar.")
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
    conteudo = resp.choices[0].message.content
    if not conteudo:
        raise ValueError(f"Juiz retornou conteúdo vazio (modelo {modelo_juiz}).")
    return json.loads(conteudo)
