from extractor.validators import so_digitos, cpf_valido, cnpj_valido

def test_so_digitos():
    assert so_digitos("123.456.789-09") == "12345678909"

def test_cpf_valido_aceita_valido():
    assert cpf_valido("123.456.789-09") is True

def test_cpf_rejeita_digito_verificador_errado():
    assert cpf_valido("123.456.789-00") is False

def test_cpf_rejeita_todos_iguais_e_tamanho_errado():
    assert cpf_valido("111.111.111-11") is False
    assert cpf_valido("123") is False

def test_cnpj_valido_e_invalido():
    assert cnpj_valido("11.222.333/0001-81") is True
    assert cnpj_valido("11.222.333/0001-80") is False
