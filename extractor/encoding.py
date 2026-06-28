"""Converte arquivos locais em blocos de conteúdo para a API."""
import base64
import os

_MIME_IMG = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
             ".png": "image/png", ".webp": "image/webp"}


def eh_pdf(caminho: str) -> bool:
    return os.path.splitext(caminho)[1].lower() == ".pdf"


def bloco_documento(caminho: str) -> dict:
    with open(caminho, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    if eh_pdf(caminho):
        return {
            "type": "file",
            "file": {
                "filename": os.path.basename(caminho),
                "file_data": f"data:application/pdf;base64,{b64}",
            },
        }
    ext = os.path.splitext(caminho)[1].lower()
    mime = _MIME_IMG.get(ext, "image/jpeg")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
