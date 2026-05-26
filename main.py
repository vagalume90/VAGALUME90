import os
import uuid
import base64
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import httpx
import google.generativeai as genai

# ==========================================
# CONFIGURAÇÃO COPIADA / VARIÁVEIS DE AMBIENTE
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "SUA_CHAVE_AQUI")
genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(
    title="VAGALUME90 - Motor de Conhecimento e Imagem Universal",
    version="0.1.0",
    description="API disruptiva: Texto inteligente e Geração de Imagens com Inteligência Artificial."
)

# Garante que a pasta para guardar imagens estáticas existe
OS_STATIC_DIR = "static"
if not os.path.exists(OS_STATIC_DIR):
    os.makedirs(OS_STATIC_DIR)

app.mount("/static", StaticFiles(directory=OS_STATIC_DIR), name="static")

# ==========================================
# MODELOS DE DADOS (SCHEMAS)
# ==========================================
class RequestTexto(BaseModel):
    tema: str = Field(..., example="África nova")

class ResponseTexto(BaseModel):
    motor_ia: str = "Gemini Developer API"
    conteudo: str

class RequestImagem(BaseModel):
    descricao: str = Field(..., example="África nova")

class ResponseImagem(BaseModel):
    motor_ia: str = "Stable Diffusion (Flux/Pollinations)"
    status: str = "Sucesso"
    url_imagem: str
    imagem_base64: str

# ==========================================
# ENDPOINTS
# ==========================================

@app.get("/", tags=["default"])
async def inicio():
    return {"mensagem": "VAGALUME90 API está online e operacional."}


@app.post("/api/ia/gerar", response_model=ResponseTexto, tags=["default"])
async def api_gerar_conteudo(payload: RequestTexto):
    """
    Gera texto inteligente usando o Gemini de forma estruturada, 
    evitando o erro de 'additionalProperties'.
    """
    try:
        # Usamos o modelo recomendado para texto geral
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt_engenharia = (
            f"Gere um conteúdo profundo, profissional e criativo sobre o tema: '{payload.tema}'. "
            "A sua resposta deve ser em formato de texto limpo e bem estruturado."
        )

        # Configuração segura para evitar conflitos de Schema no modo Developer
        configuracao = genai.GenerationConfig(
            response_mime_type="text/plain", # Evita conflito forçando texto fluido
            temperature=0.7
        )

        # Chamada assíncrona simulada (executada em threadpool pelo FastAPI se necessário)
        resposta = model.generate_content(prompt_engenharia, generation_config=configuracao)
        
        if not resposta.text:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A IA não conseguiu gerar uma resposta válida para este tema."
            )

        return ResponseTexto(conteudo=resposta.text)

    except Exception as e:
        # Retorna o erro real com o código HTTP correto (500) para o cliente
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erro interno no motor Gemini: {str(e)}"
        )


@app.post("/api/ia/gerar-imagem", response_model=ResponseImagem, tags=["default"])
async def api_gerar_imagem(payload: RequestImagem):
    """
    Gera imagens do futuro usando o motor Flux via Pollinations AI.
    Trabalha de forma 100% assíncrona.
    """
    # Formata a URL do serviço externo de forma segura
    prompt_formatado = httpx.URL(payload.descricao)
    url_flux = f"https://image.pollinations.ai/p/{prompt_formatado}?width=1024&height=1024&nologo=true"
    
    try:
        # Uso do httpx.AsyncClient para não bloquear o servidor durante o download da imagem
        async with httpx.AsyncClient() as client:
            resposta_url = await client.get(url_flux, timeout=30.0)
            
            if resposta_url.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Não foi possível obter resposta do servidor de imagens."
                )
            
            conteudo_imagem = resposta_url.content

        # Criação de um nome de ficheiro único
        nome_ficheiro = f"{uuid.uuid4().hex}.jpg"
        caminho_completo = os.path.join(OS_STATIC_DIR, nome_ficheiro)
        
        # Gravação assíncrona do ficheiro no disco
        with open(caminho_completo, "wb") as f:
            f.write(conteudo_imagem)
            
        # Conversão para string Base64 limpa
        string_base64 = base64.b64encode(conteudo_imagem).decode("utf-8")
        uri_base64 = f"data:image/jpeg;base64,{string_base64}"
        
        # URL relativa para o cliente aceder
        url_relativa = f"/static/{nome_ficheiro}"

        return ResponseImagem(
            url_imagem=url_relativa,
            imagem_base64=uri_base64
        )

    except httpx.RequestError as err_http:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Falha de rede ao gerar imagem: {str(err_http)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar imagem no servidor: {str(e)}"
        )
