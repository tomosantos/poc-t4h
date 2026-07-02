## 1. Introdução

A extração automatizada de dados de documentos heterogêneos (formulários, faturas, identidades, relatórios técnicos) é necessidade crescente em organizações que digitalizam fluxos intensivos em papel. Soluções baseadas em modelos de linguagem de grande escala emergiram como alternativa ao *Optical Character Recognition* (OCR) clássico, por interpretarem contexto semântico, estruturas não lineares e conteúdo visual sem templates predefinidos (Borchmann et al., 2021; Huang et al., 2022). A proliferação dessas soluções em produção, porém, expõe limitações operacionais que tornam a investigação de arquiteturas alternativas tecnicamente relevante e economicamente justificada.

A solução de referência é a API de extração de documentos da Tech4.ai (TECH4.AI, 2024), plataforma brasileira cujo *endpoint* `POST /document/extract/` recebe a URL de um arquivo e um `layout_id`, retornando JSON no formato `{status, extracted_data}`. O *layout* é configurado por um *visual builder*, no qual o operador define cada campo com nome, tipo de dado e descrição em linguagem natural. O processo interno estrutura-se em duas inferências sequenciais: a primeira interpreta visualmente o documento e localiza os campos; a segunda formata os valores em JSON conforme o esquema esperado. Essa arquitetura atende bem à variedade de documentos (da CNH brasileira à fatura CELPE e a artigos científicos multipágina), mas impõe quatro dores operacionais que motivam este estudo.

A primeira é a **latência acumulada**: duas chamadas por requisição, com latência total entre 4 e 10 s por documento mesmo em modelos compactos (Seção 4), proibitivo em lote ou tempo real. A segunda é o **custo duplicado**: duas cobranças de *tokens* de entrada e saída, *overhead* estrutural independente da complexidade do documento. A terceira é a **complexidade de layout**: a formatação pressupõe que a interpretação extraiu os campos corretamente, mas *layouts* irregulares, colunas múltiplas ou conteúdo multipágina elevam erros em cascata, já que um erro na primeira etapa não é recuperável pela segunda. A quarta é a **leitura fraca de gráficos e imagens**: o *pipeline* atual foi concebido para texto e dados tabulares, insuficiente para gráficos e figuras em laudos técnicos ou relatórios analíticos (Kim et al., 2022). Tomadas em conjunto, essas quatro limitações configuram um problema de pesquisa concreto e mensurável.

Este estudo investiga e avalia abordagens alternativas que reduzam latência e custo mantendo ou superando a acurácia vigente, em três eixos: (1) colapsar as duas inferências em uma única chamada (*single-pass*) via *structured output* com *constrained decoding*; (2) a adequação de *Vision-Language Models* (VLMs) compactos, avaliada por *benchmarks* públicos e experimentos locais; e (3) estratégias híbridas combinando extração determinística de texto com chamadas seletivas de VLM para conteúdo visual em documentos extensos. A análise se apoia em experimentos reprodutíveis e *benchmarks* públicos, ancorando as recomendações em evidência empírica, não em projeções especulativas.

Figura 1 - Arquiteturas comparadas: *pipeline* de duas etapas (atual), *single-pass* com *structured output* (proposta) e abordagem híbrida (para documento extenso)

![](../figuras/figura1_arquitetura.png){width=68%}

Fonte: elaboração própria.

Este estudo está organizado em seis seções. A Seção 2 descreve a metodologia, o *framework* de avaliação e a declaração de uso de IA na pesquisa. A Seção 3 apresenta a *shortlist* de técnicas e modelos, com *trade-offs* de custo, latência, acurácia e infraestrutura. A Seção 4 expõe os resultados empíricos da POC, complementados por *benchmarks* de terceiros. A Seção 5 sintetiza as conclusões e a recomendação técnica, incluindo a estratégia de escalonamento. A Seção 6 analisa a viabilidade de integração ao ambiente Tech4.ai: custos, infraestrutura e compatibilidade com o contrato de API vigente.

<!-- refs:
BORCHMANN, Łukasz; PIETRUSZKA, Michał; STANISLAWEK, Tomasz; JULKA, Dawid; GRZEGORZEK, Karol. **Towards a Multi-Task Learning Setup for Document Information Extraction**. In: *Proceedings of the EMNLP Workshop*, 2021. Disponível em: https://aclanthology.org/2021.emnlp-main.670. Acesso em: jun. 2026.

HUANG, Yupan; Liao, Tengchao; Wei, Furu; Zhu, Qi; Bao, Junwei; Cao, Yutao; ZHOU, Ming. **Layoutlmv3: Pre-training for Document AI with Unified Text and Image Masking**. In: *Proceedings of the 30th ACM International Conference on Multimedia*, 2022. Disponível em: https://arxiv.org/abs/2204.08387. Acesso em: jun. 2026.

KIM, Geewook; Hong, Teakgyu; Yim, Moonbin; Nam, JeongYeon; Park, Jinyoung; Park, Jinyeong; Yang, Wonseok; Cho, Sangdoo; Park, Seunghyun. **OCR-Free Document Understanding Transformer**. In: *Proceedings of ECCV 2022*, 2022. Disponível em: https://arxiv.org/abs/2111.15664. Acesso em: jun. 2026.

TECH4.AI. **Vision Doc Extraction API (Documentação oficial)**. 2024. Disponível em: https://docs.tech4.ai/vision/doc-extraction-api. Acesso em: jun. 2026.

TECH4.AI. **Layout Configuration**. 2024. Disponível em: https://docs.tech4.ai/vision/layout-config. Acesso em: jun. 2026.
-->
