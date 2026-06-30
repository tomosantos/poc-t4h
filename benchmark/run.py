# benchmark/run.py
"""Roda a matriz modelo x documento x braço e gera tabela de resultados."""
import json
import os
from dotenv import load_dotenv

from benchmark.layouts import DOCUMENTOS, GROUND_TRUTH
from benchmark.judge import julgar
from benchmark.metrics import acuracia_deterministica
from extractor.client import OpenRouterClient
from extractor.pipeline import extrair

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


def linha_resultado(doc_key, modelo, modo, envelope, resp, acuracia_juiz,
                    acuracia_det=None) -> dict:
    return {
        "doc": doc_key, "modelo": modelo, "modo": modo,
        "status": envelope["status"], "n_chamadas": resp.n_chamadas,
        "latencia_s": round(resp.latencia_s, 3),
        "custo_usd": resp.custo_usd,
        "acuracia_juiz": acuracia_juiz,
        "acuracia_det": acuracia_det,
    }


def tabela_markdown(linhas: list[dict]) -> str:
    cab = "| " + " | ".join(_COLUNAS) + " |"
    sep = "| " + " | ".join("---" for _ in _COLUNAS) + " |"
    corpo = ["| " + " | ".join(str(l.get(c, "")) for c in _COLUNAS) + " |"
             for l in linhas]
    return "\n".join([cab, sep, *corpo])


def _salvar(linhas: list[dict]) -> None:
    os.makedirs("benchmark/results", exist_ok=True)
    with open("benchmark/results/results.json", "w", encoding="utf-8") as f:
        json.dump(linhas, f, ensure_ascii=False, indent=2)
    with open("benchmark/results/tabela.md", "w", encoding="utf-8") as f:
        f.write(tabela_markdown(linhas))


def main():
    load_dotenv()
    cli = OpenRouterClient()
    linhas: list[dict] = []
    for doc_key in DOCS_MATRIZ:
        cfg = DOCUMENTOS[doc_key]
        for modelo in MODELOS:
            for modo in ("single", "two_step"):
                max_tok = _MAX_TOKENS.get(modelo)
                try:
                    env, resp = extrair(cfg["arquivo"], cfg["layout"], modelo,
                                        cli, modo=modo, max_tokens=max_tok)
                    veredito = julgar(cfg["arquivo"], env["extracted_data"],
                                      cli, MODELO_JUIZ)
                    if doc_key in GROUND_TRUTH:
                        ac_det, _ = acuracia_deterministica(
                            env["extracted_data"], GROUND_TRUTH[doc_key])
                    else:
                        ac_det = None
                    linhas.append(linha_resultado(doc_key, modelo, modo, env,
                                                  resp, veredito["acuracia"],
                                                  acuracia_det=ac_det))
                    print(f"ok: {doc_key}/{modelo}/{modo}")
                except Exception as e:  # registra falha e segue a matriz
                    print(f"FALHA: {doc_key}/{modelo}/{modo}: {e}")
                _salvar(linhas)  # grava incrementalmente: um hang não perde o resto
    print(f"\n{len(linhas)} linhas salvas em benchmark/results/")


if __name__ == "__main__":
    main()
