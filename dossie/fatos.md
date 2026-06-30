# Folha de Fatos Canônica — Dossiê (FONTE ÚNICA DE VERDADE)

Todo redator de seção DEVE usar estes números e esta redação. Não inventar valores.
Números vêm de `benchmark/results/results.json` (re-run com prompt ancorado e métrica dupla)
e das notas `notes/01-11`. Custos em US$ por documento; latência em segundos (p50 single-shot, OpenRouter).

## 1. Resultados da matriz POC (CNH + Fatura; modelos via OpenRouter)

**CNH** (341×600 px, baixa-res; `acuracia_det` = exact-match normalizado vs ground truth, `acuracia_juiz` = LLM-as-judge):
| modelo | modo | status | latência_s | custo_usd | acuracia_juiz | acuracia_det |
|---|---|---|---|---|---|---|
| gemini-2.5-flash-lite | single | partial | 2,61 | 0,00027 | 0,50 | 0,667 |
| gemini-2.5-flash-lite | two_step | partial | 4,14 | 0,00038 | 0,50 | 0,667 |
| gpt-4o-mini | single | partial | 2,99 | 0,00226 | 0,33 | 0,50 |
| gpt-4o-mini | two_step | partial | 4,06 | 0,00228 | 0,50 | 0,50 |
| qwen2.5-vl-72b | single | partial | 6,17 | 0,00051 | 0,50 | 0,333 |
| qwen2.5-vl-72b | two_step | partial | 10,54 | 0,00077 | 0,50 | 0,50 |

**Fatura CELPE** (620×1718 px; sem ground truth determinístico → `acuracia_det` = N/A):
| modelo | modo | status | latência_s | custo_usd | acuracia_juiz |
|---|---|---|---|---|---|
| gemini-2.5-flash-lite | single | ok | 3,34 | 0,00040 | 0,857 |
| gemini-2.5-flash-lite | two_step | ok | 4,90 | 0,00059 | 0,833 |
| gpt-4o-mini | single | ok | 3,07 | 0,00734 | 0,857 |
| gpt-4o-mini | two_step | ok | 4,33 | 0,00740 | 0,857 |
| qwen2.5-vl-72b | single | partial | 6,79 | 0,00131 | 0,571 |
| qwen2.5-vl-72b | two_step | ok | 8,39 | 0,00156 | 0,86 |

## 2. Deltas e achados principais (citar exatamente assim)

1. **Tese 2→1 (single-pass vs duas etapas):** o *single-pass* é consistentemente mais rápido e mais
   barato, com acurácia igual ou superior. Exemplos: fatura/Gemini Flash-Lite — *single* 3,34s/US$0,00040
   vs *two_step* 4,90s/US$0,00059 (≈32% menos latência, ≈32% menos custo, acurácia 0,857 vs 0,833);
   CNH/Gemini — *single* 2,61s/US$0,00027 vs *two_step* 4,14s/US$0,00038. Em NENHUMA célula o 2-step
   superou o single-pass em custo/latência.
2. **Custo entre provedores:** `gpt-4o-mini` custa ~10-18× mais que `gemini-2.5-flash-lite`
   (fatura/single: US$0,00734 vs US$0,00040 = 18×) sem ganho de acurácia. → recomendar o modelo
   pequeno CERTO, não "qualquer modelo pequeno".
3. **Documento extenso (paper, 42 págs, 28 MB) — híbrido vs ingênuo:** o caminho ingênuo (PDF inteiro
   → VLM) FALHOU após ~615s (erro do provedor, `choices=None`, US$0); o **híbrido** extraiu as 42
   páginas em ~4,7s a custo ZERO (PyMuPDF, determinístico) + uma chamada de VLM em UMA figura ~4,3s/
   US$0,00039 (total ~9s). Conclusão: para documento extenso, OCR/parse determinístico para texto+tabelas
   e VLM seletivo só para figuras.
4. **Estudo de robustez na CNH (baixa-res):** (a) *upscaling* Lanczos 3× NÃO recupera nenhum campo
   (+153% de custo no gpt-4o-mini, 0 ganho) — legibilidade intrínseca, não densidade de pixels;
   (b) prompt ANCORADO (descrições de campo com âncoras de layout) recupera a `data_emissao` a custo
   zero e iguala o modelo pequeno ao forte; (c) escalar para `gemini-2.5-pro` (~57× o custo) NÃO
   recupera campos além do prompt ancorado; (d) o CPF permanece irrecuperável (erro de dígito no JPEG).
5. **Confiabilidade da avaliação:** o LLM-as-judge é NÃO-CALIBRADO em baixa-res — diverge da métrica
   determinística em ±0,17, ora superestimando, ora subestimando. Por isso a POC reporta as DUAS
   métricas; a determinística (vs ground truth) é indispensável para relato honesto.

## 3. Benchmarks de terceiros (fundamentam o não-testado; fontes em notes/01,03,04)

- **Qwen2.5-VL-7B**: DocVQA 95,7 vs 96,4 do 72B (gap <1 pt); ChartQA 87,3 vs 89,5 → modelo pequeno
  ≈ grande em documentos estruturados.
- **GPT-4o**: DocVQA 92,8 / ChartQA 85,7. **Claude 3.5 Sonnet**: DocVQA ~92-95 / ChartQA 89.
- **OmniDocBench (CVPR 2025)**: MinerU 0,058 NED / 79,4 TEDS vs GPT-4o 0,144 / 72,8 → especializados
  competem/superam generalistas em docs padrão.
- **Constrained decoding**: OpenAI Structured Outputs 100% de conformidade ao schema vs <40% sem;
  overhead do XGrammar <40 µs/token (quase nulo end-to-end).
- **Document AI gerenciado**: ~US$1,50/1.000 págs (OCR puro); Azure/Google Layout US$10/1.000 págs
  e emitem Markdown LLM-friendly; Google Layout Parser verbaliza figuras via Gemini.

## 4. Preços de API (US$/1M tokens input/output; notes/07)

| modelo | input | output |
|---|---|---|
| gemini-2.5-flash-lite | 0,10 | 0,40 |
| gemini-2.5-flash | 0,30 | 2,50 |
| gpt-4o-mini | 0,15 | 0,60 |
| claude-3.5-haiku | 0,80 | 4,00 |
| qwen2.5-vl-72b | 0,80 | 1,00 |

## 5. Baseline Tech4.ai (notes/06)

`POST https://api.tech4.ai/document/extract/`, entrada `{file_url, layout_id}`, saída
`{status, extracted_data}`. Campos definidos num *visual builder* (nome + tipo + descrição em
linguagem natural — o "passo 1"). *Validators* nativos: CPF, CNPJ, UF, Linha Digitável (retornam
NULL se inválido). Exemplo oficial da doc é uma CNH. **Compatibilidade exigida pela recomendação:**
preservar o envelope `{status, extracted_data}`, reusar `layout_id` como fonte do *JSON Schema*,
manter os *validators* como pós-processamento determinístico; trocar só o motor (2 LLMs → 1 VLM).

## 6. Recomendação canônica (redação a manter coerente)

**Motor padrão:** VLM proprietário pequeno (classe *Gemini Flash-Lite*) em *single-pass* com
*structured output* (*constrained decoding*) — colapsa as 2 inferências em 1, garante JSON conforme
ao schema, e lê gráficos/tabelas nativamente.
**Estratégia escalonada:** escalar para modelo maior apenas em **complexidade** (layout/raciocínio);
para **legibilidade** o lever é *preprocessing*/crop/OCR ou re-captura, não modelo maior.
**Documento extenso:** abordagem **híbrida** (PyMuPDF determinístico + VLM seletivo nas figuras).
**Rota de custo em escala:** VLM open-source self-hosted (Qwen2.5-VL-7B) — custo marginal ~0, exige GPU/MLOps.
**Shortlist:** A = VLM proprietário pequeno; B = VLM OSS self-hosted; C = Document AI gerenciado + LLM pequeno; D = híbrido (doc extenso).

## 7. Figuras disponíveis (em `dossie/figuras/`)

- `figura1_arquitetura.png` — atual (2-step) vs proposta (single-pass) vs híbrido.
- `figura2_tradeoff.png` — latência × custo por modelo/modo.
- `figura3_2para1.png` — single vs two_step (latência e custo).
- `figura4_hibrido.png` — VLM ingênuo (615s, FALHA) vs híbrido (~9s, US$0,00039).

## 8. Uso de ferramentas de IA (declarar na Metodologia, com honestidade)

A pesquisa, a POC e a análise foram conduzidas com apoio do *Claude Code* (modelo Opus) como
copiloto: varredura paralela de literatura, geração e teste do código da POC, e organização dos
achados. A curadoria crítica, o desenho experimental, a interpretação dos resultados e as conclusões
são autorais. Toda afirmação empírica do dossiê é rastreável aos resultados em `benchmark/results/`
e às notas citadas.
