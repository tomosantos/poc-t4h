# Nota 09 — Teste de Upscaling na CNH (Documento 1.jpeg)

**Data:** 2026-06-28  
**Objetivo:** Verificar se redimensionar a imagem da CNH de 341×600 px para 1023×1800 px (3× LANCZOS + Sharpness 1.5) melhora a extração dos 6 campos.

---

## Configuração

- **Imagem original:** `data/Documento 1.jpeg` (341×600 px)
- **Imagem upscalada:** PNG temporário 1023×1800 px (3× LANCZOS + ImageEnhance.Sharpness 1.5), salvo fora do repositório
- **Modelos:** `google/gemini-2.5-flash-lite` e `openai/gpt-4o-mini`
- **Método:** `single_pass` + `aplicar_validators`; 4 extrações no total
- **Normalização:** casefold+strip+sem-acento para texto; dígitos apenas para CPF e datas; prefixo pai/mae removido de ambos os lados para filiação

---

## Resultados

### google/gemini-2.5-flash-lite

| Campo           | Original        | Ground Truth    | OK? | Upscalado       | OK? | Mudança |
|-----------------|-----------------|-----------------|-----|-----------------|-----|---------|
| nome            | LINCE DA SILVA  | LINCE DA SILVA  | OK  | LINCE DA SILVA  | OK  | —       |
| cpf             | null (inválido) | 091.340.611-75  | FAIL| null (inválido) | FAIL| —       |
| data_nascimento | ""              | 06/08/1961      | FAIL| 06/08/1981      | FAIL| —       |
| data_emissao    | 02/05/2017      | 22/10/2013      | FAIL| 02/05/2017      | FAIL| —       |
| filiacao_pai    | Pai José da Silva | Pai José da Silva | OK | Pai José da Silva | OK | —    |
| filiacao_mae    | Mae Maria da Silva | Mãe Maria da Silva | OK | Mae Maria da Silva | OK | —  |

**Placar:** 3/6 → 3/6 (sem mudança)  
**Latência:** 4,2 s → 4,4 s (+0,2 s)  
**Custo:** $0,000296 → $0,000285 (≈−$0,000011, dentro do ruído)

---

### openai/gpt-4o-mini

| Campo           | Original        | Ground Truth    | OK? | Upscalado       | OK? | Mudança |
|-----------------|-----------------|-----------------|-----|-----------------|-----|---------|
| nome            | Lince da Silva  | LINCE DA SILVA  | OK  | Lince da Silva  | OK  | —       |
| cpf             | null (inválido) | 091.340.611-75  | FAIL| null (inválido) | FAIL| —       |
| data_nascimento | 13/06/1981      | 06/08/1961      | FAIL| 06/08/1981      | FAIL| —       |
| data_emissao    | 22/12/2013      | 22/10/2013      | FAIL| 22/10/2019      | FAIL| —       |
| filiacao_pai    | José da Silva   | Pai José da Silva | OK | José da Silva  | OK  | —       |
| filiacao_mae    | Maria da Silva  | Mãe Maria da Silva | OK | Maria da Silva | OK | —      |

**Placar:** 3/6 → 3/6 (sem mudança)  
**Latência:** 3,1 s → 5,2 s (+2,1 s)  
**Custo:** $0,00222 → $0,00563 (+$0,00341, +153% — mais tokens visuais)

---

## Análise dos Campos Críticos

- **CPF:** nulo/inválido nos 4 casos. O modelo não consegue ler os dígitos independentemente da resolução. Provável que o campo esteja visualmente degradado ou que o modelo não extraia CPFs de documentos sintéticos/fictícios.
- **data_nascimento:** ambos os modelos leram "1981" em vez de "1961" — o algarismo `6` do ano está sendo lido como `8`. O upscaling não ajudou; o erro persiste e o dígito errado muda ligeiramente (`13/06` → `06/08`), sugerindo variância do modelo, não melhora de resolução.
- **data_emissao:** igualmente errada nos 4 casos; mês e/ou ano incorretos.

---

## Diagnóstico

O problema **não é de resolução de imagem** — é de legibilidade intrínseca do documento (fontes pequenas, possível sobreposição de campos, JPEG original com artefatos de compressão). Ampliar via LANCZOS apenas interpola pixels existentes sem recuperar informação; o upscaling "inventa" bordas que o modelo não consegue aproveitar.

---

## Custos e Latência (resumo)

| Modelo              | Δ Custo       | Δ Latência |
|---------------------|---------------|------------|
| gemini-2.5-flash-lite | ≈$0 (ruído) | +0,2 s     |
| gpt-4o-mini           | +$0,0034 (+153%) | +2,1 s |

---

## Veredicto

**Upscaling não moveu a agulha.** Nenhum campo mudou de FAIL → OK em nenhum dos dois modelos. Os campos que falhavam (CPF, data_nascimento, data_emissao) continuaram falhando com os mesmos tipos de erro. Para gpt-4o-mini, o custo mais que dobrou sem ganho algum. Para gemini-2.5-flash-lite o custo foi neutro mas o resultado idêntico.

**Recomendação:** Não valer a pena incluir upscaling no pipeline final. Investigar, em vez disso: (1) pré-processamento alternativo (binarização, denoising); (2) prompt engineering mais específico (pedir CPF com pontuação explicitamente); (3) modelo com melhor OCR nativo como `google/gemini-2.5-pro` ou `mistral/mistral-ocr-latest`.
