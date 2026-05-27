import os
import base64
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from google import genai

app = FastAPI(title="Vagalume90 API", version="1.0.0")

# Inicialização direta e limpa do cliente usando a variável do Render
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class PedidoTema(BaseModel):
    tema: str

class PedidoImagem(BaseModel):
    descricao: str

# 🔥 LISTA DE MODELOS OTIMIZADA PARA CONTA GRATUITA
MODELOS = [
    "gemini-2.0-flash-lite",       # Modelo leve ideal para o plano gratuito de 2026
    "gemini-2.0-flash",            # Fallback se o lite não responder
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

# 🔥 FUNÇÃO INTELIGENTE SIMBIÓTICA
def gerar_texto_seguro(prompt: str):
    erros = []

    for modelo in MODELOS:
        try:
            print(f"Tentando comunicação com o modelo: {modelo}")
            response = client.models.generate_content(
                model=modelo,
                contents=prompt
            )

            if response and response.text:
                return response.text, None

        except Exception as e:
            erros.append(f"{modelo}: {str(e)}")

    # Se nenhum modelo funcionar, retorna None e a lista de erros capturados
    return None, erros

# 🔥 ENDPOINT DO TEXTO
@app.post("/api/ia/gerar")
async def gerar_conteudo(pedido: PedidoTema):
    try:
        resultado, erros = gerar_texto_seguro(
            f"Escreva um texto informativo sobre: {pedido.tema}"
        )

        # Se o texto foi gerado com sucesso
        if resultado:
            return {
                "status": "Sucesso",
                "conteudo": resultado
            }

        # Se falhou em todos os modelos da lista
        return {
            "status": "Erro controlado",
            "conteudo": "Nenhum modelo disponível no momento. Verifique as cotas da Google.",
            "detalhes": erros
        }

    except Exception as e:
        return {
            "status": "Erro crítico",
            "conteudo": f"Erro inesperado no servidor: {str(e)}"
        }

# 🔥 ENDPOINT DA IMAGEM
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
