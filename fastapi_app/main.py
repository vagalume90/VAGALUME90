import os
import time
import requests
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import motor.motor_asyncio

app = FastAPI(
    title="Vagalume90 FastAPI Core",
    description="Gestor de Confirmação de Aquisição e Integração n8n",
    version="1.1.0"
)

# =======================================================
# CONFIGURAÇÕES DE AMBIENTE
# =======================================================
MONGO_URI = os.getenv("MONGO_URI")
# Chave do n8n que guardámos ontem para estruturar o fluxo
N8N_CHAVE_FLUXO = "91ea9ca4-f513-4f3f-8172-c4f3eb7dd8b5" 
# URL do webhook do n8n (podes mudar no teu painel do Render se necessário)
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", f"https://n8n.vagalume90.com/webhook/{N8N_CHAVE_FLUXO}")
WHATSAPP_SUPORTE_NUMERO = os.getenv("WHATSAPP_NUMERO", "244929894589")

if not MONGO_URI:
    raise ValueError("⚠️ ERRO CRÍTICO: A variável MONGO_URI está em falta na FastAPI!")

# Ligação Assíncrona ao MongoDB Atlas
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client["vagalume_db"]
colecao_transacoes = db["transacoes"]
colecao_produtos = db["produtos"]

# =======================================================
# MODELOS DE ENTRADA (PAYLOAD DO FLASK)
# =======================================================
class RequisicaoCompra(BaseModel):
    produto_id: str
    comprador_id: str
    afiliado_cod: str

# =======================================================
# GESTOR DE CONFIRMAÇÃO DE AQUISIÇÃO
# =======================================================

@app.post("/api/mercado/comprar")
async def confirmar_aquisicao(payload: RequisicaoCompra):
    """
    Processa a intenção de compra, gera a ordem, guarda no MongoDB 
    e notifica o ecossistema n8n para automação.
    """
    try:
        # 1. Tentar localizar o produto no MongoDB para capturar o título real
        titulo_produto = "Fórmula Tráfego Angola"
        
        if payload.produto_id != "PROD_DESTAQUE_01":
            try:
                from bson import ObjectId
                prod = await db["produtos"].find_one({"_id": ObjectId(payload.produto_id)})
                if prod:
                    titulo_produto = prod.get("titulo", "Produto Digital")
            except Exception:
                titulo_produto = f"Ativo ID: {payload.produto_id}"

        # 2. Gerar ID Único para a Ordem/Transação
        transacao_id = f"TX_{int(time.time())}"
        
        # 3. Estruturar o documento para a coleção 'transacoes'
        nova_transacao = {
            "transacao_id": transacao_id,
            "produto_id": payload.produto_id,
            "produto_titulo": titulo_produto,
            "comprador_id": payload.comprador_id,
            "afiliado_cod": payload.afiliado_cod,
            "status": "AGUARDANDO PROVA",
            "timestamp": time.time()
        }
        
        # 4. Guardar no MongoDB Atlas
        await colecao_transacoes.insert_one(nova_transacao)
        print(f"📦 [Gestor] Ordem {transacao_id} guardada no MongoDB.")

        # 5. Disparar Webhook para o n8n para iniciar o fluxo de automação
        if N8N_WEBHOOK_URL:
            payload_n8n = {
                "event": "requisicao_aquisicao",
                "transacao_id": transacao_id,
                "produto_id": payload.produto_id,
                "produto_titulo": titulo_produto,
                "comprador_id": payload.comprador_id,
                "afiliado_cod": payload.afiliado_cod,
                "status": "AGUARDANDO PROVA",
                "chave_fluxo": N8N_CHAVE_FLUXO
            }
            try:
                # Disparo rápido em background com timeout para não travar a resposta
                requests.post(N8N_WEBHOOK_URL, json=payload_n8n, timeout=2)
                print(f"📡 [n8n] Evento enviado para o webhook do n8n com sucesso.")
            except requests.exceptions.RequestException:
                print("⚠️ [n8n] Webhook do n8n não respondeu a tempo, mas a transação foi salva.")

        # 6. Construir mensagem padrão para direcionamento do WhatsApp angolano
        mensagem_whatsapp = (
            f"Olá! Quero validar o meu Ativo Digital.\n\n"
            f"⚙️ ORDEM ID: {transacao_id}\n"
            f"📘 INFOPRODUTO: {titulo_produto}\n"
            f"👤 OPERADOR: {payload.comprador_id}\n"
            f"🎯 REF: {payload.afiliado_cod}"
        )
        texto_codificado = requests.utils.quote(mensagem_whatsapp)
        whatsapp_url = f"https://api.whatsapp.com/send?phone={WHATSAPP_SUPORTE_NUMERO}&text={texto_codificado}"

        # Retorna a resposta exata que o teu Flask espera ler
        return {
            "success": True,
            "transacao_id": transacao_id,
            "status": "AGUARDANDO PROVA",
            "whatsapp_url": whatsapp_url
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno no Gestor de Aquisição: {str(e)}"
        )

@app.get("/")
async def status_sistema():
    return {
        "sistema": "Vagalume90 FastAPI Core",
        "gestor_status": "Pronto para receber aquisições",
        "fluxo_vinculado": N8N_CHAVE_FLUXO
    }
