import os
import json
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

router = APIRouter()

# Configura a chave da API do Gemini (pega direto do Render)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# =================================================================
# 1. MODELOS DE ENTRADA E SAÍDA (Telas de dados do FastAPI)
# =================================================================

# Para o Gerador de Texto
class RespostaInteligente(BaseModel):
    motor_ia: str
    status: str
    conteudo: str

class PedidoConteudo(BaseModel):
    descricao: str

# Para o Gerador de Imagem
class RespostaImagem(BaseModel):
    motor_ia: str
    status: str
    url_imagem: str

class PedidoImagem(BaseModel):
    descricao: str


# =================================================================
# 2. ROTA DE GERAR TEXTO (Gemini - Corrigido sem o Erro)
# =================================================================
@router.post("/api/ia/gerar", response_model=RespostaInteligente)
async def gerar_conteudo(pedido: PedidoConteudo):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"Gere uma resposta inteligente e disruptiva para: {pedido.descricao}"
        
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=RespostaInteligente, # Formato seguro que corrige o erro!
            ),
        )
        
        dados_resposta = json.loads(response.text)
        
        return RespostaInteligente(
            motor_ia="Gemini 1.5 Flash",
            status="Sucesso",
            conteudo=dados_resposta.get("conteudo", response.text)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no Gemini: {str(e)}")


# =================================================================
# 3. ROTA DE GERAR IMAGEM (Flux / Pollinations - O que funciona!)
# =================================================================
@router.post("/api/ia/gerar-imagem", response_model=RespostaImagem)
async def gerar_imagem(pedido: PedidoImagem):
    try:
        # Organiza o termo de busca para a IA de imagem
        prompt_formatado = pedido.descricao.replace(" ", ",")
        url_externa = f"https://image.pollinations.ai/prompt/{prompt_formatado}?width=1024&height=1024&nologo=true"
        
        # Faz o download da imagem para salvar no teu servidor do Render
        async with httpx.AsyncClient() as client:
            resposta_imagem = await client.get(url_externa)
            if resposta_imagem.status_code != 200:
                raise HTTPException(status_code=500, detail="Erro ao conectar com o motor de imagem.")
        
        # Cria um nome único para o arquivo de imagem
        import uuid
        nome_arquivo = f"{uuid.uuid4().hex}.jpg"
        pasta_static = "static"
        
        # Cria a pasta static no Render se ela não existir
        if not os.path.exists(pasta_static):
            os.makedirs(pasta_static)
            
        caminho_completo = os.path.join(pasta_static, nome_arquivo)
        
        # Guarda a imagem na pasta do teu servidor
        with open(caminho_completo, "wb") as f:
            f.write(resposta_imagem.content)
            
        return RespostaImagem(
            motor_ia="Stable Diffusion (Flux/Pollinations)",
            status="Sucesso",
            url_imagem=f"/static/{nome_arquivo}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no motor de imagem: {str(e)}")
