# 06 — Baseline: Tech4.ai Vision Doc Extraction API

> Workstream 6 — Caracterização da solução atual (BASELINE) a partir da documentação oficial.
> Toda afirmação é citada com a URL específica. O que foi **inferido** está marcado como tal.
> Doc é nichada e majoritariamente em PT-BR; conteúdo coletado via WebFetch ativo em 2026-06-26.

---

## TL;DR (5 bullets)

- **O que é:** API REST de *document data extraction* que recebe a URL de um arquivo (imagem/documento) + um `layout_id` e devolve um JSON com os campos extraídos. Endpoint único `POST https://api.tech4.ai/document/extract/`. [doc-extraction-api]
- **Como o cliente especifica os campos:** via um **layout** criado num *visual builder* (admin panel), onde cada campo tem nome, tipo de dado (Date/Text/Number...) e uma **descrição em linguagem natural** ("onde está, como é formatado, palavras-chave"). O layout é referenciado por `layout_id` na chamada — o cliente **não** envia um JSON Schema na request. [layout-config]
- **Processo de 2 etapas (do desafio):** há evidência **indireta** — a doc descreve o layout como "um mapa que você fornece a **um modelo de IA** para encontrar a informação" (etapa de interpretação) e o retorno como JSON estruturado conforme o layout (etapa de formatação). A doc **não detalha** explicitamente "2 chamadas LLM" nem latência/modelos. [layout-config]
- **Foco brasileiro forte:** *validators* nativos **CPF, CNPJ, UF e Linha Digitável de boleto**; exemplo oficial de saída é uma **CNH** (`categoria_habilitacao`, `data_validade`, `data_1a_habilitacao`). Documentação majoritariamente em português. [validators][doc-extraction-api]
- **Lacunas:** pricing, latência, limite de páginas, formatos de arquivo aceitos (PDF multipágina? JPEG?) e os modelos por baixo **não constam** em nenhuma das páginas acessíveis. [todas]

---

## O que a API faz exatamente

A API "transforma documentos e imagens em informação valiosa", identificando e extraindo dados conforme **layouts customizados** criados pelo usuário. [doc-extraction-api]

**Endpoint / método:**
- `POST https://api.tech4.ai/document/extract/` (endpoint único documentado). [doc-extraction-api]

**Autenticação:**
- Header de API key. A página do endpoint usa o header **`x-client-key`** (inferido do conteúdo do exemplo; a página de api-keys não nomeia o header explicitamente). A chave é gerada no admin panel (`https://admin.tech4.ai/login` → Settings → API Keys → Create New Key, escolhendo Module = *Vision* e Service = *Data Extraction*) e **é exibida apenas uma vez**. [doc-extraction-api][api-keys]

**Como o cliente define os campos a extrair (layout):**
- Um **layout** é "um mapa detalhado que você fornece a um modelo de IA, guiando-o a encontrar exatamente a informação que você precisa" e a organizar de forma estruturada. [layout-config]
- Construído num **visual builder**, campo a campo: (1) **nome** do campo, (2) **tipo de dado** (Date, Text, Number, ...), (3) **descrição em linguagem natural** — detalhada e informativa sobre localização, formatação e palavras-chave (ex.: "Data no canto superior direito, formato DD/MM/YYYY"). Boa prática: descrever *o que* a IA deve encontrar, não *como*. [layout-config]
- **Não** se envia JSON Schema na request — o cliente apenas referencia o layout via `layout_id`. O refinamento é **iterativo** num *playground* (upload de documentos de amostra → ajuste das descrições). [layout-config]

**Validators (qualidade / pós-processamento determinístico):**
- Ferramentas de QA que verificam se os dados extraídos são válidos. A página de layout afirma que **retornam NULL** para dados inválidos em vez de um valor incorreto; a página de cada validator descreve apenas a checagem (ex.: CPF = 11 dígitos + dígitos verificadores pelo algoritmo oficial) e **não** reafirma o comportamento NULL nem como anexá-los a um campo. [layout-config][validators][validators/cpf]
- Validators disponíveis: **Linha Digitável de Boleto**, **CPF**, **CNPJ**, **UF**. [validators]

---

## Schema de entrada / saída

### Entrada (request body) [doc-extraction-api]
| Parâmetro | Onde | Descrição |
|-----------|------|-----------|
| `x-client-key` | header | Chave de API. |
| `file_url` | body | "A URL do arquivo (imagem ou documento) que você deseja analisar". Deve ser acessível pela API (não há upload de binário documentado — é por URL). |
| `layout_id` | body | "O ID do layout que você criou para extrair os dados". Obtido na tela de gestão de layouts. |

> **Inferido:** a request usa URL de arquivo (não multipart/binário). Formatos exatos (PDF/JPEG/PNG, multipágina) **não constam** na doc acessível.

### Saída (response) [doc-extraction-api]
```json
{
  "status": "ok",            // "ok" | "partial" | "error"
  "extracted_data": {
    "categoria_habilitacao": "AB",
    "data_validade": "2034-07-11",
    "data_1a_habilitacao": "2004-03-26"
  }
}
```
- **`status`** (nível topo, aplica-se à extração inteira):
  - `ok` — todos os campos extraídos;
  - `partial` — alguns campos não extraídos;
  - `error` — nenhum campo extraído.
- **`extracted_data`** — objeto chave→valor; as **chaves são os nomes dos campos do layout**. Os valores são "crus" (string), **sem status por campo** — só existe o `status` global. [doc-extraction-api]
- **Códigos HTTP:** 200 (ok/partial/error), 400 (request malformada / file_url inválida), 401 (key inválida/ausente), 404 (`layout_id` não encontrado). [doc-extraction-api]

### Tipos de documento suportados / PT-BR
- **Não há catálogo explícito** de tipos de documento — qualquer documento é suportável desde que o usuário crie o layout correspondente (extração *layout-driven*, document-agnostic). [layout-config]
- **Evidência forte de foco brasileiro:** o exemplo oficial de saída é uma **CNH** (campos de habilitação) e os validators nativos são CPF/CNPJ/UF/boleto. Cobre diretamente **Documento 1 (CNH)** e **Documento 2 (fatura/conta de energia → linha digitável, CNPJ)** do desafio. Documentação em português. [doc-extraction-api][validators]
- **Documento 3 (paper Claude 3, multipágina com gráficos):** **nenhuma evidência** de suporte a PDF multipágina, charts ou interpretação de imagens/figuras — exatamente a limitação citada no enunciado do desafio. [não consta na doc]

---

## Implicações para a recomendação (compatibilidade)

A abordagem alternativa do dossiê (**single-pass VLM + structured output**, ver notas 02/03) precisa preservar **o contrato de saída**, não a implementação interna:

1. **Manter o envelope de resposta** `{"status": "...", "extracted_data": {...}}` com os 3 valores de status (`ok`/`partial`/`error`) e as **mesmas chaves de campo** que o layout atual produz. Um VLM com *structured output* (JSON Schema / function calling) consegue emitir esse mesmo objeto numa **única chamada**, derivando o JSON Schema a partir da definição do layout (nome + tipo de campo) — eliminando a 2ª etapa de "formatação". [doc-extraction-api]
2. **Reaproveitar `layout` como fonte do schema:** nome + tipo + descrição em linguagem natural de cada campo mapeiam 1:1 para `properties` de um JSON Schema (tipo → `type`/`format`; descrição → `description` do campo, que vira instrução do VLM). Mantém a UX atual do *visual builder* e o `layout_id` na API. [layout-config]
3. **Preservar os validators como pós-processamento determinístico** (CPF/CNPJ/UF/linha digitável → NULL se inválido). Eles são independentes do modelo e devem rodar **após** o VLM, garantindo paridade de qualidade e a semântica de NULL. Isso também ajuda a derivar `status` (`partial` quando algum campo vira NULL). [layout-config][validators]
4. **Compatibilidade de transporte:** manter `POST /document/extract/`, `x-client-key`, `file_url` + `layout_id` e os códigos HTTP (400/401/404) — a substituição fica **drop-in** para o cliente; só muda o motor interno (2 LLMs → 1 VLM single-pass). [doc-extraction-api]
5. **Ganho esperado** (alinhado ao desafio): elimina a chamada de formatação (↓ latência/custo) e o *structured output* nativo cobre layouts complexos/multipágina e interpretação de imagem/charts — pontos onde o pipeline atual é fraco. *Inferência do dossiê, não da doc.*

---

## Fontes (URLs)

- Endpoint, request/response, status, exemplo CNH, HTTP codes:
  https://docs.tech4.ai/vision/doc-extraction-api
- Layout: definição de campos, linguagem natural, validators retornam NULL, playground iterativo:
  https://docs.tech4.ai/vision/layout-config
- Lista de validators (CPF, CNPJ, UF, Linha Digitável):
  https://docs.tech4.ai/vision/validators
- Detalhe do validator CPF (11 dígitos + dígitos verificadores):
  https://docs.tech4.ai/vision/validators/cpf
- Autenticação / criação de API key (admin panel):
  https://docs.tech4.ai/getting-started/api-keys
- Visão geral do produto / módulos (Agents, Knowledge, Vision):
  https://docs.tech4.ai/
- Validators adicionais referenciados (não fetchados individualmente): `/vision/validators/digital-bill-line`, `/vision/validators/cnpj`, `/vision/validators/uf`

---

## Lacunas (não documentado / não acessível)

- **Pricing** — não consta em nenhuma página acessível.
- **Latência** — sem números; sem confirmação do nº de chamadas LLM internas.
- **Modelos por baixo** — não nomeados (apenas "um modelo de IA").
- **Limite de páginas / suporte a PDF multipágina** — não consta.
- **Formatos de arquivo aceitos** (JPEG/PNG/PDF) — não listados explicitamente; só "imagem ou documento" via URL.
- **Comportamento NULL dos validators** — afirmado na página de layout, mas **não reafirmado** nas páginas individuais dos validators.
- **Header `x-client-key`** — inferido do exemplo do endpoint; a página de api-keys não nomeia o header.
- **Processo de 2 etapas** — apenas **indício** (interpretação via layout + formatação em JSON); a doc **não confirma** "duas chamadas LLM" como descrito no desafio.
- `https://docs.tech4.ai/vision/intro` retornou **HTTP 404** — não existe; as páginas reais do módulo Vision são `layout-config`, `doc-extraction-api` e `validators`.
