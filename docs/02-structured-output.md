# Workstream 2 — Single-Pass / Structured Output

> Nota de pesquisa para o dossiê técnico. Objetivo: eliminar a 2ª chamada de LLM (formatação JSON) fazendo o modelo emitir JSON válido em **uma** inferência, reduzindo latência/custo sem perder acurácia.
> Período priorizado: 2024–2026. Cada afirmação tem URL. `[VERIFICADO]` = fato de fonte primária/oficial; `[INFERÊNCIA]` = raciocínio próprio a partir das fontes.

---

## TL;DR (5 bullets)

- **A 2ª chamada de formatação é tecnicamente eliminável hoje** em todos os provedores principais: OpenAI **Structured Outputs**, Anthropic **Structured Outputs** (GA desde nov/2025), Google **Gemini `responseSchema`**, e stacks open-source (Outlines, XGrammar, vLLM guided decoding, llama.cpp GBNF, lm-format-enforcer). Todos usam **constrained decoding** para restringir os tokens gerados ao schema. `[VERIFICADO]`
- **Constrained decoding GARANTE JSON sintaticamente válido e conforme ao schema** (é restrição determinística no momento da decodificação, não "pedido educado" no prompt). OpenAI mede **100% de conformidade** vs. **<40%** com prompting tradicional; function calling antigo ficava em ~86%. `[VERIFICADO]`
- **Overhead de latência é baixo a quase nulo, e pode até acelerar.** XGrammar reporta **<40 µs/token** e *near-zero overhead* end-to-end; coalescence (dottxt) pode tornar a geração estruturada **até 5x mais rápida** que a geração livre por pular tokens fixos do schema. Ressalva: há **custo único de compilação da gramática** na 1ª requisição (cacheado 24h na Anthropic). `[VERIFICADO]`
- **Impacto na acurácia é o ponto de debate.** O paper *"Let Me Speak Freely?"* (EMNLP 2024) afirma que formato rígido **degrada raciocínio**; a refutação da dottxt mostra que o resultado vinha de **prompts injustos e parser ruim** e que, com prompts iguais, o structured output **empata ou melhora** (GSM8K 0.77→0.78; Last Letter 0.73→0.77). Consenso prático: **separar raciocínio do schema** (campo de "reasoning" antes do "answer") resolve o trade-off em uma única chamada. `[VERIFICADO/INFERÊNCIA]`
- **Economia esperada ao remover a 2ª chamada: ~50% de latência e custo das etapas de formatação** (corte de 2 inferências para 1), sem nova infra para os provedores gerenciados. `[INFERÊNCIA]` — número de fontes que descrevem o pipeline de 2 passos; quantificação exata depende do tamanho dos tokens de cada etapa.

---

## Achados

### 1. Como eliminar a 2ª chamada — emitir JSON válido em UMA inferência

A 2ª chamada existe porque, historicamente, pedir JSON no prompt **não garantia** JSON válido — o modelo podia omitir chaves, inventar enums ou quebrar a sintaxe, exigindo uma passada de "limpeza/formatação". **Constrained decoding** remove essa necessidade: durante a decodificação, a cada passo só são amostrados tokens que mantêm a saída válida frente ao schema (máscara de logits sobre o vocabulário). Isso transforma a conformidade de "best-effort via prompt" em **garantia de engenharia**. ([Let's Data Science explainer](https://letsdatascience.com/blog/structured-outputs-making-llms-return-reliable-json), [aidancooper.co.uk constrained decoding guide](https://www.aidancooper.co.uk/constrained-decoding/))

**(a) OpenAI — JSON mode vs. Structured Outputs** `[VERIFICADO]`
- `response_format: {type: "json_schema", strict: true}`. Disponível a partir de `gpt-4o-2024-08-06` e `gpt-4o-mini`. Usa constrained sampling/decoding. ([docs](https://platform.openai.com/docs/guides/structured-outputs), [anúncio](https://openai.com/index/introducing-structured-outputs-in-the-api/))
- **JSON mode** garante apenas que a saída é JSON **válido**; **Structured Outputs** garante adicionalmente **aderência ao schema** (chaves, tipos, enums, required). Structured Outputs é a evolução do JSON mode. ([docs OpenAI](https://platform.openai.com/docs/guides/structured-outputs))
- Função equivalente em function calling com `strict: true`. ([anúncio OpenAI](https://openai.com/index/introducing-structured-outputs-in-the-api/))

**(b) Anthropic — tool use / Structured Outputs** `[VERIFICADO]`
- **Structured Outputs ficou GA** (saiu do beta inicial de 14/nov/2025). Hoje: `output_config.format` com `type: "json_schema"` (o `output_format` + header `structured-outputs-2025-11-13` viraram legados, mas ainda funcionam por um período de transição). ([Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs))
- **Mecanismo:** compila o JSON schema em uma **gramática** e restringe a geração de tokens durante a inferência → "Always valid / Type safe / Reliable, no retries needed". ([docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs), [techbytes](https://techbytes.app/posts/claude-structured-outputs-json-schema-api/))
- **Dois recursos combináveis:** (1) *JSON Outputs* (formato da resposta) e (2) *Strict Tool Use* (`strict: true`, valida nome e inputs da tool). Podem ser usados juntos ou separados. ([docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs))
- SDK helpers: definir schema uma vez em **Pydantic** (Python) ou **Zod** (TS); `client.messages.parse(...)`. ([Towards Data Science](https://towardsdatascience.com/hands-on-with-anthropics-new-structured-output-capabilities/))
- **Limites/ressalvas relevantes p/ extração de documentos:** não suporta schemas recursivos, `$ref` externo, nem restrições numéricas (`minimum`/`maximum`) ou de string (`minLength`/`maxLength`/regex backreferences). Máx. 20 strict tools, 24 campos opcionais, timeout de compilação 180s. ([docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs))

**(c) Google Gemini — structured output** `[VERIFICADO]`
- Dois parâmetros na `generationConfig`: `responseMimeType: "application/json"` (ou `text/x.enum`) + `responseSchema` (JSON Schema). ([Gemini API docs](https://ai.google.dev/gemini-api/docs/structured-output))
- **Ressalva de ordenação:** se houver descrições/schema no prompt, a **ordem das propriedades deve bater** com `responseSchema`, senão pode gerar saída malformada. Campos são opcionais por padrão; usar `required` para forçar. ([Gemini API docs](https://ai.google.dev/gemini-api/docs/structured-output), [Firebase AI Logic](https://firebase.google.com/docs/ai-logic/generate-structured-output))
- Há relatos de comportamento inconsistente em alguns modelos/casos (ex.: structured output só ativando junto de function calling em certos cenários). ([Dylan Castillo — "the good, the bad and the ugly"](https://dylancastillo.co/posts/gemini-structured-outputs.html), [Google AI forum](https://discuss.ai.google.dev/t/gemini-responds-with-structured-json-like-output-only-when-function-calling-is-enabled/112993))

**(d) Constrained decoding open-source** `[VERIFICADO]`
- **vLLM guided decoding:** parâmetros `guided_json` (JSON schema), `guided_regex`, `guided_choice`, `guided_grammar`. Backends plugáveis: **outlines**, **lm-format-enforcer**, **xgrammar**. ([vLLM Structured Outputs docs](https://docs.vllm.ai/en/v0.8.2/features/structured_outputs.html), [BentoML — Structured Decoding in vLLM](https://www.bentoml.com/blog/structured-decoding-in-vllm-a-gentle-introduction))
- **XGrammar:** engine via pushdown automaton + token-mask cache. **Backend default de vLLM, SGLang, TensorRT-LLM, MLC-LLM** (>5M downloads, MLSys 2025). ([repo](https://github.com/mlc-ai/xgrammar), [arXiv 2411.15100](https://arxiv.org/abs/2411.15100))
- **Outlines:** FSM-based; bom quando schemas são complexos e reusados em milhares de requisições (amortiza custo de compilação). ([dottxt/Outlines](https://www.aidancooper.co.uk/constrained-decoding/))
- **llama.cpp GBNF:** gramáticas GGML-BNF para forçar JSON/formatos arbitrários durante a decodificação. ([llama.cpp grammars README](https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md))
- **lm-format-enforcer:** mascara tokens inválidos (JSON Schema, regex); 1ª requisição rápida mas steady-state mais lento em schemas complexos; menos completo que Outlines/XGrammar em alguns casos de contexto longo. ([repo](https://github.com/noamgat/lm-format-enforcer), [PyPI](https://pypi.org/project/lm-format-enforcer/))

### 2. Constrained decoding garante schema válido? Overhead?

- **Garantia:** sim, **conformidade sintática + estrutural é garantida** porque é imposta na decodificação, não pedida no prompt. OpenAI: **100%** num eval de JSON schema complexo (vs. **<40%** sem); function calling tradicional ~86%. ([anúncio OpenAI](https://openai.com/index/introducing-structured-outputs-in-the-api/), [DEV — guaranteed outputs](https://dev.to/mattlewandowski93/guaranteed-structured-outputs-with-openai-5g0i)) `[VERIFICADO]`
  - **Caveat:** garante o *formato*, não a *correção semântica* do valor extraído (um campo pode ser válido pelo schema e ainda assim conter dado errado). `[INFERÊNCIA]`
- **Overhead de latência:**
  - **XGrammar:** **<40 µs/token**; ~99% do vocabulário é context-independent e pré-computável em bitmask, só ~1% precisa de inspeção em runtime → **near-zero overhead** end-to-end; **até 100x** de speedup vs. soluções anteriores de constrained decoding. ([arXiv 2411.15100](https://arxiv.org/pdf/2411.15100), [Yixin Dong / MLSys 2025](https://mlsys.org/virtual/2025/poster/3235)) `[VERIFICADO]`
  - **Pode ser MAIS RÁPIDO que geração livre:** *coalescence* (dottxt) pula tokens fixos do schema → relatado **até 5x** vs. geração vanilla. ([dottxt — Coalescence](https://blog.dottxt.ai/coalescence.html)) `[VERIFICADO]`
  - **Custo único:** compilação da gramática na 1ª requisição adiciona latência; Anthropic **cacheia a gramática compilada por 24h**. ([Claude docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)) `[VERIFICADO]`
  - **Tokens de input:** providers gerenciados injetam um system prompt explicando o formato → leve aumento de input tokens. ([Claude docs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)) `[VERIFICADO]`

### 3. Impacto na acurácia — os dois lados

**Lado "prejudica" — *Let Me Speak Freely?* (Tam et al., EMNLP 2024 Industry):** `[VERIFICADO]`
- Restrições de formato (especialmente **JSON-mode**) **degradam tarefas de raciocínio**; quanto mais estrita a restrição, maior a queda. Causa apontada: **misordering** das chaves de raciocínio e resposta final. Em **classificação** (slot-filling, intent) o formato **ajuda**. Mitigação proposta: **NL-to-Format** (responder em linguagem natural e depois converter) — i.e., o próprio paper sugere desacoplar conteúdo de formato. ([arXiv 2408.02442](https://arxiv.org/abs/2408.02442), [ACL Anthology](https://aclanthology.org/2024.emnlp-industry.91/))

**Lado "ajuda / não prejudica" — refutação da dottxt ("Say What You Mean", nov/2024):** `[VERIFICADO]`
- Reimplementando os evals com **prompts idênticos** entre as condições e **parser regex** (em vez do "AI parser" que inflava o caso unstructured), structured output **empata ou supera**:
  - GSM8K **0.77 → 0.78**; Last Letter **0.73 → 0.77**; Shuffle Object **0.41 → 0.44**.
  - Last Letter: NL estruturado 68% < JSON unstructured 73% < **JSON structured 77%**.
- Críticas metodológicas: prompts diferentes entre condições; prompt JSON do paper nem mencionava JSON/schema; "AI parser" enviesado; confusão entre "JSON-mode" e structured generation real. ([dottxt — Say What You Mean](https://blog.dottxt.ai/say-what-you-mean.html))

**Síntese prática (consenso 2025–2026):** o trade-off de raciocínio é **resolvido dentro de uma única chamada** colocando um campo de **reasoning/scratchpad livre ANTES** dos campos finais no schema (o modelo "pensa" e depois preenche), em vez de uma 2ª chamada. Para **extração de documentos** (tarefa mais próxima de slot-filling/classificação do que de raciocínio multi-hop), a evidência favorece **ganho ou neutralidade** de acurácia. ([Medium — Beyond Free-Form Text](https://medium.com/@brijeshrn/beyond-free-form-text-how-constrained-decoding-is-reshaping-structured-generation-in-llms-5f7a38bef259), [tetrate.io — LLM output parsing](https://tetrate.io/learn/ai/llm-output-parsing-structured-generation)) `[INFERÊNCIA]`

### 4. Economia ao eliminar a 2ª chamada

- O pipeline atual = **2 inferências** (interpretação + formatação JSON). Single-pass com structured output = **1 inferência** → corte de ~**50% da latência e do custo atribuíveis à etapa de formatação**. `[INFERÊNCIA — aritmética direta do "de 2 para 1 chamada"]`
- Ganhos adicionais que reforçam a economia:
  - **Sem retry/validação/parsing de erro** (constrained decoding elimina classes inteiras de falha). ([getmaxim.ai 2026 guide](https://www.getmaxim.ai/articles/reduce-llm-cost-and-latency-a-comprehensive-guide-for-2026/), [tetrate.io](https://tetrate.io/learn/ai/llm-output-parsing-structured-generation)) `[VERIFICADO]`
  - **Menos tokens de saída:** pedir saída estruturada em vez de explicação em NL reduz consumo de tokens (relatos de **20–30%**). ([getmaxim.ai](https://www.getmaxim.ai/articles/reduce-llm-cost-and-latency-a-comprehensive-guide-for-2026/)) `[VERIFICADO]`
  - **Compatível com Batch API** (-50% adicional) quando latência tolera. ([getmaxim.ai](https://www.getmaxim.ai/articles/reduce-llm-cost-and-latency-a-comprehensive-guide-for-2026/)) `[VERIFICADO]`
- **Caveat de custo:** providers gerenciados adicionam um pequeno overhead de input tokens (system prompt do formato); o saldo líquido continua fortemente positivo ao remover uma chamada inteira. `[INFERÊNCIA]`

---

## Tabela comparativa de abordagens

| Abordagem | Garantia de schema | Overhead de latência | Acurácia (extração) | Esforço de implementação |
|---|---|---|---|---|
| **OpenAI Structured Outputs** (`json_schema`, `strict`) | **Forte — 100% conformidade** ([OpenAI](https://openai.com/index/introducing-structured-outputs-in-the-api/)) | Baixo; constrained sampling gerenciado | Alta (slot-filling); usar campo reasoning p/ raciocínio | **Baixo** — só `response_format` |
| **OpenAI JSON mode** (`json_object`) | Médio — só **JSON válido**, não o schema | Baixo | Média (sem garantia de campos) | Muito baixo |
| **Anthropic Structured Outputs** (`output_config.format`) | **Forte — gramática + constrained decoding** ([Claude](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)) | Baixo; **+compilação 1ª req (cache 24h)** | Alta; SDK Pydantic/Zod | **Baixo** — schema + helper `.parse()` |
| **Anthropic Strict Tool Use** (`strict:true`) | Forte (nome+inputs da tool) | Baixo | Alta | Baixo |
| **Gemini `responseSchema`** | **Forte**, mas sensível à **ordem das props** ([Gemini](https://ai.google.dev/gemini-api/docs/structured-output)) | Baixo | Alta; relatos de inconsistência ([Castillo](https://dylancastillo.co/posts/gemini-structured-outputs.html)) | Baixo |
| **XGrammar** (vLLM/SGLang/TRT-LLM default) | **Forte — CFG/JSON** ([repo](https://github.com/mlc-ai/xgrammar)) | **Quase nulo, <40µs/tok; até 100x** vs. alternativas ([arXiv](https://arxiv.org/pdf/2411.15100)) | Alta | **Médio** — self-host inference |
| **Outlines** (FSM) | Forte | Baixo amortizado; coalescence **até 5x** vs. vanilla ([dottxt](https://blog.dottxt.ai/coalescence.html)) | Alta | Médio |
| **vLLM guided decoding** (`guided_json`) | Forte (depende do backend) | Baixo (XGrammar default) | Alta | Médio — self-host |
| **llama.cpp GBNF** | Forte (gramática BNF) | Baixo | Alta | Médio/Alto — escrever gramática |
| **lm-format-enforcer** | Forte; **falha em alguns long-context** ([repo](https://github.com/noamgat/lm-format-enforcer)) | 1ª req rápida, **steady-state mais lento** em schema complexo | Alta | Médio |
| **2 chamadas (baseline atual)** | Frágil (depende de prompt) | **~2x latência/custo** | Boa, mas cara | Baixo, porém ineficiente |

---

## Fontes (URLs)

**Provedores (oficial):**
- OpenAI Structured Outputs — docs: https://platform.openai.com/docs/guides/structured-outputs
- OpenAI — anúncio (100% vs <40%): https://openai.com/index/introducing-structured-outputs-in-the-api/
- Anthropic Claude Structured Outputs — docs: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- Gemini Structured Output — docs: https://ai.google.dev/gemini-api/docs/structured-output
- Firebase AI Logic (Gemini structured): https://firebase.google.com/docs/ai-logic/generate-structured-output

**Papers / benchmarks:**
- XGrammar (arXiv 2411.15100, MLSys 2025): https://arxiv.org/abs/2411.15100 · PDF: https://arxiv.org/pdf/2411.15100
- XGrammar MLSys poster: https://mlsys.org/virtual/2025/poster/3235
- "Let Me Speak Freely?" (arXiv 2408.02442, EMNLP 2024): https://arxiv.org/abs/2408.02442 · ACL: https://aclanthology.org/2024.emnlp-industry.91/
- dottxt — "Say What You Mean" (refutação): https://blog.dottxt.ai/say-what-you-mean.html
- dottxt — "Coalescence" (speedup): https://blog.dottxt.ai/coalescence.html

**Open-source / engenharia:**
- XGrammar repo: https://github.com/mlc-ai/xgrammar
- vLLM Structured Outputs: https://docs.vllm.ai/en/v0.8.2/features/structured_outputs.html
- BentoML — Structured Decoding in vLLM: https://www.bentoml.com/blog/structured-decoding-in-vllm-a-gentle-introduction
- lm-format-enforcer: https://github.com/noamgat/lm-format-enforcer · https://pypi.org/project/lm-format-enforcer/
- llama.cpp GBNF grammars: https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md
- Aidan Cooper — Constrained Decoding guide: https://www.aidancooper.co.uk/constrained-decoding/
- Let's Data Science — structured outputs explainer: https://letsdatascience.com/blog/structured-outputs-making-llms-return-reliable-json

**Custo/latência:**
- getmaxim.ai — Reduce LLM Cost and Latency (2026): https://www.getmaxim.ai/articles/reduce-llm-cost-and-latency-a-comprehensive-guide-for-2026/
- tetrate.io — LLM output parsing & structured generation: https://tetrate.io/learn/ai/llm-output-parsing-structured-generation
- Dylan Castillo — Gemini structured outputs (caveats): https://dylancastillo.co/posts/gemini-structured-outputs.html

---

## Lacunas (gaps a fechar com experimento na POC)

1. **Quantificação real da economia nos 3 documentos de teste** (CNH, conta CELPE, paper Claude 3). Os "~50%" são aritmética de "2→1 chamada"; falta medir latência/tokens/custo reais por documento (single-pass structured vs. baseline 2 passos). **A POC deve medir isso.**
2. **Acurácia de extração medida**, não só conformidade de schema: constrained decoding garante formato, **não** o valor correto. Precisa de ground-truth/field-level accuracy nos 3 docs, especialmente layout complexo (CELPE) e multipágina/charts (paper).
3. **Interação com VISÃO/multimodal:** quase toda a literatura de structured output é text-only. Falta evidência específica de constrained decoding sobre **VLMs** (extração direto da imagem/PDF) — relevante porque os 3 docs são imagens/PDF. Cruzar com Workstream de VLM/OCR.
4. **Gemini ordenação de propriedades + inconsistências:** confirmar empiricamente se afeta o caso de uso antes de recomendar Gemini.
5. **Limites de schema da Anthropic** (sem recursão, sem `min/max`, sem regex backreference): validar se o schema de extração alvo cabe nessas restrições; caso contrário, ajustar schema ou pós-validar.
6. **Self-hosted vs. gerenciado:** XGrammar/vLLM dão overhead quase nulo mas exigem GPU/infra; falta análise de TCO vs. API gerenciada para o volume esperado.
