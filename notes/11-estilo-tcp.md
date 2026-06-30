# Guia de Estilo — TCP de Wellinton Oliveira Santos

Referência: *Modelagem Preditiva de Sinistros Agrícolas: Uma Arquitetura de Aprendizado de Máquina sobre Dados do SISSER (2016-2025)*, UNIFAL-MG, 2026.

---

## 1. Estrutura

**Sequência de seções:**

1. Capa (instituição, autor, título, cidade/ano)
2. Folha de rosto (com nota de apresentação justificada à direita e orientadora)
3. Folha de aprovação (banca)
4. RESUMO (PT-BR) + Palavras-chave
5. ABSTRACT (EN) + Keywords
6. SUMÁRIO com numeração de páginas
7. 1 INTRODUÇÃO
8. 2 REFERENCIAL TEÓRICO (com subseções 2.1, 2.2, 2.2.1, 2.2.2, 2.2.3, 2.2.4)
9. 3 METODOLOGIA (com subseções 3.1, 3.2, 3.3, 3.4)
10. 4 RESULTADOS E DISCUSSÕES (com subseções 4.1, 4.2, 4.3, 4.4)
11. 5 CONSIDERAÇÕES FINAIS
12. REFERÊNCIAS

**Convenções de numeração:**
- Seções primárias: número arábico + título em negrito e maiúsculas (`**1 INTRODUÇÃO**`)
- Subseções de segundo nível: `2.1 SEGURO RURAL NO BRASIL` — maiúsculas, sem negrito no corpo, mas em negrito no sumário
- Subseções de terceiro nível: `2.2.1 Árvores de Decisão e *Ensembles*` — capitalização normal, termos técnicos em itálico
- Sem apêndices nem anexos neste trabalho; o padrão ABNT admite, mas o autor não os utilizou

**Resumo/Abstract:** blocos de texto corrido, sem parágrafo, sem marcadores. Uma única paragraph densa (approx. 200–250 palavras). Palavras-chave separadas por ponto-e-vírgula, em itálico no português e em redondo no inglês.

**Introdução:** encerra com parágrafo explícito de roadmap das seções ("o trabalho está organizado em cinco seções…"), indicando o conteúdo de cada uma.

**Considerações Finais:** retoma o objetivo, sintetiza os principais achados, lista limitações e indica direções futuras — sem nova subseção, tudo em parágrafos corridos.

---

## 2. Voz e Registro

**Pessoa gramatical:** impessoal / terceira pessoa do singular passiva reflexiva — nunca primeira pessoa.
- "o presente estudo tem por objetivo desenvolver…"
- "o presente artigo desenvolve e avalia…"
- "Dessa forma, o presente estudo adota a mesma lógica…"

**Formalidade:** alta. Nenhuma expressão coloquial. Distância acadêmica mantida mesmo ao descrever escolhas do próprio autor.

**Densidade de período:** parágrafos longos, com 5–10 linhas cada. Orações subordinadas encadeadas, mas nunca ambíguas. O autor conclui cada parágrafo com uma frase-síntese que fecha o argumento antes de passar ao próximo ponto.

**Tecnicidade:** alta. Termos em inglês (pipeline, feature store, point-in-time, out-of-time, baseline, overfitting, shrinkage, fine-tuning, data leakage, recall, precision) são mantidos em itálico na primeira ocorrência ou quando incorporados ao texto corrido. Siglas são definidas na primeira ocorrência e usadas livremente depois.

**Tom:** assertivo com ressalvas moderadas. O autor não especula; quando reconhece incerteza, usa "pode ser atribuído" ou "é indicativo de". Evita hedging excessivo.

---

## 3. Padrão de Argumentação

**Abertura de seção/subseção:** começa com afirmação contextual ampla que ancora o tópico no cenário econômico ou técnico maior, depois estreita para o objeto específico.
- Exemplo (Introdução): "O agronegócio brasileiro constitui um dos pilares estruturais da economia nacional… Esses resultados, no entanto, estão sujeitos a um conjunto de riscos climáticos…"

**Suporte de afirmações:** toda afirmação relevante é imediatamente seguida de citação(ões). Dados numéricos são sempre ancorados em fonte. Afirmações metodológicas são sustentadas tanto por literatura quanto por raciocínio próprio explicitado.

**Encadeamento lógico:** o autor usa conectivos explícitos e sistemáticos: "Dessa forma,", "Nesse contexto,", "Nessa perspectiva,", "Além disso,", "Por fim,", "Assim,". Os parágrafos nunca começam abruptamente — sempre há ponte com o que foi dito antes.

**Comparação com literatura:** os resultados próprios são sempre contrapostos a resultados de referência com quantificação explícita ("supera em 26 pontos percentuais o melhor resultado reportado…"). Tabelas comparativas são usadas na seção de resultados.

**Limitações:** tratadas em seção final e na discussão dos resultados; apresentadas de forma direta, sem minimização excessiva, mas acompanhadas de proposta de superação futura.

**Hipótese:** não há formulação explícita de hipótese como seção separada; a pergunta de pesquisa é implícita, derivada da lacuna identificada na literatura.

---

## 4. Convenções Visuais e de Layout

**Figuras:**
- Legenda acima: `Figura N - Título descritivo` (capitalização de sentença, sem ponto final)
- Fonte abaixo: `Fonte: elaboração própria.` ou `Fonte: elaboração própria, com base em Autor (ano).` ou `Fonte: elaboração própria. Fonte dos Dados: AUTOR (ano)`
- Numeração sequencial global (Figura 1, Figura 2, …, Figura 13)

**Tabelas:**
- Legenda acima com "Tabela N - Título" (mesmo padrão de Figura, mas usa *Tabela*)
- `Fonte: elaboração própria` abaixo
- Exemplos: `Tabela 3 - Métricas baseline dos algoritmos`

**Quadros:**
- Legenda acima com "Quadro N **–** Título" (travessão após número, diferente das Figuras/Tabelas que usam hífen simples)
- `Fonte: Elaboração própria com base em Autor (ano)` — note maiúscula em "Elaboração"
- Usados para sínteses conceituais e taxonomias (ex: Matriz de Confusão, tabela de Feature Store)

**Equações:** numeradas à direita entre parênteses — (1), (2), (3). Apresentadas em parágrafo próprio, com variáveis definidas em texto antes ou imediatamente depois.

**Listas numeradas:** usadas raramente e apenas para elencar propriedades técnicas com texto explicativo longo por item (ex: três propriedades do XGBoost na seção 2.2.2). Nunca bullet points.

**Itálico:** usado para: (a) termos estrangeiros incorporados ao texto, (b) nomes de variáveis/tabelas de dados (ex: *flSinistro*, *dtRef*, *fs\_historico\_municipio*), (c) títulos de obras nas referências (negrito para periódico/publicação).

---

## 5. Estilo de Citação

**Sistema:** ABNT autor-data (NBR 6023).

**In-text — até dois autores:**
- `(Ozaki, 2008)` — um autor
- `(Chen; Guestrin, 2016)` — dois autores, separados por ponto-e-vírgula

**In-text — três autores:**
- `(Mota; Miquelluti; Ozaki, 2020)` — todos listados, separados por ponto-e-vírgula (ABNT não usa "et al." para três autores no in-text neste trabalho)

**In-text — integrado na frase:**
- `Mota, Miquelluti e Ozaki (2020)` — vírgulas e "e" antes do último quando integrado no texto corrido

**Múltiplas referências:** separadas por ponto-e-vírgula dentro de um único par de parênteses: `(Fawcett, 2006; Mota; Miquelluti; Ozaki, 2020)`

**Referências bibliográficas (ao final):**
- Ordem alfabética pelo sobrenome do primeiro autor
- Título da obra em **negrito**
- Periódico/revista em *itálico* e negrito: `**Risks**`, `**Machine Learning**`, `**Economia Aplicada**`
- Formato: `SOBRENOME, Inicial. Título da obra. **Periódico**, v. X, n. X, p. XX–XX, ano.`
- Para livros: `SOBRENOME, Nome. **Título do Livro**: subtítulo. Cidade: Editora, ano.`
- Para sites/documentos online: `Disponível em: Link. Acesso em: DD mês. AAAA`
- Entidade governamental como autor: `BRASIL. **Título**. Cidade: Órgão, ano. Xp.`

---

## 6. Língua e Extensão

**Idioma principal:** Português do Brasil (PT-BR), com Abstract em inglês (EN-US formal).

**Extensão total:** 37 páginas (incluindo pré-textuais e referências). O corpo do texto (Introdução a Considerações Finais) ocupa páginas 6–34, ou seja, aproximadamente 29 páginas de texto.

**Extensão por seção:**
- Resumo/Abstract: ~1 página cada
- Introdução: ~2 páginas
- Referencial Teórico: ~9 páginas (a maior seção)
- Metodologia: ~8 páginas
- Resultados e Discussões: ~9 páginas
- Considerações Finais: ~2 páginas
- Referências: ~2 páginas

**Parágrafos:** tipicamente 6–12 linhas, com espaçamento 1,5 e recuo de primeira linha. Sem linha em branco entre parágrafos — separação por recuo apenas.

**Número de referências:** 26 obras citadas.

**Figuras:** 13 no total. Tabelas/Quadros: 3 no total.

---

## 7. Hábitos Estilísticos Distintivos

**Conectivos de abertura de parágrafo:** o autor quase nunca inicia parágrafo com o sujeito direto. Preferência por:
- "Dessa forma," → transição de consequência (mais frequente)
- "Nesse contexto," / "Nessa perspectiva," → transição de enquadramento
- "Além disso," → adição
- "Por fim," → encerramento de enumeração
- "Assim," → conclusão lógica

**Fórmula de roadmap da Introdução:** o último parágrafo da Introdução é sempre uma descrição explícita da estrutura do trabalho, seção a seção: "A seção 2 apresenta… A seção 3 descreve… A seção 4 apresenta… A seção 5 sintetiza…"

**Fórmula de transição entre subseções:** a última frase de cada subseção anuncia o que vem a seguir: "A subseção seguinte descreve como os arquivos brutos do SISSER foram transformados…" / "As seções 2.2.1 e 2.2.2 detalham, respectivamente, os fundamentos…"

**Definição formal seguida de aplicação:** sempre que introduz um conceito técnico, o autor o define formalmente (às vezes com notação matemática) e imediatamente explicita como ele se aplica ao problema específico deste trabalho. Ex: define classificação binária → "No presente estudo, o problema é de classificação binária: o rótulo assume valor 1 quando…"

**Qualificação assertiva sem hedging desnecessário:** afirmações de resultado são diretas: "O XGBoost obteve o melhor desempenho em todas as métricas avaliadas"; limitações são nomeadas sem minimização: "essa constatação inviabiliza o cálculo de métricas supervisionadas sobre o período OOT".

**Expressão "isto é":** usada para inserir definição/elucidação dentro do período, sempre separada por vírgulas: "a subamostragem reduz o volume da majoritária, isto é, cada camada aplica transformações incrementais…"

**Itálico para variáveis e tabelas de dados:** nomes de colunas e tabelas aparecem em itálico no meio do texto corrido, sem formatação de código, criando um estilo híbrido texto/técnico: *flSinistro*, *dtRef*, *fs\_historico\_municipio*, *pipeline*, *Feature Store*.

**Parênteses para valores de apoio:** dados numéricos secundários são inseridos entre parênteses sem interromper o fluxo: "a concentração na Região Sul é dominante, sendo responsável por 709.012 apólices, equivalentes a 65% da base total".
