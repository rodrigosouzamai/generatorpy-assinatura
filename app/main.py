from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io
from fastapi.middleware.cors import CORSMiddleware  # Importe o CORS

# --- CORREÇÃO IMPORTANTE ---
# Importe os ficheiros usando o caminho da sua estrutura de pastas
try:
    from app.utils.png_generator import generate_signature_png
    from app.utils.trilha_generator import generate_trilha_signature
    print("INFO: Geradores importados com sucesso.")
except ImportError as e:
    print("!!!!!! ERRO FATAL AO IMPORTAR GERADORES !!!!!!")
    print(f"Erro: {e}")
    print("!!!!!! Verifique se 'png_generator.py' e 'trilha_generator.py' existem na pasta 'app/utils/'. !!!!!!")
    # Este 'raise' irá "derrubar" o servidor se os ficheiros não forem encontrados
    raise e

app = FastAPI()

# 2. Aplique o CORS logo após declarar o 'app'
app.add_middleware(
    CORSMiddleware,
    # Permita o seu site específico
    allow_origins=["https://octopushelpdesk.com.br", "http://localhost:8000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SignatureRequest(BaseModel):
    name: str
    title: str
    phone: str
    image_url: str

class TrilhaRequest(SignatureRequest):
    qrCodeData: str

@app.get("/") # Adiciona uma rota "health check"
def read_root():
    print("INFO: Health check / solicitado.")
    return {"status": "ok", "message": "Gerador de Assinaturas no ar!"}

@app.post("/generate-signature")
async def generate_signature(req: SignatureRequest):
    try:
        print("INFO: A chamar /generate-signature...")
        image_bytes = generate_signature_png(req)
        return StreamingResponse(io.BytesIO(image_bytes), media_type="image/png")
    except Exception as e:
        print(f"!!!!!! ERRO em /generate-signature: {e} !!!!!!")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-trilha-signature")
async def generate_trilha_signature(req: TrilhaRequest):
    try:
        print("INFO: A chamar /generate-trilha-signature...")
        image_bytes = generate_trilha_signature(req)
        return StreamingResponse(io.BytesIO(image_bytes), media_type="image/png")
    except Exception as e:
        print(f"!!!!!! ERRO em /generate-trilha-signature: {e} !!!!!!")
        raise HTTPException(status_code=500, detail=str(e))

print("INFO: Aplicação FastAPI configurada e pronta.")

