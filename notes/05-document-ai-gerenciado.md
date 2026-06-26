# Workstream 5 — Document AI Gerenciado (serviços de nuvem)

> Nota de pesquisa para o dossiê técnico. Avalia **AWS Textract**, **Azure AI Document Intelligence** (ex-Form Recognizer) e **Google Document AI** como alternativas/complementos ao pipeline atual de 2 passos. Foco em latência, custo, layouts complexos e gráficos. Documentos-alvo: CNH brasileira, fatura CELPE, paper Claude 3.
> Preços e fatos verificados em docs/pricing oficiais (jun/2026), priorizando 2024–2026. "Verificado" = confirmado em página oficial; "Inferido" = derivado de docs secundárias ou raciocínio.

---

## TL;DR (5 bullets)

- **OCR puro é barato e rápido, mas "burro".** Detectar texto custa ~**US$ 1,50/1k págs** nos três provedores (Textract DetectDocumentText, Google Enterprise Document OCR). Latência típica de **2–4 s/página** (Azure), com modo assíncrono recomendado acima de 1 página. [Verificado]
- **Extração estruturada (key-value/tabelas/forms) é 6×–45× mais cara.** Textract Forms+Tables+Queries = **US$ 70/1k págs**; Azure Layout = **US$ 10/1k**, Custom = **US$ 30/1k**; Google Form Parser/Custom = **US$ 30/1k**, Layout Parser = **US$ 10/1k**. [Verificado]
- **PT-BR funciona para texto/tabelas/forms, mas com pegadinhas no Textract:** Queries, Invoices, Receipts e ID **só em inglês**. Google Form Parser 2.0 e Enterprise OCR cobrem **200+ idiomas** (incluindo português). Azure suporta português amplamente. [Verificado]
- **Gráficos/figuras: historicamente NÃO interpretados** (OCR só extrai texto). **Exceção emergente:** o **Google Document AI Layout Parser** agora usa **Gemini** para *verbalizar* figuras, gráficos e tabelas com descrições textuais — quebra a regra "OCR não lê gráfico". Textract e Azure Layout ainda **não interpretam** o conteúdo semântico de charts. [Verificado]
- **Padrão recomendado: Document AI como PRÉ-PROCESSAMENTO (OCR/layout → Markdown) + LLM pequeno para extração estruturada.** Azure Layout e Google Layout Parser já emitem **Markdown LLM-friendly** com tabelas preservadas — reduz custo de tokens e alucinação vs. mandar a imagem crua a um VLM. Vale a pena para CNH e fatura; para o **paper com gráficos**, um VLM direto (ou Google Layout Parser+Gemini) ainda é necessário. [Verificado/Inferido]

---

## Achados

### 1. Capacidades por serviço

**AWS Textract** [Verificado — [pricing](https://aws.amazon.com/textract/pricing/), [FAQs](https://aws.amazon.com/textract/faqs/)]
- APIs: `DetectDocumentText` (OCR), `AnalyzeDocument` (Tables, Forms, Queries, Layout, Signatures), `AnalyzeExpense` (faturas/recibos), `AnalyzeID` (documentos de identidade), `AnalyzeLending`.
- Extrai: texto, tabelas, key-value pairs (forms), respostas a perguntas (Queries), assinaturas, e blocos de layout (parágrafos, títulos, listas).
- **Layout** é gratuito quando usado com a feature Tables.
- **NÃO interpreta gráficos/charts** — apenas extrai texto que estiver dentro/ao redor deles.

**Azure AI Document Intelligence** (ex-Form Recognizer) [Verificado — [pricing](https://azure.microsoft.com/en-us/pricing/details/document-intelligence/), [RAG concept](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept/retrieval-augmented-generation?view=doc-intel-4.0.0)]
- Modelos: `prebuilt-read` (OCR), `prebuilt-layout` (estrutura + tabelas + Markdown), prebuilt para invoice/receipt/ID/business-card, e Custom Extraction/Classification.
- **Layout emite Markdown "LLM-friendly"** (tabelas em Markdown) — projetado explicitamente para chunking semântico e RAG. Suporta add-ons (high-resolution, formula, barcode, font) e Query Fields.
- **NÃO interpreta semanticamente gráficos**; detecta e extrai texto/estrutura.

**Google Document AI** [Verificado — [pricing](https://cloud.google.com/document-ai/pricing), [Layout Parser](https://docs.cloud.google.com/document-ai/docs/layout-parse-chunk), [Form Parser](https://docs.cloud.google.com/document-ai/docs/form-parser), [Enterprise OCR](https://docs.cloud.google.com/document-ai/docs/enterprise-document-ocr)]
- Processadores: **Enterprise Document OCR** (texto + manuscrito, 200+ idiomas), **Form Parser** (key-value + checkbox + tabelas, 200+ idiomas no Form Parser 2.0), **Layout Parser** (chunking + Markdown), **Custom Extractor**, e especializados (Invoice, Expense, Utility, US Driver License/Passport, Bank Statement, Pay Slip, W2).
- **DIFERENCIAL:** o **Layout Parser combina OCR + Gemini** para *anotar figuras, gráficos e tabelas com descrições textuais ricas* ("verbaliza" elementos visuais). É o único dos três que se aproxima de interpretar gráficos de forma gerenciada.

### 2. Preço concreto (US$ por 1.000 páginas) — primeira faixa

| Feature | AWS Textract | Azure Doc Intelligence | Google Document AI |
|---|---|---|---|
| OCR (texto puro) | **$1.50** (DetectDocumentText) | **~$10** prebuilt-read*; $1.50 tier S0** | **$1.50** (Enterprise OCR) |
| Tabelas | $15 | incluso no Layout ($10) | incluso no Form/Layout Parser |
| Forms / key-value | $50 | $10 (Layout) / $30 (Custom) | $30 (Form Parser) |
| Queries / Query Fields | $15 (custom $25) | $10 add-on | — |
| Layout/estrutura → Markdown | grátis c/ Tables | **$10** (Layout) | **$10** (Layout Parser) |
| Combo Forms+Tables+Queries | **$70** | ~$20–30 | ~$30 |
| Especializado (invoice/ID) | $10 (Expense) / $25 (ID) | ~$10 | **$0.10/doc até 10 págs** (Invoice/DL Parser) |

\* Nota: o valor "$10/1k" para `prebuilt-read` aparece em fontes secundárias; o **tier S0 padrão da Azure cobra OCR (Read) próximo de US$ 1,50/1k** e Layout a US$ 10/1k. Conferir na calculadora oficial Azure para a região. [Inferido — divergência entre fontes]
\*\* Faixas com desconto acima de 1M págs/mês (ex.: Textract OCR cai p/ $0.60; Forms p/ $40; Google OCR p/ $0.60 acima de 5M).

**Custo/página (comparação rápida, OCR simples):** os três convergem em **~US$ 0,0015/página** (US$ 1,50/1k). Para extração estruturada completa, **Textract é o mais caro** (US$ 0,07/pág no combo), enquanto **Azure/Google Layout ficam em US$ 0,01/pág**. Para a **CNH**, o **Google Driver License Parser a US$ 0,10/documento** é imbatível em custo unitário se a CNH cair no parser US (atenção: é parser *americano*, não brasileiro — provavelmente **não** serve para CNH-BR; usar Form Parser/Custom). [Verificado/Inferido]

### 3. Latência típica

- **Síncrono:** Textract limita ~**5 req/s** e "poucas páginas/s"; adequado a 1 página em tempo real. [Verificado — [re:Post](https://repost.aws/questions/QUGiJwOYntTM2z3Hpnrz4lTw/textract-performance-degradation)]
- **Assíncrono (recomendado p/ multipágina):** Textract processou **200 páginas em <2 min** (~1,7 pág/s) e a AWS reduziu a latência end-to-end do async em **até 50%**. [Verificado — [AWS blog](https://aws.amazon.com/blogs/aws/amazon-textract-updates-up-to-32-price-reduction-in-8-aws-regions-and-up-to-50-reduction-in-asynchronous-job-processing-times/)]
- **Azure:** **2–4 s/página** típico; relatos de 3–7 s no `prebuilt-read` S0; alerta de problema acima de 15 s/pág sustentado. [Verificado — [troubleshoot-latency](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept/troubleshoot-latency?view=doc-intel-4.0.0)]
- **Comparativo-chave:** OCR gerenciado (2–4 s/pág) é **substancialmente mais rápido que um VLM** rodando a imagem inteira, o que sustenta o padrão "pré-processar com OCR barato + LLM pequeno só no texto". [Verificado/Inferido]

### 4. Gráficos/imagens não-textuais e multipágina

- **Regra geral CONFIRMADA: OCR/Document AI clássico NÃO interpreta gráficos.** Eles extraem o texto presente (eixos, legendas) mas **não entendem** o que o gráfico comunica. Documentos que misturam texto + charts + imagens "quebram" OCR tradicional. [Verificado — pesquisa OCR vs VLM 2025]
- **Exceção/tendência 2024–2026:** o **Google Layout Parser usa Gemini para gerar descrições textuais de figuras, gráficos e tabelas** — efetivamente *verbalizando* o visual. É a forma gerenciada mais próxima de "ler gráfico". [Verificado — [Layout Parser docs](https://docs.cloud.google.com/document-ai/docs/layout-parse-chunk)]
- **Multipágina:** todos lidam bem via **modo assíncrono** (Textract async aceita PDF/TIFF multipágina; Azure e Google processam documentos longos nativamente). O risco real é **tabela que cruza páginas** e estrutura aninhada, onde tanto OCR quanto VLM têm dificuldade. [Verificado]
- **Implicação para o paper Claude 3 (Documento 3):** OCR puro perde o significado dos gráficos. Opções: (a) **Google Layout Parser+Gemini**, ou (b) **VLM direto** nas páginas com figuras. Para CNH e fatura CELPE (sem gráficos analíticos), OCR/layout gerenciado é suficiente.

### 5. Padrão de arquitetura — Document AI como pré-processamento vs. VLM direto

**Padrão proposto:** `Documento → Document AI (OCR/Layout) → Markdown estruturado → LLM pequeno → JSON`.

A favor (vs. mandar imagem crua a um VLM grande):
- **Custo de token menor:** texto/Markdown consome muito menos que tiles de imagem em alta resolução; o LLM extrator pode ser pequeno/barato. [Inferido]
- **Menos alucinação e melhor grounding:** Azure/Google emitem **Markdown LLM-friendly com tabelas preservadas**, projetado para RAG e extração — VLMs alucinam quando pistas visuais são ambíguas. [Verificado — [Azure RAG](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept/retrieval-augmented-generation?view=doc-intel-4.0.0)]
- **Latência previsível:** OCR 2–4 s/pág + 1 chamada de LLM curta tende a ser mais rápido/barato que um VLM processando a imagem inteira por página. [Inferido]

Contra / quando o VLM direto vence:
- **Gráficos e diagramas** (paper Claude 3): o pré-processamento OCR descarta a semântica visual; aí o VLM (ou Layout Parser+Gemini) é necessário.
- **Layouts muito visuais/dependentes de cor/posição** onde a estrutura é o conteúdo.

**Recomendação para os 3 documentos:**
- **CNH (Doc 1):** Document AI (Form/Custom) → LLM pequeno. Layout previsível, OCR resolve.
- **Fatura CELPE (Doc 2):** **Azure Layout → Markdown → LLM pequeno** (tabelas densas se beneficiam do Markdown estruturado), ou Textract Tables+Queries.
- **Paper Claude 3 (Doc 3):** **híbrido** — Layout Parser+Gemini *ou* VLM direto nas páginas com gráficos; OCR puro nas páginas só-texto.

---

## Tabela comparativa

| Serviço | Capacidades | Custo/1k págs (1ª faixa) | Latência | Gráficos? | PT-BR? |
|---|---|---|---|---|---|
| **AWS Textract** | OCR, Tables, Forms (KV), Queries, Layout, Signatures, Expense, ID | OCR $1.50; Tables $15; Forms $50; combo $70; Expense $10; ID $25 | Sync ~5 req/s; **async ~1,7 pág/s** (200 págs <2 min) | **Não** (só texto) | **Parcial** — texto/tabelas/forms sim; **Queries/Invoice/Receipt/ID só inglês** |
| **Azure AI Document Intelligence** | Read (OCR), Layout (+Markdown/RAG), prebuilt invoice/receipt/ID, Custom Extraction/Classification | Layout $10; Custom $30; Classification $3; Query Fields $10; add-ons $6 | **2–4 s/pág** (3–7 s relatado) | **Não** (detecta, não interpreta) | **Sim** (amplo) |
| **Google Document AI** | Enterprise OCR, Form Parser (KV+tabelas), Layout Parser (+Gemini, Markdown), Custom Extractor, especializados (invoice/DL/etc.) | OCR $1.50; Form/Custom $30; Layout $10; especializados $0.10/doc | Assíncrono; comparável (~seg/pág) | **Parcial** — **Layout Parser usa Gemini p/ verbalizar figuras/gráficos** | **Sim** — Form Parser 2.0 e OCR cobrem **200+ idiomas** |

---

## Fontes (URLs)

- AWS Textract — Pricing: https://aws.amazon.com/textract/pricing/
- AWS Textract — FAQs (idiomas suportados, PT/Queries só inglês): https://aws.amazon.com/textract/faqs/
- AWS — Textract price reduction & async latency -50%: https://aws.amazon.com/blogs/aws/amazon-textract-updates-up-to-32-price-reduction-in-8-aws-regions-and-up-to-50-reduction-in-asynchronous-job-processing-times/
- AWS re:Post — Textract sync vs async performance: https://repost.aws/questions/QUGiJwOYntTM2z3Hpnrz4lTw/textract-performance-degradation
- AWS docs — Async operations: https://docs.aws.amazon.com/textract/latest/dg/api-async.html
- Azure — Document Intelligence Pricing: https://azure.microsoft.com/en-us/pricing/details/document-intelligence/
- Azure — RAG com Document Intelligence (Markdown LLM-friendly): https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept/retrieval-augmented-generation?view=doc-intel-4.0.0
- Azure — Troubleshoot latency (2–4 s/pág, limite 15 s): https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/concept/troubleshoot-latency?view=doc-intel-4.0.0
- Google — Document AI Pricing: https://cloud.google.com/document-ai/pricing
- Google — Layout Parser + Gemini (verbaliza figuras/gráficos): https://docs.cloud.google.com/document-ai/docs/layout-parse-chunk
- Google — Form Parser (200+ idiomas): https://docs.cloud.google.com/document-ai/docs/form-parser
- Google — Enterprise Document OCR (200+ idiomas): https://docs.cloud.google.com/document-ai/docs/enterprise-document-ocr
- Contexto OCR vs VLM 2025 (gráficos, hibrido): https://atul4u.medium.com/beyond-text-extraction-the-2025-open-ocr-revolution-powered-by-vision-language-models-89ad33d36bbf
- DeepLearning.AI — Document AI: From OCR to Agentic Doc Extraction: https://learn.deeplearning.ai/courses/document-ai-from-ocr-to-agentic-doc-extraction/lesson/60su3x/layout-detection-and-reading-order

---

## Lacunas (a fechar antes do dossiê final)

- **Acurácia real em CNH-BR e fatura CELPE:** nenhum benchmark oficial testa documentos brasileiros específicos. Recomenda-se medir na POC (campos corretos / total).
- **Preço Azure `prebuilt-read` (OCR):** divergência entre fontes ($1.50 tier S0 vs ~$10 secundário). Confirmar na calculadora oficial Azure por região.
- **Latência Google Document AI:** docs oficiais não publicam pág/s; valor "comparável" é inferido. Medir empiricamente.
- **Qualidade do Gemini do Layout Parser em gráficos do paper:** docs afirmam que "verbaliza" figuras, mas não há métrica de fidelidade em charts científicos. Validar na POC com o Documento 3.
- **CNH brasileira vs parsers de ID:** AnalyzeID (Textract) e US Driver License Parser (Google) são focados em docs **americanos**; provável necessidade de Custom/Form Parser para CNH-BR. Confirmar.
- **Custo end-to-end do padrão OCR→LLM:** falta somar custo do OCR + tokens do LLM pequeno e comparar lado a lado com VLM direto (US$/documento). Calcular na fase de experimentos.
- **Residência de dados / LGPD:** não investigado se há região br-SP/processamento local para dados sensíveis (CNH). Verificar.
