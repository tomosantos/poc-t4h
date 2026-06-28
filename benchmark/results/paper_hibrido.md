# Caso 2 — Documento Extenso (paper): caminho híbrido

PDF: 42 páginas, 28.2 MB

## Contraste de abordagens

| Abordagem | Resultado | Latência | Custo (US$) |
|---|---|---|---|
| Ingênua — PDF inteiro no VLM | FALHOU (choices=None / erro do provedor) | 615.1s | None |
| Híbrida — PyMuPDF (texto+tabelas, 42 págs) | OK determinístico | 4.71s | 0 |
| Híbrida — VLM só na figura (pág 7) | interpretação | 4.3s | 0.0003855 |

## Interpretação da figura (VLM)

**Table 2: Evaluation Results for LSAT, MBE, AMC, and GRE**

This table presents the performance of different language models, including Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku, GPT-4, and GPT-3.5, across various standardized tests:

*   **LSAT (Law School Admission Test):**
    *   Claude 3 Opus scored 161.
    *   Claude 3 Sonnet scored 158.3.
    *   Claude 3 Haiku scored 156.3.
    *   GPT-4 scored 163.
    *   GPT-3.5 scored 149.

*   **MBE (Multistate Bar Exam) - 0-shot CoT:**
    *   Claude 3 Opus achieved 85% accuracy.
    *   Claude 3 Sonnet achieved 71% accuracy.
    *   Claude 3 Haiku achieved 64% accuracy.
    *   GPT-4 achieved 75.7% accuracy.
    *   GPT-3.5 achieved 45.1% accuracy.

*   **AMC (American Mathematics Competition):**
    *   **AMC 12 (5-shot CoT):** Claude 3 Opus scored 63/150. Other models' scores are also provided.
    *   **AMC 10 (5-shot CoT):** Claude 3 Opus scored 72/150. Other models' scores are also provided.
    *   **AMC 8 (5-shot CoT):** Claude 3 Opus scored 84/150. Other models' scores are also provided.

*   **GRE (Graduate Record Examinations) General Test:**
    *   **GRE (Quantitative) (5-shot CoT):** Claude 3 Opus scored 159. GPT-4 scored 163, and GPT-3.5 scored 147.
    *   **GRE (Verbal) (5-shot CoT):** Claude 3 Opus scored 166. GPT-4 scored 169, and GPT-3.5 scored 154.
    *   **GRE (Writing) (k-

## Amostra do markdown determinístico (primeiros 1500 chars)

```
## Página 1
The Claude 3 Model Family: Opus, Sonnet, Haiku
Anthropic
Abstract
We introduce Claude 3, a new family of large multimodal models – Claude 3 Opus, our
most capable offering, Claude 3 Sonnet, which provides a combination of skills and speed,
and Claude 3 Haiku, our fastest and least expensive model. All new models have vision
capabilities that enable them to process and analyze image data. The Claude 3 family
demonstrates strong performance across benchmark evaluations and sets a new standard on
measures of reasoning, math, and coding. Claude 3 Opus achieves state-of-the-art results
on evaluations like GPQA [1], MMLU [2], MMMU [3] and many more. Claude 3 Haiku
performs as well or better than Claude 2 [4] on most pure-text tasks, while Sonnet and
Opus significantly outperform it. Additionally, these models exhibit improved fluency in
non-English languages, making them more versatile for a global audience. In this report,
we provide an in-depth analysis of our evaluations, focusing on core capabilities, safety,
societal impacts, and the catastrophic risk assessments we committed to in our Responsible
Scaling Policy [5].
1
Introduction
This model card introduces the Claude 3 family of models, which set new industry benchmarks across rea-
soning, math, coding, multi-lingual understanding, and vision quality.
Like its predecessors, Claude 3 models employ various training methods, such as unsupervised learning and
Constitutional AI [6]. These models were trained using har
```