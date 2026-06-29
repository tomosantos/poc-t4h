# Design — Dossiê de Pesquisa + POC: Extração de Documentos (Tech4.ai)

**Data:** 2026-06-26 (atualizado com achados empíricos em 2026-06-28)
**Prazo de entrega:** 2026-07-01 23:59
**Autor:** Wellinton Oliveira Santos
**Status:** implementado; achados empíricos consolidados

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

Cadeia de evidências (ver `notes/`):
1. **A 2ª chamada é eliminável.** Constrained decoding (Structured Outputs da OpenAI/Anthropic GA, `responseSchema`
   do Gemini; XGrammar/Outlines no OSS) **garante** JSON conforme ao schema numa única passada, com overhead de
   latência quase nulo (XGrammar <40µs/token). `notes/02`.
2. **O `layout_id` já É o JSON Schema.** O builder da Tech4.ai vira a fonte do schema; validators viram
   pós-processamento determinístico. Integração natural. `notes/02` + `notes/06`.
3. **Modelos pequenos bastam.** Qwen2.5-VL-7B: DocVQA 95.7 vs 96.4 do 72B (gap <1pt); Gemini Flash / GPT-4o-mini
   custam ~10–20x menos que topo de linha. `notes/03`.
4. **VLM lê gráfico melhor que OCR+LLM** (ChartQA 85–89%) porque interpreta o layout visual nativamente — ataca a
   4ª dor. `notes/01` + `notes/03`.

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

A POC reporta **duas métricas de acurácia**:

- **`acuracia_det`** (determinística) — exact-match normalizado campo a campo contra o ground truth manual.
  Aplicada somente onde existe rótulo: **CNH** (6 campos). Insensível a caixa; normalização de acentos aplicada.
- **`acuracia_juiz`** (LLM-as-judge) — modelo forte (`openai/gpt-4o`) julga fidelidade da extração ao documento,
  campo a campo. Aplicada a todos os documentos.

**Observação crítica sobre calibração do juiz:** nos experimentos com a CNH (imagem de baixa resolução, 341×600 px),
o juiz demonstrou-se **não-calibrado** — gap de ±0,17 entre `acuracia_juiz` e `acuracia_det`, ora superestimando
(ex.: gpt-4o-mini juiz=0,50 vs det=0,50; Gemini juiz=0,50 vs det=0,67; mas em diagnóstico isolado gpt-4o-mini
juiz=0,83 vs det≈0,17), ora subestimando. O juiz tende a aprovar valores incorretos quando a própria imagem fonte
é de difícil leitura. **Conclusão metodológica:** a métrica determinística é indispensável para documentos com
ground truth disponível; o juiz isolado é insuficiente em cenários de baixa resolução. `notes/08`.

- **Latência:** wall-clock por documento (p50), medida no POC.
- **Custo:** `usage.cost` retornado pelo OpenRouter por request (US$/documento).
- **Benchmarks de terceiros** (fundamentam o que não dá pra testar): DocVQA, FUNSD, CORD, SROIE, ChartQA,
  OmniDocBench. `notes/01`.

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
  pdf_extract.py    # extração determinística de texto+tabelas via PyMuPDF (custo zero)
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
  validator de CPF como pós-processamento. Ground truth manual (calibração do juiz). Usa **prompt ancorado** por
  padrão: cada campo inclui descrição de âncora de layout (ex.: "'data_nascimento' está no campo rotulado
  'DATA NASC.'"), reduzindo confusão entre as múltiplas datas presentes na CNH.
- **Fatura CELPE** — campos-chave + tabela de consumo, preservando organização. Entrada como imagem.
- **Paper Claude 3** — abordagem **híbrida**: `extractor/pdf_extract.py` (PyMuPDF) extrai texto e tabelas de
  todas as 42 páginas de forma determinística (latência ~5s, custo zero); o VLM é acionado apenas para interpretar
  figuras selecionadas (ex.: página 7, ~$0,0004). Abordagem ingênua de enviar o PDF inteiro (28 MB / 42 págs) ao
  VLM falha com erro do provedor (choices=None, 615s). `benchmark/results/paper_hibrido.md`.

### 5.4 Saídas da POC
- Tabela `modelo × documento × {latência p50, custo/doc, acuracia_juiz, acuracia_det}`.
- Δ baseline-vs-single-pass (o argumento quantitativo central).
- App Docker demonstrável (Streamlit + FastAPI espelhando o contrato Tech4.ai).

### 5.5 Nuance sobre escalabilidade de modelo

Os experimentos evidenciam que **escalar para modelo maior compensa em problemas de complexidade** (layouts
elaborados, raciocínio estrutural), mas **não em problemas de legibilidade** — onde o gargalo é a resolução da
imagem fonte, não a capacidade do modelo. Para a CNH (341×600 px), gemini-2.5-pro (~57× o custo do flash-lite)
não recupera nenhum campo adicional; o lever correto é preprocessing (upscaling, crop, OCR dedicado) ou
re-captura do documento. `notes/09`, `notes/10`. Essa nuance equilibra a tese "tecnologia mais nova vs. solução
mais viável" e deve ser explicitada na recomendação final do dossiê.

---

## 6. Estrutura do Dossiê (Entregável 1 — 80%)

Espelha as 6 seções obrigatórias do desafio e as convenções do TCP de referência (`example/`):

1. **Introdução** — problema de negócio (API Tech4.ai 2-step e as 4 dores) + objetivo da pesquisa.
2. **Metodologia** — varredura paralela de pesquisa, fontes (`notes/` citadas), o que foi descartado rápido e por
   quê, e **uso de ferramentas de IA** (declarar Claude Code de forma honesta e específica).
3. **Técnicas e Modelos Avaliados** — shortlist A/B/C com trade-offs.
4. **Resultados e Experimentos** — framework de métricas (dupla: determinística + juiz) + tabela da POC +
   tabela de benchmarks de terceiros; gráficos de trade-off (custo×acurácia×latência).
5. **Conclusão e Recomendação** — defesa do single-pass VLM pequeno + structured output, com escalonamento para
   documentos com gráficos densos e nuance legibilidade vs. complexidade (§5.5).
6. **Análise de Viabilidade de Integração** — custo de infra (API vs self-host GPU: tipo de GPU/VRAM, US$/hora),
   arquitetura, e **como pluga na Tech4.ai** (preserva envelope `{status, extracted_data}`, reusa `layout_id`→schema,
   mantém validators determinísticos, mesmo contrato de transporte; troca só o motor 2-LLM → 1-VLM).

**Idioma:** Português (alinhado ao TCP de referência e ao público Tech4.ai). Termos técnicos em inglês preservados.
**Estilo:** comparar com `example/TCP de Wellinton Oliveira Santos.pdf` para estrutura, tom, densidade técnica e
convenções visuais (figuras, tabelas, legendas).

---

## 7. Ameaças à Validade (a declarar no dossiê)

- **n=3 documentos** — amostra pequena; resultados são ilustrativos, não estatisticamente significativos.
- **Viés do avaliador (LLM-as-judge) em baixa resolução** — o juiz demonstrou-se não-calibrado para a CNH
  (341×600 px): gap ±0,17 vs. acurácia determinística, aprovando valores incorretos quando a imagem fonte é de
  difícil leitura. Mitigado pela métrica determinística paralela; documentado em `notes/08`.
- **CPF da CNH irrecuperável no JPEG** — o dígito do CPF é ilegível no arquivo 341×600 px por limitação de
  legibilidade intrínseca da imagem; upscaling Lanczos não ajuda e modelos maiores também falham. A solução
  correta é preprocessing/OCR ou re-captura, não escalar o modelo. `notes/09`.
- **Fatura sem ground-truth determinístico** — sem rótulo manual, a fatura CELPE é avaliada apenas pelo juiz
  (`acuracia_juiz`); a métrica determinística não se aplica a esse documento.
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

- Validar IDs/preços de modelos no OpenRouter no momento da execução (alguns slugs mudam; `notes/07`).
- Confirmar limite de páginas do plugin file-parser para o paper (28 MB / multipágina).
- Definir o conjunto exato de campos da fatura CELPE ao inspecionar o documento.
- Modelo juiz a usar (ex.: GPT-4o ou Gemini 2.5 Pro) e o prompt de julgamento.

---

## 10. Notas de Pesquisa (fontes)

Toda a fundamentação está em `notes/`:
- `01-baseline-e-metricas.md` — métricas e benchmarks
- `02-structured-output.md` — constrained decoding / eliminar a 2ª chamada
- `03-vlms-single-pass.md` — VLMs e trade-off custo×acurácia
- `04-modelos-especializados.md` — OCR-free / layout / pipelines OSS
- `05-document-ai-gerenciado.md` — Textract / Azure / Google Doc AI
- `06-baseline-tech4ai-api.md` — caracterização da API atual
- `07-openrouter-capacidades.md` — capacidades e sintaxe do OpenRouter
- `08-diagnostico-cnh.md` — diagnóstico de baixa acurácia na CNH; não-calibração do juiz
- `09-teste-upscaling-cnh.md` — upscaling Lanczos não melhora legibilidade; +153% custo, 0 ganho
- `10-ablacao-cnh-modelo-prompt.md` — ablação modelo×prompt na CNH; gemini-2.5-pro não recupera campos extras

---

## 11. Achados Empíricos Consolidados

### Tabela de Resultados (matriz benchmark)

Fonte: `benchmark/results/tabela.md`

| doc | modelo | modo | status | latência_s | custo_usd | acuracia_juiz | acuracia_det |
|---|---|---|---|---|---|---|---|
| cnh | gemini-2.5-flash-lite | single | partial | 2.61 | 0.00027 | 0.50 | 0.667 |
| cnh | gemini-2.5-flash-lite | two_step | partial | 4.14 | 0.00038 | 0.50 | 0.667 |
| cnh | gpt-4o-mini | single | partial | 2.99 | 0.00226 | 0.33 | 0.50 |
| cnh | qwen2.5-vl-72b | single | partial | 6.17 | 0.00051 | 0.50 | 0.333 |
| fatura | gemini-2.5-flash-lite | single | ok | 3.34 | 0.00040 | 0.857 | — |
| fatura | gemini-2.5-flash-lite | two_step | ok | 4.90 | 0.00059 | 0.833 | — |
| fatura | gpt-4o-mini | single | ok | 3.07 | 0.00734 | 0.857 | — |
| fatura | qwen2.5-vl-72b | two_step | ok | 8.39 | 0.00156 | 0.86 | — |

### Achados-chave

- **Tese 2→1 confirmada:** single-pass é consistentemente mais rápido e mais barato que o 2-step, com acurácia
  igual ou melhor. Ex.: fatura/gemini single 3,3s/$0,0004 vs two_step 4,9s/$0,0006. (`notes/02`, benchmark)

- **Híbrido PDF >> VLM ingênuo (paper):** enviar o PDF inteiro (28 MB / 42 págs) ao VLM falha — 615s e erro
  do provedor (choices=None). O híbrido extrai 42 págs em ~5s a custo zero via PyMuPDF (`extractor/pdf_extract.py`)
  e usa o VLM apenas numa figura (~$0,0004). (`notes/04`, `benchmark/results/paper_hibrido.md`)

- **CNH (341×600 px) — legibilidade intrínseca é o gargalo:** upscaling Lanczos não ajuda (+153% custo,
  0 ganho — `notes/09`); prompt ancorado recupera `data_emissao` sem custo extra e empata o modelo pequeno com
  o forte; escalar para gemini-2.5-pro (~57× o custo) não recupera nenhum campo extra (`notes/10`); CPF permanece
  irrecuperável (erro de dígito no JPEG — limitação da imagem fonte, não do modelo).

- **Juiz LLM não-calibrado em baixa-res:** gap ±0,17 entre `acuracia_juiz` e `acuracia_det` na CNH — daí a
  necessidade da métrica dupla. (`notes/08`)
