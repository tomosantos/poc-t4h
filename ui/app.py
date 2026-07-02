# ui/app.py
"""UI Streamlit — POC Extração de Documentos."""
import json
import math
import os
import tempfile
from pathlib import Path

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
]

_RESULTS_PATH = Path(__file__).parent.parent / "benchmark" / "results" / "results.json"

st.set_page_config(page_title="POC Extração de Documentos", layout="wide")

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
        "depender de OCR prévio para extrair o texto bruto. "
        "É essa capacidade nativa de leitura visual que permite o pipeline "
        "*single-pass* — o modelo lê diretamente a CNH, a fatura ou o paper "
        "e retorna os dados estruturados em uma única chamada, sem etapas "
        "intermediárias de conversão imagem → texto → JSON."
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

# ── SEÇÃO 2: BENCHMARK ───────────────────────────────────────────────────────
st.header("Resultados do Benchmark")

if os.path.exists(_RESULTS_PATH):
    with open(_RESULTS_PATH, encoding="utf-8") as f:
        dados = json.load(f)
    df = pd.DataFrame(dados)
    df_display = df.copy()
    df_display["custo_usd"] = df_display["custo_usd"].apply(
        lambda x: f"${x:.5f}" if pd.notna(x) else "—"
    )
    df_display["latencia_s"] = df_display["latencia_s"].apply(lambda x: f"{x:.1f}s")
    df_display.rename(columns={
        "doc": "Documento", "modelo": "Modelo", "modo": "Modo",
        "status": "Status", "n_chamadas": "Chamadas",
        "latencia_s": "Latência", "custo_usd": "Custo",
        "acuracia_juiz": "Ac. Juiz", "acuracia_det": "Ac. Det.",
    }, inplace=True)

    def _cor_ac(val):
        if not isinstance(val, float) or math.isnan(val):
            return ""
        if val >= 0.7:
            return "background-color: #d4edda; color: #155724"
        if val >= 0.5:
            return "background-color: #fff3cd; color: #856404"
        return "background-color: #f8d7da; color: #721c24"

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

st.divider()

# ── SEÇÃO 4: DEMO ────────────────────────────────────────────────────────────
st.header("Demo")
st.markdown(
    "Esta seção roda a técnica recomendada em cada caso: `single` "
    "(single-pass VLM + structured output) para imagens, e `hybrid` "
    "(PyMuPDF determinístico + VLM só nas páginas com figura, até 3) para "
    "PDFs — selecionado automaticamente pelo tipo de arquivo enviado. O "
    "baseline `two_step` (interpretação livre + formatação JSON) existe no "
    "código (`extractor.pipeline.two_step`) mas não é exposto aqui lado a "
    "lado."
)
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
                modo = "hybrid" if sufixo.lower() == ".pdf" else "single"
                envelope, resp = extrair(
                    caminho, DOCUMENTOS[layout_id]["layout"],
                    modelo, OpenRouterClient(), modo=modo,
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
