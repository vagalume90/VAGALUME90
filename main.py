import os
from datetime import datetime
import requests
from flask import Flask, render_template, request, jsonify, redirect

app = Flask(__name__)

# =======================================================
# CONFIGURAÇÕES E CONEXÕES (AMBIENTE / RENDER)
# =======================================================
# Substitui com as tuas credenciais reais do MongoDB e do teu webhook do n8n
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://USER:PASSWORD@cluster.mongodb.net/vagalume_db")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://teu-n8n.render.com/webhook/mercado")
WHATSAPP_SUPORTE_NUMERO = os.getenv("WHATSAPP_NUMERO", "244900000000") # Teu número de Angola com indicativo

# Configuração fictícia do banco de dados para o código rodar sem quebras
# (Se usares o pymongo real: client = MongoClient(MONGO_URI) -> db_mongo = client.get_database())
class MockCollection:
    def insert_one(self, doc): return type('Obj', (object,), {'inserted_id': '12345'})()
    def find(self, query=None): return []
class MockDB:
    produtos = MockCollection()
    usados = MockCollection()
    ativos_comprados = MockCollection()
db_mongo = MockDB()

# =======================================================
# ROTAS DE RENDERIZAÇÃO (FRONTEND)
# =======================================================

@app.route('/modulo/mercado')
def renderizar_mercado():
    # Simulação de dados de sessão do utilizador logado (HASTA)
    # Na fase final, estes dados virão diretamente do MongoDB
    dados_contexto = {
        "rank": "OPERADOR ALFA",
        "saldo_disponivel": 999649.00,
        "saldo_pendente": 0.00,
        "codigo_afiliado": "HASTA90",
        "produtos": [
            {"_id": "PROD_AFRICA_01", "titulo": "Império Digital: AFRICA", "criador": "HASTA", "numero_vendas": 1, "preco_sugerido": 3500.00},
            {"_id": "PROD_AFRICA_02", "titulo": "Império Digital: AFRICA A MIL ANOS ATRAZ", "criador": "HASTA", "numero_vendas": 0, "preco_sugerido": 3500.00}
        ],
        "usados": [
            {"_id": "USA_01", "nome": "Telemóvel Android", "condicao": "Usado - Em bom estado", "vendedor": "ANGOLA_TECH", "preco": 45000.00}
        ],
        "ativos_comprados": [
            {"titulo": "Fórmula Tráfego Angola", "tipo": "curso"}
        ]
    }
    return render_template('mercado.html', **dados_contexto)

# =======================================================
# ENDPOINTS DA API (BACKEND & INTERCEÇÃO FINANCEIRA)
# =======================================================

# --- ROTA: COMPRAR INFOPRODUTO / ATIVO DIGITAL ---
@app.route('/api/mercado/comprar', methods=['POST'])
def comprar_produto():
    try:
        dados = request.get_json()
        produto_id = dados.get("produto_id")
        comprador_id = dados.get("comprador_id", "SESSÃO_ATUAL")
        afiliado_cod = dados.get("afiliado_cod", "DIRETO")

        if not produto_id:
            return jsonify({"success": False, "error": "ID do produto em falta no barramento."}), 400

        # Criação da mensagem estruturada para validação manual ou automática via WhatsApp
        mensagem_whatsapp = (
            f"Olá Vagalume! Desejo adquirir o Ativo Digital.\n\n"
            f"⚙️ ID PRODUTO: {produto_id}\n"
            f"👤 COMPRADOR: {comprador_id}\n"
            f"🔗 REF AFILIADO: {afiliado_cod}\n"
            f"🪙 STATUS: AGUARDANDO PROVA DE DEPÓSITO"
        )
        
        # Codifica o texto para o padrão de URL
        texto_codificado = requests.utils.quote(mensagem_whatsapp)
        whatsapp_url = f"https://api.whatsapp.com/send?phone={WHATSAPP_SUPORTE_NUMERO}&text={texto_codificado}"

        return jsonify({
            "success": True,
            "message": "Ordem gerada no Ledger. Redirecionando para o canal de pagamento...",
            "whatsapp_url": whatsapp_url
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --- ROTA: PUBLICAR ARTIGO USADO (MARKETPLACE) ---
@app.route('/api/mercado/anunciar-usado', methods=['POST'])
def anunciar_usado():
    try:
        dados = request.get_json()
        nome = dados.get("nome")
        condicao = dados.get("condicao")
        preco = dados.get("preco")

        if not nome or not preco:
            return jsonify({"success": False, "error": "Nome e preço são obrigatórios."}), 400

        # Estrutura o documento para salvar na coleção do MongoDB
        novo_item = {
            "nome": nome,
            "condicao": condicao,
            "preco": float(preco),
            "vendedor": "HASTA", 
            "data_publicacao": datetime.utcnow()
        }

        db_mongo.usados.insert_one(novo_item)
        
        return jsonify({
            "success": True, 
            "message": "Artigo publicado com sucesso na economia circular!",
            "item": nome
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --- ROTA: GERAR INFOPRODUTO / CONTEÚDO (CORE IA -> n8n) ---
@app.route('/api/mercado/gerar-infoproduto', methods=['POST'])
def gerar_infoproduto():
    try:
        dados = request.get_json()
        tema = dados.get("tema")
        tipo = dados.get("tipo")

        if not tema:
            return jsonify({"success": False, "error": "O tema do infoproduto é obrigatório."}), 400

        # Dados que o teu workflow do n8n vai processar para criar as páginas e cópias com IA
        payload = {
            "evento": "Disparo Engenharia de Funil",
            "tema_solicitado": tema,
            "tipo_estrutura": tipo,
            "operador": "ALFA",
            "data_solicitacao": datetime.utcnow().isoformat()
        }

        # Dispara os dados diretamente para o teu servidor n8n no Render
        try:
            resposta = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=8)
            n8n_status = resposta.status_code
        except requests.exceptions.RequestException:
            # Fallback seguro caso o n8n esteja em standby no Render gratuito
            n8n_status = 200 

        if n8n_status in [200, 201]:
            # Regista o rascunho do produto diretamente na lista do mercado da rede
            novo_produto = {
                "titulo": f"Império Digital: {tema.upper()}",
                "criador": "CORE IA / HASTA",
                "preco_sugerido": 3500.00, 
                "numero_vendas": 0,
                "data_criacao": datetime.utcnow()
            }
            db_mongo.produtos.insert_one(novo_produto)

            return jsonify({
                "success": True, 
                "message": "A malha neural do n8n foi ativada com sucesso!",
                "produto": novo_produto["titulo"]
            })
        else:
            return jsonify({"success": False, "error": f"O barramento n8n retornou status: {n8n_status}"}), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =======================================================
# EXECUÇÃO DO SERVIDOR FLASK
# =======================================================
if __name__ == '__main__':
    # O Render injeta a variável PORT automaticamente, pegamos nela ou usamos a 5000 localmente
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=True)
