import os
import io
import urllib.request  # Biblioteca nativa para ler o link do teu logo
from pydantic import BaseModel, Field
from typing import List, Dict
from google import genai
from google.genai import types
from PIL import Image  # Biblioteca para processamento de imagem

# --- CONFIGURAÇÕES DO GERADOR UNIVERSAL DE TEXTO ---
class PerguntaSimulado(BaseModel):
    pergunta: str = Field(description="A pergunta ou caso prático sobre o tema")
    opcoes: Dict[str, str] = Field(description="Dicionário com as opções A, B, C e D")
    resposta_correta: str = Field(description="Apenas a letra da opção correta (A, B, C ou D)")
    explicacao: str = Field(description="Breve explicação didática de porquê esta opção é a correta")

class ConteudoUniversal(BaseModel):
    tema_analisado: str = Field(description="O tema purificado pela IA")
    area_conhecimento: str = Field(description="A categoria do tema (Ex: Tecnologia, Direito, Gestão, Saúde)")
    resumo_teorico: str = Field(description="O núcleo do conhecimento: explicação moderna, profunda e direto ao ponto")
    simulado: List[PerguntaSimulado] = Field(description="Lista com 3 a 5 questões de alto nível para fixar o conhecimento")
    plano_acao_pratico: str = Field(description="Como o utilizador aplica este conhecimento na prática ou no mercado atual")

def gerar_conteudo_ia(tema: str) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"motor_ia": "Modo de Demonstracao", "conteudo": {"tema_analisado": tema, "resumo_teorico": "Sem chave API."}}
    
    try:
        client = genai.Client(api_key=api_key)
        prompt_sistema = (
            "Tu és o Tutor Universal do VAGALUME90. Recebe QUALQUER tema e desconstroi-o "
            "de forma brilhante, moderna, didática e extremamente prática para África."
        )
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Gera o ecossistema completo de aprendizagem para o tema: {tema}",
            config=types.GenerateContentConfig(
                system_instruction=prompt_sistema,
                response_mime_type="application/json",
                response_schema=ConteudoUniversal,
                temperature=0.3
            ),
        )
        import json
        return {"motor_ia": "Google Gemini 2.5 Flash (Real)", "conteudo": json.loads(response.text)}
    except Exception as e:
        return {"motor_ia": "Erro", "detalhe_erro": str(e)}


# --- CÓDIGO CORRIGIDO: CRIADOR DE IMAGENS COM CARIMBO DO LOGO ---
def gerar_imagem_ia(descricao_imagem: str) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    # Pegamos o link do teu logo que vais guardar no Render
    url_logo = os.environ.get("URL_LOGO_VAGALUME")
    
    if not api_key:
        return {"erro": "Falta a GEMINI_API_KEY no servidor."}
        
    try:
        client = genai.Client(api_key=api_key)
        
        # 1. IA gera a imagem de fundo (1024x1024 pixels)
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
        img_fundo = Image.open(io.BytesIO(imagem_gerada.image.image_bytes))
        
        # 2. SE O LINK DO LOGO EXISTIR, ELE COLA O LOGO EM CIMA DA IMAGEM
        if url_logo:
            try:
                # Faz o download da imagem do teu logo a partir do link
                req = urllib.request.Request(url_logo, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    logo_bytes = response.read()
                
                img_logo = Image.open(io.BytesIO(logo_bytes))
                
                # CORTE APENAS DO OLHO (Sem as letras VG90 de baixo)
                # O teu logo original é quadrado. Vamos cortar apenas a metade de cima onde está o olho.
                largura_logo, altura_logo = img_logo.size
                caixa_corte = (0, 0, largura_logo, int(altura_logo * 0.58)) # Pega do topo até 58% da altura (só o olho)
                so_o_olho = img_logo.crop(caixa_corte)
                
                # Redimensiona o olho para ficar com um tamanho bonito no canto da imagem (Ex: 140 pixels de largura)
                novo_tamanho = 140
                proporcao = novo_tamanho / float(so_o_olho.size[0])
                altura_nova = int((float(so_o_olho.size[1]) * float(proporcao)))
                so_o_olho = so_o_olho.resize((novo_tamanho, altura_nova), Image.Resampling.LANCZOS)
                
                # Posição onde o olho vai ser colado (Canto inferior direito)
                # X = 1024 - 140 - 20 (margem) = 864 | Y = 1024 - altura - 20 (margem)
                posicao_x = img_fundo.size[0] - novo_tamanho - 20
                posicao_y = img_fundo.size[1] - altura_nova - 20
                
                # Se o teu logo tiver transparência (PNG), colamos usando ele mesmo como máscara
                if img_logo.mode == 'RGBA' or 'transparency' in img_logo.info:
                    # Converte o pedaço cortado para RGBA para manter a transparência perfeita
                    so_o_olho = so_o_olho.convert("RGBA")
                    img_fundo.paste(so_o_olho, (posicao_x, posicao_y), so_o_olho)
                else:
                    # Se for fundo branco, cola normal
                    img_fundo.paste(so_o_olho, (posicao_x, posicao_y))
            except Exception as erro_logo:
                # Se falhar o download do logo por algum motivo, o código continua para não travar o utilizador
                pass

        # 3. Guarda a imagem final com o carimbo do olho na memória
        buffer_final = io.BytesIO()
        img_fundo.save(buffer_final, format="JPEG", quality=90)
        
        # 4. Converte para Base64 para o teu site exibir
        import base64
        imagem_base64 = base64.b64encode(buffer_final.getvalue()).decode('utf-8')
        
        return {
            "motor_ia": "Google Imagen 3 + Olho VAGALUME90",
            "status": "Sucesso",
            "imagem_resultado": f"data:image/jpeg;base64,{imagem_base64}"
        }
        
    except Exception as e:
        return {"erro": "Erro ao gerar imagem", "detalhe": str(e)}
