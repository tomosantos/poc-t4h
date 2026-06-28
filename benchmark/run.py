# benchmark/run.py
"""Roda a matriz modelo x documento x braço e gera tabela de resultados."""
import json
import os
from dotenv import load_dotenv

from benchmark.layouts import DOCUMENTOS
from benchmark.judge import julgar
from extractor.client import OpenRouterClient
from extractor.pipeline import extrair

MODELOS = [
    "google/gemini-2.5-flash-lite",
    "openai/gpt-4o-mini",
    "qwen/qwen2.5-vl-72b-instruct",
]
MODELO_JUIZ = "openai/gpt-4o"
_COLUNAS = ["doc", "modelo", "modo", "status", "n_chamadas",
            "latencia_s", "custo_usd", "acuracia"]


def linha_resultado(doc_key, modelo, modo, envelope, resp, acuracia) -> dict:
    return {
        "doc": doc_key, "modelo": modelo, "modo": modo,
        "status": envelope["status"], "n_chamadas": resp.n_chamadas,
        "latencia_s": round(resp.latencia_s, 3),
        "custo_usd": resp.custo_usd, "acuracia": acuracia,
    }


def tabela_markdown(linhas: list[dict]) -> str:
    cab = "| " + " | ".join(_COLUNAS) + " |"
    sep = "| " + " | ".join("---" for _ in _COLUNAS) + " |"
    corpo = ["| " + " | ".join(str(l.get(c, "")) for c in _COLUNAS) + " |"
             for l in linhas]
    return "\n".join([cab, sep, *corpo])


def main():
    load_dotenv()
    cli = OpenRouterClient()
    linhas = []
    for doc_key, cfg in DOCUMENTOS.items():
        for modelo in MODELOS:
            for modo in ("single", "two_step"):
                try:
                    env, resp = extrair(cfg["arquivo"], cfg["layout"], modelo,
                                        cli, modo=modo)
                    veredito = julgar(cfg["arquivo"], env["extracted_data"],
                                      cli, MODELO_JUIZ)
                    linhas.append(linha_resultado(doc_key, modelo, modo, env,
                                                  resp, veredito["acuracia"]))
                    print(f"ok: {doc_key}/{modelo}/{modo}")
                except Exception as e:  # registra falha e segue a matriz
                    print(f"FALHA: {doc_key}/{modelo}/{modo}: {e}")
    os.makedirs("benchmark/results", exist_ok=True)
    with open("benchmark/results/results.json", "w", encoding="utf-8") as f:
        json.dump(linhas, f, ensure_ascii=False, indent=2)
    with open("benchmark/results/tabela.md", "w", encoding="utf-8") as f:
        f.write(tabela_markdown(linhas))
    print(f"\n{len(linhas)} linhas salvas em benchmark/results/")


if __name__ == "__main__":
    main()
