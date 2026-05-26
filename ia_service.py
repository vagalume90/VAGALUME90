import os
from pydantic import BaseModel, Field
from typing import List, Dict
from google import genai
from google.genai import types

# --- ESTRUTURA DO GERADOR UNIVERSAL DE TEXTO ---
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

# --- NOVA FUNÇÃO: CRIADOR DE IMAGENS DO GEMINI (IMAGEN 3) ---
def gerar_imagem_ia(descricao_imagem: str) -> dict:
    """
    Recebe um texto/prompt e gera uma imagem futurista de alta qualidade usando o Imagen 3.
    Devolve o link temporário da imagem ou a imagem em formato texto (Base64).
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"erro": "Falta a GEMINI_API_KEY no servidor."}
        
    try:
        client = genai.Client(api_key=api_key)
        
        # Chamada ao modelo Imagen 3 da Google
        resultado = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=descricao_imagem,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                output_mime_type="image/jpeg",
                aspect_ratio="1:1" # Imagem quadrada ideal para apps/redes sociais
            )
        )
        
        # Pegamos a primeira imagem gerada
        imagem_gerada = resultado.generated_images[0]
        
        # Convertemos a imagem para um formato que o teu site consegue exibir diretamente
        import base64
        imagem_base64 = base64.b64encode(imagem_gerada.image.image_bytes).decode('utf-8')
        
        return {
            "motor_ia": "Google Imagen 3 (Real)",
            "status": "Sucesso",
            "imagem_resultado": f"data:image/jpeg;base64,{imagem_base64}"
        }
        
    except Exception as e:
        return {"erro": "Erro ao gerar imagem", "detalhe": str(e)}
