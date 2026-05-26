import os
import io
import json
import uuid
import base64
import logging
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

# Garante que as pastas necessárias existem no servidor
STATIC_DIR.mkdir(exist_ok=True)
ADM_DIR.mkdir(exist_ok=True)

# Compatibilidade de redimensionamento do Pillow
try:
    RESAMPLING = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLING = Image.LANCZOS


# =========================================================
# SCHEMAS PYDANTIC (Estruturas de Dados)
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
# CLIENTE GEMINI
# =========================================================

def obter_cliente_gemini() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("A variável GEMINI_API_KEY não foi encontrada no ambiente.")
    return genai.Client(api_key=api_key)


# =========================================================
# GERADOR DE CONTEÚDO IA (Texto)
# =========================================================

def gerar_conteudo_ia(tema: str) -> Dict:
    """
    Gera conteúdo educacional estruturado focado no mercado africano.
    """
    try:
        client = obter_cliente_gemini()

        prompt_sistema = """
        Tu és o Tutor Universal do VAGALUME90.
        O teu trabalho é:
        - Ensinar qualquer tema de forma brilhante e descomprometida.
        - Explicar conceitos complexos usando uma linguagem moderna, direta e adaptada para a realidade de África.
        - Criar aplicações reais, focando em como monetizar esse conhecimento na prática no mercado atual.
        - Desenvolver simulados inteligentes para fixação de alto nível.
        """

        prompt_usuario = f"""
        Cria um ecossistema completo de aprendizagem sobre:
        TEMA: {tema}

        Regras:
        - Explicação moderna, profunda e direta ao ponto.
        - Casos e exemplos práticos aplicados ao contexto africano.
        - Plano de ação claro focado no mercado atual.
        - Simulado inteligente com questões de alto nível.
        """

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

        if not response.text:
            raise ValueError("Resposta vazia da IA.")

        conteudo = json.loads(response.text)
        logger.info("Conteúdo IA gerado com sucesso pelo Gemini.")

        return RespostaIA(
            motor_ia="Google Gemini 2.5 Flash",
            conteudo=conteudo
        ).model_dump(by_alias=True)

    except Exception as e:
        logger.exception("Erro ao gerar conteúdo IA.")
        return RespostaIA(
            motor_ia="Erro",
            erro=f"Falha ao gerar conteúdo: {str(e)}"
        ).model_dump()


# =========================================================
# PROCESSAMENTO DE MARCA D'ÁGUA (LOGO)
# =========================================================

def aplicar_logo(
    imagem_fundo: Image.Image,
    caminho_logo: Path,
    tamanho_logo: int = 150,
    margem: int = 20
) -> Image.Image:
    """
    Aplica de forma inteligente a logo do Vagalume90 no canto inferior direito.
    """
    if not caminho_logo.exists():
        logger.warning(f"Logo não encontrada em: {caminho_logo}. Gerando imagem sem marca d'água.")
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
        logger.info("Marca d'água do olho futurista aplicada com sucesso.")
        return imagem_fundo

    except Exception:
        logger.exception("Erro ao aplicar a marca d'água na imagem.")
        return imagem_fundo


# =========================================================
# GERADOR DE IMAGEM IA (Multimodal)
# =========================================================

def gerar_imagem_ia(descricao_imagem: str, retornar_base64: bool = True) -> Dict:
    """
    Gera imagem capturando os bytes do modelo multimodal estável e aplica o olho futurista.
    """
    if not descricao_imagem.strip():
        return RespostaImagem(
            motor_ia="Erro",
            status="Falha",
            erro="A descrição da imagem não pode estar vazia."
        ).model_dump()

    try:
        client = obter_cliente_gemini()

        logger.info(f"Enviando pedido de imagem multimodal ao Gemini: {descricao_imagem}")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=descricao_imagem,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            )
        )

        imagem_bytes = None

        # Varrer as partes da resposta à procura dos bytes puros da imagem gerada
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    imagem_bytes = part.inline_data.data
                    break

        if not imagem_bytes:
            raise ValueError("O modelo do Gemini respondeu com sucesso, mas não gerou nenhum bloco de imagem válido.")

        img_fundo = Image.open(io.BytesIO(imagem_bytes))

        # Configuração inteligente da marca d'água na pasta adm
        caminho_logo = ADM_DIR / "logo_olho.png"
        if not caminho_logo.exists():
            caminho_logo = ADM_DIR / "logo_olho.jpg"

        # Mesclar plano de fundo com a logo do Vagalume90
        img_final = aplicar_logo(imagem_fundo=img_fundo, caminho_logo=caminho_logo)
        img_final = img_final.convert("RGB")

        # Gerar o arquivo físico local na pasta static com nome único
        nome_arquivo = f"{uuid.uuid4().hex}.jpg"
        caminho_saida = STATIC_DIR / nome_arquivo
        img_final.save(caminho_saida, format="JPEG", quality=90, optimize=True)
        logger.info(f"Imagem final guardada com sucesso em: {caminho_saida}")

        resposta = RespostaImagem(
            motor_ia="Google Gemini Multimodal + VAGALUME90",
            status="Sucesso",
            url_imagem=f"/static/{nome_arquivo}"
        )

        # Processar o Base64 pronto para ser exibido diretamente no Front-end
        if retornar_base64:
            buffer = io.BytesIO()
            img_final.save(buffer, format="JPEG")
            imagem_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            resposta.imagem_base64 = f"data:image/jpeg;base64,{imagem_base64}"

        return resposta.model_dump()

    except Exception as e:
        logger.exception("Erro no processamento da imagem multimodal.")
        return RespostaImagem(
            motor_ia="Erro",
            status="Falha",
            erro=f"Erro interno no processamento: {str(e)}"
        ).model_dump()


# =========================================================
# TESTE LOCAL / AMBIENTE
# =========================================================
if __name__ == "__main__":
    print("Módulo carregado com sucesso. Pronto para servir a API do VAGALUME90.")
