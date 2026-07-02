# Workstream 1 — Baseline & Métricas

> Nota de pesquisa para o dossiê técnico. Objetivo: definir como **caracterizar/medir** o problema de um pipeline de extração de documentos, mapear os **benchmarks padrão** da área, **quantificar** o custo/latência de processos em 2 etapas, e estabelecer **como avaliar interpretação de gráficos/imagens**.
> Data da pesquisa: 2026-06-26. Prioridade a fontes de 2024-2026.

---

## TL;DR (5 bullets)

- **Framework de métricas tem 3 eixos:** (1) *qualidade da extração* — F1/precision/recall e exact-match no nível de campo (key-value), ANLS para QA tolerante a OCR, e **TEDS** (Tree-Edit-Distance Similarity) + **edit distance normalizado (NED)** para estrutura de tabelas/texto; (2) *latência* — por página, reportada em p50/p95; (3) *custo* — por 1k tokens, por página e por documento. Não existe métrica única: campos discretos usam F1/exact-match, tabelas usam TEDS, texto corrido usa NED.
- **Benchmarks canônicos por dificuldade:** **FUNSD/CORD/SROIE** (KIE em formulários/recibos, métrica F1), **DocVQA/InfographicVQA/DUDE** (QA sobre documentos, métrica ANLS), **ChartQA/InfographicVQA** (gráficos/infográficos, *relaxed accuracy* 5%), e **OmniDocBench** (CVPR 2025, parsing de PDF end-to-end, 981 páginas, 9 tipos, usa NED+TEDS+CDM). Esses cobrem exatamente o espectro dos 3 documentos de teste (CNH ≈ FUNSD/SROIE; fatura CELPE ≈ CORD/OmniDocBench tabelas; paper Claude 3 ≈ DUDE/ChartQA/OmniDocBench).
- **O processo de 2 etapas (interpretação → reformatação em JSON) tende a ~2x chamadas → ~2x custo de input e latência adicional**, porque a 2ª inferência reprocessa o contexto/saída da 1ª. *Verificado por inferência*: a literatura mostra que separar "raciocínio livre" de "formatação constrita" **melhora acurácia** (ex.: 48%→61% em agregação, +12% de tokens em um caso citado) mas o custo dominante quando há **imagem** é o re-envio dos tokens visuais da página, que podem ser milhares por página.
- **Custo de visão é mensurável e dominante:** no Claude, uma imagem custa `⌈w/28⌉ × ⌈h/28⌉` *visual tokens*; uma página ~1000×1000 px ≈ **1.296 tokens**, uma página A4 densa em alta resolução chega a **~3.000-4.784 tokens**. A ~$3/Mtok (Sonnet) isso é ~$0.0039/página só de input visual; em 2 etapas que reenviam a imagem, dobra.
- **Gráficos/imagens avaliam-se por duas tarefas:** **ChartQA** (QA com *relaxed accuracy*, tolerância 5% para números) e **chart-to-table** (DePlot, métrica **RMS-F1**/RNSS). A *relaxed accuracy* tem viés conhecido (tolerância de 5% é larga demais para valores grandes e para anos), então recomenda-se complementar com chart-to-table + checagem exata.

---

## Achados detalhados

### 1. Como caracterizar/medir o problema — framework de métricas

**Eixo A — Qualidade da extração de campos (KIE / key-value).**
- **Precision / Recall / F1 no nível de campo (Field-F1):** F1 é a média harmônica de precision e recall por campo/label. Precision = predições positivas corretas / total de predições positivas; Recall = predições positivas corretas / labels positivos no ground-truth. É a métrica padrão de FUNSD, CORD e SROIE (micro-F1 sobre entidades). [nature s41598-025-15627-z; arxiv 2304.10994]
- **Exact-match:** usado quando o campo precisa bater 100% (ex.: número da CNH, CPF). Penaliza qualquer divergência, inclusive de OCR.
- **ANLS (Average Normalized Levenshtein Similarity):** métrica primária de DocVQA/InfographicVQA/DUDE. Mede similaridade por edit distance normalizado, para que erros menores de OCR não sejam punidos severamente como em exact-match. **Limitação documentada:** robusto a variação ortográfica, mas *não* captura corretude semântica, exatidão numérica nem *grounding*. [arxiv 2007.00398; arxiv 2508.18984]
- **KIEval:** métrica recente (2025) proposta especificamente para KIE de documentos, endereçando limitações de F1/ANLS. [arxiv 2503.05488]

**Eixo B — Structured-output / tabelas.**
- **TEDS (Tree-Edit-Distance-based Similarity):** introduzido junto com o PubTabNet; virou o padrão *de facto* para reconhecimento de tabelas. Converte o HTML da tabela em árvore e mede o custo mínimo de operações (inserir/deletar/renomear) para transformar a predição no ground-truth, capturando estrutura **e** conteúdo de célula. **TEDS-Struct** é a variante que ignora o texto da célula e avalia só a estrutura. [arxiv 1911.10683 (PubTabNet); arxiv 2403.04822]
- **Normalized Edit Distance (NED):** mínimo de operações de edição para transformar uma string em outra, normalizado pelo tamanho do alvo. Usado para texto corrido e *reading order*. **Menor = melhor.** [github opendatalab/OmniDocBench]
- **CDM (Character Detection Matching):** métrica de renderização para fórmulas matemáticas (complementada por BLEU). [arxiv 2412.07626]

**Eixo C — Latência.**
- Reportar **por página** e em percentis **p50/p95** (a média esconde a cauda; p95 é o que define SLA). *Inferência*: a literatura de benchmarks raramente padroniza latência, então é um eixo que o dossiê deve medir empiricamente nos 3 documentos. [inferência minha — ver lacunas]

**Eixo D — Custo.**
- **Por 1k/1M tokens:** preço base de input/output do modelo. Ex.: Claude Sonnet 4.6 = $3/Mtok input, $15/Mtok output; Opus = $5/$25; Haiku 4.5 = $1/$5; GPT-4o ≈ $2,50/$10. [platform.claude.com/pricing]
- **Por página:** o custo de visão é calculável. Claude vê a imagem em *patches* de 28×28 px; custo = `⌈width/28⌉ × ⌈height/28⌉` visual tokens. Tabela de referência: 1000×1000 px = 1.296 tokens; 1092×1092 = 1.521; 2000×1500 (alta-res) = 3.888; 3840×2160 (alta-res) = 4.784 (teto). A $3/Mtok, 1000×1000 ≈ **$3,89 por mil imagens** (~$0,0039/página). [platform.claude.com/docs/.../vision]
- **Por documento:** custo/página × nº de páginas + tokens de prompt/output. Multipágina (paper Claude 3) multiplica o custo de visão linearmente.

---

### 2. Benchmarks padrão da área (o que cada um mede + números)

- **FUNSD** — *form understanding*. 199 formulários escaneados ruidosos (149 treino / 50 teste), 9.707 entidades, 4 tipos (header, question, answer, other). Foca relações espaciais e *entity linking*. Métrica: F1. SOTA recente (ARIAL, 2025): **90,0 ANLS** no setup VQA. [springer 10.1007/s10462-024-11000-0; arxiv 2511.18192]
- **CORD** — *receipt parsing*. 1.000 recibos indonésios (800/100/100), 30 entidades hierárquicas sob menu/subtotal/total. Métrica: micro-F1. SOTA ARIAL: **85,5 ANLS / 60,2 mAP**. [arxiv 2511.18192]
- **SROIE** — KIE de recibos (ICDAR 2019, task 3). 626 treino / 347 teste; 4 campos: Company, Date, Address, Total. Métrica: F1. SOTA ARIAL: **93,1 ANLS**. [researchgate 339022568; arxiv 2511.18192]
- **DocVQA** — QA sobre imagens de documento. 50.000 perguntas sobre 12.767 imagens (formulários, recibos, relatórios; digital/impresso/manuscrito). Métrica primária: **ANLS**. SOTA ARIAL: **88,7 ANLS / 50,1 mAP**. [arxiv 2007.00398; arxiv 2511.18192]
- **InfographicVQA** — QA sobre infográficos; exige raciocínio conjunto sobre layout, texto, elementos gráficos e visualizações de dados. Métrica: ANLS. [arxiv (InfographicVQA); researchgate 354357194]
- **DUDE** — *multi-page, multi-domain* (Van Landeghem et al., 2023). PDFs completos renderizados em imagens de página + query em linguagem natural + resposta livre + evidência por página. Domínios: científico, financeiro, legal, manuais, apresentações. Métrica: ANLS. [arxiv 2305.08455; proceedings.neurips 2024 MMLongBench-Doc]
- **ChartQA** — QA sobre gráficos com raciocínio visual+lógico. ~9,6k perguntas *human* + ~23k *augmented*. Métrica: *relaxed accuracy* (5% para números, exact-match case-insensitive para texto). Referência: método proposto 76,8%; UniChart 72,4%; DePlot 69,7%; SIMPLOT 83,24% overall. [aclanthology 2022.findings-acl.177; arxiv 2203.10244]
- **OmniDocBench** — *parsing de PDF end-to-end* (CVPR 2025, OpenDataLab). **981 páginas, 9 tipos** (papers, livros, slides, relatórios financeiros, livros didáticos, provas, revistas, notas, jornais), 20k+ blocos / 80k+ spans. Métricas: NED (texto/ordem), TEDS (tabelas), CDM (fórmulas). **Já considerado "saturado" em 2025/2026** — leaderboard atual: FalconOCR 88,64 overall > DeepSeek-OCR-v2 87,66 > GPT-5.2 86,56; MinerU 2.5 com TextEdit 0,047 e Table-TEDS 88,22. [arxiv 2412.07626; github opendatalab/OmniDocBench; llamaindex blog]

**Pipeline-tools vs VLMs end-to-end no OmniDocBench (Overall Edit Distance / Table-TEDS, EN):**
MinerU **0,058 / 79,4** · Mathpix 0,101 / 77,9 · Marker 0,141 / 54,0 · GOT-OCR 0,187 / 53,5 · Nougat 0,365 / 40,3 · **GPT-4o 0,144 / 72,8** · Qwen2-VL 0,252 / 59,9 · InternVL2 0,353 / 63,8. *Leitura:* ferramentas de pipeline especializadas (MinerU/Mathpix) ainda batem VLMs genéricos em tabelas e edit distance, mas VLMs têm mais robustez em tipos especializados. [arxiv 2412.07626]

---

### 3. Por que 2 etapas adicionam latência/custo

O pipeline atual = **chamada 1** (interpretação/extração) → **chamada 2** (reformatar em JSON).
- **~2x chamadas → ~2x custo de input + latência adicional.** A 2ª inferência precisa reprocessar contexto (e frequentemente a saída completa da 1ª) antes de gerar o JSON. *Verificado por inferência a partir do modelo de billing por token*: cada chamada paga input + output independentemente; duplicar chamadas ~duplica o input cobrado. [platform.claude.com/pricing — modelo de cobrança]
- **Quando há imagem, o custo é dominado pelos visual tokens da página** (1.296–4.784 tokens/página). Se a 2ª etapa reenvia a imagem, dobra esse componente; se reenvia só o texto extraído, o overhead é menor mas a latência da 2ª ida-e-volta permanece. [platform.claude.com/.../vision]
- **Trade-off documentado:** separar "raciocínio livre" (etapa 1, sem constraint) de "formatação constrita" (etapa 2) **melhora acurácia** — exemplo citado: agregação 48%→61% com +12% de tokens; e "forçar JSON degrada raciocínio em 10–15%". Ou seja, 2 etapas existe por um bom motivo, mas o custo/latência é o preço. [medium michael.hannecke; tetrate.io; collinwilkins.com]
- **Alternativa a investigar (próximos workstreams):** *constrained decoding / structured outputs* numa **única** chamada (tool-use / JSON schema), que captura o benefício do JSON sem a 2ª ida-e-vez à rede. *Inferência minha.*

> **Quantificação de referência (a validar empiricamente):** se 1 etapa = `T_in_visual + T_in_prompt + T_out`, então 2 etapas ≈ `(T_in_visual + T_in_prompt + T_out_1) + (T_in_ctx_2 + T_out_2)`. Quando `T_in_visual` domina e é reenviado, custo ≈ **2x**; latência ≈ **1,8–2x** (segunda round-trip + TTFT). [inferência]

---

### 4. Como avaliar gráficos/imagens

- **ChartQA (relaxed accuracy):** tolera 5% de erro em respostas numéricas; texto exige exact-match (case-insensitive). **Viés conhecido e importante:** 5% é largo demais para valores grandes (1.000 → ±50) e para **anos** (5% de 2012 ≈ ±100 anos), inflando artificialmente o score. Recomenda-se reportar também acurácia exata em subconjuntos numéricos. [arxiv 2504.05506 (ChartQAPro); evalscope]
- **Chart-to-table (extrair a tabela subjacente do gráfico):** tarefa de DePlot. Métricas **RMS-F1** (Relative Mapping Similarity — alinha tabela predita × ground-truth considerando texto, números e estrutura), RNSS e RD. Referência: **DePlot RMS-F1 = 94,20** em ChartQA chart-to-table. É a métrica mais rigorosa para "leitura de gráfico" porque exige reconstruir os dados, não só responder uma pergunta. [arxiv 2212.10505 (DePlot); ritvik19 medium]
- **InfographicVQA:** avalia raciocínio conjunto sobre layout + texto + elementos gráficos + visualizações (ANLS). Cobre o caso "infográfico/figura densa" do paper Claude 3. [researchgate 354357194]
- **Recomendação de avaliação para o POC:** para o paper Claude 3 (gráficos), medir (a) chart-to-table com RMS-F1 onde houver ground-truth tabular, e (b) ChartQA-style relaxed accuracy para perguntas pontuais, sempre reportando exact-match numérico em paralelo para neutralizar o viés da tolerância de 5%. *Inferência minha.*

---

## Tabela de benchmarks

| Benchmark | O que mede | Escala | Métrica primária | Número de referência (2024-2026) | Mapeia p/ doc de teste |
|---|---|---|---|---|---|
| **FUNSD** | Form understanding / entity linking | 199 forms (149/50); 9.707 entidades | F1 | ARIAL 90,0 ANLS (VQA setup) | CNH (form) |
| **CORD** | Receipt parsing (KIE hierárquico) | 1.000 recibos (800/100/100); 30 entidades | micro-F1 | ARIAL 85,5 ANLS / 60,2 mAP | Fatura CELPE |
| **SROIE** | KIE de recibos (4 campos) | 626/347 recibos | F1 | ARIAL 93,1 ANLS | CNH / Fatura |
| **DocVQA** | QA sobre documento (1 pág) | 50k perguntas / 12.767 imgs | ANLS | ARIAL 88,7 ANLS / 50,1 mAP | Todos |
| **InfographicVQA** | QA sobre infográficos | infográficos diversos | ANLS | — (ver lacunas) | Paper (figuras) |
| **DUDE** | QA multi-página, multi-domínio | PDFs completos, resposta livre | ANLS | — (ver lacunas) | Paper Claude 3 |
| **ChartQA** | QA sobre gráficos | ~9,6k human + ~23k aug | relaxed acc. (5%) | DePlot 69,7%; UniChart 72,4%; SIMPLOT 83,24% | Paper (gráficos) |
| **ChartQA (chart-to-table)** | Reconstrução da tabela do gráfico | subset ChartQA | RMS-F1 / RNSS | DePlot 94,20 RMS-F1 | Paper (gráficos) |
| **OmniDocBench** | Parsing de PDF end-to-end | 981 págs, 9 tipos | NED + TEDS + CDM | MinerU 0,058 NED / 79,4 TEDS; GPT-4o 0,144 / 72,8 | Paper / Fatura |

*Convenção: para NED/edit-distance, **menor = melhor**; para F1/TEDS/ANLS/accuracy, **maior = melhor**.*

---

## Fontes (URLs)

**Métricas (F1, TEDS, NED, ANLS, KIEval):**
- https://www.nature.com/articles/s41598-025-15627-z.pdf
- https://arxiv.org/pdf/1911.10683 (PubTabNet / TEDS)
- https://arxiv.org/pdf/2403.04822 (UniTable)
- https://arxiv.org/pdf/2503.05488 (KIEval)
- https://arxiv.org/pdf/2304.10994 (IE: QA vs token classification)

**Benchmarks de extração / KIE / DocVQA:**
- https://arxiv.org/abs/2007.00398 e https://arxiv.org/pdf/2007.00398 (DocVQA)
- https://link.springer.com/article/10.1007/s10462-024-11000-0 (survey form understanding)
- https://arxiv.org/html/2511.18192 e https://arxiv.org/pdf/2511.18192 (ARIAL — SOTA DocVQA/FUNSD/CORD/SROIE)
- https://www.researchgate.net/publication/339022568 (ICDAR2019 SROIE)
- https://huggingface.co/datasets/rth/sroie-2019-v2 (SROIE)

**OmniDocBench:**
- https://arxiv.org/html/2412.07626v1 e https://arxiv.org/abs/2412.07626 (paper OmniDocBench)
- https://github.com/opendatalab/OmniDocBench (repo oficial + leaderboard)
- https://www.llamaindex.ai/blog/omnidocbench-is-saturated-what-s-next-for-ocr-benchmarks (saturação)

**Gráficos / chart-to-table:**
- https://aclanthology.org/2022.findings-acl.177.pdf e https://arxiv.org/pdf/2203.10244 (ChartQA)
- https://arxiv.org/pdf/2504.05506 (ChartQAPro — crítica à relaxed accuracy)
- https://evalscope.readthedocs.io/en/latest/benchmarks/chartqa.html (definição relaxed accuracy)
- https://ar5iv.labs.arxiv.org/html/2212.10505 (DePlot — chart-to-table, RMS-F1)
- https://www.researchgate.net/figure/...354357194 (InfographicVQA — breakdown ANLS)
- https://proceedings.neurips.cc/paper_files/paper/2024/file/ae0e43289bffea0c1fa34633fc608e92-Paper-Datasets_and_Benchmarks_Track.pdf (MMLongBench-Doc; contexto DUDE/multi-page)

**Custo / latência / 2 etapas:**
- https://platform.claude.com/docs/en/about-claude/pricing (preços por Mtok)
- https://platform.claude.com/docs/en/build-with-claude/vision (fórmula de visual tokens por página)
- https://medium.com/@michael.hannecke/beyond-json-picking-the-right-format-for-llm-pipelines-b65f15f77f7d (2 etapas: raciocínio vs formatação)
- https://tetrate.io/learn/ai/llm-output-parsing-structured-generation (structured output)
- https://collinwilkins.com/articles/structured-output (schema validation 2026)

---

## Afirmações não-verificadas / lacunas

1. **Latência p50/p95 padronizada:** nenhum dos benchmarks consultados publica latência por página de forma padronizada. O eixo de latência precisará ser **medido empiricamente** no POC sobre os 3 documentos. (lacuna a fechar no Workstream de experimentos)
2. **"~2x custo/latência" do pipeline de 2 etapas:** é **inferência minha** a partir do modelo de cobrança por token (não medição direta). O valor real depende de quanto contexto/imagem a 2ª etapa reenvia. Um caso citado mostrou apenas +12% de tokens — então **2x é o teto, não a regra**. Validar empiricamente.
3. **Números de referência de InfographicVQA e DUDE:** não consegui extrair SOTA numérico recente confiável nesta rodada (as buscas retornaram descrições, não leaderboards). Lacuna — buscar paperswithcode / leaderboard oficial DUDE e InfographicVQA.
4. **ChartQA — composição exata (9,6k human / 23k augmented):** número aproximado a partir de conhecimento prévio; a busca não confirmou o split exato. Verificar no paper original (arxiv 2203.10244) antes de citar no dossiê.
5. **Mapeamento doc-de-teste → benchmark** (CNH≈FUNSD, CELPE≈CORD, paper≈DUDE/ChartQA) é **proposta analítica minha**, não uma correspondência oficial. Serve para orientar a escolha de métricas, não como equivalência formal.
6. **GPT-4o pricing ($2,50/$10):** valor de fonte secundária (search), não da página oficial da OpenAI. Confirmar antes de usar em comparação de custo no dossiê.
7. **OmniDocBench "saturado" / leaderboard (FalconOCR, DeepSeek-OCR-v2, GPT-5.2):** números vêm de blog/README de 2025-2026; tratar como indicativos e re-verificar no repo oficial no momento da escrita do dossiê.
