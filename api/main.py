"""API de extração espelhando o contrato Tech4.ai: POST /extract -> {status, extracted_data}."""
import os
import tempfile
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends

from benchmark.layouts import DOCUMENTOS
from extractor.client import OpenRouterClient
from extractor.pipeline import extrair

load_dotenv()
app = FastAPI(title="POC Extração de Documentos", version="0.1.0")
MODELO_PADRAO = os.getenv("MODELO_PADRAO", "google/gemini-2.5-flash-lite")


def get_client() -> OpenRouterClient:
    return OpenRouterClient()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/layouts")
def layouts():
    return {"layouts": list(DOCUMENTOS.keys())}


@app.post("/extract")
async def extract(layout_id: str = Form(...), file: UploadFile = File(...),
                  client=Depends(get_client)):
    if layout_id not in DOCUMENTOS:
        raise HTTPException(400, f"layout_id desconhecido: {layout_id}")
    layout = DOCUMENTOS[layout_id]["layout"]
    sufixo = os.path.splitext(file.filename or "")[1] or ".bin"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=sufixo)
    caminho = tmp.name
    try:
        tmp.write(await file.read())
        tmp.close()
        envelope, _ = extrair(caminho, layout, MODELO_PADRAO, client, modo="single")
    finally:
        tmp.close()  # no-op se já fechado
        os.unlink(caminho)
    return envelope
