## 3. Técnicas e Modelos Avaliados

A análise das dores do *pipeline* atual (latência, custo redundante, fragilidade em layouts complexos, leitura fraca de gráficos) aponta para uma técnica transversal que antecede a escolha do motor: colapsar as duas inferências em uma única chamada. Ela é aplicável a toda a *shortlist* e representa o maior impacto arquitetural imediato.

### 3.1 Técnica Transversal: *Single-Pass* com *Structured Output* (*Constrained Decoding*)

O *pipeline* vigente executa duas chamadas sequenciais: a primeira interpreta o documento, a segunda formata a saída em JSON. Essa separação era historicamente necessária porque os modelos não garantiam JSON válido durante a extração. O *constrained decoding* elimina essa necessidade ao restringir, em tempo de decodificação, os *tokens* amostráveis aos que mantêm a saída conforme o *schema*, transformando a conformidade de "instrução no *prompt*" em garantia de engenharia (OpenAI, 2024; Anthropic, 2025; Dong et al., 2024).

Todos os provedores principais oferecem implementações gerenciadas. O **OpenAI Structured Outputs** (`json_schema` + `strict: true`, desde `gpt-4o-2024-08-06`) reporta **100% de conformidade** ao *schema*, contra <40% com *prompting* tradicional (OpenAI, 2024). O **Anthropic Structured Outputs** (GA desde nov/2025) compila o *schema* em gramática e a cacheia por 24h, eliminando o custo de recompilação (Anthropic, 2025). O **Gemini `responseSchema`** opera de forma equivalente. No *open-source*, o **XGrammar** (*backend* padrão de vLLM, SGLang, TensorRT-LLM) implementa *constrained decoding* via autômato de pilha, com *overhead* <**40 µs/token** e aceleração de até 100× (MLSys 2025; Dong et al., 2024).

Quanto ao impacto na acurácia, o debate foi encerrado empiricamente: "Let Me Speak Freely?" (Tam et al., EMNLP 2024) identificou degradação em raciocínio com *JSON mode*, mas a refutação da dottxt ("Say What You Mean", 2024) mostrou que o efeito vinha de *prompts* assimétricos: com *prompts* idênticos, o *structured output* empata ou supera a geração livre (Tam et al., 2024; dottxt, 2024). Extração de documentos aproxima-se de *slot-filling*/classificação, não de raciocínio multi-passo, favorecendo ganho ou neutralidade de acurácia. O colapso de duas inferências em uma reduz latência e custo da formatação sem exigir nova infraestrutura nos provedores gerenciados.

### 3.2 *Shortlist* de Motores

Estabelecida a técnica transversal, a escolha do motor determina o equilíbrio entre custo, infraestrutura, maturidade e cobertura das dores restantes. As opções são organizadas a seguir pelos rótulos canônicos usados no dossiê.

**Opção A: VLM proprietário pequeno (Gemini Flash-Lite / GPT-4o-mini).** Modelos "Flash"/"mini" leem a imagem nativamente, sem OCR externo, e emitem JSON estruturado em uma única chamada. O Gemini 2.5 Flash-Lite custa US$ 0,10/1M *tokens* de entrada e US$ 0,40/1M de saída; o GPT-4o-mini, US$ 0,15 e US$ 0,60 (OPENAI, 2025; GOOGLE, 2024). Infraestrutura mínima, com *Structured Output* gerenciado disponível de imediato.

**Opção B: VLM *open-source* self-hosted (Qwen2.5-VL-7B).** Ponto de equilíbrio da família Qwen: DocVQA 95,7 e ChartQA 87,3, contra 96,4 e 89,5 do modelo de 72B (Qwen, 2025), praticamente equivalente ao maior para CNH e faturas, com custo marginal tendendo a zero uma vez amortizada a GPU. Via API intermediada, a mesma classe apresentou 6,17 s e US$ 0,00051 na CNH, contra 2,61 s e US$ 0,00027 do Gemini Flash-Lite (POC, 2026). Principal risco: GPU exigida (16–20 GB VRAM em *bf16*, ou 8 GB em 4-bit) e o MLOps associado.

**Opção C: Document AI gerenciado + LLM pequeno.** Um serviço de Document AI em nuvem (Azure AI Document Intelligence Layout ou Google Document AI Layout Parser) converte o documento em Markdown estruturado antes de uma chamada de LLM pequeno para extração. Precificados em US$ 10/1.000 páginas, com OCR puro em ~US$ 1,50/1.000 páginas (MICROSOFT, 2024; GOOGLE, 2024; AWS, 2025). O Google Layout Parser se destaca em gráficos analíticos, usando Gemini para *verbalizar* figuras (GOOGLE, 2024), mas a arquitetura em dois serviços reintroduz integração e pode elevar a latência total.

**Opção D: Híbrido (PyMuPDF + VLM seletivo) para documento extenso.** PyMuPDF extrai texto e tabelas deterministicamente, e o VLM é invocado só nas páginas com figuras. Na POC, o PDF completo (42 páginas, 28 MB) enviado a um VLM falhou após ~615 s; a híbrida extraiu o texto em ~4,7 s a custo zero, mais uma chamada VLM de ~4,3 s a US$ 0,00039 para a figura principal, totalizando ~9 s (POC, 2026). O VLM seletivo pode ser qualquer motor da *shortlist* (A ou B), com *structured output*.

### 3.3 Síntese Comparativa

Tabela 1 - Comparativo de técnicas e motores avaliados

| Técnica / Motor | Dores atacadas | Infraestrutura | Custo relativo | Maturidade | Risco principal |
|--------------------|----------------|--------------|------------------|----------------|----------------|
| **A: VLM proprietário pequeno** (Gemini Flash-Lite, GPT-4o-mini) | Latência (2→1), custo da 2ª chamada, leitura de gráficos | API REST; sem GPU | Baixo (US$ 0,00027–0,00040/doc) | Alta (GA em todos os provedores) | Dependência de provedor; privacidade; variação de preço |
| **B: VLM OSS self-hosted** (Qwen2.5-VL-7B) | Latência (2→1), custo marginal ≈0, leitura visual | GPU ≥8 GB VRAM (4-bit); MLOps | Marginal ≈0 (capex GPU); ~US$ 0,00051/doc via API | Média (ecossistema vLLM estável) | Infra GPU/MLOps; curva de implantação |
| **C: Document AI + LLM pequeno** (Azure/Google Layout) | OCR rápido + 1 LLM; robustez em tabelas; multipágina | Dois serviços de nuvem; sem GPU | Médio (US$ 10/1k págs + tokens LLM) | Alta (SLA, suporte, auditoria) | Dois pontos de integração; latência acumulada |
| **D: Híbrido** (PyMuPDF + VLM seletivo) | Documento extenso: falha do VLM ingênuo | PyMuPDF (CPU); VLM só em figuras | Muito baixo (texto grátis; figura ~US$ 0,00039) | Média (requer orquestração de dois caminhos) | Detecção de páginas com figuras |

Fonte: elaboração própria com base em OpenAI (2024; 2025), Anthropic (2025), Google (2024), Microsoft (2024), AWS (2024; 2025), Qwen (2025), Dong et al. (2024) e resultados da POC (2026).

Nenhum motor isolado é ótimo para todos os documentos: a escolha racional é uma estratégia escalonada: A como padrão de baixo esforço, B para escala com custo marginal tendendo a zero, C quando maturidade institucional é requisito, e D para documentos extensos com texto digital. A Seção 4 apresenta os resultados empíricos que fundamentam essa hierarquia.

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
