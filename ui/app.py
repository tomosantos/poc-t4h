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
