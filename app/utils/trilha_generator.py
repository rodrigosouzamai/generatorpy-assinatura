import base64
from PIL import Image, ImageDraw, ImageFont
import io
import requests

def generate_trilha_signature(data):
    response = requests.get(data.image_url, stream=True)
    logo = Image.open(response.raw).convert("RGBA").resize((215, 215))
    base_img = Image.new("RGBA", (635, 215), (255, 255, 255, 0))
    base_img.paste(logo, (0, 0), logo)

    qr_data = data.qrCodeData.split(",")[1]
    qr_img = Image.open(io.BytesIO(base64.b64decode(qr_data))).convert("RGBA").resize((100, 100))
    base_img.paste(qr_img, (520, 100), qr_img)

    draw = ImageDraw.Draw(base_img)
    font = ImageFont.load_default()
    x_offset = 235
    draw.text((x_offset, 50), data.name, fill="black", font=font)
    draw.text((x_offset, 90), data.title, fill="black", font=font)
    draw.text((x_offset, 130), data.phone, fill="black", font=font)

    output = io.BytesIO()
    base_img.save(output, format="PNG")
    return output.getvalue()
