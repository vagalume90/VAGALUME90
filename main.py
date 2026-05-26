import os
import uuid
import base64
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import google.generativeai as genai

# Configuração do Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

router = APIRouter()

# --- Schemas ---
class PedidoConteudo(BaseModel):
    tema: str = Field(..., example="Africa")

class RespostaInteligente(BaseModel):
    motor_ia: str = "Gemini 1.5 Flash"
    status: str
    conteudo: str

class PedidoImagem(BaseModel):
    descricao: str = Field(..., example="Africa")

class RespostaImagem(BaseModel):
    motor_ia: str = "Stable Diffusion (Flux)"
    status: str
    url_imagem: str
    imagem_base64: str

# --- Rota de Texto (Estável) ---
@router.post("/api/ia/gerar", response_model=RespostaInteligente)
async def gerar_conteudo(pedido: PedidoConteudo):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(f"Escreva um texto informativo sobre: {pedido.tema}")
        
        return RespostaInteligente(
            status="Sucesso",
            conteudo=response.text
        )
    except Exception as e:
        return RespostaInteligente(
            status="Erro",
            conteudo=f"Erro ao gerar texto: {str(e)}"
        )

# --- Rota de Imagem (Otimizada) ---
@router.post("/api/ia/gerar-imagem", response_model=RespostaImagem)
async def gerar_imagem(pedido: PedidoImagem):
    try:
        url = f"https://image.pollinations.ai/p/{pedido.descricao}?width=1024&height=1024&nologo=true"
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=30.0)
            
        conteudo = resp.content
        nome_arquivo = f"{uuid.uuid4().hex}.jpg"
        pasta = "static"
        
        if not os.path.exists(pasta):
            os.makedirs(pasta)
            
        with open(f"{pasta}/{nome_arquivo}", "wb") as f:
            f.write(conteudo)
            
        return RespostaImagem(
            status="Sucesso",
            url_imagem=f"/{pasta}/{nome_arquivo}",
            imagem_base64=f"data:image/jpeg;base64,{base64.b64encode(conteudo).decode()}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
