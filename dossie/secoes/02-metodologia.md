## 2. Metodologia

A condução da pesquisa foi estruturada para garantir rastreabilidade entre cada afirmação e as fontes que a fundamentam, via varredura paralela em seis frentes conduzidas nos dias 26–27/06/2026: (1) literatura recente em *arXiv* e periódicos (2024–2026) sobre extração de documentos, *key-information extraction* e VLMs; (2) documentação oficial de APIs/SDKs (Anthropic, Google, OpenAI); (3) benchmarks públicos, com destaque para OmniDocBench (CVPR 2025) e os *leaderboards* de DocVQA, ChartQA e FUNSD/CORD/SROIE; (4) análise técnica da API da Tech4.ai (`POST /document/extract`, *layout builder*, *validators* nativos); (5) experimentos diretos com os três documentos de teste via OpenRouter, em código Python reprodutível; e (6) estudo de robustez na CNH de baixa resolução, com ablação sistemática (resolução, *prompt*, porte do modelo). Os achados foram registrados nas notas `docs/01` a `docs/11`, base documental primária citada ao longo das seções seguintes.

### 2.1 Abordagens Descartadas Rapidamente

Durante a varredura, um conjunto de abordagens foi descartado antes da fase experimental por razões técnicas ou econômicas:

1. **Treinamento do zero (*from scratch*):** exigiria corpora anotados proprietários e meses a anos de desenvolvimento. VLMs pré-treinados (Qwen2.5-VL, Gemini Flash, GPT-4o) já superam esse patamar em DocVQA e CORD sem ajuste fino (Mathew et al., 2021; Bai et al., 2025), com custo-benefício desfavorável por ordens de grandeza.

2. **OCR clássico puro sem compreensão de *layout*:** ferramentas como o Tesseract convertem pixels em texto mas não preservam a estrutura semântica de tabelas ou gráficos, inutilizável para a fatura CELPE ou o paper sem camada de análise estrutural equivalente à solução a substituir. O OmniDocBench (CVPR 2025) confirma que ferramentas de *layout analysis* como o MinerU superam VLMs genéricos pela análise estrutural, não pelo OCR isolado (Ma et al., 2024).

3. **Modelos que exigem *cluster* de GPU grande:** variantes como Qwen2-VL-72B *self-hosted*, exigindo múltiplas GPUs A100/H100, estão fora do escopo de uma POC. O Qwen2.5-VL-7B, que cabe em uma única GPU de 24 GB, atinge desempenho comparável ao 72B (gap <1 p.p. em DocVQA), tornando o *self-hosted* viável com hardware modesto (Bai et al., 2025).

4. **PDF longo ingênuo via VLM:** o envio do documento completo (42 páginas, 28 MB) falhou após ~615 s (`choices=None`, custo zero, sem retorno útil), sendo descartado em favor da abordagem híbrida da Seção 3.

### 2.2 Uso de Ferramentas de Inteligência Artificial

Em conformidade com a transparência científica: a pesquisa contou com o apoio do *Claude Code* (Opus) como copiloto computacional, para varredura de literatura/documentação, geração e depuração do código da POC e organização das notas de pesquisa. A curadoria crítica das fontes, o desenho experimental, a interpretação dos resultados e as conclusões são de autoria integral do pesquisador. Toda afirmação empírica é rastreável a `benchmark/results/` e às notas citadas, reproduzível a partir do código do repositório.

### 2.3 *Framework* de Métricas

A avaliação quantitativa do POC adotou uma métrica dupla, motivada pela constatação de que o *LLM-as-judge* sozinho não é confiável em baixa resolução:

**Acurácia determinística** (*exact-match* normalizado): compara o valor predito ao *ground truth* após normalização de caixa e espaços, expressa como fração de campos corretos sobre o total definido no *layout*. Determinística e independente de modelo, é o padrão primário para campos objetivos (nome, data de emissão, CPF na CNH).

**Acurácia por juiz LLM** (*LLM-as-judge*): um modelo separado (`gpt-4o`, via OpenRouter) recebe a imagem, a extração avaliada e o *ground truth*, e julga o acerto por campo. Essa métrica capta equivalências semânticas fora do *exact-match* (ex.: formatação de data) e cobre documentos sem *ground truth* completo, como a Fatura CELPE.

A necessidade da métrica dupla foi evidenciada no diagnóstico da CNH de baixa resolução (341×600 px): o juiz `gpt-4o` divergiu da métrica determinística entre 0,34 e 0,66 (escala 0–1), aprovando datas completamente incorretas (ex.: 03/06/1981 extraído para valor real 06/08/1961) e filiações sem os prefixos do *ground truth* (docs/08). Isso sinaliza que o juiz é não-calibrado em baixa legibilidade, possivelmente por não conseguir ele próprio ler o documento com precisão. Por isso o dossiê reporta ambas as métricas e privilegia a determinística como indicador primário.

Além da qualidade, dois eixos complementam o *framework*: **latência por documento** (p50, ponta a ponta via OpenRouter) e **custo por documento** (US$, a partir do *billing* de *tokens* reportado pela API), ambos mensurados no código do POC e reportados na Seção 4.

A Seção 3 apresenta as técnicas e modelos selecionados, com análise dos *trade-offs* entre as quatro rotas identificadas como viáveis.

<!-- refs:
BAI, Shuai et al. Qwen2.5-VL Technical Report. *arXiv*, 2025. Disponível em: https://arxiv.org/abs/2502.13923. Acesso em: 27 jun. 2026.

MA, Yutong et al. OmniDocBench: Benchmarking Document Parsing with Diverse Scales and Granularities. In: **CONFERENCE ON COMPUTER VISION AND PATTERN RECOGNITION (CVPR)**, 2025. Disponível em: https://arxiv.org/abs/2412.07626. Acesso em: 26 jun. 2026.

MATHEW, Minesh; KARATZAS, Dimosthenis; JAWAHAR, C. V. DocVQA: A Dataset for VQA on Document Images. In: **WINTER CONFERENCE ON APPLICATIONS OF COMPUTER VISION (WACV)**, 2021. Disponível em: https://arxiv.org/abs/2007.00398. Acesso em: 26 jun. 2026.
-->
