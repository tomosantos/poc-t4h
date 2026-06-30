## 6. Análise de Viabilidade de Integração

A viabilidade de substituição do motor de extração atual não se restringe à acurácia dos modelos; envolve, igualmente, custo operacional em escala, requisitos de infraestrutura, compatibilidade arquitetural com o produto existente e conformidade legal quanto à residência de dados sensíveis. Esta seção examina cada uma dessas dimensões para as três rotas da *shortlist* — A (VLM proprietário pequeno), B (VLM *open-source* *self-hosted*) e C (Document AI gerenciado + LLM pequeno) — e encerra com considerações sobre proteção de dados à luz da LGPD.

### 6.1 Custo Operacional em Escala

Os custos por documento mensurados na POC (seção 4) permitem extrapolar estimativas por mil documentos para cada rota via API. A Tabela 4 consolida esses valores, incluindo a opção de *self-host* da Rota B.

Tabela 4 - Estimativa de custo por 1.000 documentos: API por modelo vs. *self-host*

| Rota | Motor | Custo/documento (medido) | Custo/1.000 docs (API) | *Self-host* GPU | Custo/1.000 docs (*self-host*) | Volume de equilíbrio¹ |
|---|---|---|---|---|---|---|
| A | Gemini 2.5 Flash-Lite (*single-pass*) | US$ 0,00027–0,00040 | **US$ 0,27–0,40** | — | — | — |
| A | GPT-4o-mini (*single-pass*) | US$ 0,00226–0,00734 | **US$ 2,26–7,34** | — | — | — |
| A (API) | Qwen2.5-VL-72B (via OpenRouter) | US$ 0,00051–0,00131 | **US$ 0,51–1,31** | — | — | — |
| B | Qwen2.5-VL-7B (*self-hosted*) | custo marginal ≈ 0 | **≈ 0** (marginal) | A10G 24 GB VRAM, ~US$ 0,75–1,00/h | US$ 7,50–10,00² | ~150 k–2,2 M docs/mês³ |
| C | Azure/Google Layout + LLM pequeno | — | **US$ 10,30–11,00**⁴ | — | — | — |

Fonte: elaboração própria com base nos resultados da POC (`benchmark/results/results.json`) e nas tabelas de preço dos provedores.

¹ Volume mensal a partir do qual o custo acumulado do *self-host* torna-se inferior ao custo acumulado da rota API de referência, assumindo GPU dedicada rodando em regime contínuo (24 h/dia, 30 dias = ~US$ 720/mês).
² Assumindo throughput de 100 documentos/hora na GPU A10G (estimativa conservadora para inferência de um VLM-7B em FP16/INT4); instâncias equivalentes disponíveis em provedores como Lambda Labs, RunPod e AWS EC2 (`g5.xlarge`).
³ Ponto de equilíbrio vs. Gemini Flash-Lite (US$ 0,00033/doc médio): 720/0,00033 ≈ 2,18 M docs/mês. Vs. GPT-4o-mini (US$ 0,0048/doc médio): 720/0,0048 ≈ 150 k docs/mês.
⁴ Azure AI Document Intelligence Layout a US$ 10,00/1.000 páginas (Google Document AI Layout Parser equivalente) (Microsoft, 2024; Google, 2024) + LLM pequeno (Gemini Flash-Lite) estimado em US$ 0,30–1,00/1.000 docs.

Dessa forma, a Rota A com Gemini 2.5 Flash-Lite é, por ampla margem, a mais barata em qualquer volume — US$ 0,27–0,40/1.000 documentos — ao passo que o GPT-4o-mini encarece a mesma rota em 10–18 vezes sem ganho de acurácia correspondente, conforme verificado na matriz da POC (seção 4). A Rota B (*self-host*) só compensa economicamente a partir de volumes da ordem de 150 mil a 2,2 milhões de documentos por mês, dependendo do modelo API de referência, e exige que a GPU opere em regime de alta ocupação; abaixo desse patamar, o custo fixo de infraestrutura supera o custo variável de API. A Rota C, embora conservadora em termos de risco técnico, apresenta o maior custo operacional entre as rotas analisadas.

### 6.2 Requisitos de Infraestrutura

Cada rota impõe exigências distintas de implantação, manutenção e maturidade operacional:

1. **Rota A — VLM proprietário pequeno via API:** nenhuma infraestrutura adicional além de uma chave de API e conectividade HTTPS. O gerenciamento de modelos, escalabilidade, redundância e atualizações de versão são responsabilidade do provedor. É a rota de menor *time-to-market* e de mais baixo risco operacional; adequada para estágios iniciais e para equipes sem *expertise* em MLOps.

2. **Rota B — VLM *open-source* *self-hosted* (Qwen2.5-VL-7B):** exige GPU com no mínimo 16–24 GB de VRAM (ex.: NVIDIA A10G ou RTX 4090) para inferência em FP16; em INT4 (*quantized*), é possível reduzir para 8 GB de VRAM com degradação mínima de acurácia. Além do hardware, requer: (a) servidor de inferência (*vLLM*, *TGI* ou equivalente); (b) fila de tarefas assíncronas para absorver picos de volume; (c) *pipeline* de MLOps para monitoramento de *drift*, atualização de versão e *rollback*; (d) time com competência em infraestrutura de ML. O custo de capital humano e operacional deve ser somado ao custo de GPU ao avaliar o TCO (*Total Cost of Ownership*).

3. **Rota C — Document AI gerenciado + LLM pequeno:** dois serviços distintos orquestrados em sequência — (a) chamada ao serviço de OCR/layout (Azure AI Document Intelligence Layout ou Google Document AI Layout Parser) para converter o documento em Markdown estruturado; (b) chamada ao LLM pequeno para extração tipada a partir do Markdown. Implica duas integrações de API, dois contratos de SLA, dois pontos de falha e latência composta (2–4 s/página de OCR + latência do LLM). A vantagem é que ambos os serviços são totalmente gerenciados, sem GPU própria, mas o *pipeline* é mais complexo que a Rota A.

### 6.3 Integração com a Plataforma Tech4.ai

Nessa perspectiva, o aspecto de maior valor estratégico da abordagem proposta é que a substituição do motor de extração pode ser realizada de forma *drop-in*, sem alterar nenhum elemento visível ao cliente. A análise da documentação oficial da Tech4.ai (TECH4.AI, 2024) evidencia quatro pontos de compatibilidade direta:

1. **Preservação do envelope de resposta:** o contrato `{"status": "ok"|"partial"|"error", "extracted_data": {...}}` permanece inalterado. Um VLM com *structured output* (*constrained decoding*) emite o objeto JSON diretamente na única chamada de inferência, derivando `"partial"` quando campos opcionais retornam `null` após validação — exatamente a semântica atual.

2. **Reuso do `layout_id` como fonte do *JSON Schema*:** cada layout já define, por campo, nome, tipo de dado e descrição em linguagem natural. Esses três atributos mapeiam 1:1 para as propriedades de um JSON Schema (`"type"`, `"description"`) que pode ser passado ao parâmetro `response_format.json_schema` do VLM. Dessa forma, o *visual builder* existente e o fluxo de configuração de layouts pelo cliente permanecem intactos; apenas o motor de inferência interno é trocado.

3. **Manutenção dos *validators* determinísticos como pós-processamento:** os *validators* nativos de CPF, CNPJ, UF e Linha Digitável de Boleto são algoritmos determinísticos independentes do modelo de IA; sua lógica de retornar `null` para valores inválidos não tem relação com a etapa de inferência. Eles devem continuar rodando **após** a saída do VLM, como camada de pós-processamento, garantindo paridade semântica plena com o comportamento atual e preservando a qualidade dos dados extraídos.

4. **Compatibilidade de transporte:** o endpoint `POST https://api.tech4.ai/document/extract/`, o *header* de autenticação, os parâmetros `file_url` e `layout_id`, e os códigos HTTP (400, 401, 404) permanecem inalterados. A mudança de 2 LLMs para 1 VLM *single-pass* é totalmente interna, invisível para o cliente que consome a API.

Assim, o ganho operacional — eliminação de uma chamada de inferência, redução de latência de 32–46% e redução de custo proporcional (seção 4) — é obtido sem nenhuma quebra de contrato e sem impacto para as integrações já existentes dos clientes da plataforma.

### 6.4 LGPD e Residência de Dados

Os documentos processados pela plataforma Tech4.ai incluem dados pessoais sensíveis no sentido da Lei Geral de Proteção de Dados (Brasil, 2018): a CNH contém nome completo, CPF, data de nascimento e número de registro; a fatura de energia contém nome, endereço e CPF do titular. O processamento desses dados por modelos via API de terceiros implica que o dado transita e é processado fora da infraestrutura do controlador, o que exige base legal adequada, cláusulas contratuais de processamento de dados com o provedor e avaliação da localização dos servidores.

Nesse contexto, a Rota B (*self-host*) oferece a maior proteção de residência de dados: o documento nunca sai da infraestrutura controlada pelo operador, eliminando o risco de transmissão transfronteiriça. Essa característica é relevante especialmente para clientes da Tech4.ai em setores regulados (financeiro, saúde, setor público) onde exigências contratuais ou normativas impõem processamento *on-premise* ou em nuvem soberana. A Rota A, por sua vez, depende das políticas de privacidade de cada provedor de API (Google, OpenAI); ambos afirmam não treinar modelos com dados de clientes via API em suas camadas pagas, mas o dado egresso permanece como superfície de risco a ser avaliada pelo encarregado de proteção de dados (DPO) da organização. A Rota C apresenta o mesmo perfil da Rota A em termos de residência, acrescido do risco de dois provedores distintos receberem o dado.

Além disso, deve-se considerar que serviços de Document AI gerenciados (Azure, Google) oferecem opções de implantação em regiões específicas (incluindo regiões no Brasil), o que pode mitigar parte do risco de transferência internacional, ainda que não elimine a exposição ao processamento por infraestrutura de terceiros.

Por fim, a análise de viabilidade converge para a Rota A como ponto de entrada recomendado — menor custo, zero infraestrutura adicional, integração *drop-in* e *time-to-market* imediato —, com a Rota B reservada para cenários de alto volume ou requisitos estritos de residência de dados, conforme discutido na seção 5.

<!-- refs:
BRASIL. **Lei n. 13.709, de 14 de agosto de 2018**: Lei Geral de Proteção de Dados Pessoais (LGPD). Brasília: Presidência da República, 2018. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm. Acesso em: jun. 2026.

GOOGLE. **Document AI pricing**. Google Cloud, 2024. Disponível em: https://cloud.google.com/document-ai/pricing. Acesso em: jun. 2026.

MICROSOFT. **Azure AI Document Intelligence pricing**. Microsoft Azure, 2024. Disponível em: https://azure.microsoft.com/en-us/pricing/details/document-intelligence/. Acesso em: jun. 2026.

OPENROUTER. **Usage accounting**. OpenRouter Docs, 2026. Disponível em: https://openrouter.ai/docs/cookbook/administration/usage-accounting. Acesso em: jun. 2026.

OPENROUTER. **Structured outputs**. OpenRouter Docs, 2026. Disponível em: https://openrouter.ai/docs/guides/features/structured-outputs. Acesso em: jun. 2026.

TECH4.AI. **Vision: Doc Extraction API**. Tech4.ai Docs, 2024. Disponível em: https://docs.tech4.ai/vision/doc-extraction-api. Acesso em: jun. 2026.

TECH4.AI. **Vision: Layout Configuration**. Tech4.ai Docs, 2024. Disponível em: https://docs.tech4.ai/vision/layout-config. Acesso em: jun. 2026.
-->
