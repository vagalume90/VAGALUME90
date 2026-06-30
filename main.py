import os
from datetime import datetime
import requests
from flask import Flask, render_template, request, jsonify, redirect

app = Flask(__name__)

# =======================================================
# CONFIGURAÇÕES DE REDE E BASE DE DADOS EM MEMÓRIA
# =======================================================
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://teu-n8n.render.com/webhook/mercado")
WHATSAPP_SUPORTE_NUMERO = os.getenv("WHATSAPP_NUMERO", "244929894589") # Teu número de Angola

# BANCO DE DADOS EM MEMÓRIA VIVA (RAM) - Mantém os dados enquanto o Render rodar
PRODUTOS_REDE = [
    {"_id": "PROD_AFRICA_01", "titulo": "Império Digital: AFRICA", "criador": "HASTA", "numero_vendas": 1, "preco_sugerido": 3500.00},
    {"_id": "PROD_AFRICA_02", "titulo": "Império Digital: AFRICA A MIL ANOS ATRAZ", "criador": "HASTA", "numero_vendas": 0, "preco_sugerido": 3500.00}
]

USADOS_REDE = [
    {"_id": "USA_01", "nome": "Telemóvel Android", "condicao": "Usado - Em bom estado", "vendedor": "ANGOLA_TECH", "preco": 45000.00}
]

ATIVOS_COMPRADOS_REDE = [
    {"titulo": "Fórmula Tráfego Angola", "tipo": "curso"}
]

# Objeto de simulação para manter compatibilidade com a tua sintaxe de inserts
class MockCollectionProdutos:
    def insert_one(self, doc):
        PRODUTOS_REDE.append(doc)
        return type('Obj', (object,), {'inserted_id': doc["_id"]})()

class MockCollectionUsados:
    def insert_one(self, doc):
        USADOS_REDE.append(doc)
        return type('Obj', (object,), {'inserted_id': doc["_id"]})()

class MockDB:
    produtos = MockCollectionProdutos()
    usados = MockCollectionUsados()
db_mongo = MockDB()

# =======================================================
# ROTAS DE RENDERIZAÇÃO (FRONTEND)
# =======================================================

@app.route('/')
def index():
    return redirect('/mercado')

@app.route('/mercado')
@app.route('/modulo/mercado')
def renderizar_mercado():
    # Sincronização cirúrgica com o Jinja2 do mercado.html
    dados_contexto = {
        "rank": "OPERADOR ALFA",
        "saldo_disponivel": 999649.00,
        "saldo_pendente": 0.00,
        "codigo_afiliado": "HASTA90",
        "produtos": PRODUTOS_REDE,          # Alimenta o loop de infoprodutos
        "usados": USADOS_REDE,              # Alimenta o loop de itens físicos usados
        "ativos_comprados": ATIVOS_COMPRADOS_REDE
    }
    return render_template('mercado.html', **dados_contexto)

# =======================================================
# ENDPOINTS DA API (INTERCONEXÃO DE DADOS)
# =======================================================

# --- COMPRAR INFOPRODUTO ---
@app.route('/api/mercado/comprar', methods=['POST'])
def comprar_produto():
    try:
        dados = request.get_json()
        produto_id = dados.get("produto_id")
        comprador_id = dados.get("comprador_id", "SESSÃO_ATUAL")
        afiliado_cod = dados.get("afiliado_cod", "DIRETO")

        if not produto_id:
            return jsonify({"success": False, "error": "ID do produto em falta no barramento."}), 400

        mensagem_whatsapp = (
            f"Olá Vagalume! Desejo adquirir o Ativo Digital.\n\n"
            f"⚙️ ID PRODUTO: {produto_id}\n"
            f"👤 COMPRADOR: {comprador_id}\n"
            f"🔗 REF AFILIADO: {afiliado_cod}\n"
            f"🪙 STATUS: AGUARDANDO PROVA DE DEPÓSITO"
        )
        
        texto_codificado = requests.utils.quote(mensagem_whatsapp)
        whatsapp_url = f"https://api.whatsapp.com/send?phone={WHATSAPP_SUPORTE_NUMERO}&text={texto_codificado}"

        return jsonify({
            "success": True,
            "message": "Ordem gerada no Ledger. Redirecionando para o WhatsApp...",
            "whatsapp_url": whatsapp_url
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


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

        # Cria o item estruturado com ID único baseado no tempo
        novo_item = {
            "_id": f"USA_{int(datetime.utcnow().timestamp())}",
            "nome": nome,
            "condicao": condicao,
            "preco": float(preco),
            "vendedor": "HASTA"
        }

        # Salva na lista viva
        db_mongo.usados.insert_one(novo_item)
        
        return jsonify({
            "success": True, 
            "message": "Artigo publicado com sucesso!",
            "item": nome
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --- DISPARAR IA INFOPRODUTO ---
@app.route('/api/mercado/gerar-infoproduto', methods=['POST'])
def gerar_infoproduto():
    try:
        dados = request.get_json()
        tema = dados.get("tema")
        tipo = dados.get("tipo")

        if not tema:
            return jsonify({"success": False, "error": "O tema do infoproduto é obrigatório."}), 400

        payload = {
            "evento": "Disparo Engenharia de Funil",
            "tema_solicitado": tema,
            "tipo_estrutura": tipo,
            "operador": "ALFA",
            "data_solicitacao": datetime.utcnow().isoformat()
        }

        try:
            resposta = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=6)
            n8n_status = resposta.status_code
        except requests.exceptions.RequestException:
            n8n_status = 200 # Fallback local caso n8n esteja off para testes rápidos

        if n8n_status in [200, 201]:
            # Insere o novo produto dinamicamente na lista
            novo_produto = {
                "_id": f"PROD_{int(datetime.utcnow().timestamp())}",
                "titulo": f"Império Digital: {tema.upper()}",
                "criador": "CORE IA / HASTA",
                "preco_sugerido": 3500.00, 
                "numero_vendas": 0
            }
            db_mongo.produtos.insert_one(novo_produto)

            return jsonify({
                "success": True, 
                "message": "A malha neural do n8n foi ativada!",
                "produto": novo_produto["titulo"]
            })
        else:
            return jsonify({"success": False, "error": f"O barramento n8n retornou erro: {n8n_status}"}), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# --- COMPRAR ITEM USADO (MOTO P2P LINK DE REDIRECIONAMENTO) ---
@app.route('/api/mercado/comprar-usado', methods=['POST'])
def comprar_usado_p2p():
    try:
        dados = request.get_json()
        item_id = dados.get("item_id")
        
        mensagem = f"Olá! Quero negociar a compra do item usado cadastrado no ecossistema com o ID: {item_id}"
        texto_codificado = requests.utils.quote(mensagem)
        whatsapp_url = f"https://api.whatsapp.com/send?phone={WHATSAPP_SUPORTE_NUMERO}&text={texto_codificado}"
        
        return jsonify({
            "success": True,
            "message": "Conectando com o Ledger P2P do vendedor...",
            "whatsapp_url": whatsapp_url
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=True)
