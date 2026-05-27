import os
import base64
import time
import asyncio
import httpx
from fastapi import FastAPI, Request, HTTPException, status
from pydantic import BaseModel
from urllib.parse import quote
from contextlib import asynccontextmanager

# 🔥 CACHE SIMPLES (memória)
cache = {}
CACHE_TTL = 300  # 5 minutos

# 🔥 RATE LIMIT (simples por IP)
limites = {}
LIMITE_REQ = 20  # por minuto

# 🔥 GERENCIADOR DE CICLO DE VIDA (Substitui o antigo on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa o cliente HTTP global na abertura do servidor
    global client_http
    client_http = httpx.AsyncClient(
        timeout=20.0,
        headers={"User-Agent": "Vagalume90/2.0"}
    )
    yield
    # Garante o fechamento seguro e limpo quando o Render reiniciar ou desligar
    await client_http.aclose()

app = FastAPI(title="Vagalume90 API PRO", version="2.0.1", lifespan=lifespan)

class PedidoIA(BaseModel):
    tema: str
    descricao_imagem: str

# 🔒 LOGICA DE RATE LIMIT
def permitido(ip: str) -> bool:
    agora = time.time()

    if ip not in limites:
        limites[ip] = []

    # Limpa requisições antigas fora da janela de 60 segundos
    limites[ip] = [t for t in limites[ip] if agora - t < 60]

    if len(limites[ip]) >= LIMITE_REQ:
        return False

    limites[ip].append(agora)
    return True

# ⚡ LOGICA DE CACHE
def get_cache(chave: str):
    if chave in cache:
        dados, tempo = cache[chave]
        if time.time() - tempo < CACHE_TTL:
            return dados
    return None

def set_cache(chave: str, valor: str):
    cache[chave] = (valor, time.time())

# 🔥 MOTOR DE TEXTO
async def gerar_texto(prompt: str):
    cache_key = f"texto:{prompt}"
    cached = get_cache(cache_key)
    if cached:
        print("Texto recuperado do Cache!")
        return cached

    url = f"https://text.pollinations.ai/{quote(prompt)}?model=llama"

    for tentativa in range(3):
        try:
            resp = await client_http.get(url)
            if resp.status_code == 200 and resp.text.strip():
                texto = resp.text.strip()
                set_cache(cache_key, texto)
                return texto
        except Exception as e:
            print(f"Erro ao gerar texto (Tentativa {tentativa + 1}/3): {e}")
        
        # Aguarda 1 segundo antes de tentar novamente para estabilizar a rede
        if tentativa < 2:
            await asyncio.sleep(1)

    return None

# 🖼️ MOTOR DE IMAGEM
async def gerar_imagem(descricao: str):
    cache_key = f"img:{descricao}"
    cached = get_cache(cache_key)
    if cached:
        print("Imagem recuperada do Cache!")
        return cached

    url = f"https://image.pollinations.ai/prompt/{quote(descricao)}?width=1024&height=1024&nologo=true"

    for tentativa in range(3):
        try:
            resp = await client_http.get(url)
            if resp.status_code == 200:
                img = base64.b64encode(resp.content).decode("utf-8")
                resultado = f"data:image/jpeg;base64,{img}"
                set_cache(cache_key, resultado)
                return resultado
        except Exception as e:
            print(f"Erro ao gerar imagem (Tentativa {tentativa + 1}/3): {e}")
            
        if tentativa < 2:
            await asyncio.sleep(1)

    return None

# 🚀 ENDPOINT COMPLETO (Unificado e Protegido)
@app.post("/api/ia/completo")
async def gerar_completo(pedido: PedidoIA, request: Request):
    ip = request.client.host

    # Validação do Rate Limit com retorno HTTP 429 correto
    if not permitido(ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"status": "Bloqueado", "mensagem": "Muitas requisições consecutivas. Aguarde um minuto."}
        )

    prompt = f"Escreva um texto informativo em português sobre: {pedido.tema}"

    # Executa ambas as gerações em paralelo para máxima velocidade no backend
    texto, imagem = await asyncio.gather(
        gerar_texto(prompt),
        gerar_imagem(pedido.descricao_imagem)
    )

    if not texto and not imagem:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_AVAILABLE,
            detail={"status": "Erro", "mensagem": "Os serviços de IA estão temporariamente indisponíveis."}
        )

    return {
        "status": "Sucesso",
        "texto": texto,
        "imagem": imagem
    }
