import os
import base64
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai

# Configuração da API
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
            
        return {
            "status": "Sucesso",
            "imagem_base64": f"data:image/jpeg;base64,{base64.b64encode(resp.content).decode()}"
        }
    except Exception as e:
        return {"status": "Falha", "erro": str(e)}
