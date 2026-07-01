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

# Número de suporte de Angola para contingência visual ou rotas P2P
WHATSAPP_SUPORTE_NUMERO = os.getenv("WHATSAPP_NUMERO", "244929894589")

# Inicialização do Cliente MongoDB Real (Apenas leitura de Catálogo e Usados)
if MONGO_URI:
    client = MongoClient(MONGO_URI)
    db = client.get_database("vagalume_db")
else:
    raise ValueError("⚠️ ERRO CRÍTICO: A variável MONGO_URI não foi detetada no ambiente do Render!")

# Coleções locais do Flask (Catálogos estáticos e rascunhos)
colecao_produtos = db["produtos"]
colecao_usados = db["usados"]
colecao_transacoes = db["transacoes"] # Mantida apenas para leitura do inventário de e-books liberados

# =======================================================
# ROTAS DE RENDERIZAÇÃO (FRONTEND VIVO)
# =======================================================

@app.route('/')
def index():
    return redirect('/mercado')

@app.route('/mercado')
@app.route('/modulo/mercado')
def renderizar_mercado():
    id_comprador_atual = "USER_HASTA_90"
    
    lista_produtos = list(colecao_produtos.find({}))
    lista_usados = list(colecao_usados.find({}))
    
    # O inventário lê as transações que o motor financeiro já validou e marcou como LIBERADO
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
# ENDPOINTS DA API (INTEGRAÇÃO COM MOTOR FINANCEIRO)
# =======================================================

# --- ORDEM DE COMPRA (Delega a lógica financeira para o FastAPI) ---
@app.route('/api/mercado/comprar', methods=['POST'])
def comprar_produto():
    try:
        dados = request.get_json()
        produto_id = dados.get("produto_id")
        afiliado_cod = dados.get("afiliado_cod", "DIRETO")
        id_comprador_atual = "USER_HASTA_90"
        
        # 1. Validação da URL do motor financeiro FastAPI
        if not FASTAPI_URL:
            return jsonify({"success": False, "error": "Variável de ambiente FASTAPI_URL não configurada no Render."}), 500
            
        endpoint_fastapi = f"{FASTAPI_URL.rstrip('/')}/api/mercado/comprar"

        # 2. Payload estruturado para disparar o motor financeiro
        payload_fastapi = {
            "produto_id": produto_id,
            "comprador_id": id_comprador_atual,
            "afiliado_cod": afiliado_cod
        }

        # 3. Comunicação direta com o backend FastAPI
        try:
            resposta_fastapi = requests.post(endpoint_fastapi, json=payload_fastapi, timeout=10)
            resposta_dados = resposta_fastapi.json()
        except requests.exceptions.RequestException as e:
            return jsonify({"success": False, "error": f"Falha crítica de comunicação com o Motor Financeiro: {str(e)}"}), 502

        # 4. Tratamento de regras e recusas do motor financeiro
        if resposta_fastapi.status_code != 200 or not resposta_dados.get("success"):
            erro_msg = resposta_dados.get("error", "Erro desconhecido no processamento financeiro.")
            return jsonify({"success": False, "error": f"FastAPI rejeitou a ordem: {erro_msg}"}), resposta_fastapi.status_code

        # Captura o ID real gerado pela lógica financeira
        transacao_id = resposta_dados.get("transacao_id")

        # 5. Localiza o título do produto para compor a mensagem do WhatsApp
        titulo_produto = "Fórmula Tráfego Angola"
        if produto_id != "PROD_DESTAQUE_01":
            prod_db = colecao_produtos.find_one({"_id": ObjectId(produto_id) if ObjectId.is_valid(produto_id) else produto_id})
            if prod_db:
                titulo_produto = prod_db.get("titulo")

        # 6. Geração do link dinâmico de pagamento via WhatsApp com o ID do FastAPI
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

        return jsonify({
            "success": True,
            "message": "Ordem processada e integrada ao motor financeiro!",
            "transacao_id": transacao_id,
            "whatsapp_url": whatsapp_url
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"Erro interno no gateway Flask: {str(e)}"}), 500


# --- PUBLICAR ARTIGO USADO ---
@app.route('/api/mercado/anunciar-usado', methods=['POST'])
def anunciar_usado():
    try:
        dados = request.get_json()
        nome = dados.get("nome")
        condicao = dados.get("condicao")
        preco = dados.get("preco")

        if not nome or not preco:
            return jsonify({"success": False, "error": "Nome e preço são obrigatórios."}), 400

        novo_item = {
          "nome": nome,
          "condicao": condicao,
          "preco": float(preco),
          "vendedor": "HASTA",
          "data_publicacao": datetime.utcnow()
        }

        resultado = colecao_usados.insert_one(novo_item)
        novo_item["_id"] = str(resultado.inserted_id)
        
        return jsonify({"success": True, "message": "Artigo guardado no MongoDB!", "item": nome})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --- FÁBRICA DE ATIVOS (n8n) ---
@app.route('/api/mercado/gerar-infoproduto', methods=['POST'])
def gerar_infoproduto():
    try:
        dados = request.get_json()
        tema = dados.get("tema")
        tipo = dados.get("tipo")

        if not tema:
            return jsonify({"success": False, "error": "O tema do infoproduto é obrigatório."}), 400

        novo_produto = {
            "titulo": f"Império Digital: {tema.upper()}",
            "criador": "CORE IA / HASTA",
            "preco_sugerido": 3500.00, 
            "numero_vendas": 0,
            "data_criacao": datetime.utcnow(),
            "status_geracao": "PROCESSANDO"
        }
        
        resultado = colecao_produtos.insert_one(novo_produto)
        produto_id = str(resultado.inserted_id)

        payload = {
            "produto_id": produto_id,
            "tema_solicitado": tema,
            "tipo_estrutura": tipo,
            "operador": "ALFA",
            "data_solicitacao": datetime.utcnow().isoformat()
        }

        try:
            requests.post(N8N_WEBHOOK_URL, json=payload, timeout=8)
        except requests.exceptions.RequestException:
            pass 

        return jsonify({"success": True, "message": "Ordem enviada para o n8n!", "produto": novo_produto["titulo"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --- NEGOCIAÇÃO P2P DE ITENS USADOS ---
@app.route('/api/mercado/comprar-usado', methods=['POST'])
def comprar_usado_p2p():
    try:
        dados = request.get_json()
        item_id = dados.get("item_id")
        
        mensagem = f"Olá! Vi o teu artigo usado listado na plataforma Vagalume90 e desejo comprá-lo. ID do Item: {item_id}"
        texto_codificado = requests.utils.quote(mensagem)
        whatsapp_url = f"https://api.whatsapp.com/send?phone={WHATSAPP_SUPORTE_NUMERO}&text={texto_codificado}"
        
        return jsonify({"success": True, "whatsapp_url": whatsapp_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=False)
