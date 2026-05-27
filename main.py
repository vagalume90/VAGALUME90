import os
import uuid
import base64
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

# Configuração da chave do Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

app = FastAPI()

class PedidoTema(BaseModel):
    tema: str

class PedidoImagem(BaseModel):
    descricao: str

@app.post("/api/ia/gerar")
async def gerar_conteudo(pedido: PedidoTema):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        # Simples, sem esquemas complexos que causam erro
        response = model.generate_content(f"Escreva um texto informativo sobre: {pedido.tema}")
        return {"motor_ia": "Gemini 1.5 Flash", "status": "Sucesso", "conteudo": response.text}
    except Exception as e:
        return {"motor_ia": "Gemini", "status": "Erro", "erro": str(e)}

@app.post("/api/ia/gerar-imagem")
async def gerar_imagem(pedido: PedidoImagem):
    try:
        # Usando uma URL de geração de imagem mais estável e gratuita (Pollinations)
        url = f"https://image.pollinations.ai/prompt/{pedido.descricao}?width=1024&height=1024&nologo=true"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=30.0)
            
        if resp.status_code != 200:
            raise Exception(f"API de imagem retornou erro {resp.status_code}")
            
        base64_image = base64.b64encode(resp.content).decode('utf-8')
        
        return {
            "motor_ia": "Pollinations AI",
            "status": "Sucesso",
            "imagem_base64": f"data:image/jpeg;base64,{base64_image}"
        }
    except Exception as e:
        return {"motor_ia": "IA Imagem", "status": "Falha", "erro": str(e)}
