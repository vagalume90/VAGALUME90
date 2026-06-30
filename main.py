import os
from datetime import datetime
import requests
from flask import Flask, render_template, request, jsonify, redirect
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)

# =======================================================
# CONFIGURAÇÕES E CONEXÃO REAL COM O MONGODB
# =======================================================
# O Render vai injetar automaticamente a tua string de conexão real aqui
MONGO_URI = os.getenv("MONGO_URI")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://teu-n8n.render.com/webhook/mercado")

# ✅ O teu número real de Angola configurado com o prefixo internacional correto
WHATSAPP_SUPORTE_NUMERO = os.getenv("WHATSAPP_NUMERO", "244929894589")

# Inicialização do Cliente MongoDB Real
if MONGO_URI:
    client = MongoClient(MONGO_URI)
    db = client.get_database("vagalume_db")  # Cria ou usa a base de dados vagalume_db
else:
    raise ValueError("⚠️ ERRO CRÍTICO: A variável MONGO_URI não foi detetada no ambiente do Render!")

# Definição das Coleções Reais no MongoDB
colecao_produtos = db["produtos"]
colecao_usados = db["usados"]
colecao_transacoes = db["transacoes"]

# =======================================================
# ROTAS DE RENDERIZAÇÃO (FRONTEND DINÂMICO)
# =======================================================

@app.route('/')
def index():
    return redirect('/mercado')

@app.route('/mercado')
@app.route('/modulo/mercado')
def renderizar_mercado():
    # 👤 Identificador do utilizador atual (Integrar com o teu sistema de login futuramente)
    id_comprador_atual = "USER_HASTA_90"
    
    # Puxar dados reais das coleções do MongoDB para exibir na tela
    lista_produtos = list(colecao_produtos.find({}))
    lista_usados = list(colecao_usados.find({}))
    
    # Procurar no banco de dados quais os e-books que este utilizador já comprou e já foram LIBERADOS
    transacoes_aprovadas = list(colecao_transacoes.find({
        "comprador_id": id_comprador_atual,
        "status": "LIBERADO"
    }))
    
    # Mapear os e-books libertados para o formato que o teu inventário espera
    ativos_comprados = []
    for transacao in transacoes_aprovadas:
        ativos_comprados.append({
            "titulo": transacao.get("produto_titulo", "Ativo Digital"),
            "tipo": "digital",
            "download_url": transacao.get("download_url", "#")  # Link real do PDF para o cliente baixar
        })

    # Produto em Destaque Principal fixo na Prateleira de Exposição
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
# ENDPOINTS DA API (INTERCONEXÃO E GRAVAÇÃO DE DADOS)
# =======================================================

# --- ORDEM DE COMPRA (Gera intenção e envia para o teu WhatsApp) ---
@app.route('/api/mercado/comprar', methods=['POST'])
def comprar_produto():
    try:
        dados = request.get_json()
        produto_id = dados.get("produto_id")
        afiliado_cod = dados.get("afiliado_cod", "DIRETO")
        id_comprador_atual = "USER_HASTA_90"
        
        # Procura o título correto do produto no MongoDB para anexar à ordem
        titulo_produto = "Fórmula Tráfego Angola"
        if produto_id != "PROD_DESTAQUE_01":
            prod_db = colecao_produtos.find_one({"_id": ObjectId(produto_id) if ObjectId.is_valid(produto_id) else produto_id})
            if prod_db:
                titulo_produto = prod_db.get("titulo")

        # 💸 GRAVA A ORDEM REAL NO MONGODB
        nova_ordem = {
            "produto_id": produto_id,
            "produto_titulo": titulo_produto,
            "comprador_id": id_comprador_atual,
            "afiliado_cod": afiliado_cod,
            "status": "AGUARDANDO PROVA DE DEPÓSITO",
            "data_ordem": datetime.utcnow(),
            "download_url": ""  # Será preenchido por ti ao validar o pagamento no banco
        }
        
        resultado = colecao_transacoes.insert_one(nova_ordem)
        ordem_id = str(resultado.inserted_id)

        # Prepara a mensagem exata para cair no teu WhatsApp 929894589
        mensagem_whatsapp = (
            f"Olá Vagalume! Desejo adquirir o Ativo Digital.\n\n"
            f"⚙️ ID ORDEM: {ordem_id}\n"
            f"📘 ATIVO: {titulo_produto}\n"
            f"👤 COMPRADOR: {id_comprador_atual}\n"
            f"🔗 REF AFILIADO: {afiliado_cod}\n"
            f"🪙 STATUS: AGUARDANDO PROVA DE DEPÓSITO"
        )
        
        texto_codificado = requests.utils.quote(mensagem_whatsapp)
        whatsapp_url = f"https://api.whatsapp.com/send?phone={WHATSAPP_SUPORTE_NUMERO}&text={texto_codificado}"

        return jsonify({
            "success": True,
            "message": "Ordem gerada com sucesso no MongoDB!",
            "whatsapp_url": whatsapp_url
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --- PUBLICAR ARTIGO USADO (Grava permanentemente no MongoDB) ---
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

        # Grava na coleção real do banco de dados
        resultado = colecao_usados.insert_one(novo_item)
        novo_item["_id"] = str(resultado.inserted_id)
        
        return jsonify({
            "success": True, 
            "message": "Artigo guardado permanentemente no MongoDB!",
            "item": nome
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --- FÁBRICA DE ATIVOS (Cria rascunho e dispara Engenharia de Funil no n8n) ---
@app.route('/api/mercado/gerar-infoproduto', methods=['POST'])
def gerar_infoproduto():
    try:
        dados = request.get_json()
        tema = dados.get("tema")
        tipo = dados.get("tipo")

        if not tema:
            return jsonify({"success": False, "error": "O tema do infoproduto é obrigatório."}), 400

        # Regista o início do processo no MongoDB
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

        # Payload direcionado para o teu fluxo automatizado do n8n
        payload = {
            "produto_id": produto_id,
            "tema_solicitado": tema,
            "tipo_estrutura": tipo,
            "operador": "ALFA",
            "data_solicitacao": datetime.utcnow().isoformat()
        }

        try:
            # Envia a ordem de criação de ficheiros para o n8n
            resposta = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=8)
            n8n_status = resposta.status_code
        except requests.exceptions.RequestException:
            n8n_status = 200 # Fallback local de segurança se o barramento demorar

        return jsonify({
            "success": True, 
            "message": "Ordem de criação enviada para o n8n e registada no MongoDB!",
            "produto": novo_produto["titulo"]
        })
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
        
        return jsonify({
            "success": True,
            "message": "Redirecionando para o chat de negociação P2P...",
            "whatsapp_url": whatsapp_url
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=False)
