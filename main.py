import os
import base64
import time
import asyncio
import httpx
from fastapi import FastAPI, Request, HTTPException, status
from pydantic import BaseModel
from urllib.parse import quote
from contextlib import asynccontextmanager
from typing import Optional

# ⚡ CACHE SIMPLES
cache = {}
CACHE_TTL = 300  

# 🔒 RATE LIMIT
limites = {}
LIMITE_REQ = 20  

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client_http
    client_http = httpx.AsyncClient(
        timeout=30.0,
        headers={"User-Agent": "Vagalume90/2.0.3"}
    )
    yield
    await client_http.aclose()

app = FastAPI(title="Vagalume90 API PRO", version="2.0.3", lifespan=lifespan)

# 📋 MODELO DE DADOS FLEXÍVEL (A imagem agora é opcional: Optional[str] = None)
class PedidoIA(BaseModel):
    tema: str
    descricao_imagem: Optional[str] = None

def permitido(ip: str) -> bool:
    agora = time.time()
    if ip not in limites:
        limites[ip] = []
    limites[ip] = [t for t in limites[ip] if agora - t < 60]
    if len(limites[ip]) >= LIMITE_REQ:
        return False
    limites[ip].append(agora)
    return True

def get_cache(chave: str):
    if chave in cache:
        dados, tempo = cache[chave]
        if time.time() - tempo < CACHE_TTL:
            return dados
    return None

def set_cache(chave: str, valor: str):
    cache[chave] = (valor, time.time())

# 📝 MOTOR DE TEXTO BLINDADO
async def generar_texto(prompt: str):
    cache_key = f"texto:{prompt}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    url = f"https://text.pollinations.ai/{quote(prompt)}"

    for tentativa in range(3):
        try:
            resp = await client_http.get(url)
            if resp.status_code == 200:
                texto = resp.text.strip()
                if texto:
                    set_cache(cache_key, texto)
                    return texto
        except Exception as e:
            print(f"Erro no texto (Tentativa {tentativa + 1}/3): {e}")
        
        if tentativa < 2:
            await asyncio.sleep(1.5)

    return None # Retorna None em vez de mensagem de erro fixa para sabermos que falhou

# 🖼️ MOTOR DE IMAGEM BLINDADO
async def generar_imagem(descricao: str):
    cache_key = f"img:{descricao}"
    cached = get_cache(cache_key)
    if cached:
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
            print(f"Erro na imagem (Tentativa {tentativa + 1}/3): {e}")
            
        if tentativa < 2:
            await asyncio.sleep(1.5)

    return None

# 🚀 ENDPOINT INTELIGENTE E ANTIFALHAS
@app.post("/api/ia/completo")
async def gerar_completo(pedido: PedidoIA, request: Request):
    ip = request.client.host

    if not permitido(ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"status": "Bloqueado", "mensagem": "Muitas requisições. Aguarde."}
        )

    # Prepara as tarefas que vamos executar
    prompt_comando = f"Escreva um texto informativo, detalhado e profissional em português sobre: {pedido.tema}"
    
    tarefas = [generar_texto(prompt_comando)]
    gerar_uma_foto = False

    # Só adiciona a tarefa da imagem se o utilizador preencheu o campo
    if pedido.descricao_imagem and pedido.descricao_imagem.strip():
        tarefas.append(generar_imagem(pedido.descricao_imagem))
        gerar_uma_foto = True
    else:
        tarefas.append(asyncio.sleep(0)) # Linha de segurança caso não queira imagem

    # Executa tudo em paralelo sem travar
    resultados = await asyncio.gather(*tarefas)
    texto_gerado = resultados[0]
    imagem_gerada = resultados[1] if gerar_uma_foto else None

    # Se AMBOS falharem na internet, aí sim avisamos o cliente
    if not texto_gerado and (gerar_uma_foto and not imagem_generated):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_AVAILABLE,
            detail={"status": "Erro", "mensagem": "Os serviços externos de IA estão offline. Tente mais tarde."}
        )

    # Constrói a resposta dinâmica baseada no que deu certo
    resposta = {"status": "Parcial" if (not texto_gerado or (gerar_uma_foto and not imagem_gerada)) else "Sucesso"}
    
    resposta["texto"] = texto_gerado if texto_gerado else "Aviso: Não foi possível gerar o texto informativo neste momento."
    resposta["imagem"] = imagem_gerada if imagem_gerada else ("Nenhuma imagem solicitada" if not gerar_uma_foto else "Aviso: Não foi possível gerar a imagem neste momento.")

    return resposta
