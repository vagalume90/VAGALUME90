import os
import io
from pydantic import BaseModel, Field
from typing import List, Dict
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont  # <-- Biblioteca para desenhar a marca de água

# --- (Mantém as estruturas de texto e a função gerar_conteudo_ia iguais acima) ---

def gerar_imagem_ia(descricao_imagem: str) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"erro": "Falta a GEMINI_API_KEY no servidor."}
        
    try:
        client = genai.Client(api_key=api_key)
        
        # 1. Gera a imagem original no Imagen 3
        resultado = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=descricao_imagem,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="1:1"
            )
        )
        
        imagem_gerada = resultado.generated_images[0]
        
        # 2. PROCESSO DA MARCA DE ÁGUA: Abre os bytes da imagem com o Pillow
        img = Image.open(io.BytesIO(imagem_gerada.image.image_bytes))
        
        # Criamos uma camada transparente para desenhar o texto
        camada_desenho = ImageDraw.Draw(img)
        
        # Texto que vai ficar na imagem
        texto_marca = "VAGALUME90"
        
        # Configuramos uma fonte padrão do sistema (Tamanho 40)
        try:
            fonte = ImageFont.load_default(size=40)
        except:
            fonte = ImageFont.load_default() # Fallback caso o sistema não mude o tamanho
            
        # Posição: Canto inferior direito (Imagens do Imagen são 1024x1024 por padrão)
        # Colocamos na posição X=750 e Y=950 para ficar no cantinho de baixo
        posicao = (750, 950)
        
        # Desenha o texto: Cor branca com um contorno preto leve para dar leitura em qualquer fundo
        camada_desenho.text(posicao, texto_marca, fill=(255, 255, 255), font=fonte, stroke_width=2, stroke_fill=(0, 0, 0))
        
        # 3. Salva a imagem modificada de volta em memória (Bytes)
        buffer_final = io.BytesIO()
        img.save(buffer_final, format="JPEG", quality=90)
        
        # 4. Transforma em Base64 para enviar para o teu site
        import base64
        imagem_base64 = base64.b64encode(buffer_final.getvalue()).decode('utf-8')
        
        return {
            "motor_ia": "Google Imagen 3 + Proteção VAGALUME90",
            "status": "Sucesso",
            "imagem_resultado": f"data:image/jpeg;base64,{imagem_base64}"
        }
        
    except Exception as e:
        return {"erro": "Erro ao gerar imagem com marca de água", "detalhe": str(e)}
