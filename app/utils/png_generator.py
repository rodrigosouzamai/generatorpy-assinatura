import requests
from PIL import Image, ImageDraw, ImageFont
import io

def generate_signature_png(data):
    response = requests.get(data.image_url, stream=True)
    bg = Image.new("RGBA", (635, 215), (255, 255, 255, 0))
    logo = Image.open(response.raw).convert("RGBA").resize((215, 215))
    bg.paste(logo, (0, 0), logo)

    draw = ImageDraw.Draw(bg)
    font = ImageFont.load_default()
    x_offset = 235
    draw.text((x_offset, 50), data.name, fill="black", font=font)
    draw.text((x_offset, 90), data.title, fill="black", font=font)
    draw.text((x_offset, 130), data.phone, fill="black", font=font)

    output = io.BytesIO()
    bg.save(output, format="PNG")
    return output.getvalue()
