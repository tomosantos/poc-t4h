# Reestruturação do Streamlit (`ui/app.py`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reestruturar `ui/app.py` para cobrir os 5 *must-haves* da demo (Abordagem, Conceitos, Achados Chave, Benchmark, Demo) na ordem definida no spec, convertendo Achados Chave de boxes coloridos para accordion.

**Architecture:** Mudança contida em um único arquivo (`ui/app.py`), puramente de apresentação — sem alteração de lógica de extração, benchmark ou dados. Testado com `streamlit.testing.v1.AppTest`, que executa o script Streamlit em modo headless e expõe os elementos renderizados (headers, markdown, expanders) para asserção via pytest, sem precisar de browser.

**Tech Stack:** Python, Streamlit 1.56, pytest, `streamlit.testing.v1.AppTest`.

## Global Constraints

- Nenhuma mudança em `extractor/`, `benchmark/`, lógica de extração ou dados de benchmark (spec, seção "Fora de escopo").
- Conteúdo textual dos 5 achados em "Achados Chave" é o mesmo já existente — só muda o container visual de boxes coloridos para `st.expander`.
- Seção "Abordagem Utilizada" explica só o *quê* (não o como/implementação).
- Ordem final das seções: Header → Abordagem Utilizada → Conceitos Abordados → Benchmark → Achados Chave → Extração ao Vivo.
- Testes rodam via `pytest` a partir da raiz do repo (`testpaths = tests` em `pytest.ini`); `AppTest.from_file("ui/app.py")` assume cwd = raiz do repo.

---

### Task 1: Seção "Abordagem Utilizada" + remoção da linha resumida do header

**Files:**
- Modify: `ui/app.py:34-41` (bloco do header)
- Test: `tests/test_ui_app.py` (novo arquivo)

**Interfaces:**
- Produces: seção Streamlit com `st.header("Abordagem Utilizada")` seguida de um `st.markdown` com o parágrafo explicativo. Nenhuma função nova é criada — é código de script, não uma API.

- [ ] **Step 1: Escrever o teste que falha**

Criar `tests/test_ui_app.py`:

```python
from streamlit.testing.v1 import AppTest


def _run_app():
    at = AppTest.from_file("ui/app.py")
    at.run(timeout=30)
    assert not at.exception
    return at


def test_header_tagline_sem_linha_de_abordagem():
    at = _run_app()
    tagline = at.markdown[0].value
    assert "Abordagem:" not in tagline
    assert "Documentos:" in tagline


def test_secao_abordagem_utilizada_existe():
    at = _run_app()
    headers = [h.value for h in at.header]
    assert "Abordagem Utilizada" in headers
    assert headers.index("Abordagem Utilizada") < headers.index("Resultados do Benchmark")
    corpo = "\n".join(m.value for m in at.markdown)
    assert "single-pass" in corpo
    assert "duas chamadas" in corpo
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `pytest tests/test_ui_app.py -v`
Expected: FAIL — `test_header_tagline_sem_linha_de_abordagem` falha porque a tagline atual contém `"Abordagem:"`; `test_secao_abordagem_utilizada_existe` falha porque o header `"Abordagem Utilizada"` não existe.

- [ ] **Step 3: Implementar a mudança mínima**

Em `ui/app.py`, substituir o bloco (linhas 34-41):

```python
# ── SEÇÃO 1: HEADER ──────────────────────────────────────────────────────────
st.title("POC — Extração de Documentos")
st.markdown(
    "**Abordagem:** single-pass VLM + structured output  ·  "
    "**Documentos:** CNH · Fatura CELPE · Paper acadêmico  ·  "
    "**Modelos:** baseline mid-tier 2024/2025 + candidatos 2025/2026"
)
st.divider()
```

por:

```python
# ── SEÇÃO 1: HEADER ──────────────────────────────────────────────────────────
st.title("POC — Extração de Documentos")
st.markdown(
    "**Documentos:** CNH · Fatura CELPE · Paper acadêmico  ·  "
    "**Modelos:** baseline mid-tier 2024/2025 + candidatos 2025/2026"
)
st.divider()

# ── SEÇÃO 1B: ABORDAGEM UTILIZADA ────────────────────────────────────────────
st.header("Abordagem Utilizada")
st.markdown(
    "O POC substitui o pipeline atual — duas chamadas de modelo, uma para "
    "interpretar o documento e outra para formatar o resultado em JSON — por "
    "uma única chamada *single-pass* com saída estruturada. O modelo lê o "
    "documento (imagem ou PDF) e já retorna os dados no formato final, "
    "eliminando uma etapa inteira do processo sem trocar de arquitetura de "
    "modelo."
)
st.divider()
```

- [ ] **Step 4: Rodar o teste para confirmar que passa**

Run: `pytest tests/test_ui_app.py -v`
Expected: PASS (2 testes)

- [ ] **Step 5: Commit**

```bash
git add ui/app.py tests/test_ui_app.py
git commit -m "feat: adiciona seção Abordagem Utilizada ao Streamlit"
```

---

### Task 2: Seção "Conceitos Abordados" (4 expanders)

**Files:**
- Modify: `ui/app.py` (logo após a seção "Abordagem Utilizada" criada na Task 1, antes de "Resultados do Benchmark")
- Test: `tests/test_ui_app.py` (adicionar teste)

**Interfaces:**
- Consumes: nada da Task 1 além da ordem de seções (a seção Conceitos vem depois de Abordagem Utilizada e antes de Benchmark).
- Produces: 4 `st.expander` com labels exatos `"Single-pass vs. two-step"`, `"VLM (Vision-Language Model)"`, `"Structured output / constrained decoding"`, `"LLM-as-judge vs. métrica determinística"`.

- [ ] **Step 1: Escrever o teste que falha**

Adicionar a `tests/test_ui_app.py`:

```python
def test_secao_conceitos_abordados_tem_4_expanders():
    at = _run_app()
    headers = [h.value for h in at.header]
    assert "Conceitos Abordados" in headers
    assert headers.index("Abordagem Utilizada") < headers.index("Conceitos Abordados")
    assert headers.index("Conceitos Abordados") < headers.index("Resultados do Benchmark")

    labels_esperados = {
        "Single-pass vs. two-step",
        "VLM (Vision-Language Model)",
        "Structured output / constrained decoding",
        "LLM-as-judge vs. métrica determinística",
    }
    labels_encontrados = {e.label for e in at.expander}
    assert labels_esperados.issubset(labels_encontrados)
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `pytest tests/test_ui_app.py -v`
Expected: FAIL — `"Conceitos Abordados"` não está em `headers`.

- [ ] **Step 3: Implementar a mudança mínima**

Em `ui/app.py`, logo depois do `st.divider()` que fecha a seção "Abordagem Utilizada" (adicionada na Task 1) e antes do comentário `# ── SEÇÃO 2: BENCHMARK`, inserir:

```python
# ── SEÇÃO 1C: CONCEITOS ABORDADOS ────────────────────────────────────────────
st.header("Conceitos Abordados")

with st.expander("Single-pass vs. two-step"):
    st.markdown(
        "O pipeline tradicional divide a extração em duas chamadas de "
        "modelo: uma para interpretar o documento em texto livre, outra "
        "para reformatar esse texto em JSON estruturado. A abordagem "
        "*single-pass* consolida as duas etapas em uma única chamada, "
        "usando saída estruturada (JSON Schema) para garantir o formato "
        "final diretamente na primeira interpretação."
    )

with st.expander("VLM (Vision-Language Model)"):
    st.markdown(
        "Um *Vision-Language Model* é um modelo multimodal capaz de "
        "processar imagem e texto na mesma entrada, interpretando o "
        "conteúdo visual do documento (layout, tabelas, campos) sem "
        "depender de OCR prévio para extrair o texto bruto."
    )

with st.expander("Structured output / constrained decoding"):
    st.markdown(
        "*Structured output* força o modelo a gerar apenas tokens que "
        "respeitam um schema JSON pré-definido, restringindo "
        "(*constrained decoding*) o espaço de saída possível a cada passo "
        "de geração. Isso elimina erros de formatação e a necessidade de "
        "uma segunda chamada só para normalizar o texto em JSON."
    )

with st.expander("LLM-as-judge vs. métrica determinística"):
    st.markdown(
        "*LLM-as-judge* usa um modelo de linguagem para avaliar se a "
        "extração está correta, comparando o resultado com a imagem ou "
        "com um gabarito. É útil, mas pode ser leniente. A métrica "
        "determinística compara campo a campo o valor extraído contra um "
        "*ground truth* fixo, sem subjetividade — por isso o POC usa as "
        "duas em conjunto."
    )

st.divider()
```

- [ ] **Step 4: Rodar o teste para confirmar que passa**

Run: `pytest tests/test_ui_app.py -v`
Expected: PASS (3 testes)

- [ ] **Step 5: Commit**

```bash
git add ui/app.py tests/test_ui_app.py
git commit -m "feat: adiciona seção Conceitos Abordados ao Streamlit"
```

---

### Task 3: Reestruturar "Achados Chave" de boxes coloridos para 5 expanders

**Files:**
- Modify: `ui/app.py:91-130` (bloco atual de `col1, col2 = st.columns(2)` até o `st.info` final)
- Test: `tests/test_ui_app.py` (adicionar teste)

**Interfaces:**
- Consumes: nada das Tasks 1-2 além da posição (a seção "Achados Chave" continua depois de "Resultados do Benchmark").
- Produces: 5 `st.expander` com labels exatos: `"Prompt ancorado supera escalação de modelo"`, `"Juiz LLM é leniente — métrica dupla é necessária"`, `"CPF: gargalo de legibilidade intrínseca"`, `"Single-pass funciona para fatura e paper"`, `"Modelos testados são mid-tier 2024/2025 — abordagem é model-agnostic"`.

- [ ] **Step 1: Escrever o teste que falha**

Adicionar a `tests/test_ui_app.py`:

```python
def test_secao_achados_chave_tem_5_expanders():
    at = _run_app()
    labels_esperados = [
        "Prompt ancorado supera escalação de modelo",
        "Juiz LLM é leniente — métrica dupla é necessária",
        "CPF: gargalo de legibilidade intrínseca",
        "Single-pass funciona para fatura e paper",
        "Modelos testados são mid-tier 2024/2025 — abordagem é model-agnostic",
    ]
    labels_encontrados = [e.label for e in at.expander]
    for label in labels_esperados:
        assert label in labels_encontrados

    # Não deve sobrar nenhum st.info/st.warning/st.success da versão antiga
    # (a seção de Conceitos usa só st.markdown dentro de expander, então
    # qualquer alert restante pertence à implementação antiga de Achados).
    assert len(at.info) == 0
    assert len(at.warning) == 0
    assert len(at.success) == 0
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `pytest tests/test_ui_app.py -v`
Expected: FAIL — `at.expander` não contém os 5 labels (a seção atual usa `st.info`/`st.warning`/`st.success` em colunas); `at.info`/`at.warning`/`at.success` não estão vazios.

- [ ] **Step 3: Implementar a mudança mínima**

Em `ui/app.py`, substituir todo o bloco (linhas 91-130, do `col1, col2 = st.columns(2)` até o `st.info` final antes de `st.divider()`):

```python
col1, col2 = st.columns(2)
with col1:
    st.info(
        "**Prompt ancorado supera escalação de modelo**\n\n"
        "`gemini-2.5-flash-lite` com prompt com âncoras de campo atinge o mesmo 4/6 "
        "que `gemini-2.5-pro`, a **57× menos custo**. "
        "Escalação de modelo não compensa para documentos com layout ambíguo."
    )
    st.info(
        "**Juiz LLM é leniente — métrica dupla é necessária**\n\n"
        "`gpt-4o` como juiz aprovou datas incorretas ao comparar com imagem de baixa "
        "resolução. Métrica determinística (campo a campo vs. ground truth) é mais "
        "confiável que LLM-as-judge isolado."
    )
with col2:
    st.warning(
        "**CPF: gargalo de legibilidade intrínseca**\n\n"
        "Falha em **100% dos modelos e modos** no baseline. Upscaling 3× LANCZOS "
        "não ajudou (+153% custo, zero ganho). "
        "DeepSeek V4 Flash foi testado mas não tinha suporte a imagem no OpenRouter "
        "à época da avaliação (`Error 404: No endpoints found that support image input`), "
        "excluído da matriz final. Candidatos com OCR superior: `qwen3-vl-32b`."
    )
    st.success(
        "**Single-pass funciona para fatura e paper**\n\n"
        "Acurácia ≥ 0.85 com modelo pequeno. Two-step acrescenta latência e custo "
        "sem ganho proporcional em documentos sem ambiguidade de layout."
    )

st.info(
    "**Modelos testados são mid-tier 2024/2025 — a abordagem é model-agnostic**\n\n"
    "Baseline: `gemini-2.5-flash-lite` \\$0.10/1M · `gpt-4o-mini` \\$0.15/1M · "
    "`qwen2.5-vl-72b` \\$0.80/1M.  \n"
    "Candidatos 2025/2026 incluídos nesta versão: `qwen3-vl-32b` \\$0.10/1M "
    "(melhor OCR, mesmo custo) · `deepseek-v4-flash` \\$0.09/1M (mais barato) · "
    "`gemini-3.1-flash-lite` \\$0.25/1M · `gpt-5-mini` \\$0.25/1M · "
    "`claude-haiku-4.5` \\$1.00/1M.  \n"
    "Modelos frontier (GPT-5.5 \\$5/1M, Sonnet 4.6 \\$3/1M) são 20–50× mais caros "
    "sem ganho proporcional esperado para extração de documentos estruturados."
)
```

por:

```python
with st.expander("Prompt ancorado supera escalação de modelo"):
    st.markdown(
        "`gemini-2.5-flash-lite` com prompt com âncoras de campo atinge o mesmo 4/6 "
        "que `gemini-2.5-pro`, a **57× menos custo**. "
        "Escalação de modelo não compensa para documentos com layout ambíguo."
    )

with st.expander("Juiz LLM é leniente — métrica dupla é necessária"):
    st.markdown(
        "`gpt-4o` como juiz aprovou datas incorretas ao comparar com imagem de baixa "
        "resolução. Métrica determinística (campo a campo vs. ground truth) é mais "
        "confiável que LLM-as-judge isolado."
    )

with st.expander("CPF: gargalo de legibilidade intrínseca"):
    st.markdown(
        "Falha em **100% dos modelos e modos** no baseline. Upscaling 3× LANCZOS "
        "não ajudou (+153% custo, zero ganho). "
        "DeepSeek V4 Flash foi testado mas não tinha suporte a imagem no OpenRouter "
        "à época da avaliação (`Error 404: No endpoints found that support image input`), "
        "excluído da matriz final. Candidatos com OCR superior: `qwen3-vl-32b`."
    )

with st.expander("Single-pass funciona para fatura e paper"):
    st.markdown(
        "Acurácia ≥ 0.85 com modelo pequeno. Two-step acrescenta latência e custo "
        "sem ganho proporcional em documentos sem ambiguidade de layout."
    )

with st.expander("Modelos testados são mid-tier 2024/2025 — abordagem é model-agnostic"):
    st.markdown(
        "Baseline: `gemini-2.5-flash-lite` \\$0.10/1M · `gpt-4o-mini` \\$0.15/1M · "
        "`qwen2.5-vl-72b` \\$0.80/1M.  \n"
        "Candidatos 2025/2026 incluídos nesta versão: `qwen3-vl-32b` \\$0.10/1M "
        "(melhor OCR, mesmo custo) · `deepseek-v4-flash` \\$0.09/1M (mais barato) · "
        "`gemini-3.1-flash-lite` \\$0.25/1M · `gpt-5-mini` \\$0.25/1M · "
        "`claude-haiku-4.5` \\$1.00/1M.  \n"
        "Modelos frontier (GPT-5.5 \\$5/1M, Sonnet 4.6 \\$3/1M) são 20–50× mais caros "
        "sem ganho proporcional esperado para extração de documentos estruturados."
    )
```

- [ ] **Step 4: Rodar o teste para confirmar que passa**

Run: `pytest tests/test_ui_app.py -v`
Expected: PASS (4 testes)

- [ ] **Step 5: Rodar a suíte completa de testes de UI e confirmar ordem final das seções**

Run: `pytest tests/test_ui_app.py -v`
Expected: 4 passed — confirma cobertura de Abordagem, Conceitos, e Achados Chave, e que a ordem de headers é `["Abordagem Utilizada", "Conceitos Abordados", "Resultados do Benchmark", "Achados Chave", "Extração ao Vivo"]`.

- [ ] **Step 6: Commit**

```bash
git add ui/app.py tests/test_ui_app.py
git commit -m "refactor: converte Achados Chave de boxes coloridos para expanders"
```

---

### Task 4: Explicitar o que a seção "Extração ao Vivo" demonstra

**Files:**
- Modify: `ui/app.py:134-138` (header + caption da seção "Extração ao Vivo")
- Test: `tests/test_ui_app.py` (adicionar teste)

**Interfaces:**
- Consumes: nada das Tasks 1-3 além da posição (a seção continua sendo a última, sem mudança de lógica de `extrair(...)`).
- Produces: um `st.markdown` explicativo entre `st.header("Extração ao Vivo")` e o `st.caption` já existente.

- [ ] **Step 1: Escrever o teste que falha**

Adicionar a `tests/test_ui_app.py`:

```python
def test_secao_demo_explica_single_pass_e_limite_two_step():
    at = _run_app()
    corpo = "\n".join(m.value for m in at.markdown)
    assert "single-pass" in corpo
    assert "two_step" in corpo or "two-step" in corpo
    assert "lado a lado" in corpo
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `pytest tests/test_ui_app.py -v`
Expected: FAIL — nenhum `st.markdown` atual menciona `"lado a lado"` nem `two_step`/`two-step` perto de `single-pass`.

- [ ] **Step 3: Implementar a mudança mínima**

Em `ui/app.py`, substituir:

```python
st.header("Extração ao Vivo")
st.caption(
    "Reproduza qualquer extração — verifique os achados acima com seus próprios documentos."
)
```

por:

```python
st.header("Extração ao Vivo")
st.markdown(
    "Esta seção roda o modo `single` (single-pass VLM + structured output), a "
    "técnica recomendada e validada no benchmark acima. O baseline `two_step` "
    "(interpretação livre + formatação JSON) existe no código "
    "(`extractor.pipeline.two_step`) mas não é exposto aqui lado a lado — quem "
    "só usa esta seção não vê a técnica antiga sendo reproduzida, só a "
    "recomendada."
)
st.caption(
    "Reproduza qualquer extração — verifique os achados acima com seus próprios documentos."
)
```

- [ ] **Step 4: Rodar o teste para confirmar que passa**

Run: `pytest tests/test_ui_app.py -v`
Expected: PASS (5 testes)

- [ ] **Step 5: Commit**

```bash
git add ui/app.py tests/test_ui_app.py
git commit -m "docs: explicita no Streamlit que a Demo roda single-pass, não two-step"
```

---

## Verificação final (fora dos tasks, checklist manual)

- [ ] Rodar `streamlit run ui/app.py` e conferir visualmente que as 6 seções aparecem na ordem correta e os expanders de Conceitos e Achados Chave têm o mesmo padrão visual.
- [ ] Conferir que a tabela de Benchmark (com o fix de cor já aplicado) e a seção "Extração ao Vivo" continuam funcionando sem mudança.
