import base64
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import traceback # Para logs de erro detalhados

# --- CORREÇÃO: Função para carregar uma fonte de forma segura ---
def get_font(url, size):
    """Faz o download de um ficheiro de fonte .ttf e carrega-o."""
    try:
        # Tenta obter a fonte a partir do URL
        r = requests.get(url, allow_redirects=True)
        r.raise_for_status() # Verifica se o download falhou
        font_file = io.BytesIO(r.content)
        return ImageFont.truetype(font_file, size)
    except Exception as e:
        print(f"ERRO CRÍTICO: Não foi possível carregar a fonte de {url}. Usando fonte padrão. Erro: {e}")
        # Se o download falhar, volta para a fonte padrão como última tentativa
        return ImageFont.load_default()

def generate_trilha_signature(data):
    try:
        # --- URLs das Fontes ---
        # Estamos a usar a "Inter", a mesma fonte do seu site
        font_bold_url = "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Bold.ttf"
        font_regular_url = "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Regular.ttf"

        # --- Carregar Fontes de forma segura ---
        font_name = get_font(font_bold_url, 18)
        font_title = get_font(font_regular_url, 14)
        font_phone = get_font(font_bold_url, 14)

        # --- Processamento do GIF (lê apenas o primeiro frame) ---
        response_logo = requests.get(data.image_url, stream=True)
        logo = Image.open(response_logo.raw).convert("RGBA")
        
        # O layout no HTML (trilha-signature-preview) tem 450x120
        # O fundo é #C3AEF4
        base_img = Image.new("RGBA", (450, 120), "#C3AEF4")
        
        # O logo no HTML é 140px de largura, vamos redimensionar
        logo_width = 140
        logo_height = int((logo_width / float(logo.size[0])) * float(logo.size[1]))
        logo_resized = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        
        # Cola o logo (centralizado na célula de 140px)
        base_img.paste(logo_resized, (5, (120 - logo_height) // 2), logo_resized)

        # --- Processamento do QR Code ---
        qr_data = data.qrCodeData.split(",")[1]
        qr_img_raw = Image.open(io.BytesIO(base64.b64decode(qr_data))).convert("RGBA")
        
        # O QR no HTML tem 110x110 (incluindo padding)
        qr_img_resized = qr_img_raw.resize((100, 100), Image.Resampling.LANCZOS)
        
        # Cria um fundo branco para o QR code
        qr_bg = Image.new("RGBA", (110, 110), "white")
        qr_bg.paste(qr_img_resized, (5, 5)) # Adiciona 5px de padding

        # Cola o QR code (com fundo) na imagem base
        base_img.paste(qr_bg, (450 - 110 - 5, (120 - 110) // 2)) # 5px da borda direita

        # --- Adiciona Texto ---
        draw = ImageDraw.Draw(base_img)
        text_color = "#0E2923" # Cor do texto no HTML
        x_offset = 150 # Posição de início do texto (depois do logo)
        
        # Nome
        draw.text((x_offset, 30), data.name, fill=text_color, font=font_name)
        # Cargo
        draw.text((x_offset, 55), data.title, fill=text_color, font=font_title)
        # Telefone
        draw.text((x_offset, 75), data.phone, fill=text_color, font=font_phone)

        # --- Salva a imagem ---
        # O frontend está à espera de um GIF, mas o seu código gera um PNG.
        # Isto não é o ideal, mas o frontend (gerador_assinatura.html) está
        # programado para aceitar um PNG, por isso vamos manter.
        output = io.BytesIO()
        base_img.save(output, format="PNG")
        print("INFO: Imagem Trilha gerada com sucesso.")
        return output.getvalue()

    except Exception as e:
        # --- LOG DE ERRO ---
        # Se algo falhar, isto irá imprimir o erro completo nos logs do Railway
        print("!!!!!! ERRO AO GERAR ASSINATURA TRILHA !!!!!!")
        print(traceback.format_exc())
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # Levanta o erro para o FastAPI o reportar
        raise e
