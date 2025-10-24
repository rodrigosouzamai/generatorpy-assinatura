from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io
from app.utils.png_generator import generate_signature_png
from app.utils.trilha_generator import generate_trilha_signature
from fastapi.middleware.cors import CORSMiddleware  # Importe o CORS

# --- CORREÇÃO AQUI ---
# 1. Declare o 'app' APENAS UMA VEZ
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

@app.post("/generate-signature") # <-- O frontend estava chamando o nome errado
async def generate_signature(req: SignatureRequest):
    try:
        # ATENÇÃO: Seu backend está gerando PNG. 
        # Se você quer GIF, a função 'generate_signature_png' precisa gerar um GIF.
        image_bytes = generate_signature_png(req)
        return StreamingResponse(io.BytesIO(image_bytes), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-trilha-signature")
async def generate_trilha_signature(req: TrilhaRequest):
    try:
        # ATENÇÃO: Seu backend está gerando PNG. 
        # Se você quer GIF, a função 'generate_trilha_signature' precisa gerar um GIF.
        image_bytes = generate_trilha_signature(req)
        return StreamingResponse(io.BytesIO(image_bytes), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
