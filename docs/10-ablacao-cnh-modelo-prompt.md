# Ablação 2×2 CNH: Modelo × Prompt

**Data:** 2026-06-28  
**Documento:** `data/Documento 1.jpeg` (CNH, 341×600 px)  
**Campos avaliados:** nome, cpf, data_nascimento, data_emissao, filiacao_pai, filiacao_mae (6 total)  
**Ground truth:**
- nome: `LINCE DA SILVA`
- cpf: `091.340.611-75` (dígitos: `09134061175`)
- data_nascimento: `06/08/1961`
- data_emissao: `22/10/2013`
- filiacao_pai: `Pai José da Silva`
- filiacao_mae: `Mãe Maria da Silva`

---

## Configuração dos Experimentos

**Modelos:**
- **small** = `google/gemini-2.5-flash-lite`
- **strong** = `google/gemini-2.5-pro`

**Condições de prompt:**
- **GENERIC** = `_PROMPT_EXTRACAO` original (sem ancoragem de campo)
- **ANCHORED** = Layout CNH enriquecido com descrições-âncora por campo (e.g. `data_emissao = "data no rodapé rotulada 'DATA EMISSÃO' — NÃO a 1ª habilitação nem a validade"`)

**Pontuação:** match determinístico com normalização justa — casefold + strip de acentos; CPF e datas comparados apenas pelos dígitos; filiação remove token-prefixo ("pai"/"mãe") de ambos os lados.

---

## Tabela 2×2

| Célula | Modelo | Prompt | Score | cpf | data_nascimento | data_emissao | Custo (USD) | Latência (s) |
|--------|--------|--------|-------|-----|-----------------|--------------|-------------|--------------|
| small_GENERIC | gemini-2.5-flash-lite | GENERIC | **3/6** | FAIL | FAIL | FAIL | $0.000279 | 3.7 |
| small_ANCHORED | gemini-2.5-flash-lite | ANCHORED | **4/6** | FAIL | FAIL | OK | $0.000294 | 3.2 |
| strong_GENERIC | gemini-2.5-pro | GENERIC | **4/6** | FAIL | FAIL | OK | $0.019894 | 16.0 |
| strong_ANCHORED | gemini-2.5-pro | ANCHORED | **4/6** | FAIL | FAIL | OK | $0.012784 | 11.1 |

---

## Dados Brutos por Célula

### small_GENERIC (3/6)
```json
{
  "nome": "LINCE DA SILVA",       // OK
  "cpf": "891.340.611-75",        // FAIL — 1º dígito errado (8 vs 0)
  "data_nascimento": "02/05/2017", // FAIL — confunde com outra data
  "data_emissao": "02/05/2018",   // FAIL — confunde com validade
  "filiacao_pai": "Pai José da Silva", // OK (após strip prefixo)
  "filiacao_mae": "Mae Maria da Silva" // OK (após strip prefixo)
}
```

### small_ANCHORED (4/6)
```json
{
  "nome": "LINCE DA SILVA",       // OK
  "cpf": "",                      // FAIL — recusa ler (confessa não ver)
  "data_nascimento": "",          // FAIL — recusa ler
  "data_emissao": "22/10/2013",   // OK — ancoragem corrigiu
  "filiacao_pai": "José da Silva", // OK
  "filiacao_mae": "Maria da Silva" // OK
}
```

### strong_GENERIC (4/6)
```json
{
  "nome": "LINCE DA SILVA",       // OK
  "cpf": "891.340.611-75",        // FAIL — mesmo erro de leitura do 1º dígito
  "data_nascimento": "02/05/2017", // FAIL — mesma confusão
  "data_emissao": "22/10/2013",   // OK — modelo forte já âncora corretamente
  "filiacao_pai": "José da Silva", // OK
  "filiacao_mae": "Maria da Silva" // OK
}
```

### strong_ANCHORED (4/6)
```json
{
  "nome": "LINCE DA SILVA",       // OK
  "cpf": "891.340.611-75",        // FAIL — 1º dígito ainda errado
  "data_nascimento": "02/05/2017", // FAIL — confusão persiste
  "data_emissao": "22/10/2013",   // OK
  "filiacao_pai": "José da Silva", // OK
  "filiacao_mae": "Maria da Silva" // OK
}
```

---

## Análise por Diagnóstico

### CPF — Problema de Legibilidade (intrinsic)
O modelo extrai `891.340.611-75` em todas as células que conseguem ler o campo. O 1º dígito real é `0`, mas a imagem (341×600 px, baixa resolução) o torna ambíguo para qualquer modelo. O upscaling já havia sido testado sem ganho (nota 09). Nenhum dos dois levers (modelo nem prompt) resolve legibilidade intrínseca.

### data_nascimento — Problema de Disambiguação Não Resolvido
A ancoragem de `data_emissao` funcionou (o modelo para de confundir com a validade). Porém `data_nascimento` (`06/08/1961`) permanece errada em todos os 4 runs — os modelos retornam `02/05/2017` ou ficam em branco. Isso sugere que a ambiguidade de datas da CNH tem uma terceira fonte não endereçada: o modelo interpreta `06/08/1961` como outra data ou não encontra o campo correto. A âncora para `data_nascimento` no prompt ANCHORED diz "data rotulada 'DATA NASCIMENTO'" mas a legibilidade ou o layout do JPEG impede a localização.

### data_emissao — Resolvida por Ancoragem (e por modelo forte)
- small_GENERIC: FAIL (confunde com validade `02/05/2018`)
- small_ANCHORED: OK (ancoragem corrigiu a confusão)
- strong_GENERIC: OK (modelo forte resolve sem âncora)
- strong_ANCHORED: OK

A âncora equivale ao ganho do modelo forte neste campo específico — ambos levam ao mesmo resultado.

---

## Delta de Custo

| Transição | Custo médio | Delta |
|-----------|-------------|-------|
| small (média das 2 condições) | ~$0.000286 | — |
| strong (média das 2 condições) | ~$0.016339 | **~57× mais caro** |

O modelo forte é ~57× mais caro por chamada e **não acrescenta nenhum campo correto** em relação ao small+ANCHORED.

---

## Veredicto

| Hipótese | Resultado |
|----------|-----------|
| Ancoragem corrige as datas? | **Parcialmente** — corrige `data_emissao`, mas não `data_nascimento` |
| Modelo forte corrige CPF? | **Não** — CPF permanece errado em todos os 4 runs |
| Modelo forte supera ancoragem? | **Não** — atinge o mesmo 4/6 que small+ANCHORED, a custo 57× maior |
| Qual lever importa? | **Prompt > Modelo** para este documento — ancoragem é o único lever com efeito positivo; escalação não acrescenta |

### Recomendação para estratégia em camadas
A ancoragem do prompt deve ser **padronizada** no layout da CNH — ela corrige `data_emissao` sem custo extra. O modelo forte não recupera os campos restantes (`cpf`, `data_nascimento`) e custa ~57× mais: **escalação não compensa para CNH**. Os dois campos que permanecem com falha (`cpf` e `data_nascimento`) têm natureza diferente:
- `cpf`: problema de legibilidade intrínseca da imagem — requer pré-processamento de imagem ou OCR especializado (Document AI / Tesseract com região de corte)
- `data_nascimento`: provável problema de layout/ambiguidade não endereçado pela âncora atual — pode se beneficiar de âncora mais específica com coordenadas visuais ("campo à esquerda do CPF") ou de um prompt de cadeia de raciocínio (CoT) que liste todas as datas visíveis antes de atribuir
