import os
import uuid
import base64
import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import google.generativeai as genai

router = APIRouter()

# Configuração da chave (Garanta que a variável está definida no Render)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Modelos de Dados
class RespostaInteligente(BaseModel):
    motor_ia: str = "Gemini 1.5 Flash"
    status: str = "Sucesso"
    conteudo: str

class PedidoConteudo(BaseModel):
    tema: str = Field(..., example="Africa")

class RespostaImagem(BaseModel):
    motor_ia: str = "Stable Diffusion (Flux/Pollinations)"
    status: str = "Sucesso"
    url_imagem: str
    imagem_base64: str

class PedidoImagem(BaseModel):
    descricao: str = Field(..., example="Africa")

# ROTA DE TEXTO (CORRIGIDA)
@router.post("/api/ia/gerar", response_model=RespostaInteligente)
async def gerar_conteudo(pedido: PedidoConteudo):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Chamada direta sem forçar schema complexo
        response = model.generate_content(
            f"Gere um texto informativo sobre: {pedido.tema}",
            generation_config={"temperature": 0.7}
        )
        
        return RespostaInteligente(
            conteudo=response.text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no Gemini: {str(e)}")

# ROTA DE IMAGEM
@router.post("/api/ia/gerar-imagem", response_model=RespostaImagem)
async def gerar_imagem(pedido: PedidoImagem):
    try:
        # Prompt Pollinations
        url_flux = f"https://image.pollinations.ai/p/{pedido.descricao}?width=1024&height=1024&nologo=true"
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url_flux)
            
        conteudo = resp.content
        nome_arquivo = f"{uuid.uuid4().hex}.jpg"
        
        if not os.path.exists("static"):
            os.makedirs("static")
            
        with open(f"static/{nome_arquivo}", "wb") as f:
            f.write(conteudo)
            
        return RespostaImagem(
            url_imagem=f"/static/{nome_arquivo}",
            imagem_base64=f"data:image/jpeg;base64,{base64.b64encode(conteudo).decode()}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
