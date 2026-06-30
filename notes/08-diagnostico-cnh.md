# Diagnóstico de Baixa Acurácia — CNH (Documento 1.jpeg)

Data: 2026-06-28  
Método: 3 extrações single-pass + 1 chamada ao juiz (`openai/gpt-4o`)

---

## 1. Resultados do Benchmark (results.json)

| Modelo | Modo | Status | Acurácia (juiz) |
|---|---|---|---|
| google/gemini-2.5-flash-lite | single | partial | 0.33 |
| google/gemini-2.5-flash-lite | two_step | partial | 0.33 |
| openai/gpt-4o-mini | single | partial | 0.50 |
| openai/gpt-4o-mini | two_step | partial | **0.83** |
| qwen/qwen2.5-vl-72b-instruct | single | partial | 0.67 |
| qwen/qwen2.5-vl-72b-instruct | two_step | partial | 0.67 |

Todos os runs retornam `status=partial` porque o campo `cpf` retorna `None` em TODOS os modelos e modos — o validator CPF zera o campo quando o modelo não extrai um CPF válido ou extrai valor incorreto.

---

## 2. Ground Truth

```json
{
  "nome":              "LINCE DA SILVA",
  "cpf":               "091.340.611-75",
  "data_nascimento":   "06/08/1961",
  "data_emissao":      "22/10/2013",
  "filiacao_pai":      "Pai José da Silva",
  "filiacao_mae":      "Mãe Maria da Silva"
}
```

**Nota:** Os valores de `filiacao_pai` e `filiacao_mae` no ground truth incluem o prefixo literal "Pai" / "Mãe", que é incomum em CNHs reais e provavelmente reflete uma ficção do documento de teste. Modelos tendem a extrair apenas o nome.

---

## 3. Extração campo a campo por modelo

### 3.1 google/gemini-2.5-flash-lite

| Campo | Extraído | Ground Truth | Match (det.) |
|---|---|---|---|
| nome | LINCE DA SILVA | LINCE DA SILVA | OK |
| cpf | None (validador zerou) | 091.340.611-75 | FAIL |
| data_nascimento | **02/05/2017** | 06/08/1961 | FAIL |
| data_emissao | 22/10/2013 | 22/10/2013 | OK |
| filiacao_pai | Pai José da Silva | Pai José da Silva | OK |
| filiacao_mae | Mae Maria da Silva | Mãe Maria da Silva | OK (pós-normalização) |

Acurácia determinística: 4/6 ≈ 0.67 (juiz reportou 0.33 — discrepância grave, ver seção 5).

### 3.2 openai/gpt-4o-mini

| Campo | Extraído | Ground Truth | Match (det.) |
|---|---|---|---|
| nome | Lince da Silva | LINCE DA SILVA | OK (case-insensitive) |
| cpf | None (validador zerou) | 091.340.611-75 | FAIL |
| data_nascimento | **03/06/1981** | 06/08/1961 | FAIL |
| data_emissao | **22/12/2013** | 22/10/2013 | FAIL (mês errado: 12 vs 10) |
| filiacao_pai | José da Silva | Pai José da Silva | FAIL (falta prefixo "Pai") |
| filiacao_mae | Maria da Silva | Mãe Maria da Silva | FAIL (falta prefixo "Mãe") |

Acurácia determinística: 1/6 ≈ 0.17 (juiz reportou 0.83 — juiz muito leniente).

### 3.3 qwen/qwen2.5-vl-72b-instruct

| Campo | Extraído | Ground Truth | Match (det.) |
|---|---|---|---|
| nome | Lince da Silva | LINCE DA SILVA | OK |
| cpf | None (validador zerou) | 091.340.611-75 | FAIL |
| data_nascimento | **06/05/1991** | 06/08/1961 | FAIL |
| data_emissao | **22/10/2019** | 22/10/2013 | FAIL (ano errado: 2019 vs 2013) |
| filiacao_pai | Joaél da Silva | Pai José da Silva | FAIL (nome corrompido) |
| filiacao_mae | (alucinação repetitiva — string gigante de lixo) | Mãe Maria da Silva | FAIL |

Acurácia determinística: 1/6 ≈ 0.17 (juiz reportou 0.67 — juiz leniente).

---

## 4. Chamada ao Juiz (openai/gpt-4o avaliando extração do gpt-4o-mini)

**Acurácia reportada pelo juiz:** 0.83

| Campo | Juiz | Match Determinístico | Concordância | Extraído |
|---|---|---|---|---|
| nome | TRUE | TRUE | AGREE | 'Lince da Silva' |
| cpf | FALSE | FALSE | AGREE | None |
| data_nascimento | **TRUE** | FALSE | **DISAGREE** | '03/06/1981' |
| data_emissao | **TRUE** | FALSE | **DISAGREE** | '22/12/2013' |
| filiacao_pai | **TRUE** | FALSE | **DISAGREE** | 'José da Silva' |
| filiacao_mae | **TRUE** | FALSE | **DISAGREE** | 'Maria da Silva' |

**Comentário do juiz:** "O CPF extraído está como null, mas o documento possui um número de CPF visível."

O juiz acertou apenas o CPF e o nome. Para os outros 4 campos errou ao aprovar valores incorretos.

---

## 5. Classificação das Causas Raiz

| Campo | Causa | Detalhe |
|---|---|---|
| **cpf** | **(a) Extração falha — limitação do modelo** | Todos os 3 modelos retornam None. O validador CPF em `pipeline.py` zera valores inválidos. O CPF é visível mas pequeno na imagem; os modelos ou não lêem ou transcrevem dígitos errados (CPF inválido → zerado). Isso força `status=partial` em 100% dos runs. |
| **data_nascimento** | **(a) + (b) Extração genuinamente errada + juiz leniente** | Todos os modelos erram completamente (datas muito diferentes: 1961 vs 1981/1991/2017). A CNH tem múltiplas datas próximas (nascimento, habilitação, validade, emissão) em campos pequenos — confusão de layout. O juiz (`gpt-4o`) aprova valores incorretos sem verificar contra o documento. |
| **data_emissao** | **(a) + (b) Extração parcialmente errada + juiz leniente** | Gemini acerta; gpt-4o-mini erra o mês (10→12); Qwen erra o ano (2013→2019). O juiz aprova mesmo assim. Possível ambiguidade de campo (data de 1ª habilitação vs data de emissão). |
| **filiacao_pai / filiacao_mae** | **(c) + (d) Mismatch de formato + ground truth discutível** | Modelos extraem "José da Silva" / "Maria da Silva" (correto semanticamente). Ground truth exige prefixo "Pai " / "Mãe " que não é padrão de CNH. O juiz aprova sem prefixo (conduta mais razoável). A comparação determinística falha por causa do prefixo artificial no ground truth. |

### Resumo das causas por frequência

1. **Causa principal — imagem de baixa resolução:** O CPF (campo mais crítico) falha em 100% dos modelos. Datas são transcritas com dígitos errados. A imagem `.jpeg` é pequena e comprimida, tornando texto fino ilegível para VLMs.
2. **Causa secundária — ground truth com prefixos artificiais ("Pai", "Mãe"):** Penaliza modelos que extraem o nome limpo, inflando as falhas de filiação na métrica determinística.
3. **Causa terciária — juiz LLM muito leniente:** O juiz (`gpt-4o`) aprova datas e nomes incorretos ao comparar com a imagem, provavelmente porque a própria imagem é difícil de ler. Isso infla a acurácia reportada (ex.: gpt-4o-mini aparece com 0.83 mas acurácia real é ~0.17).
4. **Causa quaternária — múltiplas datas na CNH sem âncora de campo:** Sem instrução explícita de qual campo visual corresponde a "data_nascimento" vs "data_emissão", modelos confundem campos.

---

## 6. Recomendações

1. **Corrigir os valores de ground truth para filiacao_pai/filiacao_mae:** Remover os prefixos "Pai " e "Mãe " do `GROUND_TRUTH_CNH`. A extração semântica correta é o nome, não o rótulo impresso. Isso corrige pelo menos 2 campos de falha na métrica determinística para Gemini.

2. **Separar duas métricas no benchmark:** (a) *Acurácia vs. Ground Truth* (determinística, comparação direta) e (b) *Fidelidade ao Documento* (LLM-as-judge). Atualmente o benchmark usa apenas o juiz, mascarando casos onde o juiz é leniente (gpt-4o-mini parece melhor que Gemini quando na prática Gemini é mais fiel para a CNH). Isso deve ser discutido explicitamente no dossiê como limitação da metodologia.

3. **Melhorar o prompt de extração para CNHs com campo-âncora visual:** Adicionar instrução explícita como "Na CNH, 'data_nascimento' está no campo rotulado 'DATA NASC.', 'data_emissao' no campo 'DATA EMISSÃO'" — ou fornecer um layout de campos esperados. Isso reduz a confusão entre as múltiplas datas.

4. **Considerar pré-processamento de imagem (upscaling/binarização) antes da chamada VLM:** O CPF falhando em 100% sugere que a resolução da imagem é o gargalo primário. Um passo de super-resolução ou OCR dedicado (ex.: Tesseract com região de interesse) aplicado ao CPF antes do VLM eliminaria a causa raiz do `status=partial` universal.
