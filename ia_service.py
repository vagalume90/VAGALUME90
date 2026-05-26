import os
import uuid
import base64
import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import google.generativeai as genai

router = APIRouter()

# Configura a chave da API do Gemini (pega direto do Render)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "SUA_CHAVE_AQUI")
genai.configure(api_key=GEMINI_API_KEY)

# =================================================================
# 1. MODELOS DE ENTRADA E SAÍDA (Schemas das Telas do FastAPI)
# =================================================================

class RespostaInteligente(BaseModel):
    motor_ia: str = "Gemini 1.5 Flash"
    status: str = "Sucesso"
    conteudo: str

class PedidoConteudo(BaseModel):
    descricao: str = Field(..., example="África nova")

class RespostaImagem(BaseModel):
    motor_ia: str = "Stable Diffusion (Flux/Pollinations)"
    status: str = "Sucesso"
    url_imagem: str
    imagem_base64: str

class PedidoImagem(BaseModel):
    descricao: str = Field(..., example="África nova")

# =================================================================
# 2. ROTA DE GERAR TEXTO (Gemini - Versão Ultra Estável)
# =================================================================
@router.post("/api/ia/gerar", response_model=RespostaInteligente)
async def gerar_conteudo(pedido: PedidoConteudo):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt_instrucao = (
            f"Gere uma resposta profunda, profissional e disruptiva para: {pedido.descricao}"
        )
        
        # Forçamos texto simples para garantir compatibilidade total com a API Developer
        configuracao = genai.GenerationConfig(
            response_mime_type="text/plain",
            temperature=0.7
        )
        
        response = model.generate_content(prompt_instrucao, generation_config=configuracao)
        
        if not response.text:
            raise HTTPException(status_code=500, detail="A IA retornou uma resposta vazia.")
            
        return RespostaInteligente(
            motor_ia="Gemini 1.5 Flash",
            status="Sucesso",
            conteudo=response.text
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erro no Gemini: {str(e)}"
        )

# =================================================================
# 3. ROTA DE GERAR IMAGEM (Flux / Pollinations)
# =================================================================
@router.post("/api/ia/gerar-imagem", response_model=RespostaImagem)
async def gerar_imagem(pedido: PedidoImagem):
    try:
        # Prepara o texto para ser transmitido de forma segura na URL
        prompt_formatado = httpx.URL(pedido.descricao)
        url_externa = f"https://image.pollinations.ai/p/{prompt_formatado}?width=1024&height=1024&nologo=true"
        
        # Faz o download da imagem de forma assíncrona
        async with httpx.AsyncClient() as client:
            resposta_imagem = await client.get(url_externa, timeout=30.0)
            if resposta_imagem.status_code != 200:
                raise HTTPException(status_code=502, detail="O servidor de imagens falhou.")
        
        conteudo_binario = resposta_imagem.content

        # Configura as pastas e nomes únicos para salvar no Render
        nome_arquivo = f"{uuid.uuid4().hex}.jpg"
        pasta_static = "static"
        
        if not os.path.exists(pasta_static):
            os.makedirs(pasta_static)
            
        caminho_completo = os.path.join(pasta_static, nome_arquivo)
        
        # Guarda o arquivo físico da imagem no servidor
        with open(caminho_completo, "wb") as f:
            f.write(conteudo_binario)
            
        # Transforma a imagem em código Base64
        string_base64 = base64.b64encode(conteudo_binario).decode("utf-8")
        uri_base64 = f"data:image/jpeg;base64,{string_base64}"
        
        return RespostaImagem(
            motor_ia="Stable Diffusion (Flux/Pollinations)",
            status="Sucesso",
            url_imagem=f"/static/{nome_arquivo}",
            imagem_base64=uri_base64
        )
        
    except httpx.RequestError as err_rede:
        raise HTTPException(status_code=503, detail=f"Erro de rede ao gerar imagem: {str(err_rede)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no motor de imagem: {str(e)}")
