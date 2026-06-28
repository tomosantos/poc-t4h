import base64
from extractor.encoding import bloco_documento, eh_pdf

def test_imagem_vira_image_url_base64(tmp_path):
    p = tmp_path / "x.jpg"
    p.write_bytes(b"\xff\xd8\xff\xe0teste")
    bloco = bloco_documento(str(p))
    assert bloco["type"] == "image_url"
    assert bloco["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert not eh_pdf(str(p))

def test_pdf_vira_file_block(tmp_path):
    p = tmp_path / "x.pdf"
    p.write_bytes(b"%PDF-1.4 teste")
    bloco = bloco_documento(str(p))
    assert bloco["type"] == "file"
    assert bloco["file"]["filename"] == "x.pdf"
    assert bloco["file"]["file_data"].startswith("data:application/pdf;base64,")
    assert eh_pdf(str(p))
