# Extração de Documentos — Single-Pass VLM + Structured Output

Desafio técnico para a vaga de **Pesquisador de IA Generativa (P&D)**: investigar e validar
abordagens alternativas ao pipeline de extração de dados de documentos da Tech4.ai, que hoje
roda em **duas inferências sequenciais** (interpretação visual + formatação em JSON).

A recomendação deste projeto — detalhada no **dossiê** — é colapsar as duas chamadas em uma
única inferência (*single-pass*), usando um VLM com *structured output* (`json_schema` +
*constrained decoding*) para gerar diretamente o envelope `{status, extracted_data}` já no
formato esperado pela API da Tech4.ai. Para o caso do paper acadêmico (documento extenso, com
gráficos), avalia-se também uma estratégia **híbrida**: extração determinística de texto/tabelas
via PyMuPDF, com o VLM acionado apenas nas páginas que contêm figuras.

## Deliverables

| Entregável | Onde | Peso |
|---|---|---|
| **Dossiê de pesquisa** — introdução, metodologia, técnicas avaliadas, experimentos/resultados, conclusão e viabilidade | [`dossie/Dossie-Wellinton-Oliveira-Santos.pdf`](dossie/Dossie-Wellinton-Oliveira-Santos.pdf) (fonte em [`dossie/dossie.md`](dossie/dossie.md)) | 80% |
| **POC** — API + UI + benchmark reproduzível contra os 3 documentos de teste | este repositório (`extractor/`, `api/`, `ui/`, `benchmark/`) | 20% |

## Setup

```bash
cp .env.example .env   # preencha OPENROUTER_API_KEY
pip install -r requirements.txt
pytest                 # roda os testes (chamadas de rede são skipadas sem chave)
```

## Como rodar

| O quê | Comando | Endereço |
|---|---|---|
| API (FastAPI) | `uvicorn api.main:app --reload` | <http://localhost:8000/docs> |
| UI (Streamlit) | `streamlit run ui/app.py` | <http://localhost:8501> |
| Docker (API + UI) | `docker compose up` | :8000 e :8501 |
| Benchmark completo | `python -m benchmark.run` | grava em `benchmark/results/{results.json,tabela.md}` |
| Demo híbrida do paper | `python -m benchmark.paper_hibrido` | PyMuPDF + VLM só na figura |

A API espelha o contrato da Tech4.ai:

```
POST /extract   (multipart: layout_id, file)  ->  {status: "ok"|"partial"|"error", extracted_data: {...}}
GET  /layouts   ->  {layouts: ["cnh", "fatura", "paper"]}
GET  /health    ->  {status: "ok"}
```

## Documentos de teste

Em `data/`, representando o espectro de dificuldade de extração:

| Arquivo | Tipo | Características |
|---|---|---|
| `Documento 1.jpeg` | CNH brasileira | Formulário estruturado, layout previsível |
| `Documento 2.jpg` | Fatura de energia CELPE | Layout complexo, tabelas, informação densa |
| `Documento 3.pdf` | Paper "Claude 3 Model Family" | Múltiplas páginas, gráficos, imagens, texto acadêmico |

## Estrutura do repositório

```
extractor/    # motor de extração: client OpenRouter (single-pass e two-step),
              # schemas JSON a partir do Layout, validators (CPF/CNPJ),
              # extração determinística de PDF via PyMuPDF
api/          # FastAPI — expõe /extract, /layouts, /health
ui/           # Streamlit — dashboard de benchmark + extração ao vivo
benchmark/    # matriz modelo x documento x modo, LLM-as-judge, acurácia
              # determinística vs. ground truth, resultados em results/
tests/        # suíte pytest (unit + smoke) cobrindo todos os módulos acima
dossie/       # fonte (Markdown + Pandoc/xeLaTeX) e PDF final do dossiê
docs/         # notas de pesquisa (01–11) que fundamentam o dossiê
.specs/       # design docs e planos de implementação
data/         # os 3 documentos de teste
```

## Achados-chave do benchmark

Resumo (ver dossiê para análise completa e o Achados-Chave da UI para o detalhamento):

- **Prompt ancorado > escalação de modelo**: `gemini-2.5-flash-lite` com prompt com âncoras de
  campo iguala `gemini-2.5-pro` a 57× menos custo.
- **CPF é o gargalo**: falha em 100% dos modelos/modos no baseline; upscaling 3× não ajuda
  (+153% custo, zero ganho).
- **Single-pass já é suficiente** para fatura e paper (acurácia ≥ 0.85); two-step só acrescenta
  latência/custo sem ganho em documentos sem ambiguidade de layout.
- **LLM-as-judge é leniente** — por isso o benchmark reporta duas métricas: acurácia por juiz
  (`gpt-4o`) e acurácia determinística campo a campo contra o ground truth da CNH.

## Testes

```bash
pytest
```

Cobre schemas, validators, encoding, extração de PDF, pipeline, API, layouts, métricas e
LLM-as-judge. Testes que dependem de rede (chamadas reais ao OpenRouter) são skipados
automaticamente se `OPENROUTER_API_KEY` não estiver configurada.
