# extractor/models.py
"""Modelos de dados da POC."""
from typing import Literal, Optional
from pydantic import BaseModel


class FieldSpec(BaseModel):
    nome: str
    tipo: Literal["text", "number", "date"]
    descricao: str
    validador: Optional[Literal["cpf", "cnpj"]] = None


class Layout(BaseModel):
    layout_id: str
    descricao: str
    campos: list[FieldSpec]
