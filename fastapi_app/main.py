from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import os
import urllib.parse
from pymongo import MongoClient

app = FastAPI()

# =============================
# CONFIG
# =============================
MONGO_URI = os.getenv("MONGO_URI")
WHATSAPP_NUM = os.getenv("WHATSAPP_NUMERO", "244929894589")

if not MONGO_URI:
    raise Exception("MONGO_URI não configurado")

client = MongoClient(MONGO_URI)
db = client["vagalume_db"]

# =============================
# MODELO
# =============================
class Compra(BaseModel):
    produto_id: str
    comprador_id: str
    afiliado_cod: str = "DIRETO"

# =============================
# TESTE
# =============================
@app.get("/")
def root():
    return {"status": "FastAPI Vagalume90 online 🚀"}

# =============================
# COMPRA
# =============================
@app.post("/api/mercado/comprar")
async def comprar(payload: Compra):

    produto = db.produtos.find_one({"_id": payload.produto_id})

    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    preco = float(produto.get("preco_sugerido", 0))
    produtor_id = produto.get("criador_id", "CORE")

    # 💰 divisão
    taxa = preco * 0.20
    afiliado_valor = 0
    produtor_valor = preco * 0.80

    if payload.afiliado_cod != "DIRETO":
        afiliado_valor = preco * 0.20
        produtor_valor = preco * 0.60

    transacao = {
        "produto_id": payload.produto_id,
        "comprador_id": payload.comprador_id,
        "valor": preco,
        "divisao": {
            "plataforma": taxa,
            "afiliado": afiliado_valor,
            "produtor": produtor_valor
        },
        "status": "PENDENTE",
        "data": datetime.utcnow()
    }

    resultado = db.transacoes.insert_one(transacao)
    transacao_id = str(resultado.inserted_id)

    # WhatsApp
    msg = f"""VAGALUME90 - COMPRA

ID: {transacao_id}
Produto: {produto.get('titulo')}
Valor: {preco} KZ

Envie comprovativo."""
    
    link = f"https://api.whatsapp.com/send?phone={WHATSAPP_NUM}&text={urllib.parse.quote(msg)}"

    return {
        "success": True,
        "transacao_id": transacao_id,
        "whatsapp_url": link
    }
