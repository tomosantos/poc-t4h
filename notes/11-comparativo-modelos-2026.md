# Comparativo de Modelos 2025/2026

**Data:** 2026-06-29
**Documentos avaliados:** CNH (Documento 1.jpeg), Fatura CELPE (Documento 2.jpg)
**Juiz:** openai/gpt-4o
**Todos os runs:** single + two_step (exceto casos com falha de modo: qwen2.5-vl-72b sem single na CNH; qwen3-vl-8b sem single na fatura)

---

## Tabela de Resultados (médias por modelo)

| Modelo | Tier | Preço Input/1M | Ac. Juiz (média) | Ac. Det. (CNH) | Latência média | Custo médio/extração |
|--------|------|---------------|-----------------|----------------|---------------|---------------------|
| google/gemini-2.5-flash-lite | Baseline | $0.10 | 0.482 | 0.667 | 3.3s | $0.00037 |
| openai/gpt-4o-mini | Baseline | $0.15 | 0.689 | 0.500 | 4.0s | $0.00482 |
| qwen/qwen2.5-vl-72b-instruct | Baseline | $0.80 | 0.634 | 0.500 | 6.3s | $0.00114 |
| google/gemini-3.1-flash-lite | 2025/2026 | $0.25 | 0.762 | 0.667 | 3.6s | $0.00085 |
| openai/gpt-5-mini | 2025/2026 | $0.25 | 0.798 | 0.500 | 25.9s | $0.00380 |
| anthropic/claude-haiku-4.5 | 2025/2026 | $1.00 | 0.506 | 0.000 | 8.7s | $0.00311 |
| qwen/qwen3-vl-8b-instruct | 2025/2026 | $0.08 | 0.570 | 0.500 | 4.4s | $0.00022 |
| qwen/qwen3-vl-32b-instruct | 2025/2026 | $0.10 | 0.762 | 0.333 | 6.2s | $0.00022 |
| deepseek/deepseek-v4-flash | 2025/2026 | $0.09 | — | — | — | — |

> deepseek/deepseek-v4-flash removido do benchmark: sem suporte a visão via OpenRouter.

---

## Análise por Documento

### CNH (Documento 1.jpeg)

- **Melhor Ac. Det. (determinística):** google/gemini-2.5-flash-lite e google/gemini-3.1-flash-lite, ambos com Ac. Det. = 0.667 (4/6 campos corretos). Os demais modelos ficaram em 0.500 (3/6), com exceção do claude-haiku-4.5 que obteve 0.000 — extraiu os campos mas com valores sistematicamente errados, provavelmente por dificuldade OCR no documento JPEG com baixo contraste.
- **Melhor Ac. Juiz na CNH:** gemini-3.1-flash-lite two_step (0.833) e gpt-5-mini single / qwen3-vl-32b single (ambos 0.833). A divergência entre Ac. Det. e Ac. Juiz para o qwen3-vl-32b é notável: o juiz avalia positivamente mas a comparação determinística revela erro na estrutura — sinal de que o juiz penaliza menos variações de formatação que a métrica exata.
- **CPF (campo mais crítico, hash-comparado):** Nenhum modelo extraiu corretamente nos testes com modo single; o two_step do gemini-3.1-flash-lite foi o único run que atingiu Ac. Det. = 0.667 com Ac. Juiz = 0.833, sugerindo que a instrução em duas etapas ajuda na reconstrução do número mascarado.
- **Achado:** Os modelos 2025/2026 não representam ganho uniforme na CNH. O gemini-3.1-flash-lite (successor direto do baseline gemini-2.5-flash-lite) mantém a mesma Ac. Det. mas eleva o Ac. Juiz de 0.250 para 0.667 no modo single, indicando melhor raciocínio sobre campos parcialmente legíveis. O gpt-5-mini supera o gpt-4o-mini no Ac. Juiz (0.750 vs 0.667) mas não no Ac. Det. (ambos 0.500), e é 13× mais lento (30.8s vs 3.9s na CNH). O qwen3-vl-32b mostra boa Ac. Juiz (0.667) a custo ultrabaixo ($0.00019/extração), tornando-se competitivo em volume.

### Fatura CELPE (Documento 2.jpg)

- **Melhor modelo:** Empate entre google/gemini-3.1-flash-lite, openai/gpt-5-mini (two_step), qwen/qwen3-vl-32b, google/gemini-2.5-flash-lite (two_step) e anthropic/claude-haiku-4.5 (two_step) — todos com Ac. Juiz = 0.857.
- **Eficiência de custo na fatura:** O qwen3-vl-32b atinge 0.857 a $0.00025/extração, equivalente ao gemini-2.5-flash-lite ($0.00043) mas com acurácia 20 pontos percentuais acima no modo two_step. O gpt-4o-mini é o mais caro na fatura ($0.00737/extração) sem correspondente ganho de acurácia (0.712).
- **Achado:** A fatura CELPE penaliza mais modelos menores que a CNH. O qwen3-vl-8b cai para 0.710 (apenas two_step disponível), enquanto o claude-haiku-4.5 apresenta comportamento inverso ao da CNH: na fatura sobe para 0.762 (single) e 0.857 (two_step), sugerindo que seu ponto forte é layout de texto denso, não documentos com campos posicionais e foto. O gpt-5-mini two_step (0.857) demonstra consistência entre os dois documentos mas às custas de latência elevada (32.8s na fatura).

---

## Recomendações por Caso de Uso

| Caso de uso | Modelo recomendado | Justificativa |
|-------------|-------------------|---------------|
| Extração de CNH em escala | google/gemini-3.1-flash-lite | Melhor Ac. Det. (0.667) entre os modelos testados, latência baixa (3.6s), custo moderado ($0.00085). Supera o predecessor gemini-2.5-flash-lite em Ac. Juiz sem aumento expressivo de custo. |
| Extração de faturas em escala | qwen/qwen3-vl-32b-instruct | Atinge Ac. Juiz máxima (0.857) a custo ultra-baixo ($0.00025/extração), 3× mais barato que o gemini-3.1-flash-lite e 30× mais barato que o gpt-4o-mini para o mesmo nível de acurácia. |
| Máxima acurácia (custo secundário) | openai/gpt-5-mini | Melhor Ac. Juiz média geral (0.798), consistente entre CNH (0.750) e fatura (0.845). A penalidade de latência (25.9s média) é aceitável em contextos batch off-line. |
| Menor custo possível | qwen/qwen3-vl-8b-instruct | Custo de $0.00022/extração (empate com qwen3-vl-32b), mas com Ac. Juiz global de 0.570 — adequado para triagem inicial ou filtragem onde a taxa de erro pode ser tolerada ou corrigida a posteriori. |

---

## Conclusão

Os modelos 2025/2026 confirmam a hipótese de que a geração mais recente oferece acurácia superior sem necessariamente aumentar o custo: o gemini-3.1-flash-lite eleva o Ac. Juiz de 0.482 para 0.762 em relação ao predecessor, e o qwen3-vl-32b iguala-o com custo 4× menor. O gpt-5-mini lidera em acurácia média geral (0.798) mas sua latência de ~26s inviabiliza uso síncrono em produção. O claude-haiku-4.5 decepciona na CNH (Ac. Det. = 0.000) e apresenta custo elevado ($0.00311/extração) sem compensação de acurácia frente ao gemini-3.1-flash-lite ou qwen3-vl-32b. Para o pipeline single-pass + structured output recomendado no dossier, o gemini-3.1-flash-lite representa o melhor equilíbrio geral entre acurácia, latência e custo; o qwen3-vl-32b é a alternativa econômica quando o volume justifica priorizar custo sobre latência marginal.
