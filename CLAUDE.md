# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

This is a technical challenge for a **Generative AI Researcher (R&D)** position. The goal is to investigate and validate alternative approaches to a document data extraction pipeline that currently uses a two-step LLM process (interpretation + JSON formatting). The main problems to address: high latency, high cost, complexity with multi-page/complex layouts, and limited image/chart interpretation.

**Deadline:** July 1, 2026 at 23:59.

## Deliverables

1. **Research Dossier (80% weight)** — A technical PDF with: introduction, methodology, evaluated techniques, experiments/results, conclusions, and viability analysis.
2. **POC (20% weight)** — A minimal implementation (Jupyter notebook, Python script, or simple API) demonstrating the recommended approach against the 3 test documents.

## Test Data

All sample documents are in `data/`:

| File | Type | Characteristics |
|------|------|-----------------|
| `Documento 1.jpeg` | Brazilian CNH (Driver's License) | Structured form, predictable layout |
| `Documento 2.jpg` | CELPE energy bill | Complex layout, tables, dense information |
| `Documento 3.pdf` | Claude 3 Model Family paper | Multi-page, charts, images, academic text |

These three documents represent the spectrum of extraction difficulty the POC must handle.

## Custom Skills

Four research-oriented skills are installed in `.claude/skills/`:

- **`search-first`** — Run before writing any code; searches npm/PyPI/MCP/GitHub for existing solutions.
- **`research-agent`** — System prompt playbook for building citation-backed research agents (TL;DR → findings → sources → unverified).
- **`research-tasks`** — Lightweight web-research process: search → save to `notes/` → structured answer.
- **`academic-researcher`** — Framework for literature reviews, paper analysis, and citation formatting (APA/MLA/Chicago).

## Writing Reference

`example/TCP de Wellinton Oliveira Santos.pdf` is a prior academic paper by the same author. Use it as the reference standard for the research dossier in terms of:

- **Document structure** — how sections are sequenced, titled, and scoped
- **Writing style** — tone, level of formality, and degree of technical density
- **Argumentation pattern** — how claims are introduced, supported, and concluded
- **Visual/layout conventions** — use of figures, tables, captions, and spacing

When drafting or reviewing any section of the research dossier, compare against this document to maintain consistency with the author's established voice and academic register.

## Architecture

There is no build system yet. When implementing the POC, prefer Python with a `requirements.txt` or a Jupyter notebook (`notebooks/`) for reproducibility. Save research notes as markdown under `notes/`. The challenge specification is at `Desafio Técnico_ Pesquisador de IA Generativa (P&D).pdf`.
