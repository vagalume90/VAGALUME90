import os
from fastapi import FastAPI
from pydantic import BaseModel
from ia_service import gerar_conteudo_ia, gerar_imagem_ia

app = FastAPI(
    title="VAGALUME90 - Motor de Conhecimento e Imagem Universal",
    description="API disruptiva: Texto inteligente e Geração de Imagens com Inteligência Artificial."
)

class RequisicaoTema(BaseModel):
    tema: str

# Novo modelo para receber o pedido da imagem
class RequisicaoImagem(BaseModel):
    descricao: str

@app.get("/")
def inicio():
    return {"projeto": "VAGALUME90", "status": "Online", "recursos": "Texto + Imagem Ativados"}

@app.post("/api/ia/gerar")
def api_gerar_conteudo(requisicao: RequisicaoTema):
    return gerar_conteudo_ia(requisicao.tema)

# NOVA ROTA PARA CRIAR IMAGENS
@app.post("/api/ia/gerar-imagem")
def api_gerar_imagem(requisicao: RequisicaoImagem):
    """
    Digita o que queres ver e o Imagen 3 cria a imagem do futuro na hora.
    """
    return gerar_imagem_ia(requisicao.descricao)
