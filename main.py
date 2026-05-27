import os
import base64
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai

# Configuração da API do Google
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

app = FastAPI()

class PedidoTema(BaseModel):
    tema: str

class PedidoImagem(BaseModel):
    descricao: str

@app.post("/api/ia/gerar")
async def gerar_conteudo(pedido: PedidoTema):
    try:
        # Mudamos para 'gemini-pro' para garantir compatibilidade com a versão v1beta da API
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(f"Escreva um texto informativo sobre: {pedido.tema}")
        return {"status": "Sucesso", "conteudo": response.text}
    except Exception as e:
        return {"status": "Erro", "conteudo": str(e)}

@app.post("/api/ia/gerar-imagem")
async def gerar_imagem(pedido: PedidoImagem):
    try:
        url = f"https://image.pollinations.ai/prompt/{pedido.descricao}?width=1024&height=1024&nologo=true"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=30.0)
            
        if resp.status_code != 200:
            return {"status": "Falha", "erro": f"Erro na API de imagem: {resp.status_code}"}
            
        base64_image = base64.b64encode(resp.content).decode('utf-8')
        return {
            "status": "Sucesso",
            "imagem_base64": f"data:image/jpeg;base64,{base64_image}"
        }
    except Exception as e:
        return {"status": "Falha", "erro": str(e)}
