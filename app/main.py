from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io
from app.utils.png_generator import generate_signature_png
from app.utils.gif_generator import generate_signature_gif
from app.utils.trilha_generator import generate_trilha_signature

app = FastAPI()

class SignatureRequest(BaseModel):
    name: str
    title: str
    phone: str
    image_url: str

class TrilhaRequest(SignatureRequest):
    qrCodeData: str

@app.post("/generate-signature")
async def generate_signature(req: SignatureRequest):
    try:
        image_bytes = generate_signature_png(req)
        return StreamingResponse(io.BytesIO(image_bytes), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-gif-signature")
async def generate_gif_signature(req: SignatureRequest):
    try:
        gif_bytes = generate_signature_gif(req)
        return StreamingResponse(io.BytesIO(gif_bytes), media_type="image/gif")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-trilha-signature")
async def generate_trilha_signature(req: TrilhaRequest):
    try:
        image_bytes = generate_trilha_signature(req)
        return StreamingResponse(io.BytesIO(image_bytes), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
