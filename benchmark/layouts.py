"""Layouts dos 3 documentos de teste e ground truth da CNH."""
from extractor.models import FieldSpec, Layout

LAYOUT_CNH = Layout(layout_id="cnh", descricao="CNH brasileira", campos=[
    FieldSpec(nome="nome", tipo="text", descricao="Nome completo do condutor"),
    FieldSpec(nome="cpf", tipo="text", descricao="CPF do condutor", validador="cpf"),
    FieldSpec(nome="data_nascimento", tipo="date", descricao="Data de nascimento"),
    FieldSpec(nome="data_emissao", tipo="date", descricao="Data de emissão do documento"),
    FieldSpec(nome="filiacao_pai", tipo="text", descricao="Nome do pai (filiação)"),
    FieldSpec(nome="filiacao_mae", tipo="text", descricao="Nome da mãe (filiação)"),
])

LAYOUT_FATURA = Layout(layout_id="fatura", descricao="Fatura de energia CELPE", campos=[
    FieldSpec(nome="titular", tipo="text", descricao="Nome do titular da conta"),
    FieldSpec(nome="cnpj_distribuidora", tipo="text",
              descricao="CNPJ da distribuidora", validador="cnpj"),
    FieldSpec(nome="mes_referencia", tipo="text", descricao="Mês/ano de referência"),
    FieldSpec(nome="vencimento", tipo="date", descricao="Data de vencimento"),
    FieldSpec(nome="valor_total", tipo="number", descricao="Valor total a pagar em reais"),
    FieldSpec(nome="consumo_kwh", tipo="number", descricao="Consumo do mês em kWh"),
    FieldSpec(nome="numero_instalacao", tipo="text", descricao="Número da instalação/cliente"),
])

LAYOUT_PAPER = Layout(layout_id="paper", descricao="Paper acadêmico (Claude 3)", campos=[
    FieldSpec(nome="titulo", tipo="text", descricao="Título do artigo"),
    FieldSpec(nome="resumo_markdown", tipo="text",
              descricao="Conteúdo principal em Markdown preservando tabelas; "
                        "descreva gráficos/figuras em texto"),
])

DOCUMENTOS = {
    "cnh": {"layout": LAYOUT_CNH, "arquivo": "data/Documento 1.jpeg"},
    "fatura": {"layout": LAYOUT_FATURA, "arquivo": "data/Documento 2.jpg"},
    "paper": {"layout": LAYOUT_PAPER, "arquivo": "data/Documento 3.pdf"},
}

# Rótulos manuais — preenchidos inspecionando data/Documento 1.jpeg.
# Servem de calibração do juiz LLM no benchmark.
GROUND_TRUTH_CNH = {
    "nome": "LINCE DA SILVA",
    "cpf": "091.340.611-75",
    "data_nascimento": "06/08/1961",
    "data_emissao": "22/10/2013",
    "filiacao_pai": "Pai José da Silva",
    "filiacao_mae": "Mãe Maria da Silva",
}
