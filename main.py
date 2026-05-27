import os
import base64
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
# IMPORTANTE: Mudança para a nova SDK oficial de 2026
from google import genai
from google.genai import errors

app = FastAPI(title="Vagalume90 API", version="1.0.0")

# Inicializa o cliente oficial. Ele vai procurar automaticamente 
# pela variável de ambiente GEMINI_API_KEY no Render.
try:
    client = genai.Client()
except Exception as e:
    client = None
    print(f"Aviso: Erro ao inicializar o cliente Gemini. Verifique a GEMINI_API_KEY. Erro: {e}")

class PedidoTema(BaseModel):
    tema: str

class PedidoImagem(BaseModel):
    descricao: str

@app.post("/api/ia/gerar")
async def gerar_conteudo(pedido: PedidoTema):
    if not client:
        return {"status": "Erro", "conteudo": "Cliente Gemini não inicializado. Verifique a chave de API no Render."}
        
    try:
        # Método oficial e atualizado para geração de conteúdo em 2026
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=f"Escreva um texto informativo sobre: {pedido.tema}",
        )
        return {"status": "Sucesso", "conteudo": response.text}
        
    except errors.APIError as e:
        # Captura erros específicos da API do Google (ex: chave inválida, modelo não encontrado)
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
