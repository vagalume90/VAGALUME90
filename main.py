import os
import base64
import time
import asyncio
import httpx
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from urllib.parse import quote
from contextlib import asynccontextmanager
from typing import Optional

# ⚡ CACHE SIMPLES E RATE LIMIT
cache = {}
CACHE_TTL = 300  
limites = {}
LIMITE_REQ = 20  

# 🔒 SIMULAÇÃO DE BASE DE DADOS EM MEMÓRIA (Para teste inicial rápido)
# No futuro, isto será ligado ao Supabase/PostgreSQL para ficar guardado para sempre.
base_de_dados_utilizadores = {}

# 🔑 CONFIGURAÇÃO DE SEGURANÇA (Chave Digital / Token)
TOKEN_SECRETO = "Vagalume90_Chave_Secreta_Super_Protegida_2026"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client_http
    client_http = httpx.AsyncClient(
        timeout=30.0,
        headers={"User-Agent": "Vagalume90/2.1.0"}
    )
    yield
    await client_http.aclose()

app = FastAPI(title="Vagalume90 API PRO", version="2.1.0", lifespan=lifespan)

# 📋 MODELOS DE DADOS (Estruturas de validação)
class RegistoUtilizador(BaseModel):
    email: EmailStr
    password: str

class PedidoIA(BaseModel):
    tema: str
    descricao_imagem: Optional[str] = None

# 🔒 LÓGICA DE PROTEÇÃO DE TRÁFEGO
def permitido(ip: str) -> bool:
    agora = time.time()
    if ip not in limites:
        limites[ip] = []
    limites[ip] = [t for t in limites[ip] if agora - t < 60]
    if len(limites[ip]) >= LIMITE_REQ:
        return False
    limites[ip].append(agora)
    return True

# ⚡ LÓGICA DE CACHE
def get_cache(chave: str):
    if chave in cache:
        dados, tempo = cache[chave]
        if time.time() - tempo < CACHE_TTL:
            return dados
    return None

def set_cache(chave: str, valor: str):
    cache[chave] = (valor, time.time())


# ==========================================
# 🚪 ROTAS DE AUTENTICAÇÃO (NOVO)
# ==========================================

@app.post("/api/auth/register", status_code=status.HTTP_211_CREATED)
async def registar_utilizador(dados: RegistoUtilizador):
    email_limpo = dados.email.lower().strip()
    
    if email_limpo in base_de_dados_utilizadores:
        raise HTTPException(status_code=400, detail="Este email já está registado no Vagalume90.")
    
    if len(dados.password) < 6:
        raise HTTPException(status_code=400, detail="A password deve ter pelo menos 6 caracteres.")
    
    # Guarda o utilizador (com criptografia simulada para este teste rápido)
    password_criptografada = f"seguro_{base64.b64encode(dados.password.encode()).decode()}"
    base_de_dados_utilizadores[email_limpo] = {
        "email": email_limpo,
        "password": password_criptografada
    }
    
    return {"status": "Sucesso", "mensagem": "Utilizador registado com sucesso! Já pode fazer login."}


@app.post("/api/auth/login")
async def fazer_login(form_data: OAuth2PasswordRequestForm = Depends()):
    email_limpo = form_data.username.lower().strip()
    utilizador = base_de_dados_utilizadores.get(email_limpo)
    
    if not utilizador:
        raise HTTPException(status_code=400, detail="Email ou password incorretos.")
        
    password_validar = f"seguro_{base64.b64encode(form_data.password.encode()).decode()}"
    if utilizador["password"] != password_validar:
        raise HTTPException(status_code=400, detail="Email ou password incorretos.")
    
    # Se acertou, gera o Token (Chave Digital) com o email dele dentro
    token_acesso = base64.b64encode(f"{email_limpo}:{TOKEN_SECRETO}".encode()).decode()
    
    return {
        "access_token": token_acesso, 
        "token_type": "bearer",
        "mensagem": "Login efetuado com sucesso!"
    }


# 🛡️ FUNÇÃO QUE VALIDA SE O UTILIZADOR ESTÁ LOGADO ANTES DE LIBERAR A IA
async def obter_utilizador_atual(token: str = Depends(oauth2_scheme)):
    try:
        decodificado = base64.b64decode(token.encode()).decode()
        email, segredo = decodificado.split(":")
        if segredo != TOKEN_SECRETO:
            raise HTTPException(status_code=401, detail="Token inválido.")
        return email
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autorizado. Por favor, faça login primeiro.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ==========================================
# 📝 MOTORES DE IA (TEXTO E IMAGEM)
# ==========================================

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
        except Exception:
            pass
        if tentativa < 2:
            await asyncio.sleep(1.5)
    return None

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
        except Exception:
            pass
        if tentativa < 2:
            await asyncio.sleep(1.5)
    return None


# ==========================================
# 🚀 ENDPOINT DE IA BLINDADO COM AUTENTICAÇÃO
# ==========================================

# Repare o final da linha abaixo: adicionámos a dependência do login obrigatório!
@app.post("/api/ia/completo")
async def gerar_completo(pedido: PedidoIA, request: Request, email_utilizador: str = Depends(obter_utilizador_atual)):
    ip = request.client.host

    if not permitido(ip):
        raise HTTPException(status_code=429, detail="Muitas requisições. Aguarde.")

    prompt_comando = f"Escreva um texto informativo, detalhado e profissional em português sobre: {pedido.tema}"
    
    tarefas = [generar_texto(prompt_comando)]
    gerar_uma_foto = False

    if pedido.descricao_imagem and pedido.descricao_imagem.strip():
        tarefas.append(generar_imagem(pedido.descricao_imagem))
        gerar_uma_foto = True
    else:
        tarefas.append(asyncio.sleep(0))

    resultados = await asyncio.gather(*tarefas)
    texto_gerado = resultados[0]
    imagem_generated = resultados[1] if gerar_uma_foto else None

    if not texto_gerado and (gerar_uma_foto and not imagem_generated):
        raise HTTPException(status_code=503, detail="Serviços de IA offline.")

    resposta = {
        "status": "Sucesso",
        "utilizador_autorizado": email_utilizador, # Mostra quem pediu
        "texto": texto_gerado if texto_gerado else "Não foi possível gerar o texto.",
        "imagem": imagem_generated if imagem_generated else "Nenhuma imagem solicitada."
    }

    return resposta
