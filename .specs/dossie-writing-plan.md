# Plano de Escrita — Dossiê de Pesquisa (Entregável 1, 80%)

**Objetivo:** produzir um documento técnico-científico em PDF (~15-18 páginas), em PT-BR,
seguindo a voz do TCP de referência (`docs/estilo-tcp.md`), cobrindo as 6 seções
obrigatórias do desafio, fundamentado nas 11 notas de pesquisa e nos resultados empíricos
da POC (`benchmark/results/`).

**Idioma:** Português (BR). Termos técnicos em inglês, em *itálico*.
**Extensão-alvo:** ~15-18 páginas.
**Toolchain de saída:** Markdown único → `pandoc` (via `pypandoc-binary`) + TinyTeX → PDF acadêmico.
Fallback se TinyTeX falhar no Windows: `pandoc` → DOCX (o autor exporta a PDF) ou HTML estilizado.

---

## Regras de Estilo (de `docs/estilo-tcp.md`) — vinculantes para todo redator

1. **Voz:** impessoal, 3ª pessoa ("o presente estudo…", "observa-se que…"). Nunca 1ª pessoa.
   Alta formalidade, sem coloquialismos.
2. **Parágrafo:** abre com âncora contextual → sustenta com citação/número → fecha com síntese.
   Conectivos explícitos entre parágrafos ("Dessa forma,", "Nesse contexto,", "Além disso,", "Por fim,").
3. **Sinais de estrutura:** Introdução termina com parágrafo-roteiro (section-by-section);
   cada subseção termina com frase prospectiva anunciando a próxima.
4. **Citações:** ABNT autor-data in-text — "(Autor, ano)"; até três autores "(A; B; C, ano)".
   Bibliografia em ordem alfabética, título do veículo em **negrito**.
5. **Visuais:** legenda ACIMA "Figura N - Título" com linha de fonte abaixo; equações numeradas
   à direita; *termos técnicos* em itálico; listas NUMERADAS (não bullets) para enumerações técnicas.

> Nota de honestidade: as notas de pesquisa citam fontes por URL. Para ABNT, cada URL relevante
> deve virar uma referência formal (autor/instituição, ano, título, "Disponível em: <URL>. Acesso em: jun. 2026.").
> Onde a autoria for institucional (OpenAI, Anthropic, Google), usar a instituição como autor.

---

## Estrutura e Briefs por Seção

Cada seção abaixo é uma unidade de redação (um subagente por seção, com este brief + as fontes citadas).

### Front matter
- **Título:** ex. "Da Extração em Duas Etapas ao *Single-Pass*: Uma Análise de Viabilidade de
  Abordagens Alternativas para Extração de Dados de Documentos".
- **Autor:** Wellinton Oliveira Santos. **Data:** junho/2026.
- **Resumo** (~150-200 palavras): problema, método, principal achado (tese 2→1 confirmada;
  híbrido para documento extenso; recomendação escalonada), e a recomendação. **Palavras-chave:**
  extração de documentos, *Vision-Language Models*, *structured output*, *constrained decoding*, OCR.

### 1. Introdução  (~1,5 pp)
- **Objetivo:** contextualizar o problema de negócio e o objetivo da pesquisa.
- **Conteúdo:** a API Tech4.ai de extração (`POST /document/extract`, envelope
  `{status, extracted_data}`, *layout builder*) e seu *pipeline* de 2 inferências; as 4 dores
  (latência, custo, complexidade de layout, leitura fraca de gráficos); objetivo: abordagem que
  reduza latência/custo mantendo/aumentando acurácia. Encerrar com **parágrafo-roteiro**.
- **Fontes:** design §1, `docs/06` (Tech4.ai).
- **Visuais:** nenhum (ou Figura 1 da arquitetura, se preferir abrir aqui).

### 2. Metodologia  (~2 pp)
- **Objetivo:** descrever como a pesquisa foi conduzida (rigor + reprodutibilidade).
- **Conteúdo:** (1) varredura paralela de literatura/repositórios/docs (6 frentes →
  `docs/01-07`); (2) abordagens consideradas e **descartadas rapidamente** e por quê
  (ex.: treinar modelo do zero; OCR clássico puro sem layout; modelos que exigem cluster de GPU);
  (3) **Uso de Ferramentas de IA** — declarar honestamente o uso do *Claude Code* (Opus) como
  copiloto de pesquisa, geração de POC e análise, mantendo a análise crítica e as conclusões como
  autorais; (4) **framework de métricas**: Field-F1/exact-match determinístico vs. *ground truth*
  E *LLM-as-judge* (com a ressalva de não-calibração), latência/página, custo/documento.
- **Fontes:** design §2/§4, `docs/01`, `docs/08` (não-calibração do juiz).
- **Visuais:** nenhum.

### 3. Técnicas e Modelos Avaliados  (~3 pp)
- **Objetivo:** *shortlist* analítica das técnicas/modelos mais viáveis.
- **Conteúdo:** abrir com a técnica transversal — **colapsar 2→1 via *single-pass* + *structured
  output* (*constrained decoding*)** — e então a *shortlist* de motores:
  - **A. VLM proprietário pequeno** (Gemini Flash/Lite, GPT-4o-mini): menor esforço, sem infra.
  - **B. VLM open-source self-hosted** (Qwen2.5-VL-7B): custo marginal ~0 em escala, exige GPU.
  - **C. Document AI gerenciado** (Azure/Google Layout) + LLM pequeno: conservador, robusto.
  - **D. Híbrido para documento extenso** (PyMuPDF determinístico + VLM só na figura).
  Discutir *trade-offs* de cada um (acurácia × custo × latência × infra × manutenção).
- **Fontes:** `docs/02` (structured output), `docs/03` (VLMs), `docs/04` (especializados/OCR-free),
  `docs/05` (Document AI), design §3.
- **Visuais:** **Tabela 1** — comparativo das técnicas (colunas: técnica, ataca quais dores, infra,
  custo relativo, maturidade, risco).

### 4. Resultados e Experimentos  (~4-5 pp) — coração empírico
- **Objetivo:** apresentar métricas, experimentos (POC + benchmarks de terceiros) e *trade-offs*.
- **Conteúdo:**
  1. **Setup da POC:** OpenRouter, SDK `openai`, 3 documentos, matriz modelo × documento × {single, two_step},
     juiz `gpt-4o`, métrica dupla. (Reprodutível; código no repositório.)
  2. **Tese 2→1 (empírico):** *single-pass* consistentemente mais rápido e barato que 2-step com
     acurácia igual/melhor (ex.: fatura/Gemini single 3,3s/US$0,0004 vs 2-step 4,9s/US$0,0006).
  3. **Documento extenso (Caso 2):** **híbrido vs. ingênuo** — VLM no PDF inteiro (28MB/42p) FALHA
     (615s → erro do provedor); híbrido extrai 42p em ~5s a custo zero + VLM só na figura.
  4. **Documento estruturado (CNH) — estudo de robustez:** baixa-res (341×600); *upscaling* não
     ajuda; prompt ancorado recupera campo de graça; escalar modelo (~57× custo) não recupera
     campos extras; CPF irrecuperável → ablação (`docs/09`, `docs/10`).
  5. **Confiabilidade da avaliação:** juiz LLM **não-calibrado** em baixa-res (gap 0,34–0,66) →
     justifica a métrica determinística dupla (`docs/08`).
  6. **Fundamentação por benchmarks de terceiros:** DocVQA, ChartQA, OmniDocBench, CORD/FUNSD
     (números de `docs/01`, `docs/03`, `docs/04`) — para o que não foi testado localmente.
- **Fontes:** design §4/§11, `docs/01,03,04,08,09,10`, `benchmark/results/{tabela.md,results.json,paper_hibrido.md}`.
- **Visuais:** **Tabela 2** (matriz de resultados da POC); **Tabela 3** (benchmarks de terceiros);
  **Figura 2** (latência × custo por modelo/modo); **Figura 3** (single-pass vs 2-step: barras de
  latência e custo); **Figura 4** (híbrido vs ingênuo no paper).

### 5. Conclusão e Recomendação  (~1,5 pp)
- **Objetivo:** recomendar e justificar.
- **Conteúdo:** recomendar **VLM pequeno + *single-pass* + *structured output*** como motor padrão,
  com **estratégia escalonada** e a **nuance crítica**: escalar para *complexidade* (layout/raciocínio),
  não para *legibilidade* (onde o lever é *preprocessing*/re-captura); **híbrido** para documento
  extenso. Justificar pelos *trade-offs* medidos e pelo contexto Tech4.ai. Equilibrar "tecnologia
  mais nova" × "solução mais viável".
- **Fontes:** design §5/§11.
- **Visuais:** nenhum (ou repetir Figura 2 como âncora).

### 6. Análise de Viabilidade de Integração  (~2-2,5 pp)
- **Objetivo:** custo, infraestrutura e *fit* arquitetural com a Tech4.ai.
- **Conteúdo:** (1) **Custo:** API (US$/1k docs por modelo, extrapolado dos custos medidos) vs.
  self-host GPU (tipo de GPU/VRAM, US$/hora, ponto de equilíbrio de volume); (2) **Infraestrutura:**
  o que cada rota exige (nenhuma para A; GPU + MLOps para B; 2 serviços para C); (3) **Integração
  Tech4.ai:** preservar o envelope `{status, extracted_data}`, reusar o `layout_id` como fonte do
  *JSON Schema*, manter os *validators* determinísticos (CPF/CNPJ) como pós-processamento, trocando
  só o motor 2-LLM → 1-VLM; (4) LGPD/residência de dados (self-host vs. API).
- **Fontes:** `docs/05,06,07`, design §6.
- **Visuais:** **Tabela 4** (estimativa de custo de infra: API vs self-host).

### Referências
- Converter todas as URLs citadas nas notas em referências ABNT (ordem alfabética; veículo em negrito).
- **Fontes:** todas as seções "Fontes" de `docs/01-10`.

---

## Produção de Figuras (matplotlib, a partir de `benchmark/results/results.json`)

Script `dossie/figuras.py` (não versionar em `benchmark/`), gera PNGs em `dossie/figuras/`:
1. **Figura 1 — Arquitetura:** diagrama conceitual atual (2-step) vs proposto (single-pass) vs
   híbrido PDF. (Diagrama desenhado; pode ser matplotlib/box ou descrito para finalização manual.)
2. **Figura 2 — Trade-off:** dispersão/barras latência (s) × custo (US$) por modelo×modo (docs CNH+fatura).
3. **Figura 3 — 2→1:** barras pareadas single vs two_step (latência e custo) para o mesmo modelo.
4. **Figura 4 — Híbrido vs ingênuo (paper):** barras (latência) + anotação de FALHA do ingênuo.

---

## Toolchain & Montagem

1. Instalar `pip install pypandoc-binary` (empacota pandoc). Verificar `pypandoc.get_pandoc_version()`.
2. Instalar TinyTeX (Windows, sem admin) — via script oficial; se falhar, fallback DOCX/HTML.
3. Estrutura de arquivos: seções em `dossie/secoes/NN-*.md`; montar `dossie/dossie.md` (concatenado,
   front matter YAML para pandoc: título, autor, data, `documentclass: article`, `geometry`, `lang: pt-BR`).
4. Converter: `pandoc dossie/dossie.md -o dossie/Dossie-Wellinton.pdf --pdf-engine=xelatex --toc`
   (numbered sections, TOC, fontes com acentos via xelatex). Ajustar template para a estética do TCP.

---

## Plano de Execução (subagentes sonnet; controlador opus revisa e costura)

1. **Setup:** instalar toolchain (pandoc+TinyTeX), validar com um "hello world" .md→.pdf. (gate)
2. **Figuras:** gerar `dossie/figuras/*.png` a partir dos resultados. (1 subagente)
3. **Redação por seção:** 1 subagente por seção (3, 4 e 6 são as densas; 1, 2, 5 menores), cada um
   recebe o brief desta seção + as notas-fonte; produz `dossie/secoes/NN-*.md` na voz do TCP.
   Ordem: 1 → 2 → 3 → 4 → 5 → 6 → Referências. (Resultados/§4 depende das figuras.)
4. **Revisão de coerência:** controlador lê as seções, verifica continuidade, conectivos, números
   consistentes com `benchmark/results/`, e fecha lacunas.
5. **Montagem + PDF:** concatenar, rodar pandoc, inspecionar o PDF, ajustar.
6. **QA final:** checar contra os 4 critérios do desafio (profundidade, rigor, clareza, pragmatismo),
   conferir que "Engenheiro E Gerente de Produto" conseguem ler, e que o uso de IA está declarado.
7. **Entrega:** PDF + repositório Git remoto (ação externa — só com OK do autor).

---

## Riscos
- **TinyTeX no Windows** pode ser custoso; fallback DOCX/HTML pronto.
- **Acurácia da CNH baixa** é um resultado honesto — enquadrar como *estudo de robustez* e evidência
  da nuance escalonamento≠legibilidade, não como falha da abordagem.
- **n=3 documentos** — declarar como ilustrativo, ancorar generalização nos benchmarks de terceiros.
- **Citações ABNT** a partir de URLs — exige cuidado para não inventar autoria; usar instituição quando aplicável.
