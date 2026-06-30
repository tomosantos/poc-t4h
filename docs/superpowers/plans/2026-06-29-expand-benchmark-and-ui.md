# Expansão da Matriz de Benchmark + Redesign da UI

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expandir a matriz de benchmark com 6 modelos 2025/2026, rodar os testes, redesenhar a UI Streamlit em 4 seções (header, benchmark, achados, extração ao vivo), e documentar os achados comparativos.

**Architecture:** Três tarefas em sequência com dependência unidirecional: (1) ampliar `benchmark/run.py` e rodar a matriz completa → `results.json` atualizado; (2) redesenhar `ui/app.py` consumindo esse JSON e expondo extração ao vivo com comparação campo a campo; (3) escrever nota de achados com os números reais do benchmark.

**Tech Stack:** Python 3.10+, Streamlit ≥ 1.36, Pandas, OpenRouter API via `openai` SDK, `python-dotenv`.

## Global Constraints

- Todos os novos modelos são chamados via OpenRouter com a mesma interface do baseline (`openai` SDK + `response_format json_schema strict`)
- Falhas de modelo são capturadas por `try/except` — não interrompem a matriz
- `max_tokens=4000` para todos os modelos novos (paridade com baseline ≈ 3000)
- `DOCS_MATRIZ` permanece `["cnh", "fatura"]` — paper usa caminho híbrido separado
- UI permanece single-file em `ui/app.py` — não criar arquivos auxiliares
- `pandas` deve estar em `requirements.txt`

---

### Task 1: Expandir matriz de benchmark e rodar testes

**Files:**
- Modify: `benchmark/run.py` (linhas 13–33)
- Modify: `requirements.txt`
- Produces: `benchmark/results/results.json`, `benchmark/results/results_baseline.json`

**Interfaces:**
- Produces: `results.json` com entradas para 9 modelos × 2 docs × 2 modos (≈ 36 linhas)

- [ ] **Step 1: Adicionar pandas ao requirements.txt**

Abrir `requirements.txt` e adicionar ao final:
```
pandas>=2.2.0
```

Instalar no ambiente ativo:
```bash
pip install "pandas>=2.2.0"
```

- [ ] **Step 2: Fazer backup do results.json atual**

```bash
cp benchmark/results/results.json benchmark/results/results_baseline.json
```

Verificar que o arquivo foi criado:
```bash
ls benchmark/results/
```
Esperado: `results.json` e `results_baseline.json`.

- [ ] **Step 3: Substituir MODELOS e _MAX_TOKENS em benchmark/run.py**

Substituir as linhas 13–33 de `benchmark/run.py` por:

```python
MODELOS = [
    # Baseline (mid-tier 2024/2025)
    "google/gemini-2.5-flash-lite",
    "openai/gpt-4o-mini",
    "qwen/qwen2.5-vl-72b-instruct",
    # Candidatos 2025/2026
    "google/gemini-3.1-flash-lite",
    "openai/gpt-5-mini",
    "anthropic/claude-haiku-4.5",
    "qwen/qwen3-vl-8b-instruct",
    "qwen/qwen3-vl-32b-instruct",
    "deepseek/deepseek-v4-flash",
]
MODELO_JUIZ = "openai/gpt-4o"
_COLUNAS = ["doc", "modelo", "modo", "status", "n_chamadas",
            "latencia_s", "custo_usd", "acuracia_juiz", "acuracia_det"]

DOCS_MATRIZ = ["cnh", "fatura"]

_MAX_TOKENS: dict[str, int] = {
    "google/gemini-2.5-flash-lite":    3000,
    "openai/gpt-4o-mini":              3000,
    "qwen/qwen2.5-vl-72b-instruct":    3000,
    "google/gemini-3.1-flash-lite":    4000,
    "openai/gpt-5-mini":               4000,
    "anthropic/claude-haiku-4.5":      4000,
    "qwen/qwen3-vl-8b-instruct":       4000,
    "qwen/qwen3-vl-32b-instruct":      4000,
    "deepseek/deepseek-v4-flash":      4000,
}
```

- [ ] **Step 4: Rodar o benchmark**

```bash
set PYTHONPATH=. && python -m benchmark.run
```

Acompanhar saída — cada linha `ok: cnh/modelo/modo` confirma uma extração. Falhas são logadas mas não interrompem a matriz (o script salva incrementalmente).

Esperado ao final:
```
N linhas salvas em benchmark/results/
```
onde N ≈ 36 (9 modelos × 2 docs × 2 modos), descontando eventuais falhas.

- [ ] **Step 5: Verificar results.json**

```bash
python -c "import json; d=json.load(open('benchmark/results/results.json')); print(len(d),'linhas'); [print(m) for m in sorted(set(r['modelo'] for r in d))]"
```

Esperado: 9 modelos listados, ≥ 30 linhas.

- [ ] **Step 6: Commit**

```bash
git add benchmark/run.py benchmark/results/results.json benchmark/results/results_baseline.json requirements.txt
git commit -m "feat: expand benchmark matrix to 9 models (mid-tier 2024-2026)"
```

---

### Task 2: Redesenhar ui/app.py

**Files:**
- Rewrite: `ui/app.py`

**Interfaces:**
- Consumes: `benchmark/results/results.json` (Task 1), `benchmark.layouts.DOCUMENTOS`, `benchmark.layouts.GROUND_TRUTH`, `extractor.client.OpenRouterClient`, `extractor.pipeline.extrair`
- `extrair(caminho, layout, modelo, client, modo) → (envelope, resp)` onde `envelope = {"status": str, "extracted_data": dict}` e `resp.latencia_s`, `resp.custo_usd`, `resp.n_chamadas` são os campos de métricas

- [ ] **Step 1: Reescrever ui/app.py**

Substituir o conteúdo inteiro de `ui/app.py` por:

```python
# ui/app.py
"""UI Streamlit — POC Extração de Documentos."""
import json
import math
import os
import tempfile

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from benchmark.layouts import DOCUMENTOS, GROUND_TRUTH
from extractor.client import OpenRouterClient
from extractor.pipeline import extrair

load_dotenv()

MODELOS_UI = [
    "google/gemini-2.5-flash-lite",
    "openai/gpt-4o-mini",
    "qwen/qwen2.5-vl-72b-instruct",
    "google/gemini-3.1-flash-lite",
    "openai/gpt-5-mini",
    "anthropic/claude-haiku-4.5",
    "qwen/qwen3-vl-8b-instruct",
    "qwen/qwen3-vl-32b-instruct",
    "deepseek/deepseek-v4-flash",
]

_RESULTS_PATH = "benchmark/results/results.json"

st.set_page_config(page_title="POC Extração de Documentos", layout="wide")

# ── SEÇÃO 1: HEADER ──────────────────────────────────────────────────────────
st.title("POC — Extração de Documentos")
st.markdown(
    "**Abordagem:** single-pass VLM + structured output  ·  "
    "**Documentos:** CNH · Fatura CELPE · Paper acadêmico  ·  "
    "**Modelos:** baseline mid-tier 2024/2025 + candidatos 2025/2026"
)
st.divider()

# ── SEÇÃO 2: BENCHMARK ───────────────────────────────────────────────────────
st.header("Resultados do Benchmark")

if os.path.exists(_RESULTS_PATH):
    with open(_RESULTS_PATH, encoding="utf-8") as f:
        dados = json.load(f)
    df = pd.DataFrame(dados)
    df_display = df.copy()
    df_display["custo_usd"] = df_display["custo_usd"].apply(
        lambda x: f"${x:.5f}" if x is not None else "—"
    )
    df_display["latencia_s"] = df_display["latencia_s"].apply(lambda x: f"{x:.1f}s")
    df_display.rename(columns={
        "doc": "Documento", "modelo": "Modelo", "modo": "Modo",
        "status": "Status", "n_chamadas": "Chamadas",
        "latencia_s": "Latência", "custo_usd": "Custo",
        "acuracia_juiz": "Ac. Juiz", "acuracia_det": "Ac. Det.",
    }, inplace=True)

    def _cor_ac(val):
        if not isinstance(val, float):
            return ""
        if val >= 0.7:
            return "background-color: #d4edda"
        if val >= 0.5:
            return "background-color: #fff3cd"
        return "background-color: #f8d7da"

    st.dataframe(
        df_display.style.map(_cor_ac, subset=["Ac. Juiz", "Ac. Det."]),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "**Ac. Det.:** comparação determinística campo a campo vs. ground truth (CNH apenas).  "
        "**Ac. Juiz:** avaliação por LLM-as-judge (`gpt-4o`).  "
        "Divergências entre métricas indicam leniência do juiz — ver Achados Chave."
    )
else:
    st.warning(
        "Resultados não encontrados. Execute `python -m benchmark.run` para gerar."
    )

st.divider()

# ── SEÇÃO 3: ACHADOS CHAVE ───────────────────────────────────────────────────
st.header("Achados Chave")

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
        "Candidatos com OCR nativo superior (`qwen3-vl`, `deepseek-v4`) são "
        "os próximos a testar."
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

st.divider()

# ── SEÇÃO 4: EXTRAÇÃO AO VIVO ────────────────────────────────────────────────
st.header("Extração ao Vivo")
st.caption(
    "Reproduza qualquer extração — verifique os achados acima com seus próprios documentos."
)

col_m, col_l = st.columns(2)
with col_m:
    modelo = st.selectbox("Modelo", MODELOS_UI)
with col_l:
    layout_id = st.selectbox("Layout", list(DOCUMENTOS.keys()))

arquivo = st.file_uploader(
    "Documento (jpg / png / webp / pdf)", type=["jpg", "jpeg", "png", "webp", "pdf"]
)

if arquivo and st.button("Extrair", type="primary"):
    sufixo = os.path.splitext(arquivo.name)[1] or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=sufixo) as tmp:
        tmp.write(arquivo.getvalue())
        caminho = tmp.name

    col_doc, col_res = st.columns(2)
    with col_doc:
        st.subheader("Documento")
        if sufixo.lower() != ".pdf":
            st.image(arquivo.getvalue())
        else:
            st.info("PDF enviado.")

    with col_res:
        st.subheader("Resultado")
        with st.spinner("Extraindo..."):
            try:
                envelope, resp = extrair(
                    caminho, DOCUMENTOS[layout_id]["layout"],
                    modelo, OpenRouterClient(), modo="single",
                )
                m1, m2, m3 = st.columns(3)
                m1.metric("Status", envelope["status"])
                m2.metric("Latência", f"{resp.latencia_s:.2f}s")
                m3.metric("Custo", f"${resp.custo_usd:.5f}" if resp.custo_usd else "—")

                gt = GROUND_TRUTH.get(layout_id)
                extracted = envelope.get("extracted_data", {})

                if gt:
                    st.subheader("Comparação campo a campo")
                    rows = []
                    for campo, valor_gt in gt.items():
                        valor_ext = str(extracted.get(campo) or "").strip()
                        ok = valor_ext.lower() == str(valor_gt).strip().lower()
                        rows.append({
                            "Campo": campo,
                            "Extraído": valor_ext or "—",
                            "Ground Truth": valor_gt,
                            "Match": "✓" if ok else "✗",
                        })
                    df_campos = pd.DataFrame(rows)

                    def _cor_match(val):
                        if val == "✓":
                            return "color: green; font-weight: bold"
                        if val == "✗":
                            return "color: red; font-weight: bold"
                        return ""

                    st.dataframe(
                        df_campos.style.map(_cor_match, subset=["Match"]),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.json(extracted)

            except Exception as e:
                st.error(f"Falha: {e}")
            finally:
                os.unlink(caminho)
```

- [ ] **Step 2: Verificar importação sem erro**

```bash
set PYTHONPATH=. && python -c "import ui.app; print('ok')"
```

Esperado: `ok` (sem traceback).

- [ ] **Step 3: Rodar Streamlit e verificar as 4 seções**

```bash
set PYTHONPATH=. && streamlit run ui/app.py
```

Abrir http://localhost:8501 e confirmar:
1. Título e subtítulo visíveis
2. Tabela de benchmark com cores (verde ≥ 0.7, amarelo ≥ 0.5, vermelho < 0.5)
3. Quatro cards de achados + card de modelos
4. Upload funcional + campo a campo com ✓/✗ ao usar layout CNH

- [ ] **Step 4: Commit**

```bash
git add ui/app.py
git commit -m "feat: redesign UI - benchmark table, achados chave, live extraction with field comparison"
```

---

### Task 3: Nota de achados comparativos 2025/2026

**Files:**
- Create: `notes/11-comparativo-modelos-2026.md`

**Interfaces:**
- Consumes: `benchmark/results/results.json` (Task 1)

- [ ] **Step 1: Extrair dados do results.json para construir a nota**

Rodar para obter a tabela por modelo:

```bash
python -c "
import json, statistics
d = json.load(open('benchmark/results/results.json'))
modelos = sorted(set(r['modelo'] for r in d))
for m in modelos:
    runs = [r for r in d if r['modelo'] == m]
    aj = [r['acuracia_juiz'] for r in runs if r['acuracia_juiz'] is not None]
    ad = [r['acuracia_det'] for r in runs if r['acuracia_det'] is not None]
    lat = [r['latencia_s'] for r in runs]
    custo = [r['custo_usd'] for r in runs if r['custo_usd'] is not None]
    print(f'{m}')
    print(f'  Ac.Juiz={statistics.mean(aj):.2f}  Ac.Det={statistics.mean(ad):.2f if ad else \"n/a\"}  Lat={statistics.mean(lat):.1f}s  Custo=\${statistics.mean(custo):.5f}')
"
```

- [ ] **Step 2: Criar notes/11-comparativo-modelos-2026.md**

Usar a saída do Step 1 para preencher a tabela abaixo e completar a análise. O template:

```markdown
# Comparativo de Modelos 2025/2026

**Data:** 2026-06-29
**Documentos avaliados:** CNH (Documento 1.jpeg), Fatura CELPE (Documento 2.jpg)
**Juiz:** openai/gpt-4o
**Todos os runs:** single + two_step

---

## Tabela de Resultados (médias por modelo)

| Modelo | Tier | Preço Input/1M | Ac. Juiz (média) | Ac. Det. (CNH) | Latência média | Custo médio/extração |
|--------|------|---------------|-----------------|----------------|---------------|---------------------|
| google/gemini-2.5-flash-lite | Baseline | $0.10 | [preencher] | [preencher] | [preencher] | [preencher] |
| openai/gpt-4o-mini | Baseline | $0.15 | [preencher] | [preencher] | [preencher] | [preencher] |
| qwen/qwen2.5-vl-72b-instruct | Baseline | $0.80 | [preencher] | [preencher] | [preencher] | [preencher] |
| google/gemini-3.1-flash-lite | 2025/2026 | $0.25 | [preencher] | [preencher] | [preencher] | [preencher] |
| openai/gpt-5-mini | 2025/2026 | $0.25 | [preencher] | [preencher] | [preencher] | [preencher] |
| anthropic/claude-haiku-4.5 | 2025/2026 | $1.00 | [preencher] | [preencher] | [preencher] | [preencher] |
| qwen/qwen3-vl-8b-instruct | 2025/2026 | $0.08 | [preencher] | [preencher] | [preencher] | [preencher] |
| qwen/qwen3-vl-32b-instruct | 2025/2026 | $0.10 | [preencher] | [preencher] | [preencher] | [preencher] |
| deepseek/deepseek-v4-flash | 2025/2026 | $0.09 | [preencher] | [preencher] | [preencher] | [preencher] |

---

## Análise por Documento

### CNH (Documento 1.jpeg)
- Melhor modelo: [preencher] com Ac. Det. = [X]/6
- CPF extraído corretamente por: [listar modelos que conseguiram ou "nenhum"]
- Achado: [análise dos novos modelos vs. baseline]

### Fatura CELPE (Documento 2.jpg)
- Melhor modelo: [preencher] com Ac. Juiz = [X]
- Achado: [análise dos novos modelos vs. baseline]

---

## Recomendações por Caso de Uso

| Caso de uso | Modelo recomendado | Justificativa |
|-------------|-------------------|---------------|
| Extração de CNH em escala | [preencher] | [preencher] |
| Extração de faturas em escala | [preencher] | [preencher] |
| Máxima acurácia (custo secundário) | [preencher] | [preencher] |
| Menor custo possível | [preencher] | [preencher] |

---

## Conclusão

[Resumo em 3-4 linhas comparando baseline vs. modelos 2025/2026 e o que isso significa
para a recomendação da abordagem single-pass + structured output.]
```

Substituir todos os `[preencher]` com os dados reais do Step 1 e análise qualitativa.

- [ ] **Step 3: Commit**

```bash
git add notes/11-comparativo-modelos-2026.md
git commit -m "docs: nota comparativa modelos 2025/2026 com resultados do benchmark expandido"
```
