# Workstream 4 — Modelos Especializados / OCR-free / Document-AI Open-Source

> Nota de pesquisa para o dossiê técnico. Foco: reduzir latência/custo do pipeline de extração
> em 2 passos, possivelmente auto-hospedando modelos menores/especializados.
> Documentos-alvo: **Doc 1** (CNH — formulário estruturado), **Doc 2** (fatura CELPE — layout
> complexo, tabelas), **Doc 3** (paper Claude 3 — multipágina, fórmulas, gráficos, tabelas).
> Data: 2026-06-26. Priorização 2023-2026.

---

## TL;DR (5 bullets)

1. **Três famílias distintas**, não intercambiáveis: (a) **OCR-free VDU** (Donut, Pix2Struct, Nougat) que vão de imagem → JSON/Markdown direto; (b) **layout-aware** (LayoutLMv3, LayoutXLM, LiLT) que exigem OCR+bounding boxes e brilham em formulários (FUNSD/CORD); (c) **pipelines PDF→Markdown modernos** (Marker, MinerU, Docling, PaddleOCR-VL, dots.ocr, DeepSeek-OCR) que preservam tabelas/fórmulas/layout — categoria onde está o estado-da-arte 2025-2026.
2. **Para o Doc 3 (paper acadêmico), Nougat é o especialista histórico** (PDF científico → Markdown+LaTeX, entende fórmulas e tabelas), mas tem limitações sérias: janela de 1024 tokens trunca até ~80% das páginas densas e ~1 em 500 páginas degenera em repetição/alucinação [verificado]. Em 2025-2026 foi **superado por Marker/MinerU/PaddleOCR-VL**, que são mais robustos e mantidos ativamente.
3. **Para formulários previsíveis (Doc 1 CNH)**, especializar compensa: LayoutLMv3-Large atinge **~92.1 F1 em FUNSD** e **~96.6 F1 em CORD** com inferência muito mais barata que VLM generalista [verificado]. Donut (OCR-free, MIT) é alternativa end-to-end sem caixa de OCR separada.
4. **Infra é viável em GPU modesta**: a maioria dos modelos especializados roda em **3-8 GB VRAM** (Donut, dots.ocr ~3.5 GB, GOT-OCR ~3 GB, Granite-Docling ~0.5 GB); custo cloud na faixa de **US$4-7 por 10.000 páginas** em L40S/A100. Atenção: throughput em batch grande (512 págs) pode estourar 40+ GB VRAM (PaddleOCR-VL: 42 GB médio em A100) [verificado].
5. **Regra de decisão**: especialize quando o documento é **homogêneo e de alto volume** (CNH, fatura padronizada) — ganho de custo/latência é grande e a manutenção é baixa. Use **VLM generalista** quando há **alta variabilidade/scans ruins/watermarks** ou quando o custo de manter N modelos especializados supera o de uma única API. Modelos OCR-specialized de 0.9B (PP-OCRv5, GLM-OCR) já **rivalizam/superam VLMs de 235B** em parsing de documento padrão [verificado].

---

## Achados detalhados

### 1) Modelos OCR-free de Visual Document Understanding (VDU)

**Donut** (Clova/NAVER, 2021) — Transformer encoder-decoder (Swin + BART) que vai de **imagem → JSON estruturado sem OCR**. SOTA em velocidade/acurácia na sua época para parsing de recibos/formulários. Licença **MIT** (uso comercial liberado) [verificado]. Erros típicos: pega informação de região errada do documento ou comete pequenos erros de "OCR implícito" (mas **não alucina campos inteiros** como o Pix2Struct) [verificado]. Bom candidato para Doc 1 (CNH) e campos fixos da fatura.

**Pix2Struct** (Google, 2022) — pré-treinado em screenshots de páginas web parseadas em HTML; input de resolução variável. **Pix2Struct-Large supera Donut em ~9 pontos no DocVQA** [verificado]. Licença **Apache 2.0** [verificado]. Limitação: **alucinação** — gera campos completamente inventados e às vezes falha em retornar campos (observado em documentos de patente) [verificado].

**Nougat** (Meta, 2023) — **especialista em documentos acadêmicos**: PDF científico → Markdown com **fórmulas em LaTeX e tabelas** reconstruídas; coloca corpo de tabela e captions ao fim do Markdown da página [verificado]. **Diretamente relevante ao Doc 3.** Limitações documentadas [verificado]:
- **Janela de 1024 tokens** insuficiente para 1 página densa — **até 80.5% das páginas sofrem truncamento**.
- **Repetição/alucinação**: ~1 em 500 páginas degenera em texto repetitivo (mitigável com repetition penalty).
- **Desalinhamento posicional**: figuras/tabelas podem não corresponder à posição no source.
- Corner cases de fórmula escapam à checagem de sintaxe.
- **Status 2025-2026**: superado por Marker/MinerU em robustez; ainda útil como baseline acadêmico.

### 2) Modelos de layout (precisam de OCR + bounding boxes)

| Modelo | Ideia | FUNSD F1 | CORD F1 | Licença |
|---|---|---|---|---|
| **LayoutLMv3** (MS, 2022) | Texto+imagem+layout com masking unificado | **92.08** (Large) / ~91.19 (Base) | **96.6** (Large) / 96.53 (Base) | **CC BY-NC-SA 4.0** (não-comercial!) [verificado] |
| **LayoutXLM** (MS) | LayoutLM multilíngue | — (forte em XFUND) | — | CC BY-NC-SA 4.0 [inferido pela família] |
| **LiLT** (2022) | Separa stream de linguagem e de layout → **language-agnostic** | competitivo | competitivo | **MIT** (mais permissivo) [inferido] |

- Variantes recentes empurram o teto: **GraphLayoutLM** chega a **93.15 F1 (FUNSD)** e **97.75 F1 (CORD, Large)** [verificado].
- Para DocVQA, LayoutLMv3 atinge **ANLS 83.37** [verificado].
- **Caveat de licença**: LayoutLMv3/XLM são **CC BY-NC** → bloqueiam uso comercial direto. Para produção comercial, preferir **LiLT (MIT)** ou Donut (MIT). [verificado/inferido]
- **Trade-off central**: exigem um OCR upstream (Tesseract/PaddleOCR/Surya) que produz texto + caixas → pipeline em 2 estágios próprio, com erro acumulado de OCR. Ótimos quando o layout é estável (formulários).

### 3) Pipelines OCR modernos / document-to-markdown (estado-da-arte 2025-2026)

**Marker** (datalab-to) — PDF/imagem/DOCX/PPTX/XLSX/HTML/EPUB → Markdown/JSON; usa **Surya** para OCR; roda em **GPU/CPU/Apple MPS**. **~5 GB VRAM pico / 3.5 GB médio por worker**; **~25 páginas/s em H100 batch** [verificado]. Boa qualidade em tabelas e fórmulas. Opção de LLM-enhancement.

**MinerU** (OpenDataLab / Shanghai AI Lab) — usa PaddleOCR + modelos próprios de layout. **Melhor detecção de layout para documentos complexos** e excelência em CJK; **tabelas excelentes** [verificado]. Suporte de hardware mais amplo (NVIDIA, AMD, Ascend, Cambricon etc.). GPU recomendada.

**Docling** (IBM, Linux Foundation AI project) — saída estruturada rica, integrações RAG; **Granite-Docling** VLM associado precisa de só **~0.5 GB VRAM** e ~80-100 págs/min [verificado].

**PaddleOCR-VL-1.x** (0.9B) — **líder no OmniDocBench-OCR-block**; **~96.33% no OmniDocBench v1.6**; menores edit distances em todos os scripts; **VRAM ~2 GB (FP16)**, mas **42.1 GB médio em batch de 512 numa A100**; ~45-60 págs/min; **~US$7.27 / 10K págs** (L40S); 100+ idiomas; **Apache 2.0** [verificado].

**dots.ocr** — layout-aware VLM; **~3.5 GB VRAM (FP16)**, roda em qualquer GPU 8 GB+; **MIT** [verificado]. Recomendado como ponto de partida para extração layout-aware.

**DeepSeek-OCR** — **~8 GB VRAM (FP16)**; **~US$4.36-6.10 / 10K págs** (30-40% mais barato que PaddleOCR-VL); **MIT** [verificado].

**GOT-OCR 2.0** — **~3 GB VRAM**; roda em consumer (RTX 4090); alto throughput (~65-80 págs/min); **Apache 2.0** [verificado].

**docTR / Surya / PaddleOCR (engines OCR tradicionais)** — leves, rápidos, bons para documentos digitais limpos de layout simples; **sofrem com layout pesado, manuscrito e scans de baixa qualidade** [verificado]. PaddleOCR roda em CPU e GPU, com variantes mobile/edge; **Apache 2.0** [verificado]. Servem como camada de OCR para os modelos layout-aware da seção 2.

**PyMuPDF4LLM** — sem ML, **conversão mais rápida**, mas **fórmulas: nenhuma** e tabelas só razoáveis [verificado]. Útil só para PDFs nativos (text-layer), não para imagens/scans (Doc 1 e 2 são imagens → não serve sozinho).

---

## Tabela comparativa

| Modelo/Pipeline | Tarefa | Acurácia (benchmark) | Infra (VRAM/CPU) | Licença |
|---|---|---|---|---|
| **Donut** | OCR-free img→JSON (formulários/recibos) | SOTA velocidade/acurácia na época; DocVQA ANLS ~67.5 [verificado] | GPU ~3-6 GB; CPU lento mas viável | MIT |
| **Pix2Struct** | OCR-free img→texto (web/UI/VQA) | DocVQA-Large > Donut +9 pts [verificado] | GPU ~base/large | Apache 2.0 |
| **Nougat** | PDF acadêmico→Markdown+LaTeX (Doc 3) | Forte em fórmulas; trunca ~80% págs densas; ~1/500 repete [verificado] | GPU recomendada; CPU lento | CC BY-NC (código MIT; checar pesos) [inferido] |
| **LayoutLMv3** | Layout-aware (OCR+bbox) formulários | FUNSD 92.08 / CORD 96.6 / DocVQA ANLS 83.37 [verificado] | GPU; precisa OCR upstream | **CC BY-NC-SA 4.0** (não-comercial) |
| **LayoutXLM** | Layout-aware multilíngue | Forte em XFUND [verificado] | GPU + OCR | CC BY-NC-SA 4.0 [inferido] |
| **LiLT** | Layout-aware language-agnostic | Competitivo c/ LayoutLMv3 [verificado] | GPU + OCR; leve | MIT [inferido] |
| **Marker** | PDF→Markdown/JSON (geral) | Tabelas/fórmulas "boas"; ~25 págs/s H100 [verificado] | **5 GB pico / 3.5 GB médio**; GPU/CPU/MPS | (open-source; checar repo) |
| **MinerU** | PDF→Markdown (layout complexo) | Tabelas "excelentes" [verificado] | GPU recomendada; multi-vendor HW | AGPL/open (checar) [inferido] |
| **Docling / Granite-Docling** | PDF→Markdown estruturado | — | **~0.5 GB VRAM**; ~80-100 págs/min | Apache 2.0 |
| **PaddleOCR-VL (0.9B)** | OCR-VL doc parsing | **OmniDocBench v1.6 96.33%**; menor edit dist [verificado] | 2 GB FP16; **42 GB batch-512 A100**; ~$7.27/10K | Apache 2.0 |
| **dots.ocr** | Layout-aware VLM | líder layout (sem nº edit dist aqui) | **~3.5 GB FP16**, 8 GB+ GPU | MIT |
| **DeepSeek-OCR** | OCR-VL | — (sem nº no bench citado) | **~8 GB FP16**; ~$4.36-6.10/10K | MIT |
| **GOT-OCR 2.0** | OCR-VL | — | **~3 GB**; RTX 4090 ok; alto throughput | Apache 2.0 |
| **docTR/Surya/PaddleOCR** | OCR engine tradicional | bom em digital limpo; fraco em scan ruim [verificado] | leve; **CPU viável** | Apache 2.0 |
| **PyMuPDF4LLM** | PDF nativo→MD (sem ML) | tabelas razoáveis; **fórmulas nenhuma** [verificado] | **CPU, mais rápido**; sem GPU | (open) |

*Onde marcado "[inferido]", a licença não foi confirmada na busca e deve ser verificada no repositório oficial antes de uso em produção.*

---

## 4) Custo de self-hosting (verificado, ordens de grandeza)

- **GPU típica suficiente**: 1x L40S (48 GB) ou A100 para os VLMs; muitos modelos cabem em **8-24 GB** (RTX 4090/A10) para inferência single-stream.
- **Custo por 10K páginas (on-demand)**: PaddleOCR-VL **~US$7.27** (L40S); DeepSeek-OCR **~US$4.36-6.10**; Granite-Docling o mais barato (VRAM mínima).
- **Throughput**: 45-100 págs/min por modelo VLM compacto; Marker ~25 págs/s em H100 batch.
- **Alerta de VRAM em batch**: latência baixa exige batch grande → PaddleOCR-VL chega a **42 GB** em batch 512 na A100. Para CPU, OCR tradicional (docTR/PaddleOCR/Surya) é viável, mas os VLMs de parsing são lentos demais sem GPU.

## 5) Quando especializar vs. usar VLM generalista

**Especializar (modelo dedicado/OCR-free/layout-aware) compensa quando:**
- Documento **homogêneo e alto volume** (CNH Doc 1, fatura CELPE Doc 2 com template estável) → custo/latência despencam.
- **Modelos especializados de 0.9B (PP-OCRv5, GLM-OCR) superam VLMs generalistas de 235B** (Qwen3-VL-235B, Gemini-3 Pro) em parsing de documento padrão — **contagem de parâmetros não é o fator decisivo** [verificado].
- Fine-tuning domain-specific **compensa contagem menor de parâmetros** [verificado].
- Licença/privacidade exigem self-hosting on-prem.

**Usar VLM generalista quando:**
- **Alta variabilidade / scans ruins / watermarks / fundos coloridos** → generalistas têm **mais resiliência e adaptabilidade** [verificado].
- Diversidade de tipos de documento alta → manter **N modelos especializados** (cada um com seu OCR, fine-tune, monitoramento) custa mais em **manutenção** que uma única API/VLM.
- Doc 3 (paper, fórmulas, gráficos): pipeline PDF→Markdown moderno (Marker/MinerU/PaddleOCR-VL) **ou** VLM forte; Nougat puro é frágil hoje.

**Trade-off resumido (acurácia × infra × manutenção):**
- **Acurácia**: especializados ganham em domínio fechado; generalistas ganham em "in-the-wild".
- **Infra**: especializados rodam em GPU modesta (3-8 GB) ou até CPU (OCR clássico); generalistas grandes exigem GPU robusta ou API paga.
- **Manutenção**: especializado = +esforço por documento (dataset, fine-tune, drift); generalista = -esforço, +custo por token.

**Recomendação para o desafio (3 docs):**
- **Doc 1 (CNH)**: layout-aware (LiLT-MIT ou LayoutLMv3 se non-commercial OK) ou Donut → barato e preciso.
- **Doc 2 (fatura)**: pipeline PDF→MD com layout forte (MinerU/PaddleOCR-VL) p/ tabelas, + extração estruturada.
- **Doc 3 (paper)**: Marker ou MinerU (Markdown+LaTeX) > Nougat puro.
- Camada única de **VLM generalista** como fallback de robustez para casos fora da distribuição.

---

## Fontes (URLs)

- Donut (OCR-free Document Understanding Transformer): https://arxiv.org/abs/2111.15664 · https://ar5iv.labs.arxiv.org/html/2111.15664
- OCR-Free Document Data Extraction with Transformers (Donut vs Pix2Struct, alucinação): https://towardsdatascience.com/ocr-free-document-data-extraction-with-transformers-2-2-38ce26f41951/
- Pix2Struct: https://arxiv.org/html/2210.03347
- Nougat (paper): https://arxiv.org/pdf/2308.13418 · repo: https://github.com/facebookresearch/nougat
- Nougat truncamento 80%/repetição (Layout-Aware Text Editing): https://arxiv.org/html/2512.18115v1 · Arabic-Nougat: https://arxiv.org/html/2411.17835v1
- LayoutLMv3 (paper): https://arxiv.org/pdf/2204.08387 · ResearchGate: https://www.researchgate.net/publication/360030234
- LayoutLM family / FUNSD-CORD F1 / ANLS / licenças: https://llmbook.apartsin.com/part-5-multimodal-llms/module-21-document-understanding-ocr/section-21.2.html · https://github.com/huggingface/blog/blob/main/document-ai.md
- GraphLayoutLM (FUNSD 93.15 / CORD 97.75): https://arxiv.org/pdf/2308.07777
- LiLT: https://www.philschmid.de/fine-tuning-lilt
- Pipelines PDF→Markdown (Marker/Docling/MinerU/pdf-craft/PyMuPDF4LLM): https://themenonlab.blog/blog/best-open-source-pdf-to-markdown-tools-2026
- OCR/VLM self-host GPU cloud (VRAM/custo/throughput): https://www.spheron.network/blog/best-open-source-ocr-vlm-self-host-gpu-cloud-2026/
- Marker repo: https://github.com/datalab-to/marker
- 12 ferramentas open-source de parsing (MinerU/PaddleOCR): https://liduos.com/en/posts/ai-develope-tools-series-2-open-source-doucment-parsing/
- 8 OCR models compared (Modal): https://modal.com/blog/8-top-open-source-ocr-models-compared
- PaddleOCR-VL (paper 0.9B): https://arxiv.org/pdf/2510.14528 · docs: https://www.paddleocr.ai/latest/en/version3.x/algorithm/PaddleOCR-VL/PaddleOCR-VL.html
- PaddleOCR-VL VRAM 42GB batch / OmniDocBench: https://www.amd.com/en/developer/resources/technical-articles/2026/unlocking-high-performance-document-parsing-of-paddleocr-vl-1-5-.html
- PP-OCRv5 0.9B rivaliza com VLMs gigantes: https://arxiv.org/pdf/2603.24373
- GLM-OCR 0.9B > Qwen3-VL-235B/Gemini-3 Pro: https://arxiv.org/html/2603.10910v1
- OmniDocBench (benchmark): https://arxiv.org/html/2412.07626v1 · saturação: https://www.llamaindex.ai/blog/omnidocbench-is-saturated-what-s-next-for-ocr-benchmarks
- Best Open Source OCR Tools 2026: https://unstract.com/blog/best-opensource-ocr-tools/

---

## Lacunas (a confirmar antes do dossiê final)

1. **Números exatos de Donut em CORD** (tree-edit-distance accuracy / field F1) não saíram limpos na busca — confirmar no paper original (~91 TED-acc reportado historicamente, **não verificado** aqui).
2. **Licenças marcadas [inferido]** (LiLT, LayoutXLM, MinerU, Marker, Nougat pesos): confirmar no repositório oficial antes de assumir uso comercial.
3. **Acurácia OmniDocBench de dots.ocr / DeepSeek-OCR / GOT-OCR**: a fonte de custo não trouxe os números de edit distance — buscar tabela OmniDocBench v1.5/1.6 oficial.
4. **Throughput/latência CPU-only** dos VLMs de parsing: não quantificado; OCR clássico é a única via CPU realista, mas falta nº págs/min.
5. **Teste empírico nos 3 docs reais** (CNH/CELPE/paper) ainda não feito — benchmarks são proxies; a POC deve medir acurácia/latência/custo nos documentos do desafio.
6. **dots.ocr / DeepSeek-OCR são recentes (2025-2026)** — maturidade de produção e suporte de longo prazo ainda incertos.
