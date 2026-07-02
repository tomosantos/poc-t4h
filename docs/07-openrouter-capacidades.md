# 07 — Capacidades técnicas do OpenRouter para POC de extração de documentos

> Pesquisa via WebFetch ativo da documentação oficial (openrouter.ai/docs). Data: 2026-06-26.
> Cada afirmação cita a URL da página de origem. Lacunas listadas no final.

---

## TL;DR

- **OpenAI-compatible**: `base_url="https://openrouter.ai/api/v1"`, SDK `openai` do Python funciona como drop-in replacement. (quickstart)
- **Structured outputs**: sim, `response_format` com `type: "json_schema"` + `strict: true`. Disponível em modelos suportados (OpenAI GPT-4o+, Gemini, Claude Sonnet 4.5/Opus 4.1+, Fireworks, maioria dos open-source). Validar compatibilidade na página de cada modelo. (structured-outputs)
- **Tool/function calling**: sim, formato OpenAI-compatible (`tools` + `tool_choice` auto/none/required). (tool-calling)
- **Visão**: enviar imagem como `type: "image_url"` (base64 data URL **ou** URL remota). Formatos: png, jpeg, webp, gif. (image-understanding)
- **PDF**: aceito **diretamente** via `type: "file"` (base64 `data:application/pdf;base64,...` ou URL). Processamento configurável via plugin `file-parser` com 3 engines (native / mistral-ocr / cloudflare-ai). (pdfs)
- **Custo/usage**: `usage.cost` (US$ autoritativo) + `usage.cost_details` + token counts vêm **automáticos** em toda resposta (params `usage.include` agora DEPRECATED/sempre-on). (usage-accounting)
- **Recomendação POC**: começar com `google/gemini-2.5-flash` ou `openai/gpt-4o-mini` (multimodais, baratos, suportam structured output) + `response_format json_schema strict` para extração tipada.

---

## 1. Structured Output (sintaxe + modelos)

**Fonte:** https://openrouter.ai/docs/guides/features/structured-outputs

Suporta `response_format` em dois modos:
- `{ "type": "json_object" }` — JSON válido genérico (JSON mode).
- `{ "type": "json_schema", "json_schema": { ... } }` — schema estrito.

`strict: true` é suportado e **recomendado** pela doc (garante aderência exata ao schema). A request falha com erro se o modelo não suportar structured outputs ou se o JSON Schema for inválido.

### Sintaxe exata da request
```json
{
  "model": "google/gemini-2.5-flash",
  "messages": [{ "role": "user", "content": "..." }],
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "extracao_documento",
      "strict": true,
      "schema": {
        "type": "object",
        "properties": { "nome": { "type": "string" }, "cpf": { "type": "string" } },
        "required": ["nome", "cpf"],
        "additionalProperties": false
      }
    }
  }
}
```

### Modelos que suportam (conforme doc)
- **OpenAI**: GPT-4o e posteriores
- **Google**: modelos Gemini
- **Anthropic**: Claude Sonnet 4.5, Opus 4.1+
- **Fireworks**: todos
- **Open-source**: a maioria

> Validar caso-a-caso: a página de cada modelo lista a compatibilidade com structured outputs. (https://openrouter.ai/docs/guides/overview/models)

### Plugin relacionado: Response Healing
O plugin **response-healing** ativa automaticamente em requests não-streaming quando se usa `response_format` (`json_schema` ou `json_object`) — repara JSON malformado. (https://openrouter.ai/docs/guides/features/plugins/response-healing)

### Tool / Function Calling
**Fonte:** https://openrouter.ai/docs/guides/features/tool-calling — OpenAI-compatible.

- Parâmetro `tools`: array de `{ "type": "function", "function": { "name", "description", "parameters" (JSON Schema) } }`.
- `tool_choice`: `"auto"` (default), `"none"`, `"required"`, ou tool específico `{"type":"function","function":{"name":"..."}}`.
- Resposta: `finish_reason: "tool_calls"` + array `tool_calls` (`id`, `type`, `function.name`, `function.arguments` como string JSON).
- Retorno do resultado: append da mensagem assistant + mensagem `{"role":"tool","tool_call_id":...,"content":...}`, reenviando `messages` + `tools`.

---

## 2. Visão / Multimodal (como enviar imagem + PDF + IDs de modelo)

### Imagens
**Fonte:** https://openrouter.ai/docs/guides/overview/multimodal/image-understanding

Content array com objetos `text` + `image_url`. O `image_url.url` aceita **URL remota** OU **base64 data URL**.

```python
import base64, requests

def encode_image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

data_url = f"data:image/jpeg;base64,{encode_image_to_base64('Documento 1.jpeg')}"

content = [
    {"type": "text", "text": "Extraia os campos da CNH."},
    {"type": "image_url", "image_url": {"url": data_url}}
]
```
Formatos suportados: `image/png`, `image/jpeg`, `image/webp`, `image/gif`.

### PDFs (aceitos diretamente)
**Fonte:** https://openrouter.ai/docs/guides/overview/multimodal/pdfs

PDF enviado via content type `type: "file"` — funciona em **qualquer modelo** do OpenRouter (o OpenRouter faz o parsing quando o modelo não tem file input nativo).

```json
{
  "type": "file",
  "file": {
    "filename": "document.pdf",
    "file_data": "data:application/pdf;base64,<BASE64>"
  }
}
```
`file_data` também aceita URL pública direta (ex.: `"https://bitcoin.org/bitcoin.pdf"`).

**Engines de parsing (plugin `file-parser`):**
| Engine | Uso | Custo |
|--------|-----|-------|
| `native` | Modelos com file input nativo; cobrado como input tokens normais | preço de input tokens do modelo |
| `mistral-ocr` | Scans / PDFs com muita imagem; melhor OCR | ~US$ 0,01 por 1.000 páginas |
| `cloudflare-ai` | PDF → markdown via Cloudflare Workers AI | **grátis** (sem custo) |

> `pdf-text` está deprecated → redireciona para `cloudflare-ai`. Default: `native` se disponível, senão `cloudflare-ai`.

```json
"plugins": [ { "id": "file-parser", "pdf": { "engine": "mistral-ocr" } } ]
```

### IDs exatos dos modelos de visão (slugs OpenRouter)
| Modelo | Slug / ID | Visão |
|--------|-----------|-------|
| GPT-4o-mini | `openai/gpt-4o-mini` | sim |
| Gemini 2.5 Flash | `google/gemini-2.5-flash` | sim |
| Gemini 2.5 Flash Lite | `google/gemini-2.5-flash-lite` | sim |
| Gemini 2.0 Flash | `google/gemini-2.0-flash-*` | **DEPRECATED (1 jun)** — ver lacunas |
| Claude 3.5 Haiku | `anthropic/claude-3.5-haiku` | sim |
| Qwen2.5-VL 72B | `qwen/qwen2.5-vl-72b-instruct` | sim |
| Llama 3.2 90B Vision | `meta-llama/llama-3.2-90b-vision-instruct` | sim |
| Llama 3.2 11B Vision | `meta-llama/llama-3.2-11b-vision-instruct` | sim |

---

## 3. Custo / Usage

**Fonte:** https://openrouter.ai/docs/cookbook/administration/usage-accounting

Toda resposta chat completion já retorna o custo autoritativo em US$ e contagem de tokens — **sem config adicional**. Os params `usage: { include: true }` e `stream_options: { include_usage: true }` estão **DEPRECATED** (usage agora sempre incluído).

Estrutura do objeto `usage`:
```json
{
  "prompt_tokens": 194,
  "completion_tokens": 2,
  "total_tokens": 196,
  "cost": 0.95,
  "cost_details": { "upstream_inference_cost": 19 },
  "prompt_tokens_details": { "cached_tokens": 0, "cache_write_tokens": 0 },
  "completion_tokens_details": { "reasoning_tokens": 0 }
}
```
- `usage.cost` = custo total da request em US$.
- `cost_details.upstream_inference_cost` só é preenchido para requests **BYOK** (Bring Your Own Key); caso contrário 0/null.
- Em streaming, o `usage` vem na última mensagem SSE.

**Endpoint /generation (stats assíncronas):** usar o generation ID retornado para consultar `/api/v1/generation` após a request. Útil para auditoria histórica.
> A doc de usage-accounting referencia o endpoint mas **não traz o schema exato** (URL/método/campos). Ver lacunas.

---

## 4. Tabela de preços (US$ / 1M tokens)

Fonte primária = páginas individuais de modelo em openrouter.ai. Preços podem variar por provider/routing e mudam com frequência — confirmar na request via `usage.cost`.

| Modelo | Slug | Input (US$/1M) | Output (US$/1M) | Fonte |
|--------|------|---------------:|----------------:|-------|
| GPT-4o-mini | `openai/gpt-4o-mini` | 0,15 | 0,60 | openrouter.ai/openai/gpt-4o-mini |
| Gemini 2.5 Flash | `google/gemini-2.5-flash` | 0,30 | 2,50 | openrouter.ai/google/gemini-2.5-flash |
| Gemini 2.5 Flash Lite | `google/gemini-2.5-flash-lite` | 0,10 | 0,40 | openrouter.ai/google/gemini-2.5-flash-lite |
| Claude 3.5 Haiku | `anthropic/claude-3.5-haiku` | 0,80 | 4,00 | openrouter.ai/anthropic/claude-3.5-haiku |
| Qwen2.5-VL 72B | `qwen/qwen2.5-vl-72b-instruct` | 0,80 | 1,00 | openrouter.ai/qwen/qwen2.5-vl-72b-instruct |
| Llama 3.2 90B Vision | `meta-llama/llama-3.2-90b-vision-instruct` | ~0,35* | ~0,40* | *fonte secundária — ver lacunas |

\* Llama 3.2 90B Vision: a página oficial não exibiu o número no fetch; ~0,35/~0,40 vem de fonte terceira. Confirmar direto na página antes de citar no dossiê. Existe variante `:free`.

---

## 5. Snippet Python de exemplo (extração com structured output + imagem)

```python
import base64
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="<OPENROUTER_API_KEY>",
)

def img_data_url(path, mime="image/jpeg"):
    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"

schema = {
    "name": "cnh",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "nome": {"type": "string"},
            "cpf": {"type": "string"},
            "numero_registro": {"type": "string"},
            "validade": {"type": "string"},
        },
        "required": ["nome", "cpf", "numero_registro", "validade"],
        "additionalProperties": False,
    },
}

resp = client.chat.completions.create(
    model="google/gemini-2.5-flash",
    extra_headers={"HTTP-Referer": "<SITE>", "X-OpenRouter-Title": "POC-Extracao"},
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Extraia os campos da CNH conforme o schema."},
            {"type": "image_url", "image_url": {"url": img_data_url("data/Documento 1.jpeg")}},
        ],
    }],
    response_format={"type": "json_schema", "json_schema": schema},
)

print(resp.choices[0].message.content)   # JSON tipado
print("USD:", resp.usage.model_dump().get("cost"))  # custo da request
print(resp.usage.prompt_tokens, resp.usage.completion_tokens)
```

**Para PDF multipágina (Documento 3.pdf)** — usar content `type: "file"` + plugin `file-parser`. Como o SDK `openai` não tipa `plugins`/`file`, passar via `extra_body`:
```python
resp = client.chat.completions.create(
    model="google/gemini-2.5-flash",
    messages=[{"role": "user", "content": [
        {"type": "text", "text": "Resuma e extraia tabelas/figuras."},
        {"type": "file", "file": {
            "filename": "Documento 3.pdf",
            "file_data": f"data:application/pdf;base64,{base64.b64encode(open('data/Documento 3.pdf','rb').read()).decode()}"
        }},
    ]}],
    extra_body={"plugins": [{"id": "file-parser", "pdf": {"engine": "mistral-ocr"}}]},
)
```

---

## 6. Fontes (URLs verificadas via WebFetch)

- Structured outputs: https://openrouter.ai/docs/guides/features/structured-outputs
- Response Healing plugin: https://openrouter.ai/docs/guides/features/plugins/response-healing
- Tool/function calling: https://openrouter.ai/docs/guides/features/tool-calling
- Image inputs: https://openrouter.ai/docs/guides/overview/multimodal/image-understanding
- PDF inputs: https://openrouter.ai/docs/guides/overview/multimodal/pdfs
- Multimodal overview: https://openrouter.ai/docs/guides/overview/multimodal/overview
- Usage accounting: https://openrouter.ai/docs/cookbook/administration/usage-accounting
- Quickstart (OpenAI compat): https://openrouter.ai/docs/quickstart
- Models list: https://openrouter.ai/docs/guides/overview/models
- Páginas de modelo (preços/IDs): openrouter.ai/openai/gpt-4o-mini · /google/gemini-2.5-flash · /google/gemini-2.5-flash-lite · /anthropic/claude-3.5-haiku · /qwen/qwen2.5-vl-72b-instruct · /meta-llama/llama-3.2-90b-vision-instruct

---

## 7. Lacunas (o que NÃO foi confirmado na doc oficial)

1. **Schema exato do endpoint `/generation`** — a doc de usage-accounting referencia mas não detalha URL/método/campos (`total_cost`, `native_tokens_prompt`, etc.). Buscar em `/docs/api/reference` antes de codar a auditoria assíncrona. (As páginas `/docs/api/reference/get-a-generation` e `/docs/features/tool-calling` retornaram 404 — usar os slugs `/docs/guides/...` corretos.)
2. **Gemini 2.0 Flash** — sinalizado como **DEPRECATED em 1 de junho** por fonte secundária; não confirmei na doc oficial nem o slug exato. Usar Gemini 2.5 Flash/Flash-Lite na POC.
3. **Preço Llama 3.2 90B Vision** (~0,35/~0,40) e ausência de pricing do **Llama 3.2 11B Vision** — vieram de fonte terceira; a página oficial não renderizou os números no fetch. Confirmar direto antes de citar no dossiê.
4. **Claude 3.5 Haiku visão** — preço (0,80/4,00) confirmado; suporte a imagem do 3.5 Haiku **não foi confirmado explicitamente** na página (família Claude 3.5 geralmente suporta, mas validar).
5. **Limites de tamanho/quantidade de páginas de PDF** e limites de imagens por request não foram localizados na doc.
6. **`mistral-ocr` US$ 0,01/1.000 páginas** — número da página de PDFs; reconfirmar pois custos de OCR mudam.
