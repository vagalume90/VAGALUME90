import os
import io
import json
import uuid
import base64
import logging
import urllib.parse
import requests  # Certifica-te de ter 'requests' no requirements.txt
from pathlib import Path
from typing import List, Dict, Optional

from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from PIL import Image

# =========================================================
# CONFIGURAÇÃO GLOBAL
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
ADM_DIR = BASE_DIR / "adm"

STATIC_DIR.mkdir(exist_ok=True)
ADM_DIR.mkdir(exist_ok=True)

try:
    RESAMPLING = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLING = Image.LANCZOS


# =========================================================
# SCHEMAS PYDANTIC
# =========================================================

class PerguntaSimulado(BaseModel):
    pergunta: str = Field(description="Pergunta prática sobre o tema")
    opcoes: Dict[str, str] = Field(description="Opções A, B, C e D")
    resposta_correta: str = Field(description="Letra correta (A, B, C ou D)")
    explicacao: str = Field(description="Explicação didática da resposta")


class ConteudoUniversal(BaseModel):
    tema_analisado: str
    area_conhecimento: str
    resumo_teorico: str
    simulado: List[PerguntaSimulado]
    plano_action_pratico: str = Field(alias="plano_acao_pratico")


class RespostaIA(BaseModel):
    motor_ia: str
    conteudo: Optional[dict] = None
    erro: Optional[str] = None


class RespostaImagem(BaseModel):
    motor_ia: str
    status: str
    url_imagem: Optional[str] = None
    imagem_base64: Optional[str] = None
    erro: Optional[str] = None


# =========================================================
# GERADOR DE CONTEÚDO IA (Google Gemini 2.5 Flash)
# =========================================================

def obter_cliente_gemini() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("A variável GEMINI_API_KEY não foi encontrada.")
    return genai.Client(api_key=api_key)


def gerar_conteudo_ia(tema: str) -> Dict:
    """Gera o ecossistema de texto estruturado usando o Gemini."""
    try:
        client = obter_cliente_gemini()
        prompt_sistema = (
            "Tu és o Tutor Universal do VAGALUME90. Ensinas qualquer tema de forma moderna, "
            "direta e adaptada para África, focando em mercado e monetização."
        )
        prompt_usuario = f"Cria um ecossistema completo de aprendizagem sobre: {tema}"

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_usuario,
            config=types.GenerateContentConfig(
                system_instruction=prompt_sistema,
                response_mime_type="application/json",
                response_schema=ConteudoUniversal,
                temperature=0.3,
            ),
        )
        return RespostaIA(
            motor_ia="Google Gemini 2.5 Flash",
            conteudo=json.loads(response.text)
        ).model_dump(by_alias=True)
    except Exception as e:
        logger.exception("Erro no texto do Gemini.")
        return RespostaIA(motor_ia="Erro", erro=str(e)).model_dump()


# =========================================================
# PROCESSAMENTO DE MARCA D'ÁGUA (LOGO)
# =========================================================

def aplicar_logo(imagem_fundo: Image.Image, caminho_logo: Path, tamanho_logo: int = 150, margem: int = 20) -> Image.Image:
    if not caminho_logo.exists():
        logger.warning(f"Logo não encontrada em: {caminho_logo}")
        return imagem_fundo
    try:
        img_logo = Image.open(caminho_logo).convert("RGBA")
        proporcao = tamanho_logo / float(img_logo.size[0])
        nova_altura = int(float(img_logo.size[1]) * proporcao)
        img_logo = img_logo.resize((tamanho_logo, nova_altura), RESAMPLING)
        
        imagem_fundo = imagem_fundo.convert("RGBA")
        pos_x = imagem_fundo.width - tamanho_logo - margem
        pos_y = imagem_fundo.height - nova_altura - margem
        imagem_fundo.paste(img_logo, (pos_x, pos_y), img_logo)
        return imagem_fundo
    except Exception:
        logger.exception("Erro ao aplicar logo.")
        return imagem_fundo


# =========================================================
# GERADOR DE IMAGEM IA (Stable Diffusion - 100% Gratuito)
# =========================================================

def gerar_imagem_ia(descricao_imagem: str, retornar_base64: bool = True) -> Dict:
    """Gera uma imagem incrível usando Stable Diffusion de forma totalmente gratuita."""
    if not descricao_imagem.strip():
        return RespostaImagem(motor_ia="Erro", status="Falha", erro="Descrição vazia.").model_dump()

    try:
        # Formata o texto do prompt para que o link da internet consiga ler corretamente
        prompt_codificado = urllib.parse.quote(descricao_imagem)
        
        # URL da API estável e gratuita do Stable Diffusion (Pollinations)
        url_api = f"https://image.pollinations.ai/p/{prompt_codificado}?width=1024&height=1024&nologo=true"
        
        logger.info(f"Fazendo pedido ao Stable Diffusion: {url_api}")
        
        # Faz o download dos bytes da imagem gerada
        response = requests.get(url_api, timeout=30)
        if response.status_code != 200:
            raise ValueError(f"A API do Stable Diffusion respondeu com erro código: {response.status_code}")

        imagem_bytes = response.content
        img_fundo = Image.open(io.BytesIO(imagem_bytes))

        # Procura pelo logo do olho futurista do Vagalume90
        caminho_logo = ADM_DIR / "logo_olho.png"
        if not caminho_logo.exists():
            caminho_logo = ADM_DIR / "logo_olho.jpg"

        # Aplica a marca d'água no canto inferior direito
        img_final = aplicar_logo(imagem_fundo=img_fundo, caminho_logo=caminho_logo)
        img_final = img_final.convert("RGB")

        # Guarda o arquivo físico localmente na pasta static do servidor
        nome_arquivo = f"{uuid.uuid4().hex}.jpg"
        caminho_saida = STATIC_DIR / nome_arquivo
        img_final.save(caminho_saida, format="JPEG", quality=90, optimize=True)
        logger.info(f"Imagem guardada com sucesso em: {caminho_saida}")

        resposta = RespostaImagem(
            motor_ia="Stable Diffusion (Flux/Pollinations)",
            status="Sucesso",
            url_imagem=f"/static/{nome_arquivo}"
        )

        # Transforma em base64 se o teu painel precisar de renderização instantânea
        if retornar_base64:
            buffer = io.BytesIO()
            img_final.save(buffer, format="JPEG")
            imagem_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            resposta.imagem_base64 = f"data:image/jpeg;base64,{imagem_base64}"

        return resposta.model_dump()

    except Exception as e:
        logger.exception("Erro ao gerar imagem no Stable Diffusion.")
        return RespostaImagem(
            motor_ia="Stable Diffusion",
            status="Falha",
            erro=f"Erro interno no processamento: {str(e)}"
        ).model_dump()


if __name__ == "__main__":
    print("Módulo Híbrido Estável VAGALUME90 (Gemini + Stable Diffusion) carregado.")
