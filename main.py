import os
import base64
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from google.genai import errors

app = FastAPI(title="Vagalume90 API", version="1.0.0")

# Procurar a chave guardada no Render de forma segura
chave_render = os.environ.get("GEMINI_API_KEY")

try:
    if chave_render:
        # Inicializa usando a chave que está escondida no Render
        client = genai.Client(api_key=chave_render)
    else:
        client = None
        print("AVISO: A variável GEMINI_API_KEY não foi encontrada no Render.")
except Exception as e:
    client = None
    print(f"Erro ao inicializar cliente: {e}")

class PedidoTema(BaseModel):
    tema: str

class PedidoImagem(BaseModel):
    descricao: str

@app.post("/api/ia/gerar")
async def gerar_conteudo(pedido: PedidoTema):
    if not client:
        return {
            "status": "Erro", 
            "conteudo": "A API não detetou a chave GEMINI_API_KEY nas definições do Render. Verifique a aba Environment."
        }
        
    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=f"Escreva um texto informativo sobre: {pedido.tema}",
        )
        return {"status": "Sucesso", "conteudo": response.text}
        
    except errors.APIError as e:
        return {"status": "Erro", "conteudo": f"Erro na API do Gemini: {e.message} (Código: {e.code})"}
    except Exception as e:
        return {"status": "Erro", "conteudo": f"Erro inesperado: {str(e)}"}

@app.post("/api/ia/gerar-imagem")
async def gerar_imagem(pedido: PedidoImagem):
    try:
        url = f"https://image.pollinations.ai/prompt/{pedido.descricao}?width=1024&height=1024&nologo=true"
        async with httpx.AsyncClient() as client_http:
            resp = await client_http.get(url, timeout=30.0)
            
        if resp.status_code != 200:
            return {"status": "Falha", "erro": f"Erro na API de imagem: {resp.status_code}"}
            
        base64_image = base64.b64encode(resp.content).decode('utf-8')
        return {
            "status": "Sucesso",
            "imagem_base64": f"data:image/jpeg;base64,{base64_image}"
        }
    except Exception as e:
        return {"status": "Falha", "erro": str(e)}
