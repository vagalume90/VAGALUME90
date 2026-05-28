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
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

# ==========================================
# 🔐 CONFIGURAÇÃO DE SEGURANÇA
# ==========================================

SECRET_KEY = "SUPER_CHAVE_ULTRA_SECRETA_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ==========================================
# 🧠 BASE DE DADOS (MEMÓRIA - MVP)
# ==========================================

db_users = {}

# ==========================================
# ⚡ CLIENTE GLOBAL HTTP
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client_http
    client_http = httpx.AsyncClient(
        timeout=30.0,
        headers={"User-Agent": "Vagalume90/PRO"}
    )
    yield
    await client_http.aclose()

app = FastAPI(title="Vagalume90 API PRO", version="3.0.0", lifespan=lifespan)

# ==========================================
# 📋 MODELOS DE DADOS
# ==========================================

class UserRegister(BaseModel):
    email: EmailStr
    password: str

class PedidoTexto(BaseModel):
    tema: str

class PedidoImagem(BaseModel):
    descricao_imagem: str

class PedidoCompleto(BaseModel):
    tema: str
    descricao_imagem: Optional[str] = None

# ==========================================
# 🔑 FUNÇÕES DE SEGURANÇA
# ==========================================

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)

def criar_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def obter_utilizador(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

        if not email:
            raise HTTPException(status_code=401, detail="Token inválido")

        return email

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

# ==========================================
# 🛡️ RATE LIMIT
# ==========================================

limite_user = {}

def check_limite(user):
    agora = time.time()

    if user not in limite_user:
        limite_user[user] = []

    limite_user[user] = [t for t in limite_user[user] if agora - t < 60]

    if len(limite_user[user]) > 15:
        raise HTTPException(status_code=429, detail="Muitas requisições. Por favor, aguarde um minuto.")

    limite_user[user].append(agora)

# ==========================================
# 🚪 AUTENTICAÇÃO
# ==========================================

@app.post("/api/auth/register", tags=["Autenticação"])
async def register(user: UserRegister):
    if user.email in db_users:
        raise HTTPException(status_code=400, detail="Utilizador já existe")

    db_users[user.email] = {
        "email": user.email,
        "password": hash_password(user.password)
    }

    return {"msg": "Utilizador criado com sucesso"}

@app.post("/api/auth/login", tags=["Autenticação"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db_users.get(form_data.username)

    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Credenciais inválidas")

    token = criar_token({"sub": form_data.username})

    return {
        "access_token": token,
        "token_type": "bearer"
    }

# ==========================================
# 🧠 MOTORES DE IA (POLLINATIONS)
# ==========================================

MAX_TEXTO = 3000

async def gerar_texto(prompt: str):
    url = f"https://text.pollinations.ai/{quote(prompt)}"
    try:
        resp = await client_http.get(url)
        if resp.status_code == 200:
            return resp.text[:MAX_TEXTO]
    except:
        pass
    return None

async def gerar_imagem(descricao: str):
    url = f"https://image.pollinations.ai/prompt/{quote(descricao)}?width=1024&height=1024&nologo=true"
    try:
        resp = await client_http.get(url)
        if resp.status_code == 200:
            img = base64.b64encode(resp.content).decode()
            return f"data:image/jpeg;base64,{img}"
    except:
        pass
    return None

# ==========================================
# 🚀 ENDPOINTS DE INTELIGÊNCIA ARTIFICIAL
# ==========================================

@app.post("/api/ia/texto-apenas", tags=["Inteligência Artificial"])
async def rota_texto_apenas(pedido: PedidoTexto, user: str = Depends(obter_utilizador)):
    """Gera EXCLUSIVAMENTE o artigo em texto. Não gasta processamento de imagem."""
    check_limite(user)
    
    prompt = f"Escreva um texto informativo em português sobre: {pedido.tema}"
    texto = await gerar_texto(prompt)
    
    if not texto:
        raise HTTPException(status_code=503, detail="Erro ao gerar texto da IA")
        
    return {
        "status": "Sucesso",
        "user": user,
        "texto": texto
    }

@app.post("/api/ia/imagem-apenas", tags=["Inteligência Artificial"])
async def rota_imagem_apenas(pedido: PedidoImagem, user: str = Depends(obter_utilizador)):
    """Gera EXCLUSIVAMENTE a imagem em alta resolução."""
    check_limite(user)
    
    imagem = await gerar_imagem(pedido.descricao_imagem)
    
    if not imagem:
        raise HTTPException(status_code=503, detail="Erro ao gerar imagem da IA")
        
    return {
        "status": "Sucesso",
        "user": user,
        "imagem": imagem
    }

@app.post("/api/ia/completo", tags=["Inteligência Artificial"])
async def gerar_completo(pedido: PedidoCompleto, user: str = Depends(obter_utilizador)):
    """Gera Texto E Imagem em simultâneo (Combo completo)."""
    check_limite(user)

    prompt = f"Escreva um texto informativo em português sobre: {pedido.tema}"

    texto_task = gerar_texto(prompt)
    img_task = gerar_imagem(pedido.descricao_imagem) if pedido.descricao_imagem else asyncio.sleep(0)

    texto, imagem = await asyncio.gather(texto_task, img_task)

    if not texto:
        raise HTTPException(status_code=503, detail="Erro ao gerar conteúdo")

    return {
        "status": "Sucesso",
        "user": user,
        "texto": texto,
        "imagem": imagem if imagem else "Sem imagem"
    }
