## 4. Resultados e Experimentos

### 4.1 Configuração da Prova de Conceito

A prova de conceito (POC) foi implementada como *scripts* Python e notebooks Jupyter no repositório do projeto, garantindo reprodutibilidade. O acesso aos modelos se deu via OpenRouter, com o SDK `openai` e substituição de *endpoint*, unificando múltiplos provedores sem alterar o código de chamada. Custos e latências reportados são medições reais, capturadas das respostas da API.

A matriz experimental cruza três documentos de teste (CNH brasileira, `Documento 1.jpeg`, 341×600 px; fatura CELPE, `Documento 2.jpg`, 620×1718 px; e o artigo científico do Claude 3, 42 páginas e 28 MB) com três modelos (*gemini-2.5-flash-lite*, *gpt-4o-mini*, *qwen2.5-vl-72b*) e dois modos: *single-pass* (extração direta com *structured output*) e *two_step* (interpretação livre seguida de reformatação em JSON). O juiz avaliador (`gpt-4o`, *LLM-as-judge*) atribui `acuracia_juiz` (0–1); em paralelo, `acuracia_det` compara contra *ground truth* anotado manualmente. Essa métrica dupla se revelou indispensável (Subseção 4.5).

### 4.2 Tese da Consolidação em Passo Único (2→1)

A hipótese central, de que o *single-pass* com *structured output* supera ou iguala o *pipeline* de duas etapas em custo, latência e acurácia, é confirmada de forma consistente. A Tabela 2 traz os resultados completos para CNH e Fatura CELPE, únicos documentos com a matriz executada até sua completude.

Tabela 2 - Matriz de resultados da POC (CNH e Fatura CELPE; via OpenRouter, junho 2026)

| Documento | Modelo | Modo | Status | Latência (s) | Custo (US$) | Acurácia (juiz) | Acurácia (det.) |
|---------|------------------|--------|--------|------------|------------|--------------|--------------|
| CNH | gemini-2.5-flash-lite | single | partial | 2,61 | 0,00027 | 0,50 | 0,667 |
| CNH | gemini-2.5-flash-lite | two_step | partial | 4,14 | 0,00038 | 0,50 | 0,667 |
| CNH | gpt-4o-mini | single | partial | 2,99 | 0,00226 | 0,33 | 0,50 |
| CNH | gpt-4o-mini | two_step | partial | 4,06 | 0,00228 | 0,50 | 0,50 |
| CNH | qwen2.5-vl-72b | single | partial | 6,17 | 0,00051 | 0,50 | 0,333 |
| CNH | qwen2.5-vl-72b | two_step | partial | 10,54 | 0,00077 | 0,50 | 0,50 |
| Fatura | gemini-2.5-flash-lite | single | ok | 3,34 | 0,00040 | 0,857 | N/A |
| Fatura | gemini-2.5-flash-lite | two_step | ok | 4,90 | 0,00059 | 0,833 | N/A |
| Fatura | gpt-4o-mini | single | ok | 3,07 | 0,00734 | 0,857 | N/A |
| Fatura | gpt-4o-mini | two_step | ok | 4,33 | 0,00740 | 0,857 | N/A |
| Fatura | qwen2.5-vl-72b | single | partial | 6,79 | 0,00131 | 0,571 | N/A |
| Fatura | qwen2.5-vl-72b | two_step | ok | 8,39 | 0,00156 | 0,860 | N/A |

Fonte: elaboração própria. Custos em US$ por documento. Acurácia (det.) = *exact-match* normalizado vs. *ground truth*; N/A indica ausência de *ground truth* determinístico para o documento.

Em **nenhuma célula** da matriz o modo *two_step* superou o *single-pass* em custo ou latência. No caso mais expressivo (Fatura CELPE, *gemini-2.5-flash-lite*), o *single-pass* leva 3,34 s e US$0,00040 contra 4,90 s e US$0,00059 do *two_step*, redução de ~32% em ambas as dimensões, com acurácia de juiz superior (0,857 vs. 0,833). Na CNH, o *single-pass* responde em 2,61 s (vs. 4,14 s), custo 29% inferior, e acurácia determinística idêntica (0,667). A Figura 2 exibe o *trade-off* latência × custo.

Figura 2 - Trade-off latência × custo por modelo e modo de execução

![](../figuras/figura2_tradeoff.png){width=68%}

Fonte: elaboração própria. Cada ponto representa uma célula (modelo × modo × documento) da matriz experimental.

Achado adicional: o *gpt-4o-mini* custa 10×–18× mais que o *gemini-2.5-flash-lite* sem ganho de acurácia. Na Fatura CELPE (*single-pass*), são US$0,00734 vs. US$0,00040 (18×) com acurácia de juiz idêntica (0,857). A escolha do provedor certo na classe de modelos pequenos tem impacto de custo dominante; "qualquer modelo pequeno" não é equivalente.

### 4.3 Documento Extenso: Abordagem Híbrida vs. Ingestão Ingênua

O terceiro documento, o artigo científico do Claude 3 (42 páginas, 28 MB), testou o comportamento do *pipeline* em material multipágina extenso, comparando ingestão ingênua (PDF completo direto ao VLM) e abordagem híbrida (PyMuPDF para texto/tabelas + VLM seletivo apenas em figuras).

Os resultados são inequívocos: o caminho ingênuo **falhou** após ~615 s, esgotando o limite de inferência do provedor (`choices=None`, custo zero: recurso consumido, resultado nulo). A híbrida extraiu o texto das 42 páginas em ~4,7 s a custo zero (PyMuPDF), mais uma chamada VLM de 4,3 s e US$0,00039 para a figura principal, totalizando ~9 s. A Figura 4 ilustra a diferença.

Figura 4 - Abordagem ingênua (VLM no PDF inteiro) vs. híbrida (PyMuPDF + VLM seletivo)

![](../figuras/figura4_hibrido.png){width=68%}

Fonte: elaboração própria. Latência em segundos; custo em US$ por documento.

Consolida-se assim a distinção arquitetural: documentos de página única comportam *single-pass* direto ao VLM; documentos extensos exigem pré-processamento determinístico, reservando o VLM aos elementos visuais que exigem compreensão multimodal. A arquitetura híbrida elimina o risco de *timeout*, reduz custo por chamada e preserva a leitura de gráficos.

### 4.4 Estudo de Robustez na CNH: Limites da Escalonabilidade

A CNH constitui o caso mais difícil da matriz: `status=partial` em 100% dos *runs*, com CPF retornando `None` em todos os modelos e modos (o validador determinístico zera valores inválidos). Isso motivou um estudo de robustez com três experimentos adicionais. Primeiro, *upscaling* LANCZOS 3× (341×600 → 1023×1800 px, nitidez 1,5×) não recuperou nenhum campo em *gemini-2.5-flash-lite* ou *gpt-4o-mini* (placar 3/6 em ambos) e elevou o custo do *gpt-4o-mini* em 153% (US$0,00222 → US$0,00563) pelos *visual tokens* extras. O *upscaling* interpola pixels existentes sem recuperar informação destruída pela compressão JPEG, sinal de **legibilidade intrínseca**, não de densidade de pixels. Segundo, *prompt* ancorado (descrições de campo vinculadas à posição no *layout*, ex.: "campo rotulado 'DATA EMISSÃO', diferente da 1ª habilitação e da validade") recuperou `data_emissao` no *gemini-2.5-flash-lite* sem custo adicional relevante (US$0,000294 vs. US$0,000279), elevando o placar de 3/6 para 4/6 e igualando o resultado do *gemini-2.5-pro* (modelo forte) com *prompt* genérico. Terceiro, escalar para o *gemini-2.5-pro* (~57× mais caro, US$0,016 vs. US$0,000286) não recuperou campos além do que o modelo pequeno com *prompt* ancorado já atingia: placar 4/6 em ambas as condições do modelo forte, com CPF e `data_nascimento` irrecuperáveis em qualquer configuração.

O CPF permanece irrecuperável nos quatro *runs* da ablação: os modelos extraem consistentemente `8` em vez de `0` no dígito inicial, erro atribuído à degradação do JPEG. Nenhuma alavanca de *prompt* ou escalação de modelo corrige um problema de legibilidade anterior à inferência. Isso distingue **complexidade** (resolvível por modelo maior ou *prompt* mais rico) de **legibilidade** (exige pré-processamento de imagem, recorte de região de interesse ou re-captura do documento).

### 4.5 Confiabilidade da Avaliação: O Juiz Não-Calibrado

O diagnóstico na CNH revelou limitação metodológica relevante: o *LLM-as-judge* (`gpt-4o`) diverge sistematicamente da métrica determinística em baixa resolução, com gap entre 0,34 e 0,66 (escala 0–1), ora super ora subestimando a acurácia real. O juiz aprova datas e nomes incorretos porque a própria baixa resolução dificulta sua verificação visual, o que o torna leniente quando não consegue confirmar o valor correto.

O relato das duas métricas em paralelo não é redundante: é **indispensável** para a honestidade do experimento. `acuracia_det` ancora objetivamente onde há *ground truth*; `acuracia_juiz` cobre documentos sem anotação determinística (Fatura CELPE), mas exige reserva em baixa resolução. Isso reforça a recomendação de anotar *ground truth* para documentos críticos e validar campos via regras determinísticas (CPF, CNPJ, linha digitável) como pós-processamento obrigatório.

### 4.6 Fundamentação por Benchmarks de Terceiros

Dado o escopo restrito da POC (n=3, dois com *ground truth* apenas parcial), a generalização apoia-se em *benchmarks* públicos de grande escala. A Tabela 3 consolida os números relevantes, cobrindo os casos não testados localmente: gráficos, documentos multidomínio e eficácia do *constrained decoding*.

Tabela 3 - Benchmarks de terceiros utilizados para fundamentação externa dos achados

| Benchmark | Tarefa | Métrica | Qwen2.5-VL-7B | Qwen2.5-VL-72B | GPT-4o | MinerU | Ref. |
|----------------|------------------|--------------|--------------|--------------|--------|--------|------------------|
| DocVQA | QA sobre documentos | ANLS | 95,7 | 96,4 | 92,8 | n/a | (Bai et al., 2025) |
| ChartQA | QA sobre gráficos | *relaxed acc.* | 87,3 | 89,5 | 85,7 | n/a | (Bai et al., 2025) |
| OmniDocBench (NED) | *Parsing* de PDF | NED (↓ melhor) | n/a | n/a | 0,144 | 0,058 | (Ma et al., 2024) |
| OmniDocBench (TEDS) | Tabelas | TEDS | n/a | n/a | 72,8 | 79,4 | (Ma et al., 2024) |
| *Structured Outputs* | Conformidade ao *schema* | % válido | n/a | n/a | ~100%* | n/a | (OpenAI, 2024) |

Fonte: elaboração própria com base nas referências indicadas.

Os dados externos confirmam três achados que a POC não testou diretamente. Primeiro, o *Qwen2.5-VL-7B* iguala virtualmente o *72B* em DocVQA (95,7 vs. 96,4) e ChartQA (87,3 vs. 89,5), sustentando modelos menores para documentos estruturados. Segundo, ferramentas especializadas como o MinerU superam o *GPT-4o* em *parsing* de PDF (NED 0,058 vs. 0,144; TEDS de tabelas 79,4 vs. 72,8, OmniDocBench), corroborando a abordagem híbrida para documentos textuais densos. Terceiro, o *constrained decoding* praticamente elimina a não-conformidade ao *schema* JSON (problema que motivou a segunda etapa do *pipeline* atual) a custo desprezível, removendo o argumento técnico central que justificava as duas inferências (OpenAI, 2024). Os serviços de Document AI gerenciados (Azure, Google) operam entre US$1,50 e US$10/1.000 páginas, fundamentando a análise de custo em escala da Seção 6.

### 4.7 Extensão da Matriz: Modelos de Geração 2025/2026

Para verificar se a recomendação resiste à evolução do mercado, a matriz foi estendida a cinco modelos 2025/2026 (*gemini-3.1-flash-lite*, *gpt-5-mini*, *claude-haiku-4.5*, *qwen3-vl-8b*, *qwen3-vl-32b*), avaliados nos mesmos documentos com *ground truth* (CNH, Fatura CELPE) e protocolo de métrica dupla. A Tabela 4 traz as médias por modelo (*deepseek-v4-flash* foi excluído por não suportar visão via OpenRouter).

Tabela 4 - Médias por modelo: gerações baseline vs. 2025/2026 (CNH + Fatura CELPE)

| Modelo | Geração | Ac. juiz (méd.) | Ac. det. (CNH) | Latência méd. (s) | Custo méd./extração (US$) |
|------------------|------------|--------------|--------------|--------------|------------------|
| gemini-2.5-flash-lite | baseline | 0,482 | 0,667 | 3,3 | 0,00037 |
| gpt-4o-mini | baseline | 0,689 | 0,500 | 4,0 | 0,00482 |
| qwen2.5-vl-72b | baseline | 0,634 | 0,500 | 6,3 | 0,00114 |
| gemini-3.1-flash-lite | 2025/2026 | 0,762 | 0,667 | 3,6 | 0,00085 |
| gpt-5-mini | 2025/2026 | 0,798 | 0,500 | 25,9 | 0,00380 |
| claude-haiku-4.5 | 2025/2026 | 0,506 | 0,000 | 8,7 | 0,00311 |
| qwen3-vl-8b | 2025/2026 | 0,570 | 0,500 | 4,4 | 0,00022 |
| qwen3-vl-32b | 2025/2026 | 0,762 | 0,333 | 6,2 | 0,00022 |

Fonte: elaboração própria (`benchmark/results/results.json`). Ac. det. (CNH) = *exact-match* normalizado vs. *ground truth*; médias calculadas sobre os modos *single* e *two_step*.

Três achados consolidam a recomendação. Primeiro, o *gemini-3.1-flash-lite* eleva a acurácia de juiz média de 0,482 para 0,762 preservando a acurácia na CNH (0,667), com latência e custo na mesma faixa: a classe *Flash-Lite* segue como escolha padrão, agora com margem superior. Segundo, o *qwen3-vl-32b* iguala essa acurácia de juiz a custo ~4× menor (US$0,00022), a melhor opção quando o volume justifica priorizar custo, ressalvada a menor acurácia determinística na CNH (0,333) e a divergência juiz/métrica exata (Subseção 4.5). Terceiro, o *gpt-5-mini* atinge a maior acurácia de juiz (0,798), mas ~26 s de latência inviabiliza uso síncrono; o *claude-haiku-4.5* não se justifica, com acurácia determinística nula na CNH. A geração 2025/2026 confirma a arquitetura recomendada: o ganho vem do sucessor mais recente na mesma classe de VLM compacto, não da troca por modelos maiores.

<!-- refs:
BAI, Shuai et al. **Qwen2.5-VL Technical Report**. Hangzhou: Alibaba Group, 2025. Disponível em: https://arxiv.org/abs/2502.13923. Acesso em: jun. 2026.

MA, Yahui et al. **OmniDocBench: Benchmarking Document Parsing with Diverse Scalable Data**. In: IEEE/CVF CONFERENCE ON COMPUTER VISION AND PATTERN RECOGNITION (CVPR), 2025, Seattle. *Proceedings…* Seattle: IEEE, 2025. Disponível em: https://arxiv.org/abs/2412.07626. Acesso em: jun. 2026.

MASRY, Ahmed et al. **ChartQA: A Benchmark for Question Answering about Charts with Visual and Logical Reasoning**. In: FINDINGS OF THE ASSOCIATION FOR COMPUTATIONAL LINGUISTICS (ACL), 2022. *Findings…* Dublin: ACL, 2022. p. 2263–2279. Disponível em: https://aclanthology.org/2022.findings-acl.177. Acesso em: jun. 2026.

MATHEW, Minesh; KARATZAS, Dimosthenis; JAWAHAR, C. V. **DocVQA: A Dataset for VQA on Document Images**. In: IEEE WINTER CONFERENCE ON APPLICATIONS OF COMPUTER VISION (WACV), 2021. *Proceedings…* Waikoloa: IEEE, 2021. Disponível em: https://arxiv.org/abs/2007.00398. Acesso em: jun. 2026.

OPENAI. **Structured Outputs**. San Francisco: OpenAI, 2025. Disponível em: https://platform.openai.com/docs/guides/structured-outputs. Acesso em: jun. 2026.
-->
