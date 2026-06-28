# POC — Extração de Documentos (single-pass + structured output)

Demonstra a recomendação do dossiê: colapsar o pipeline de 2 inferências em 1
chamada (VLM + structured output via OpenRouter), espelhando o contrato da
Tech4.ai (`{status, extracted_data}`).

## Setup
```bash
cp .env.example .env   # e preencha OPENROUTER_API_KEY
pip install -r requirements.txt
pytest                 # roda os testes (chamadas de rede são skipadas sem chave)
```

## Rodar
- API:  `uvicorn api.main:app --reload`  → http://localhost:8000/docs
- UI:   `streamlit run ui/app.py`        → http://localhost:8501
- Docker: `docker compose up`            → API :8000, UI :8501
- Benchmark: `python -m benchmark.run`   → benchmark/results/{results.json,tabela.md}
- Demo híbrida do paper (PyMuPDF + VLM na figura): `python -m benchmark.paper_hibrido`

## Arquitetura
`extractor/` (engine) · `api/` (FastAPI) · `ui/` (Streamlit) · `benchmark/` (experimento + LLM-as-judge).
Ver `.specs/` para spec e plano.
