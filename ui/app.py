# ui/app.py
"""UI Streamlit: upload de documento + extração lado a lado."""
import os
import tempfile
import streamlit as st
from dotenv import load_dotenv

from benchmark.layouts import DOCUMENTOS
from extractor.client import OpenRouterClient
from extractor.pipeline import extrair

load_dotenv()
st.set_page_config(page_title="POC Extração de Documentos", layout="wide")
st.title("POC — Extração de Documentos (single-pass + structured output)")

modelo = st.sidebar.selectbox("Modelo", [
    "google/gemini-2.5-flash-lite", "openai/gpt-4o-mini",
    "qwen/qwen2.5-vl-72b-instruct"])
layout_id = st.sidebar.selectbox("Layout", list(DOCUMENTOS.keys()))
arquivo = st.file_uploader("Documento (jpg/png/pdf)",
                           type=["jpg", "jpeg", "png", "webp", "pdf"])

if arquivo and st.button("Extrair"):
    sufixo = os.path.splitext(arquivo.name)[1] or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=sufixo) as tmp:
        tmp.write(arquivo.getvalue())
        caminho = tmp.name
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Documento")
        if sufixo.lower() != ".pdf":
            st.image(arquivo.getvalue())
        else:
            st.info("PDF enviado (pré-visualização não exibida).")
    with col2:
        st.subheader("Extração")
        with st.spinner("Extraindo..."):
            try:
                envelope, resp = extrair(caminho, DOCUMENTOS[layout_id]["layout"],
                                         modelo, OpenRouterClient(), modo="single")
                st.json(envelope)
                st.caption(f"status={envelope['status']} · {resp.n_chamadas} chamada(s) "
                           f"· {resp.latencia_s:.2f}s · custo=${resp.custo_usd}")
            except Exception as e:
                st.error(f"Falha: {e}")
            finally:
                os.unlink(caminho)
