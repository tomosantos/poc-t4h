# Workstream 3 — VLMs Single-Pass para Extração de Documentos

> Nota de pesquisa citada. Foco: substituir o pipeline LLM de 2 passos (interpretação + formatação JSON) por **um único modelo Vision-Language (VLM) que lê a imagem direto** (sem OCR separado). Objetivo: reduzir latência/custo mantendo acurácia em CNH, fatura de energia e paper acadêmico com gráficos.
>
> Data da pesquisa: 2026-06-26. Janela priorizada: 2024-2026. `[VERIF]` = número confirmado em fonte primária/benchmark; `[INFER]` = estimativa ou número de fonte secundária a validar.

---

## TL;DR (5 bullets)

1. **VLMs single-pass são viáveis e maduros (2024-2026).** Modelos como GPT-4o, Gemini 2.0 Flash, Claude 3.5 Sonnet/Haiku, e os open-source Qwen2.5-VL, InternVL2.5/3.5 leem a imagem do documento e emitem JSON estruturado em **uma só chamada**, colapsando o pipeline de 2 passos e eliminando o OCR externo. `[VERIF]`
2. **O OCR separado deixou de ser necessário em docs estruturados:** VLMs SOTA marcam DocVQA na faixa de **92-96%** e OCRBench >850/1000, igualando ou superando pipelines OCR+LLM em texto impresso. `[VERIF]`
3. **VLMs leem gráficos e tabelas melhor que OCR+LLM** porque interpretam o layout visual nativamente. ChartQA fica em **85-89%** nos modelos fortes — um pipeline OCR perde a estrutura visual do gráfico/eixos antes do LLM ver. `[VERIF parcial]`
4. **Modelos pequenos chegam muito perto dos grandes em docs estruturados.** Qwen2.5-VL-**7B** marca DocVQA **95.7** vs **96.4** do 72B (gap de 0.7 pt); ChartQA 87.3 vs 89.5 (gap ~2 pt). Para CNH/fatura, o 7B é praticamente equivalente ao 72B. `[VERIF]`
5. **O trade-off favorece os "Flash/mini/7B".** Gemini 2.0 Flash (~US$0,10-0,40/1M) e GPT-4o-mini (US$0,15/4,80) custam ~10-20x menos que GPT-4o, com latência sub-segundo a poucos segundos por página. **Recomendação:** modelo pequeno/Flash para CNH+fatura; reservar modelo grande (ou validação) só para o paper com gráficos densos. `[VERIF/INFER]`

---

## Achados

### 1. Panorama de modelos viáveis (single-pass, sem OCR externo)

**Proprietários (API):**
- **GPT-4o / GPT-4o-mini** (OpenAI): visão nativa, JSON mode + structured outputs. GPT-4o é o "grande" de referência; o mini é a opção de baixo custo. `[VERIF]`
- **Gemini 2.0 Flash** (Google): otimizado para baixa latência/custo, multimodal nativo, bom para processamento em lote de PDFs/imagens. Também há 1.5 Flash/Pro. `[VERIF]`
- **Claude 3.5 Sonnet / 3.5 Haiku** (Anthropic): forte em visão de documentos; Sonnet supera GPT-4o em DocVQA/ChartQA em algumas medições; Haiku é a variante barata. `[VERIF]`

**Open-source (self-host):**
- **Qwen2.5-VL** (3B/7B/72B): atual referência open em documento/OCR; 7B é o "sweet spot". `[VERIF]`
- **InternVL2.5 / InternVL3.5** (2B até 78B): top open em DocVQA/OCRBench. `[VERIF]`
- **Llama 3.2 Vision** (11B/90B): visão da Meta; competitivo mas atrás de Qwen/InternVL em OCR denso. `[INFER]`
- **MiniCPM-V** (~8B): "GPT-4V level no celular"; OCRBench 725, DocVQA 84.8 (V2.5). Forte custo/VRAM. `[VERIF]`
- **Phi-3.5-vision** (~4B): pequeno, eficiente, bom para edge; abaixo dos líderes em OCR denso. `[INFER]`
- **dots.ocr**: VLM especializado em parsing de documento (OCR + layout + chart), forte em DocVQA/ChartQA/InfoVQA mantendo capacidade VLM geral. Bom candidato a "parser de PDF". `[VERIF parcial]`

### 2. VLMs vs OCR+LLM em gráficos e tabelas

- **Tabelas:** VLMs preservam estrutura (~95%+ de layout preservado, saída markdown/HTML), enquanto OCR tradicional perde alinhamento de linhas/colunas a menos que colunas sejam pré-marcadas/templates. Isso é direto para a **fatura CELPE** (tabelas densas). `[VERIF qualitativo — f22labs]`
- **Gráficos:** a evidência quantitativa é o **ChartQA**, em que VLMs fortes marcam 85-89%. Um pipeline OCR+LLM **não** tem score nativo de ChartQA porque o OCR descarta a semântica visual do gráfico (eixos, barras, tendência) antes do LLM — o VLM "vê" o gráfico. Isso ataca diretamente a fraqueza citada no problema (leitura de gráficos do paper). `[VERIF parcial — inferência sobre o pipeline OCR]`
- **Ressalva:** em **OCR denso de texto puro** (muitas linhas pequenas, manuscrito, baixa resolução), pipelines OCR especializados (ou VLMs-OCR dedicados como dots.ocr, MinerU2.5, granite-docling) ainda podem ter vantagem de fidelidade caractere-a-caractere e latência. OCRBench v2 (com localização) ainda é difícil para VLMs gerais. `[VERIF]`

### 3. Trade-off custo × acurácia (números concretos)

- **Pequeno ≈ grande em doc estruturado:** Qwen2.5-VL-7B vs 72B → DocVQA **95.7 vs 96.4**; ChartQA **87.3 vs 89.5**. O gap (<1 pt em DocVQA) é irrelevante para CNH (form previsível) e pequeno para fatura. `[VERIF]`
- **Custo de API:** GPT-4o US$2,50/10 por 1M (in/out) vs **GPT-4o-mini US$0,15/0,80** (~16x mais barato no input) vs **Gemini 2.0 Flash ~US$0,10-0,30 input**. Claude 3.5 Haiku US$0,80/4,00. `[VERIF]`
- **Latência:** Qwen2.5-VL-7B ~**0,29 s/imagem** (servido localmente), 32B/72B >1 s/imagem. Em pipelines de parsing, modelos rápidos (granite-docling, MinerU2.5) <0,9 s/página; Qwen2.5-VL-3B via vLLM ~4,5 s/doc. APIs de doc parsing: Gemini 3 Flash ~2,41¢/página (0,65¢ com reasoning mínimo). `[VERIF/INFER — secundárias]`
- **Conclusão de trade-off:** para os 3 documentos do desafio, a estratégia ótima é **escalonada**: Flash/mini/7B para CNH e fatura (alta acurácia, custo ~10-20x menor, latência baixa); reservar modelo grande (GPT-4o/Claude Sonnet/Qwen-72B) **apenas** para o paper com gráficos complexos onde os ~2 pts de ChartQA importam. `[INFER — recomendação]`

---

## Tabela de Modelos

| Modelo | DocVQA | ChartQA | OCRBench | Custo (US$/1M in+out) ou VRAM | Latência/página | Tipo |
|---|---|---|---|---|---|---|
| **GPT-4o** | 92.8 `[V]` | 85.7 `[V]` | ~736 `[I]` | $2.50 / $10.00 `[V]` | ~1-3 s `[I]` | prop |
| **GPT-4o-mini** | ~ (alto) `[I]` | ~ `[I]` | ~ `[I]` | $0.15 / $0.80 `[V]` | <2 s `[I]` | prop |
| **Gemini 2.0 Flash** | 52.7* `[V]` | 68.5* `[V]` | 83.3*†  `[V]` | ~$0.10 / $0.40 `[V]` | sub-seg a ~2 s `[I]` | prop |
| **Claude 3.5 Sonnet** | 92.3-95.2 `[V]` | 89.0 `[V]` | — | $3.00 / $15.00 `[I]` | ~2-4 s `[I]` | prop |
| **Claude 3.5 Haiku** | — `[I]` | — | — | $0.80 / $4.00 `[V]` | <2 s `[I]` | prop |
| **Qwen2.5-VL-7B** | **95.7** `[V]` | 87.3 `[V]` | OCRBench_v2 56.3 `[V]` | ~16-20 GB (bf16) / ~8 GB (4-bit) `[I]` | ~0.29 s/img `[V]` | OSS |
| **Qwen2.5-VL-72B** | **96.4** `[V]` | 89.5 `[V]` | ~874 `[V]` | ~140+ GB (multi-GPU) `[I]` | >1 s/img `[V]` | OSS |
| **InternVL2.5-78B** | 95.1 `[V]` | 88.3 `[V]` | 854 `[V]` | multi-GPU (~160 GB bf16) `[I]` | >1 s `[I]` | OSS |
| **InternVL3.5-2B** | 89.4 `[V]` | — | — | ~4-6 GB `[I]` | rápido `[I]` | OSS |
| **Llama 3.2 Vision 11B/90B** | ~ `[I]` | ~ `[I]` | abaixo de Qwen `[I]` | 11B ~24 GB / 90B multi-GPU `[I]` | — | OSS |
| **MiniCPM-V 2.5 (~8B)** | 84.8 `[V]` | — | 725 `[V]` | ~8-16 GB / roda em celular `[V]` | rápido `[I]` | OSS |
| **Phi-3.5-vision (~4B)** | ~ `[I]` | ~ `[I]` | abaixo dos líderes `[I]` | ~8 GB `[I]` | rápido (edge) `[I]` | OSS |
| **dots.ocr** | forte `[V parcial]` | forte `[V parcial]` | forte `[V parcial]` | OSS (compacto) `[I]` | — | OSS |

`[V]` = verificado em fonte; `[I]` = inferido/secundário.
*Gemini 2.0 Flash (exp): os números 52.7 (DocVQA) / 68.5 (ChartQA) vêm de uma medição comparativa e parecem **baixos vs. o esperado** para a família Flash (1.5 Flash já marca DocVQA >89). Provável diferença de protocolo/prompt (zero-shot, sem ANLS calibrado) — **tratar com cautela e re-medir no POC**. †OCRBench 83.3 também sob esse protocolo.

---

## Fontes (URLs)

- Qwen2.5-VL benchmarks (DocVQA 95.7/96.4, ChartQA 87.3/89.5, OCRBench): https://qwen.ai/blog?id=qwen2.5-vl
- Qwen2.5-VL Technical Report (arXiv): https://arxiv.org/pdf/2502.13923
- Qwen2.5-VL-7B detalhes/benchmarks: https://www.emergentmind.com/topics/qwen2-5-vl-7b-model
- DocVQA Leaderboard (GPT-4o 92.8, Qwen 96.4/95.7): https://llm-stats.com/benchmarks/docvqa
- GPT-4o vs Gemini vs Claude (DocVQA/ChartQA: GPT-4o 92.8/85.7, Claude Opus 89.3/80.8): https://encord.com/blog/gpt-4o-vs-gemini-vs-claude-3-opus/
- Claude 3.5 Sonnet vs GPT-4o (DocVQA 92.3, ChartQA 89.0): https://www.vellum.ai/blog/claude-3-5-sonnet-vs-gpt4o
- Claude 3.5 Sonnet launch (visão supera GPT-4o): https://www.anthropic.com/news/claude-3-5-sonnet
- Gemini 2.0 Flash benchmarks (DocVQA 52.7, ChartQA 68.5, OCRBench 83.3 — protocolo a checar): https://atul4u.medium.com/beyond-text-extraction-the-2025-open-ocr-revolution-powered-by-vision-language-models-89ad33d36bbf
- Gemini 1.5 Technical Report (contexto Flash): https://arxiv.org/pdf/2403.05530
- InternVL2.5-78B (DocVQA 95.1, ChartQA 88.3, OCRBench 854): https://arxiv.org/html/2412.05271v1
- InternVL3.5 report (InternVL3.5-2B DocVQA 89.4): https://arxiv.org/html/2508.18265v1
- MiniCPM-V (DocVQA 84.8, OCRBench 725, "no celular"): https://arxiv.org/pdf/2408.01800
- OCRBench v2 (avaliação OCR de LMMs, localização): https://arxiv.org/html/2501.00321v2
- OmniDocBench (parsing de PDF página-a-página): https://arxiv.org/pdf/2412.07626
- dots.ocr / parsing multimodal (InfoVQA, DocVQA, ChartQA): https://arxiv.org/html/2603.13032v1
- OCR vs VLM — tabelas/layout (~95%+ preservado, VLM > OCR em estrutura): https://www.f22labs.com/blogs/ocr-vs-vlm-vision-language-models-key-comparison/
- Latência Qwen2.5-VL (7B 0.29 s/img; 3B vLLM 4.5 s/doc; parsing <0.9 s/pág): https://www.kunalganglani.com/blog/llm-api-latency-benchmarks-2026 / https://arxiv.org/pdf/2604.08538
- Custo de parsing por página (Gemini 3 Flash 2.41¢; 0.65¢ reasoning mínimo): https://arxiv.org/pdf/2604.08538
- Pricing APIs (GPT-4o $2.50/$10, mini $0.15/$0.80, Gemini Flash, Claude): https://intuitionlabs.ai/articles/llm-api-pricing-comparison-2025
- Gemini API pricing oficial: https://ai.google.dev/gemini-api/docs/pricing
- Claude pricing oficial (3.5 Haiku $0.80/$4.00): https://platform.claude.com/docs/en/about-claude/pricing

---

## Lacunas (a fechar no POC / próxima rodada)

1. **Gemini 2.0 Flash com números inconsistentes.** O 52.7 (DocVQA) / 68.5 (ChartQA) destoa do esperado da família Flash; precisa de fonte primária do Google (model card) ou medição própria no POC com os 3 docs. **Risco alto se a recomendação depender do Flash.**
2. **GPT-4o-mini, Claude 3.5 Haiku, Phi-3.5-vision, Llama 3.2 Vision:** faltam DocVQA/ChartQA/OCRBench numéricos verificados de fonte primária. Tabela tem `[I]`.
3. **Latência por página inconsistente entre fontes** (varia com self-host vs API, batch, vLLM, resolução da imagem). Não há um número único confiável "por página" comparável entre todos — **medir no POC** com CNH/fatura/paper reais.
4. **VRAM exato** depende de quantização (bf16 vs 4-bit/AWQ/GPTQ) e resolução máxima de imagem; números são estimativas de ordem de grandeza.
5. **Sem benchmark direto OCR+LLM vs VLM single-pass nos 3 docs do desafio** (CNH BR, fatura CELPE, paper Claude 3). Evidência de gráficos/tabelas é qualitativa (f22labs) + proxy ChartQA. **O POC deve gerar essa comparação head-to-head** (acurácia de campos, custo, latência) — é o que fecha a viabilidade.
6. **Acurácia de extração de CAMPO (KIE/JSON)** difere de DocVQA (QA). DocVQA alto não garante JSON perfeito; usar OCRBench (KIE) + métrica própria de campos no POC.
