# Design — Dossiê de Pesquisa + POC: Extração de Documentos (Tech4.ai)

**Data:** 2026-06-26
**Prazo de entrega:** 2026-07-01 23:59
**Autor:** Wellinton Oliveira Santos
**Status:** aprovado para implementação (pós-brainstorming)

---

## 1. Contexto e Problema

A Tech4.ai possui uma API de extração de dados de documentos (`POST https://api.tech4.ai/document/extract/`,
entrada `{file_url, layout_id}`, saída `{status, extracted_data}`). Hoje o motor usa um LLM em **dois passos**:
(1) interpretação/extração e (2) uma segunda inferência só para formatar o resultado no schema JSON do cliente.
Os campos são definidos num *visual builder* onde cada campo tem nome + tipo + **descrição em linguagem natural** —
esse é o "passo 1". A API tem validators determinísticos nativos (CPF, CNPJ, UF, Linha Digitável) e o exemplo
oficial da documentação é uma **CNH**.

**Dores declaradas no desafio (cenário fictício):**
- **Latência** — o processo de 2 etapas é lento.
- **Custo** — modelos de ponta a cada chamada são caros.
- **Complexidade** — documentos extensos (muitas páginas) e layouts complexos (tabelas aninhadas, formulários densos).
- **Limitações** — interpretação fraca de gráficos e imagens não-textuais.

**Objetivo da pesquisa:** identificar e validar uma abordagem alternativa que **reduza latência e custo** mantendo
ou aumentando a **acurácia** da extração.

**Documentos de teste** (`data/`):
| Arquivo | Conteúdo | Desafio para o pipeline |
|---------|----------|--------------------------|
| `Documento 1.jpeg` | CNH brasileira | Form estruturado, layout previsível |
| `Documento 2.jpg` | Fatura de energia CELPE | Layout complexo, tabelas, info densa |
| `Documento 3.pdf` | Paper "Claude 3 Model Family" | Multipágina, gráficos, imagens, texto acadêmico |

---

## 2. Tese Central (a ser confirmada empiricamente pela POC)

**Colapsar 2 inferências → 1, via VLM single-pass + structured output (constrained decoding).**

Cadeia de evidências (ver `docs/`):
1. **A 2ª chamada é eliminável.** Constrained decoding (Structured Outputs da OpenAI/Anthropic GA, `responseSchema`
   do Gemini; XGrammar/Outlines no OSS) **garante** JSON conforme ao schema numa única passada, com overhead de
   latência quase nulo (XGrammar <40µs/token). `docs/02`.
2. **O `layout_id` já É o JSON Schema.** O builder da Tech4.ai vira a fonte do schema; validators viram
   pós-processamento determinístico. Integração natural. `docs/02` + `docs/06`.
3. **Modelos pequenos bastam.** Qwen2.5-VL-7B: DocVQA 95.7 vs 96.4 do 72B (gap <1pt); Gemini Flash / GPT-4o-mini
   custam ~10–20x menos que topo de linha. `docs/03`.
4. **VLM lê gráfico melhor que OCR+LLM** (ChartQA 85–89%) porque interpreta o layout visual nativamente — ataca a
   4ª dor. `docs/01` + `docs/03`.

A tese ataca **as 4 dores simultaneamente**: latência (1 chamada), custo (modelo pequeno + 1 chamada), layouts
complexos (VLM nativo), gráficos (visão).

---

## 3. Shortlist de Técnicas (Seção 3 do dossiê)

| | Técnica | Prós | Contras |
|--|---------|------|---------|
| **A** | VLM proprietário pequeno + structured output (Gemini Flash / GPT-4o-mini) | Menor esforço, sem infra, corta latência+custo | Dependência de fornecedor, custo por chamada |
| **B** | VLM open-source self-hosted (Qwen2.5-VL-7B) + structured output | Custo marginal ~zero em escala, dados on-prem (LGPD) | Exige GPU, manutenção, MLOps |
| **C** | Document AI gerenciado (Azure/Google Layout → markdown) + LLM pequeno | Conservador, próximo do baseline, robusto a scans ruins | 2 sistemas, OCR perde semântica de gráficos (exceto Google Layout Parser+Gemini) |

**Recomendação provável:** A como caminho de menor risco/maior velocidade de entrega, com B como rota de
otimização de custo em escala. A POC valida A (e mede B via proxy de API). Conclusão final fica condicionada
aos resultados.

---

## 4. Framework de Métricas (Seção 4 do dossiê)

- **Qualidade de extração:** Field-F1 / exact-match para campos key-value; avaliação de fidelidade via **LLM-as-judge**
  (modelo forte julga extração contra o documento). Calibração: conjunto manual dos 6 campos da CNH para reportar
  concordância juiz↔humano (mitiga viés do avaliador). Para tabelas/markdown: avaliação qualitativa + spot-check.
- **Latência:** medida no POC (wall-clock por documento, p50). Benchmarks de terceiros não padronizam latência.
- **Custo:** `usage.cost` retornado automaticamente pelo OpenRouter por request (US$/documento).
- **Benchmarks de terceiros** (fundamentam o que não dá pra testar): DocVQA, FUNSD, CORD, SROIE, ChartQA,
  OmniDocBench. `docs/01`.

---

## 5. Desenho da POC

**Stack:** Python, SDK `openai` apontando para OpenRouter (`base_url=https://openrouter.ai/api/v1`), sem GPU local.
Servida em **Docker**. Camada visual em **Streamlit**.

### 5.1 Estrutura de código
```
extractor/          # núcleo reutilizável
  client.py         # cliente OpenRouter: single-pass + response_format json_schema strict
  schemas.py        # layout/campos → JSON Schema (por documento)
  validators.py     # CPF/CNPJ determinísticos (espelha Tech4.ai)
  pipeline.py       # orquestra extração; suporta modo 2-step (baseline) e 1-step
api/                # FastAPI: POST /extract → {status, extracted_data}  (contrato Tech4.ai)
ui/                 # Streamlit: upload do doc + imagem e JSON lado a lado
benchmark/          # harness do experimento → tabela do dossiê
  run.py            # roda matriz modelo×documento×{braço}, coleta latência/custo
  judge.py          # LLM-as-judge para acurácia de fidelidade
data/               # os 3 documentos (já presentes)
Dockerfile
docker-compose.yml  # sobe API + UI
requirements.txt
.env.example        # OPENROUTER_API_KEY
```

### 5.2 Experimento central — demonstra a tese "2→1"
| Braço | O que faz | Mede |
|------|-----------|------|
| Baseline (2-step) | Chamada 1: extração livre → Chamada 2: formata em JSON | latência + custo (soma) |
| Recomendado (1-step) | 1 chamada com `response_format: json_schema, strict:true` | latência + custo + Δ vs baseline |

**Matriz de modelos** (todos via OpenRouter, todos single-pass exceto o braço baseline):
`google/gemini-2.5-flash-lite`, `openai/gpt-4o-mini`, `qwen/qwen2.5-vl-72b-instruct` (proxy do cenário OSS
self-hosted sem GPU local), opcional `anthropic/claude-3.5-haiku`.

### 5.3 Por documento
- **CNH** — schema com 6 campos (Nome, CPF, Data de Nascimento, Data de emissão, filiação pai, filiação mãe) +
  validator de CPF como pós-processamento. Ground truth manual (calibração do juiz).
- **Fatura CELPE** — campos-chave + tabela de consumo, preservando organização. Entrada como imagem.
- **Paper Claude 3** — PDF multipágina via plugin file-parser do OpenRouter → markdown preservando tabelas +
  interpretação de 1–2 gráficos.

### 5.4 Saídas da POC
- Tabela `modelo × documento × {latência p50, custo/doc, acurácia (juiz)}`.
- Δ baseline-vs-single-pass (o argumento quantitativo central).
- App Docker demonstrável (Streamlit + FastAPI espelhando o contrato Tech4.ai).

---

## 6. Estrutura do Dossiê (Entregável 1 — 80%)

Espelha as 6 seções obrigatórias do desafio e as convenções do TCP de referência (`example/`):

1. **Introdução** — problema de negócio (API Tech4.ai 2-step e as 4 dores) + objetivo da pesquisa.
2. **Metodologia** — varredura paralela de pesquisa, fontes (`docs/` citadas), o que foi descartado rápido e por
   quê, e **uso de ferramentas de IA** (declarar Claude Code de forma honesta e específica).
3. **Técnicas e Modelos Avaliados** — shortlist A/B/C com trade-offs.
4. **Resultados e Experimentos** — framework de métricas + tabela da POC + tabela de benchmarks de terceiros;
   gráficos de trade-off (custo×acurácia×latência).
5. **Conclusão e Recomendação** — defesa do single-pass VLM pequeno + structured output, com escalonamento para
   documentos com gráficos densos.
6. **Análise de Viabilidade de Integração** — custo de infra (API vs self-host GPU: tipo de GPU/VRAM, US$/hora),
   arquitetura, e **como pluga na Tech4.ai** (preserva envelope `{status, extracted_data}`, reusa `layout_id`→schema,
   mantém validators determinísticos, mesmo contrato de transporte; troca só o motor 2-LLM → 1-VLM).

**Idioma:** Português (alinhado ao TCP de referência e ao público Tech4.ai). Termos técnicos em inglês preservados.
**Estilo:** comparar com `example/TCP de Wellinton Oliveira Santos.pdf` para estrutura, tom, densidade técnica e
convenções visuais (figuras, tabelas, legendas).

---

## 7. Ameaças à Validade (a declarar no dossiê)

- **n=3 documentos** — amostra pequena; resultados são ilustrativos, não estatisticamente significativos.
- **Viés do avaliador (LLM-as-judge)** — mitigado por conjunto de calibração manual na CNH e por declarar o juiz usado.
- **Latência não padronizada** — medições do POC dependem de rede/fila do OpenRouter; reportar p50 e condições.
- **Qwen via API ≠ self-host** — o braço B é um *proxy*; o custo real de self-hosting é estimado por benchmark, não medido.
- **Benchmarks de terceiros** podem usar protocolos diferentes; usados como apoio, não como medida direta dos 3 docs.

---

## 8. Riscos de Execução / Cronograma (~5 dias)

| Dia | Foco |
|-----|------|
| 1 | Fechar pesquisa (feito), montar esqueleto da POC (engine + API + Streamlit + Docker) |
| 2 | Rodar experimento (matriz modelo×doc×braço), coletar latência/custo, implementar juiz |
| 3 | Consolidar resultados, gráficos; rascunho das Seções 1–4 do dossiê |
| 4 | Seções 5–6 (recomendação + viabilidade), revisão de rigor e estilo vs TCP |
| 5 | Polimento do dossiê (PDF), README da POC, repositório Git, buffer |

**80/20 mantido:** a engine da POC é enxuta; o esforço maior vai para análise e escrita do dossiê.

---

## 9. Lacunas Abertas (resolver durante a execução)

- Validar IDs/preços de modelos no OpenRouter no momento da execução (alguns slugs mudam; `docs/07`).
- Confirmar limite de páginas do plugin file-parser para o paper (28 MB / multipágina).
- Definir o conjunto exato de campos da fatura CELPE ao inspecionar o documento.
- Modelo juiz a usar (ex.: GPT-4o ou Gemini 2.5 Pro) e o prompt de julgamento.

---

## 10. Notas de Pesquisa (fontes)

Toda a fundamentação está em `docs/`:
- `01-baseline-e-metricas.md` — métricas e benchmarks
- `02-structured-output.md` — constrained decoding / eliminar a 2ª chamada
- `03-vlms-single-pass.md` — VLMs e trade-off custo×acurácia
- `04-modelos-especializados.md` — OCR-free / layout / pipelines OSS
- `05-document-ai-gerenciado.md` — Textract / Azure / Google Doc AI
- `06-baseline-tech4ai-api.md` — caracterização da API atual
- `07-openrouter-capacidades.md` — capacidades e sintaxe do OpenRouter
