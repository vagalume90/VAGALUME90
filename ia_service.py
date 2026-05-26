import os
import io
from pydantic import BaseModel, Field
from typing import List, Dict
from google import genai
from google.genai import types
from PIL import Image

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


# --- CÓDIGO DO CRIADOR DE IMAGENS COM O OLHO NA PASTA ADM ---
def gerar_imagem_ia(descricao_imagem: str) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"erro": "Falta a GEMINI_API_KEY no servidor."}
        
    try:
        client = genai.Client(api_key=api_key)
        
        # 1. IA gera a imagem de fundo usando o modelo correto da Google
        resultado = client.models.generate_images(
            model='imagen-3.0-generate-001',
            prompt=descricao_imagem,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="1:1"
            )
        )
        
        imagem_generada = resultado.generated_images[0]
        img_fundo = Image.open(io.BytesIO(imagem_generada.image.image_bytes))
        
        # 2. PROCESSO DA MARCA DE ÁGUA LOCAL (PASTA ADM)
        nome_arquivo_logo = "adm/logo_olho.jpg"
        
        if os.path.exists(nome_arquivo_logo):
            img_logo = Image.open(nome_arquivo_logo)
            
            # Ajusta o tamanho do olho na imagem final
            novo_tamanho = 150
            proporcao = novo_tamanho / float(img_logo.size[0])
            altura_nova = int((float(img_logo.size[1]) * float(proporcao)))
            img_logo = img_logo.resize((novo_tamanho, altura_nova), Image.Resampling.LANCZOS)
            
            # Posiciona no canto inferior direito
            posicao_x = img_fundo.size[0] - novo_tamanho - 20
            posicao_y = img_fundo.size[1] - altura_nova - 20
            
            img_fundo.paste(img_logo, (posicao_x, posicao_y))
            
        # 3. Guarda a imagem final combinada na memória
        buffer_final = io.BytesIO()
        img_fundo.save(buffer_final, format="JPEG", quality=90)
        
        # 4. Transforma em Base64 para exibir no teu site
        import base64
        imagem_base64 = base64.b64encode(buffer_final.getvalue()).decode('utf-8')
        
        return {
            "motor_ia": "Google Imagen 3 + Olho Futurista VAGALUME90",
            "status": "Sucesso",
            "imagem_resultado": f"data:image/jpeg;base64,{imagem_base64}"
        }
        
    except Exception as e:
        return {"erro": "Erro ao gerar imagem", "detalhe": str(e)}
