"""Converte arquivos locais em blocos de conteúdo para a API."""
import base64
import os

_MIME_IMG = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
             ".png": "image/png", ".webp": "image/webp"}


def eh_pdf(caminho: str) -> bool:
    return os.path.splitext(caminho)[1].lower() == ".pdf"


def _detectar_mime_por_magic(dados: bytes) -> str | None:
    """Detecta o MIME type real pelo conteúdo do arquivo (magic bytes).

    Suporta JPEG, PNG e WebP. Retorna None se não reconhecido.
    """
    if dados[:2] == b"\xff\xd8":
        return "image/jpeg"
    if dados[:4] == b"\x89PNG":
        return "image/png"
    # WebP: primeiros 4 bytes == 'RIFF' e bytes 8-12 == 'WEBP'
    if dados[:4] == b"RIFF" and dados[8:12] == b"WEBP":
        return "image/webp"
    return None


def bloco_documento(caminho: str) -> dict:
    with open(caminho, "rb") as f:
        raw = f.read()
    b64 = base64.b64encode(raw).decode("ascii")
    if eh_pdf(caminho):
        return {
            "type": "file",
            "file": {
                "filename": os.path.basename(caminho),
                "file_data": f"data:application/pdf;base64,{b64}",
            },
        }
    # Detecta MIME real pelos magic bytes; cai de volta na extensão se desconhecido
    mime = _detectar_mime_por_magic(raw)
    if mime is None:
        ext = os.path.splitext(caminho)[1].lower()
        mime = _MIME_IMG.get(ext, "image/jpeg")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
