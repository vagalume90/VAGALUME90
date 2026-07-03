import os
import time
from datetime import datetime
import requests
from flask import Flask, render_template, request, jsonify, redirect
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from bson import ObjectId

app = Flask(__name__)

# =======================================================
# CONFIGURAÇÕES DE AMBIENTE (SISTEMA INTEGRADO MONGO)
# =======================================================
MONGO_URI = os.getenv("MONGO_URI")
FASTAPI_URL = os.getenv("FASTAPI_URL")
WHATSAPP_SUPORTE_NUMERO = os.getenv("WHATSAPP_NUMERO", "244929894589")

if not MONGO_URI:
    raise ValueError("⚠️ ERRO CRÍTICO: A variável MONGO_URI está ausente no ambiente!")

# Lógica de conexão resiliente ao MongoDB Atlas
def obter_conexao_mongo(uri, max_tentativas=5):
    for i in range(max_tentativas):
        try:
            print(f"🔄 [Mongo Core] A conectar ao cluster... (Tentativa {i+1}/{max_tentativas})")
            client = MongoClient(uri, serverSelectionTimeoutMS=3000)
            client.server_info() # Força a validação da conexão real
            return client
        except ServerSelectionTimeoutError as e:
            if i < max_tentativas - 1:
                print("⏳ [Mongo Core] Cluster a inicializar ou ocupado. Aguardando 2s...")
                time.sleep(2)
            else:
                raise e

client = obter_conexao_mongo(MONGO_URI)
db = client["vagalume_db"]

colecao_produtos = db["produtos"]
colecao_transacoes = db["transacoes"]

# =======================================================
# ROTAS DE INTERAÇÃO
# =======================================================

@app.route('/')
def index():
    return redirect('/modulo/mercado')

@app.route('/modulo/mercado')
def renderizar_mercado():
    try:
        # Recupera produtos reais do MongoDB
        produtos = list(colecao_produtos.find().sort("_id", -1))
        
        # Converte ObjectId para String para não quebrar a renderização do Jinja2
        for p in produtos:
            p["_id"] = str(p["_id"])
            
    except Exception as e:
        return jsonify({
            "code": 503, 
            "message": "O banco de dados não está pronto ou está a demorar a responder.", 
            "details": str(e)}
        ), 503

    produto_destaque = {
        "_id": "PROD_DESTAQUE_01",
        "titulo": "Fórmula Tráfego Angola (Acesso Vitalício)",
        "preco_sugerido": 7500.00,
        "descricao": "O mapa completo para dominar anúncios e escala digital no mercado angolano."
    }

    # Dados mockados do teu operador sincronizados com o painel visual
    dados_contexto = {
        "rank": "OPERADOR ALFA",
        "saldo_disponivel": 999649.00,
        "codigo_afiliado": "HASTA90",
        "produto_destaque": produto_destaque,
        "produtos": produtos
    }
    return render_template('mercado.html', **dados_contexto)

@app.route('/api/mercado/comprar', methods=['POST'])
def comprar_produto():
    try:
        dados = request.get_json() or {}
        produto_id = dados.get("produto_id")
        afiliado_cod = dados.get("afiliado_cod", "DIRETO")
        comprador_id = "USER_HASTA_90"
        
        if not FASTAPI_URL:
            return jsonify({"success": False, "error": "A variável FASTAPI_URL não foi configurada!"}), 500

        # Rota da FastAPI que processa a tua regra de negócio/automação
        url_fastapi = f"{FASTAPI_URL.rstrip('/')}/api/mercado/comprar"
        
        payload = {
            "produto_id": str(produto_id),
            "comprador_id": comprador_id,
            "afiliado_cod": afiliado_cod
        }
        
        # Comunicação com a tua FastAPI externa
        resposta = requests.post(url_fastapi, json=payload, timeout=10)
        
        if resposta.status_code != 200:
            return jsonify({"success": False, "error": f"Erro retornado pela FastAPI: {resposta.text}"}), 500
            
        return jsonify(resposta.json())

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/mercado/gerar-infoproduto', methods=['POST'])
def gerar_infoproduto():
    try:
        dados = request.get_json() or {}
        tipo_acao = dados.get("tipo", "manual")
        
        if tipo_acao == "ia":
            tema = dados.get("tema", "Geral")
            produto = {
                "titulo": f"Império Digital: {tema.upper()}",
                "preco_sugerido": 3500.00,
                "descricao": f"Infoproduto gerado automaticamente através da inteligência artificial no nicho de {tema}.",
                "criador_id": "VAGALUME CORE",
                "download_url": "https://vagalume90.com/downloads/pack-ia",
                "created_at": datetime.utcnow()
            }
        else:
            titulo = dados.get("titulo")
            preco = dados.get("preco", 3500.00)
            download_url = dados.get("download_url", "#")
            descricao = dados.get("descricao", "Sem descrição disponível.")
            
            if not titulo:
                return jsonify({"success": False, "error": "Título do produto está em falta!"}), 400
                
            produto = {
                "titulo": titulo,
                "preco_sugerido": float(preco),
                "descricao": descricao,
                "download_url": download_url,
                "criador_id": "USER_HASTA_90",
                "created_at": datetime.utcnow()
            }

        colecao_produtos.insert_one(produto)
        return jsonify({"success": True})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=False)
