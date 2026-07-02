## 6. Análise de Viabilidade de Integração

A viabilidade de substituição do motor de extração não se restringe à acurácia dos modelos: envolve custo em escala, infraestrutura, compatibilidade arquitetural e residência de dados sensíveis. Esta seção examina cada dimensão para as três rotas da *shortlist* (A: VLM proprietário pequeno; B: *self-hosted*; C: Document AI + LLM pequeno) e encerra com a LGPD.

### 6.1 Custo Operacional em Escala

Os custos por documento mensurados na POC (seção 4) permitem extrapolar estimativas por mil documentos para cada rota via API. A Tabela 5 consolida esses valores, incluindo a opção de *self-host* da Rota B.

Tabela 5 - Estimativa de custo por 1.000 documentos: API por modelo vs. *self-host*

| Rota | Motor | Custo/documento (medido) | Custo/1.000 docs (API) | *Self-host* GPU | Custo/1.000 docs (*self-host*) | Volume de equilíbrio¹ |
|------|------------------|------------------|----------------|------------------|------------------|----------------|
| A | Gemini 2.5 Flash-Lite (*single-pass*) | US$ 0,00027–0,00040 | **US$ 0,27–0,40** | n/a | n/a | n/a |
| A | GPT-4o-mini (*single-pass*) | US$ 0,00226–0,00734 | **US$ 2,26–7,34** | n/a | n/a | n/a |
| A (API) | Qwen2.5-VL-72B (via OpenRouter) | US$ 0,00051–0,00131 | **US$ 0,51–1,31** | n/a | n/a | n/a |
| B | Qwen2.5-VL-7B (*self-hosted*) | custo marginal ≈ 0 | **≈ 0** (marginal) | A10G 24 GB VRAM, ~US$ 0,75–1,00/h | US$ 7,50–10,00² | ~150 k–2,2 M docs/mês³ |
| C | Azure/Google Layout + LLM pequeno | n/a | **US$ 10,30–11,00**⁴ | n/a | n/a | n/a |

Fonte: elaboração própria com base nos resultados da POC (`benchmark/results/results.json`) e nas tabelas de preço dos provedores.

¹ Volume mensal a partir do qual o custo acumulado do *self-host* fica abaixo da rota API de referência, assumindo GPU dedicada 24/7 (30 dias ≈ US$ 720/mês). ² Assumindo throughput de 100 documentos/hora na GPU A10G (VLM-7B em FP16/INT4); instâncias equivalentes em Lambda Labs, RunPod ou AWS EC2 (`g5.xlarge`). ³ Ponto de equilíbrio vs. Gemini Flash-Lite (US$ 0,00033/doc médio): 720/0,00033 ≈ 2,18 M docs/mês; vs. GPT-4o-mini (US$ 0,0048/doc médio): 720/0,0048 ≈ 150 k docs/mês.
⁴ Azure/Google Layout a US$ 10,00/1.000 páginas (Microsoft, 2024; Google, 2024) + LLM pequeno estimado em US$ 0,30–1,00/1.000 docs.

A Rota A com Gemini 2.5 Flash-Lite é a mais barata em qualquer volume (US$ 0,27–0,40/1.000 documentos); o GPT-4o-mini encarece a mesma rota em 10–18× sem ganho de acurácia (seção 4). A Rota B só compensa a partir de 150 mil a 2,2 milhões de documentos/mês; abaixo disso, o custo fixo supera o variável de API. A Rota C tem o maior custo operacional entre as três.

### 6.2 Requisitos de Infraestrutura

Cada rota impõe exigências distintas de implantação, manutenção e maturidade operacional:

1. **Rota A, VLM proprietário via API:** nenhuma infraestrutura além de chave de API e HTTPS. Menor *time-to-market* e risco operacional, ideal sem *expertise* em MLOps.

2. **Rota B, self-hosted (Qwen2.5-VL-7B):** exige GPU com 16–24 GB VRAM em FP16 (8 GB em INT4), servidor de inferência (vLLM/TGI), fila assíncrona, *pipeline* de MLOps e equipe com competência em infra de ML, custo humano e operacional que se soma à GPU no TCO.

3. **Rota C, Document AI + LLM pequeno:** dois serviços em sequência: OCR/*layout* convertendo em Markdown estruturado, depois LLM pequeno para extração tipada. Duas integrações, dois SLAs, dois pontos de falha e latência composta; ambos gerenciados, sem GPU própria, mas *pipeline* mais complexo que a Rota A.

### 6.3 Integração com a Plataforma Tech4.ai

O aspecto de maior valor estratégico é que a substituição do motor pode ser *drop-in*, sem alterar nada visível ao cliente. A documentação da Tech4.ai (TECH4.AI, 2024) evidencia quatro pontos de compatibilidade direta. Primeiro, o **envelope de resposta é preservado**: o contrato `{"status": ..., "extracted_data": {...}}` permanece inalterado: o VLM com *structured output* emite o JSON diretamente na única chamada, derivando `"partial"` quando campos opcionais retornam `null`, exatamente a semântica atual. Segundo, o **`layout_id` é reutilizado como fonte do JSON Schema**: nome, tipo e descrição de cada campo mapeiam 1:1 para um JSON Schema passado a `response_format.json_schema`; o *visual builder* existente permanece intacto, só o motor interno muda. Terceiro, os **validators determinísticos são mantidos como pós-processamento**: CPF, CNPJ, UF e Linha Digitável continuam rodando após a saída do VLM. Quarto, a **compatibilidade de transporte** é integral: *endpoint*, autenticação, parâmetros e códigos HTTP permanecem inalterados: a troca de 2 LLMs para 1 VLM *single-pass* é totalmente interna. O ganho operacional (uma chamada a menos, ~32% de latência, seção 4) é obtido sem quebra de contrato nem impacto nas integrações existentes.

### 6.4 LGPD e Residência de Dados

Os documentos da Tech4.ai incluem dados pessoais sensíveis (LGPD, Brasil 2018): a CNH traz nome, CPF, data de nascimento e registro; a fatura, nome, endereço e CPF. Processá-los via API de terceiros exige base legal adequada, cláusulas contratuais com o provedor e avaliação da localização dos servidores.

A Rota B (*self-host*) oferece a maior proteção: o documento nunca sai da infraestrutura do operador, relevante para setores regulados (financeiro, saúde, público) com exigência de processamento *on-premise*. A Rota A depende das políticas de privacidade do provedor; ambos afirmam não treinar modelos com dados de API pagos, mas o dado egresso é uma superfície de risco a avaliar pelo DPO. A Rota C tem o mesmo perfil da A, com o risco adicional de dois provedores receberem o dado. Serviços gerenciados (Azure, Google) oferecem implantação em regiões específicas (incluindo o Brasil), mitigando parte do risco sem eliminar a exposição a infraestrutura de terceiros.

A análise de viabilidade converge para a Rota A como ponto de entrada recomendado (menor custo, zero infraestrutura adicional, integração *drop-in*), com a Rota B reservada para alto volume ou requisitos estritos de residência de dados (seção 5).

<!-- refs:
BRASIL. **Lei n. 13.709, de 14 de agosto de 2018**: Lei Geral de Proteção de Dados Pessoais (LGPD). Brasília: Presidência da República, 2018. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm. Acesso em: jun. 2026.

GOOGLE. **Document AI pricing**. Google Cloud, 2024. Disponível em: https://cloud.google.com/document-ai/pricing. Acesso em: jun. 2026.

MICROSOFT. **Azure AI Document Intelligence pricing**. Microsoft Azure, 2024. Disponível em: https://azure.microsoft.com/en-us/pricing/details/document-intelligence/. Acesso em: jun. 2026.

OPENROUTER. **Usage accounting**. OpenRouter Docs, 2026. Disponível em: https://openrouter.ai/docs/cookbook/administration/usage-accounting. Acesso em: jun. 2026.

OPENROUTER. **Structured outputs**. OpenRouter Docs, 2026. Disponível em: https://openrouter.ai/docs/guides/features/structured-outputs. Acesso em: jun. 2026.

TECH4.AI. **Vision: Doc Extraction API**. Tech4.ai Docs, 2024. Disponível em: https://docs.tech4.ai/vision/doc-extraction-api. Acesso em: jun. 2026.

TECH4.AI. **Vision: Layout Configuration**. Tech4.ai Docs, 2024. Disponível em: https://docs.tech4.ai/vision/layout-config. Acesso em: jun. 2026.
-->
