## 3. Técnicas e Modelos Avaliados

A análise das dores identificadas no *pipeline* atual — latência elevada, custo redundante, fragilidade ante layouts complexos e incapacidade de interpretar gráficos — aponta para uma técnica transversal que antecede a escolha do motor: o colapso das duas inferências em uma única chamada. Essa técnica é aplicável a todas as abordagens da *shortlist* e representa o ganho arquitetural de maior impacto imediato.

### 3.1 Técnica Transversal: *Single-Pass* com *Structured Output* (*Constrained Decoding*)

O *pipeline* vigente executa, sequencialmente, duas chamadas de modelo de linguagem: a primeira para interpretar o documento e a segunda para formatar a saída em JSON. Essa separação foi historicamente justificada pela incapacidade dos modelos de garantir JSON sintaticamente válido e conforme a um *schema* ao mesmo tempo em que realizavam a tarefa de extração. O *constrained decoding* elimina essa necessidade ao restringir, em tempo de decodificação, os tokens amostráveis àqueles que mantêm a saída válida em relação ao *schema* fornecido — transformando a conformidade de uma "instrução no *prompt*" em uma garantia de engenharia (OpenAI, 2024; Anthropic, 2025; Dong et al., 2024).

Todos os provedores principais disponibilizam implementações gerenciadas dessa técnica: o **OpenAI Structured Outputs** (`json_schema` com `strict: true`, disponível desde `gpt-4o-2024-08-06`) reporta **100% de conformidade** ao *schema* em avaliações internas, contra menos de 40% com *prompting* tradicional e aproximadamente 86% com *function calling* clássico (OpenAI, 2024); o **Anthropic Structured Outputs** (disponível em disponibilidade geral desde novembro de 2025) compila o *schema* em uma gramática e a cacheia por 24 horas, eliminando o custo de compilação em chamadas subsequentes (Anthropic, 2025); o **Gemini `responseSchema`** opera de forma equivalente, com a ressalva de que a ordem das propriedades no *schema* deve corresponder às descrições no *prompt* para evitar saída malformada (Google, 2025). No ecossistema *open-source*, o **XGrammar** — adotado como *backend* padrão pelo vLLM, SGLang e TensorRT-LLM — implementa *constrained decoding* via autômato de pilha com *bitmask* de vocabulário pré-computável, alcançando *overhead* inferior a **40 µs/token** e, segundo estudo apresentado no MLSys 2025, aceleração de até 100× em relação a soluções anteriores de *constrained decoding* (Dong et al., 2024). A biblioteca **Outlines** (dottxt), baseada em autômatos de estados finitos, adiciona a técnica de *coalescence*, que permite pular tokens fixos do *schema* durante a geração e reporta aceleração de até 5× em relação à geração livre (dottxt, 2024).

Em relação ao impacto sobre a acurácia de extração, o debate foi encerrado empiricamente: o artigo "Let Me Speak Freely?" (Tam et al., EMNLP 2024) identificou degradação em tarefas de raciocínio com *JSON mode*, mas a refutação da dottxt ("Say What You Mean", 2024) demonstrou que os resultados decorriam de *prompts* assimétricos entre condições; com *prompts* idênticos, o *structured output* empata ou supera a geração livre (GSM8K: 0,77 → 0,78; Last Letter: 0,73 → 0,77). Para tarefas de extração de documentos — próximas a *slot-filling* e classificação, e não a raciocínio multi-passo — a evidência favorece ganho ou neutralidade de acurácia, especialmente quando um campo de raciocínio livre antecede os campos de extração no *schema* (Tam et al., 2024; dottxt, 2024). O colapso de duas inferências em uma reduz a latência e o custo atribuíveis à etapa de formatação sem exigir nova infraestrutura nos provedores gerenciados.

### 3.2 *Shortlist* de Motores

Estabelecida a técnica transversal, a escolha do motor de inferência determina o equilíbrio entre custo, infraestrutura, maturidade e cobertura das dores restantes. A *shortlist* a seguir é organizada pelos rótulos canônicos utilizados ao longo deste dossiê.

**Opção A — VLM proprietário pequeno (Gemini Flash-Lite / GPT-4o-mini).** Modelos da classe "Flash" ou "mini" leem a imagem do documento nativamente — sem OCR externo — e emitem JSON estruturado em uma única chamada, atacando simultaneamente a latência elevada (duas inferências → uma), o custo redundante e a limitação de leitura de gráficos. O Gemini 2.5 Flash-Lite apresenta custo de US$ 0,10/1M *tokens* de entrada e US$ 0,40/1M de saída; o GPT-4o-mini, US$ 0,15 e US$ 0,60 respectivamente (OPENAI, 2025; GOOGLE, 2024). A infraestrutura exigida é mínima: acesso via API REST, sem GPU, sem MLOps. O *Structured Output* gerenciado pelo provedor está disponível imediatamente. O risco principal é a dependência de terceiros para dados potencialmente sensíveis (CNH, documentos fiscais) e a variabilidade de preço ao longo do tempo.

**Opção B — VLM *open-source* self-hosted (Qwen2.5-VL-7B).** O Qwen2.5-VL-7B constitui o ponto de equilíbrio da família Qwen em documentos estruturados: marca **DocVQA 95,7** e **ChartQA 87,3**, contra 96,4 e 89,5 do modelo de 72 bilhões de parâmetros — um gap inferior a 1 ponto percentual em DocVQA e de aproximadamente 2 pontos em ChartQA (Qwen, 2025). Essa proximidade torna o modelo de 7B praticamente equivalente ao maior para formulários previsíveis (CNH) e faturas. O custo marginal por documento tende a zero em escala, uma vez amortizada a infraestrutura de GPU. Para fins de comparação, a mesma classe de modelo em via de API intermediada (OpenRouter) apresentou latência de **6,17 s** e custo de **US$ 0,00051** na CNH, contra **2,61 s** e **US$ 0,00027** do Gemini Flash-Lite no mesmo modo *single-pass* (resultados da POC, 2026). O *constrained decoding* é implementado via vLLM com XGrammar como *backend* padrão. Os riscos centrais são: necessidade de GPU (aproximadamente 16-20 GB de VRAM em *bf16*, ou 8 GB em quantização 4-bit), MLOps associado, e maturidade menor de suporte de longo prazo do que APIs gerenciadas.

**Opção C — Document AI gerenciado + LLM pequeno.** Nessa arquitetura, um serviço de *Document AI* em nuvem (Azure AI Document Intelligence Layout ou Google Document AI Layout Parser) converte o documento em Markdown estruturado — com tabelas preservadas, listas e hierarquia de títulos — antes de uma única chamada de LLM pequeno para extração de campos. O Azure Layout e o Google Layout Parser estão precificados em **US$ 10/1.000 páginas** (OCR estruturado com Markdown LLM-*friendly*), enquanto o OCR puro dos três provedores converge em aproximadamente **US$ 1,50/1.000 páginas** (MICROSOFT, 2024; GOOGLE, 2024; AWS, 2025). A vantagem é a maturidade e o suporte a documentos multipágina via modo assíncrono (AWS Textract processou 200 páginas em menos de 2 minutos no modo *async*). O diferencial do Google Layout Parser é relevante para documentos com gráficos analíticos: o processador utiliza Gemini para *verbalizar* figuras e gráficos com descrições textuais, sendo o único dos três provedores a se aproximar da interpretação semântica de *charts* (GOOGLE, 2024). A limitação da opção C é a arquitetura em dois serviços (Document AI + LLM), que reintroduz uma camada de integração e pode elevar a latência total. O risco de residência de dados (LGPD) é análogo ao da opção A.

**Opção D — Híbrido (PyMuPDF + VLM seletivo) para documento extenso.** Para documentos multipágina com camada de texto nativa (PDFs digitais como artigos acadêmicos), a abordagem mais eficiente separa o processamento por tipo de conteúdo: PyMuPDF extrai texto e tabelas de forma determinística, sem custo de inferência; o VLM é invocado apenas nas páginas que contêm figuras ou gráficos analíticos. Os resultados da POC demonstram o impacto dessa separação de forma inequívoca: a tentativa ingênua de enviar o PDF completo de 42 páginas e 28 MB a um VLM resultou em falha do provedor após aproximadamente 615 segundos; a abordagem híbrida extraiu o texto das 42 páginas em **~4,7 s a custo zero** via PyMuPDF, mais uma chamada de VLM de **~4,3 s a US$ 0,00039** para a figura principal — total de aproximadamente **9 s** (POC, 2026). Essa opção não conflita com as anteriores: o VLM seletivo pode ser qualquer motor da *shortlist* (A ou B), operando com *structured output*.

### 3.3 Síntese Comparativa

Tabela 1 - Comparativo de técnicas e motores avaliados

| Técnica / Motor | Dores atacadas | Infraestrutura | Custo relativo | Maturidade | Risco principal |
|---|---|---|---|---|---|
| **A — VLM proprietário pequeno** (Gemini Flash-Lite, GPT-4o-mini) + *single-pass* + *structured output* | Latência (2→1 inferência), custo da 2ª chamada, leitura de gráficos/tabelas | API REST; sem GPU | Baixo (US$ 0,00027–0,00040/doc; ~US$ 10/1M *tokens* saída) | Alta (GA em todos os provedores; docs extensas, SLA definido) | Dependência de provedor; privacidade de dados; variação de preço |
| **B — VLM OSS self-hosted** (Qwen2.5-VL-7B) + vLLM/XGrammar | Latência (2→1), custo marginal zero em escala, leitura visual | GPU (≥8 GB VRAM com 4-bit); MLOps | Zero marginal (capex GPU); ~US$ 0,00051/doc via API intermediada | Média (modelo maduro; ecossistema vLLM estável; suporte longo prazo incerto) | Infra GPU/MLOps; custo de operação; curva de implantação |
| **C — Document AI gerenciado + LLM pequeno** (Azure/Google Layout) | Latência (OCR rápido + 1 LLM), robustez em tabelas/formulários, multipágina | Dois serviços de nuvem; sem GPU | Médio (US$ 10/1k págs OCR estruturado + tokens LLM) | Alta (Azure/Google: SLA, suporte, auditoria); Google Layout Parser interpreta gráficos via Gemini | Dois pontos de integração; latência acumulada; Google Layout + Gemini para charts (qualidade em charts científicos não benchmarkada) |
| **D — Híbrido** (PyMuPDF + VLM seletivo) | Documento extenso: falha do VLM ingênuo, custo/página, latência | PyMuPDF (CPU, sem GPU); VLM só nas páginas com figuras | Muito baixo (texto: custo zero; figuras: ~US$ 0,00039/figura) | Média (PyMuPDF madura; integração requer orquestração de dois caminhos) | Detecção de páginas com figuras; manutenção do orquestrador; não se aplica a imagens digitalizadas |

Fonte: elaboração própria com base em OpenAI (2024; 2025), Anthropic (2025), Google (2024), Microsoft (2024), AWS (2024; 2025), Qwen (2025), Dong et al. (2024) e resultados da POC (2026).

A análise comparativa evidencia que nenhum motor isolado é ótimo para todos os tipos de documento: a escolha racional é uma estratégia escalonada — opção A como motor padrão de baixo esforço, opção B para escala com custo marginal tendendo a zero, opção C quando maturidade operacional e suporte institucional são requisitos, e opção D para documentos extensos com texto digital. A Seção 4 apresenta os resultados empíricos da POC e os *benchmarks* de terceiros que fundamentam quantitativamente essa hierarquia.

<!-- refs:
ANTHROPIC. **Structured Outputs**. San Francisco: Anthropic, 2025. Disponível em: https://platform.claude.com/docs/en/build-with-claude/structured-outputs. Acesso em: jun. 2026.

AWS. **Amazon Textract Pricing**. Seattle: Amazon Web Services, 2025. Disponível em: https://aws.amazon.com/textract/pricing/. Acesso em: jun. 2026.

AWS. **Amazon Textract Updates**. Seattle: Amazon Web Services, 2024. Disponível em: https://aws.amazon.com/blogs/aws/amazon-textract-updates-up-to-32-price-reduction-in-8-aws-regions-and-up-to-50-reduction-in-asynchronous-job-processing-times/. Acesso em: jun. 2026.

MICROSOFT. **Azure AI Document Intelligence Pricing**. Redmond: Microsoft, 2024. Disponível em: https://azure.microsoft.com/en-us/pricing/details/document-intelligence/. Acesso em: jun. 2026.

DONG, Yixin et al. **XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models**. arXiv:2411.15100. [S.l.]: MLSys, 2025. Disponível em: https://arxiv.org/abs/2411.15100. Acesso em: jun. 2026.

DOTTXT. **Say What You Mean: Constrained Generation and Its Discontents**. [S.l.]: dottxt, 2024. Disponível em: https://blog.dottxt.ai/say-what-you-mean.html. Acesso em: jun. 2026.

DOTTXT. **Coalescence: Making Structured Generation Fast**. [S.l.]: dottxt, 2024. Disponível em: https://blog.dottxt.ai/coalescence.html. Acesso em: jun. 2026.

GOOGLE. **Gemini API Structured Output**. Mountain View: Google, 2025. Disponível em: https://ai.google.dev/gemini-api/docs/structured-output. Acesso em: jun. 2026.

GOOGLE. **Document AI Pricing**. Mountain View: Google, 2024. Disponível em: https://cloud.google.com/document-ai/pricing. Acesso em: jun. 2026.

GOOGLE. **Layout Parser**. Mountain View: Google, 2024. Disponível em: https://docs.cloud.google.com/document-ai/docs/layout-parse-chunk. Acesso em: jun. 2026.

OPENAI. **Introducing Structured Outputs in the API**. San Francisco: OpenAI, 2024. Disponível em: https://openai.com/index/introducing-structured-outputs-in-the-api/. Acesso em: jun. 2026.

OPENAI. **Structured Outputs**. San Francisco: OpenAI, 2025. Disponível em: https://platform.openai.com/docs/guides/structured-outputs. Acesso em: jun. 2026.

OPENAI. **API Pricing**. San Francisco: OpenAI, 2025. Disponível em: https://platform.openai.com/docs/pricing. Acesso em: jun. 2026.

QWEN. **Qwen2.5-VL**. [S.l.]: Alibaba Cloud, 2025. Disponível em: https://qwen.ai/blog?id=qwen2.5-vl. Acesso em: jun. 2026.

TAM, Zhi Rui et al. **Let Me Speak Freely? A Study of LLM Responses to Structured Formats**. In: *Proceedings of EMNLP 2024 Industry Track*. [S.l.]: ACL, 2024. Disponível em: https://aclanthology.org/2024.emnlp-industry.91/. Acesso em: jun. 2026.
-->
