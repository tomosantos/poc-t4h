"""Métrica determinística: compara extração com o ground truth, campo a campo.

Complementa o LLM-as-judge (que se mostrou não-confiável em documentos de baixa
resolução — ver notes/08). Normalização justa: casefold, sem acento, sem
pontuação; CPF e datas comparados só por dígitos; filiação ignora prefixo
pai/mãe. Reportar AS DUAS métricas (determinística e juiz) é decisão de método.
"""
import unicodedata


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def _so_digitos(s: str) -> str:
    return "".join(c for c in s if c.isdigit())


def normalizar(campo: str, valor) -> str:
    if valor is None:
        return ""
    v = _sem_acento(str(valor)).casefold().strip()
    if campo == "cpf" or campo.startswith("data"):
        return _so_digitos(v)
    if campo.startswith("filiacao"):
        for pref in ("pai ", "mae "):
            if v.startswith(pref):
                v = v[len(pref):]
    return "".join(ch for ch in v if ch.isalnum() or ch == " ").strip()


def acuracia_deterministica(extracted: dict, ground_truth: dict) -> tuple[float, dict]:
    """Retorna (fração 0..1 de campos corretos, dict campo->bool)."""
    por_campo = {}
    for campo, esperado in ground_truth.items():
        por_campo[campo] = normalizar(campo, extracted.get(campo)) == normalizar(campo, esperado)
    acerto = sum(por_campo.values()) / len(ground_truth) if ground_truth else 0.0
    return acerto, por_campo
