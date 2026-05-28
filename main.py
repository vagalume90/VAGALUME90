from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="Vagalume90 API PRO", version="2.1.0")

# Configuração da Tranca de Segurança (OAuth2 / JWT)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Simulador de Base de Dados de Utilizadores para o Teste
USER_DB = {}

# Modelos de Dados (O que o site envia para a API)
class UserAuth(BaseModel):
    email: str
    password: str

class PedidoTexto(BaseModel):
    tema: str

class PedidoImagem(BaseModel):
    descricao_imagem: str

class PedidoCompleto(BaseModel):
    tema: str
    descricao_imagem: str

# Função que valida se o utilizador está logado (A TRANCA)
def verificar_utilizador_logado(token: str = Depends(oauth2_scheme)):
    # Se o token existir, liberta o acesso. Se não, bloqueia.
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autorizado. Por favor, faça login primeiro.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

# --- ROTAS DE AUTENTICAÇÃO ---

@app.post("/api/auth/register", tags=["Autenticação"])
def registar_utilizador(user: UserAuth):
    if user.email in USER_DB:
        raise HTTPException(status_code=400, detail="Este email já está registado.")
    USER_DB[user.email] = user.password
    return {"status": "Sucesso", "mensagem": "Utilizador registado com sucesso! Já pode fazer login."}

@app.post("/api/auth/login", tags=["Autenticação"])
def fazer_login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_password = USER_DB.get(form_data.username)
    if not user_password or user_password != form_data.password:
        raise HTTPException(status_code=400, detail="Email ou senha incorretos.")
    return {"access_token": form_data.username, "token_type": "bearer"}


# --- ROTAS DA INTELIGÊNCIA ARTIFICIAL (PROTEGIDAS) ---

@app.post("/api/ia/texto-apenas", tags=["Inteligência Artificial"])
def gerar_texto_apenas(pedido: PedidoTexto, token: str = Depends(verificar_utilizador_logado)):
    """Gera APENAS o artigo em texto. Não gasta créditos de imagem."""
    # Aqui o motor da IA vai processar apenas o texto
    artigo_gerado = f"**Artigo sobre {pedido.tema}**\n\nConteúdo focado exclusivamente em texto para o mercado de Angola..."
    return {
        "status": "Sucesso",
        "utilizador_autorizado": token,
        "texto": artigo_gerado
    }

@app.post("/api/ia/imagem-apenas", tags=["Inteligência Artificial"])
def gerar_imagem_apenas(pedido: PedidoTarget := PedidoImagem, token: str = Depends(verificar_utilizador_logado)):
    """Gera APENAS a imagem em Base64. Não gasta tempo a criar texto."""
    # Aqui o motor da IA vai processar apenas a imagem
    imagem_base64 = "data:image/jpeg;base64,...(código_da_imagem_aqui)..."
    return {
        "status": "Sucesso",
        "utilizador_autorizado": token,
        "imagem": imagem_base64
    }

@app.post("/api/ia/completo", tags=["Inteligência Artificial"])
def gerar_completo(pedido: PedidoCompleto, token: str = Depends(verificar_utilizador_logado)):
    """Gera Texto E Imagem em simultâneo (Como estava antes, mas agora trancado)."""
    artigo_gerado = f"**Artigo Completo sobre {pedido.tema}**\n\nTexto estruturado..."
    imagem_base64 = "data:image/jpeg;base64,...(código_da_imagem_aqui)..."
    return {
        "status": "Sucesso",
        "utilizador_autorizado": token,
        "texto": artigo_gerado,
        "imagem": imagem_base64
    }
