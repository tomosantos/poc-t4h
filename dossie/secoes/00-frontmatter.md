# Da Extração em Duas Etapas ao *Single-Pass*: Uma Análise de Viabilidade de Abordagens Alternativas para Extração de Dados de Documentos {.unlisted .unnumbered}

**Autor:** Wellinton Oliveira Santos

**Data:** junho de 2026

---

## Resumo {.unlisted .unnumbered}

O processamento automatizado de documentos constitui um componente crítico em sistemas de inteligência artificial voltados à digitalização de processos empresariais. A API de extração de dados da Tech4.ai, solução de referência neste estudo, opera por meio de um *pipeline* de duas inferências de modelos de linguagem: uma etapa de interpretação visual do documento e uma etapa subsequente de formatação estruturada em JSON, o que introduz latência acumulada, custo duplicado por chamada e fragilidade diante de layouts complexos ou conteúdo visual não textual. O presente estudo investiga a viabilidade de abordagens alternativas capazes de reduzir latência e custo mantendo ou superando a acurácia da solução vigente. A metodologia combinou varredura de literatura especializada, análise de benchmarks públicos e uma prova de conceito empírica com três documentos representativos — CNH, fatura de energia e artigo científico multipágina — avaliados em uma matriz de modelos e modos de inferência via OpenRouter. Os resultados confirmam que a arquitetura *single-pass*, com um *Vision-Language Model* compacto e *structured output* via *constrained decoding*, colapsa as duas inferências em uma única chamada com ganhos consistentes de latência (≈32%) e custo (≈32%), sem perda de acurácia. Para documentos extensos, a abordagem híbrida — extração determinística por PyMuPDF combinada a VLM seletivo apenas nas figuras — demonstrou-se superior à ingestão ingênua do PDF completo. Recomenda-se o VLM proprietário compacto (classe *Gemini Flash-Lite*) em modo *single-pass* como motor padrão, com estratégia de escalonamento baseada em complexidade de layout, não em resolução de imagem.

**Palavras-chave:** *extração de documentos*; *Vision-Language Models*; *structured output*; *constrained decoding*; *single-pass inference*; processamento de documentos.
