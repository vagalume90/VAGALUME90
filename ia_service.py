import os
import json
import httpx
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai

router = APIRouter()

# Configura a chave da API do Gemini (pega direto do Render)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# =================================================================
# 1. MODELOS DE ENTRADA E SAÍDA (Ajustados ao teu Swagger)
# =================================================================

# Para o Gerador de Texto (/api/ia/gerar)
class RespostaInteligente(BaseModel):
    motor_ia: str
    conteudo: str | None
    erro: str | None

class PedidoConteudo(BaseModel):
    tema: str  # Alterado de 'descricao' para 'tema' para bater com o teu site


# Para o Gerador de Imagem (/api/ia/gerar-imagem)
class RespostaImagem(BaseModel):
    motor_ia: str
    status: str
    url_imagem: str

class PedidoImagem(BaseModel):
    descricao: str  # Este já estava correto no teu site


# =================================================================
# 2. ROTA DE GERAR TEXTO (Gemini - Totalmente Corrigido)
# =================================================================
@router.post("/api/ia/gerar", response_model=RespostaInteligente)
async def generar_conteudo(pedido: PedidoConteudo):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Criamos um formato de resposta restrito em JSON que a API gratuita aceita
        prompt = (
            f"Gere um conteúdo curto, inteligente e disruptivo sobre o tema: {pedido.tema}. "
            f"Responda OBRIGATORIAMENTE em formato JSON com o seguinte formato exato: "
            f'{{"conteudo": "sua resposta aqui"}}'
        )
        
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            ),
        )
        
        # Tenta ler o JSON que o Gemini devolveu
        dados_resposta = json.loads(response.text)
        
        return RespostaInteligente(
            motor_ia="Gemini 1.5 Flash",
            conteudo=dados_resposta.get("conteudo", response.text),
            erro=None
        )
        
    except Exception as e:
        # Se falhar, devolve o formato de erro que o teu sistema espera
        return RespostaInteligente(
            motor_ia="Erro",
            conteudo=None,
            erro=str(e)
        )


# =================================================================
# 3. ROTA DE GERAR IMAGEM (Flux / Pollinations - Mantido)
# =================================================================
@router.post("/api/ia/gerar-imagem", response_model=RespostaImagem)
async def gerar_imagem(pedido: PedidoImagem):
    try:
        # Formata o texto para a URL da IA
        prompt_formatado = pedido.descricao.replace(" ", ",")
        url_externa = f"https://image.pollinations.ai/prompt/{prompt_formatado}?width=1024&height=1024&nologo=true"
        
        # Faz o download da imagem gerada
        async with httpx.AsyncClient() as client:
            resposta_imagem = await client.get(url_externa)
            if resposta_imagem.status_code != 200:
                raise HTTPException(status_code=500, detail="Erro ao conectar com o motor de imagem.")
        
        # Cria a pasta static se não existir no Render
        pasta_static = "static"
        if not os.path.exists(pasta_static):
            os.makedirs(pasta_static)
            
        # Salva o arquivo com nome único
        nome_arquivo = f"{uuid.uuid4().hex}.jpg"
        caminho_completo = os.path.join(pasta_static, nome_arquivo)
        
        with open(caminho_completo, "wb") as f:
            f.write(resposta_imagem.content)
            
        return RespostaImagem(
            motor_ia="Stable Diffusion (Flux/Pollinations)",
            status="Sucesso",
            url_imagem=f"/static/{nome_arquivo}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no motor de imagem: {str(e)}")
