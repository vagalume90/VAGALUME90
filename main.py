import os
from datetime import datetime
import requests
from flask import Flask, render_template, request, jsonify, redirect
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)

# =======================================================
# CONFIGURAÇÕES E CONEXÕES REAIS
# =======================================================
MONGO_URI = os.getenv("MONGO_URI")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://teu-n8n.render.com/webhook/mercado")
FASTAPI_URL = os.getenv("FASTAPI_URL")
VAGALUME_API_KEY = os.getenv("VAGALUME_API_KEY", "chave_secreta_default")
WHATSAPP_SUPORTE_NUMERO = os.getenv("WHATSAPP_NUMERO", "244929894589")

if MONGO_URI:
    client = MongoClient(MONGO_URI)
    db = client.get_database("vagalume_db")
else:
    raise ValueError("⚠️ ERRO CRÍTICO: A variável MONGO_URI não foi detetada no Render!")

colecao_produtos = db["produtos"]
colecao_usados = db["usados"]
colecao_transacoes = db["transacoes"]

# =======================================================
# ROTAS DE RENDERIZAÇÃO
# =======================================================

@app.route('/')
def index():
    return redirect('/modulo/mercado')

@app.route('/mercado')
@app.route('/modulo/mercado')
def renderizar_mercado():
    id_comprador_atual = "USER_HASTA_90"
    lista_produtos = list(colecao_produtos.find({}))
    lista_usados = list(colecao_usados.find({}))
    
    transacoes_aprovadas = list(colecao_transacoes.find({
        "comprador_id": id_comprador_atual,
        "status": "LIBERADO"
    }))
    
    ativos_comprados = []
    for transacao in transacoes_aprovadas:
        ativos_comprados.append({
            "titulo": transacao.get("produto_titulo", "Ativo Digital"),
            "tipo": "digital",
            "download_url": transacao.get("download_url", "#")
        })

    produto_destaque = {
        "_id": "PROD_DESTAQUE_01",
        "titulo": "Fórmula Tráfego Angola (Acesso Vitalício)",
        "criador": "VAGALUME CORE",
        "preco_sugerido": 7500.00,
        "descricao": "O mapa completo para dominar anúncios e escala digital no mercado angolano."
    }

    dados_contexto = {
        "rank": "OPERADOR ALFA",
        "saldo_disponivel": 999649.00,
        "saldo_pendente": 0.00,
        "codigo_afiliado": "HASTA90",
        "produto_destaque": produto_destaque,
        "produtos": lista_produtos,
        "usados": lista_usados,
        "ativos_comprados": ativos_comprados
    }
    return render_template('mercado.html', **dados_contexto)

# =======================================================
# ENDPOINTS DA API
# =======================================================

@app.route('/api/mercado/comprar', methods=['POST'])
def comprar_produto():
    try:
        dados = request.get_json() or {}
        produto_id = dados.get("produto_id")
        afiliado_cod = dados.get("afiliado_cod", "DIRETO")
        id_comprador_atual = request.headers.get("X-USER-ID", "USER_HASTA_90")
        
        print(f"📡 Flask recebeu ordem para o Produto: {produto_id} | Comprador: {id_comprador_atual}")
        
        if not FASTAPI_URL:
            print("❌ ERRO: FASTAPI_URL não está configurada no Render.")
            return jsonify({"success": False, "error": "Variável FASTAPI_URL ausente no backend."}), 500
            
        endpoint_fastapi = f"{FASTAPI_URL.rstrip('/')}/api/mercado/comprar"

        payload_fastapi = {
            "produto_id": produto_id,
            "comprador_id": id_comprador_atual,
            "afiliado_cod": afiliado_cod
        }

        headers_seguranca = {
            "Content-Type": "application/json",
            "X-USER-ID": id_comprador_atual,
            "Authorization": f"Bearer {VAGALUME_API_KEY}"
        }

        try:
            print(f"🔗 Encaminhando para o FastAPI: {endpoint_fastapi}")
            resposta_fastapi = requests.post(endpoint_fastapi, json=payload_fastapi, headers=headers_seguranca, timeout=10)
            resposta_dados = resposta_fastapi.json()
            print(f"📥 FastAPI respondeu com Status: {resposta_fastapi.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Falha crítica de conexão com o FastAPI: {str(e)}")
            return jsonify({"success": False, "error": f"O Motor Financeiro está offline: {str(e)}"}), 502

        if resposta_fastapi.status_code != 200 or not resposta_dados.get("success"):
            erro_msg = resposta_dados.get("error", "Recusa não especificada.")
            return jsonify({"success": False, "error": f"FastAPI Recusou: {erro_msg}"}), resposta_fastapi.status_code

        transacao_id = resposta_dados.get("transacao_id")

        titulo_produto = "Fórmula Tráfego Angola"
        if produto_id != "PROD_DESTAQUE_01":
            prod_db = colecao_produtos.find_one({"_id": ObjectId(produto_id) if ObjectId.is_valid(produto_id) else produto_id})
            if prod_db:
                titulo_produto = prod_db.get("titulo")

        mensagem_whatsapp = (
            f"Olá Vagalume! Desejo adquirir o Ativo Digital.\n\n"
            f"⚙️ ID ORDEM: {transacao_id}\n"
            f"📘 ATIVO: {titulo_produto}\n"
            f"👤 COMPRADOR: {id_comprador_atual}\n"
            f"🔗 REF AFILIADO: {afiliado_cod}\n"
            f"🪙 STATUS: AGUARDANDO PROVA DE DEPÓSITO"
        )
        
        texto_codificado = requests.utils.quote(mensagem_whatsapp)
        whatsapp_url = f"https://api.whatsapp.com/send?phone={WHATSAPP_SUPORTE_NUMERO}&text={texto_codificado}"

        print(f"✅ Sucesso! Link do WhatsApp gerado: {whatsapp_url}")
        return jsonify({
            "success": True,
            "transacao_id": transacao_id,
            "whatsapp_url": whatsapp_url
        })

    except Exception as e:
        print(f"❌ Erro interno no Flask: {str(e)}")
        return jsonify({"success": False, "error": f"Erro interno do gateway: {str(e)}"}), 500

@app.route('/api/mercado/anunciar-usado', methods=['POST'])
def anunciar_usado():
    try:
        dados = request.get_json()
        novo_item = {
          "nome": dados.get("nome"),
          "condicao": dados.get("condicao"),
          "preco": float(dados.get("preco")),
          "vendedor": "HASTA",
          "data_publicacao": datetime.utcnow()
        }
        colecao_usados.insert_one(novo_item)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/mercado/gerar-infoproduto', methods=['POST'])
def gerar_infoproduto():
    try:
        dados = request.get_json()
        tema = dados.get("tema")
        novo_produto = {
            "titulo": f"Império Digital: {tema.upper()}",
            "criador": "CORE IA / HASTA",
            "preco_sugerido": 3500.00, 
            "data_criacao": datetime.utcnow()
        }
        resultado = colecao_produtos.insert_one(novo_produto)
        payload = { "produto_id": str(resultado.inserted_id), "tema_solicitado": tema }
        try: requests.post(N8N_WEBHOOK_URL, json=payload, timeout=5)
        except: pass 
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/mercado/comprar-usado', methods=['POST'])
def comprar_usado_p2p():
    try:
        dados = request.get_json()
        item_id = dados.get("item_id")
        mensagem = f"Olá! Quero mediar o artigo usado ID: {item_id}"
        texto_codificado = requests.utils.quote(mensagem)
        return jsonify({"success": True, "whatsapp_url": f"https://api.whatsapp.com/send?phone={WHATSAPP_SUPORTE_NUMERO}&text={texto_codificado}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=False)
