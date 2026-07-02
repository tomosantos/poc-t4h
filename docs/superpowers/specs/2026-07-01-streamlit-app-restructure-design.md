# Reestruturação do Streamlit (`ui/app.py`)

## Contexto

O POC (`ui/app.py`) hoje cobre 3 dos 5 *must-haves* definidos para a
demo: Benchmark, Achados Chave e Demo ao vivo. Faltam "Abordagem
Utilizada" (existe só como uma linha no header) e "Conceitos
Abordados" (não existe). Além disso, a seção "Achados Chave" atual usa
4 boxes coloridos (`st.info`/`st.warning`/`st.success`) em 2 colunas —
decisão do usuário foi trocar por um padrão de accordion uniforme,
consistente com a nova seção de Conceitos.

Também foi corrigido nesta sessão o contraste de cores da tabela de
benchmark (`_cor_ac` em `ui/app.py`), que ficava ilegível no tema
escuro do Streamlit — texto claro sobre fundo pastel claro. Fix já
aplicado (adiciona `color:` a cada faixa), fora do escopo deste spec.

## Objetivo

Reestruturar `ui/app.py` para cobrir os 5 *must-haves* na ordem abaixo,
mantendo Benchmark e Demo intactos e convertendo Achados Chave para o
mesmo padrão visual da nova seção Conceitos.

## Escopo

Novas seções + 1 seção reestruturada, todas dentro de `ui/app.py`. Sem
mudança de lógica de extração, benchmark ou dados — só camada de
apresentação.

### Ordem final das seções

1. **Header** — mantém título; remove a linha resumida de "Abordagem"
   do `st.markdown` inicial (linha 36-40), já que vira seção própria.
2. **Abordagem Utilizada** *(nova)* — explica só o *quê* (não o como):
   consolidação do pipeline de duas etapas (interpretação + formatação
   JSON) em uma única chamada *single-pass* com *structured output*.
   Texto corrido, 1 parágrafo curto, sem detalhe de implementação
   (schema, código, chamadas de API).
3. **Conceitos Abordados** *(nova)* — 4 `st.expander(expanded=False)`,
   um por conceito, mesmo padrão visual entre si:
   - Single-pass vs. two-step
   - VLM (Vision-Language Model)
   - Structured output / constrained decoding
   - LLM-as-judge vs. métrica determinística

   Cada expander: título curto + 2-4 frases de explicação. Sem jargão
   não definido; assume leitor familiarizado com IA generativa mas não
   necessariamente com esses termos específicos.
4. **Benchmark** *(sem mudança)* — mantém `st.dataframe` com
   `_cor_ac` já corrigido.
5. **Achados Chave** *(reestruturada)* — troca os 4 boxes coloridos em
   2 colunas + 1 box de contexto por **5 `st.expander`** (mesmo padrão
   visual da seção Conceitos), um por achado, fechados por padrão:
   - Prompt ancorado supera escalação de modelo
   - Juiz LLM é leniente — métrica dupla é necessária
   - CPF: gargalo de legibilidade intrínseca
   - Single-pass funciona para fatura e paper
   - Modelos testados são mid-tier 2024/2025 — abordagem é model-agnostic

   Conteúdo textual de cada achado é o mesmo já existente no código
   atual (linhas 92-130) — só muda o container visual, não o texto.
6. **Extração ao Vivo (Demo)** *(pequeno acréscimo textual)* — a lógica
   não muda, mas fica implícito hoje o que a seção demonstra. Adicionar
   um parágrafo logo após o header deixando explícito que: (a) a seção
   roda o modo `single` (single-pass VLM + structured output), a
   técnica recomendada e validada no benchmark; (b) o baseline
   `two-step` existe no código (`extractor.pipeline.two_step`) mas não
   é exposto aqui para comparação lado a lado — quem só usa esta seção
   não vê a técnica antiga sendo reproduzida, só a recomendada.

## Fora de escopo

- Qualquer mudança em `extractor/`, `benchmark/`, lógica de extração
  ou dados de benchmark.
- Mudança no fix de cores da tabela (`_cor_ac`) — já aplicado.
- Dossiê PDF (`dossie/`) — os 5 *must-haves* são só para o Streamlit,
  não para o documento de pesquisa.

## Critério de sucesso

- `ui/app.py` roda sem erro (`streamlit run ui/app.py`).
- As 6 seções aparecem na ordem acima.
- Conceitos e Achados Chave usam o mesmo padrão de `st.expander`,
  visualmente consistentes entre si.
- Nenhum dado, texto de achado ou lógica de benchmark/demo foi
  alterado além do container visual.
