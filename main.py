from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os

app = Flask(__name__)

# CHAVE SECRETA DA SESSÃO (Essencial para manter utilizadores logados)
app.secret_key = os.environ.get('SECRET_KEY', 'VAGALUME90_CHAVE_NEURAL_SECRETA')

# CONEXÃO LÓGICA AO MONGODB ATLAS
# O Render puxa a URI diretamente das variáveis de ambiente para segurança
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://usuario:senha@cluster.mongodb.net/vagalume90_db')
client = MongoClient(MONGO_URI)
db = client.get_database() # Seleciona a base de dados ativa

# =================================================================
# 1. ROTAS DE AUTENTICAÇÃO E ENTRADA
# =================================================================

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('modulo_mercado'))
    return "<h1>PORTAL VAGALUME90</h1><p>Ecrã de Login Central. Autenticação Neural Requerida.</p>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# =================================================================
# 2. MÓDULO MERCADO (ALAVANCA) - ROTAS VISUAIS
# =================================================================

@app.route('/modulo/mercado')
def modulo_mercado():
    # Bloqueio de Segurança: Se não estiver logado, recua para a entrada
    if 'username' not in session:
        return redirect(url_for('index'))
        
    # Puxar dados estendidos do utilizador logado no MongoDB Atlas
    user_data = db.users.find_one({"username": session['username']})
    if not user_data:
        return "Erro Crítico: Operador não detetado na base de dados.", 404
    
    # Extrair os produtos criados pelo Core IA que estão ativos na rede
    produtos_ia = list(db.infoprodutos.find({"status": "ativo"}))
    
    # Extrair os itens físicos do Marketplace de Usados
    itens_usados = list(db.marketplace_usados.find({"status": "disponivel"}))
    
    # Injetar os dados dinâmicos diretamente no template mercado.html
    return render_template(
        'mercado.html',
        rank=session.get('rank', 'OPERADOR ALFA'),
        saldo_disponivel=user_data.get('saldo', {}).get('disponivel', 0.0),
        saldo_pendente=user_data.get('saldo', {}).get('pendente', 0.0),
        codigo_afiliado=user_data.get('afiliacao', {}).get('codigo', ''),
        produtos=produtos_ia,
        usados=itens_usados
    )

# =================================================================
# 3. ENDPOINTS DA API - TRANSAÇÕES FINANCEIRAS ACID (LEDGER)
# =================================================================

@app.route('/api/mercado/comprar', methods=['POST'])
def processar_compra_v2():
    if 'username' not in session:
        return jsonify({"error": "Acesso negado. Autenticação necessária."}), 403
        
    data = request.get_json() or {}
    produto_id = data.get('produto_id')
    ref_afiliado = data.get('ref') # Username do afiliado que indicou
    comprador_username = session['username']
    
    if not produto_id:
        return jsonify({"error": "Parâmetro 'produto_id' em falta no payload."}), 400

    # Puxar a parametrização de comissão ativa na coleção 'configuracoes'
    config = db.configuracoes.find_one({"_id": "sistema_config"})
    if not config:
        # Fallback de segurança (Padrão: 40% Afiliado, 50% Criador, 10% Plataforma)
        pct_afiliado, pct_criador, pct_plataforma = 40, 50, 10
    else:
        pct_afiliado = config['comissoes_percentual']['afiliado']
        pct_criador = config['comissoes_percentual']['criador']
        pct_plataforma = config['comissoes_percentual']['plataforma']

    try:
        # INÍCIO DA TRANSAÇÃO ACID: Garante que ou roda tudo com sucesso, ou cancela tudo
        with client.start_session() as mongo_session:
            with mongo_session.start_transaction():
                
                comprador = db.users.find_one({"username": comprador_username}, session=mongo_session)
                produto = db.infoprodutos.find_one({"_id": ObjectId(produto_id)}, session=mongo_session)
                
                if not produto:
                    return jsonify({"error": "O infoproduto solicitado não existe."}), 404
                    
                preco_total = produto.get('preco_sugerido', 0.0)
                
                # Validação de Saldo contra o Ledger do utilizador
                if comprador.get('saldo', {}).get('disponivel', 0.0) < preco_total:
                    return jsonify({"error": "Saldo Vagalume insuficiente para esta operação."}), 400
                    
                # Impedir que o criador compre o seu próprio produto usando link de afiliado
                if ref_afiliado == produto['criador']:
                    ref_afiliado = None

                # Divisão analítica dos valores
                comissao_afiliado = (preco_total * pct_afiliado) / 100 if ref_afiliado else 0.0
                lucro_criador = (preco_total * pct_criador) / 100 if ref_afiliado else (preco_total * (pct_criador + pct_afiliado)) / 100
                taxa_plataforma = (preco_total * pct_plataforma) / 100

                # OPERAÇÃO 1: Deduzir o valor total do saldo do comprador
                db.users.update_one(
                    {"username": comprador_username},
                    {"$inc": {"saldo.disponivel": -preco_total, "estatisticas.compras": 1}},
                    session=mongo_session
                )
                
                # OPERAÇÃO 2: Creditar o lucro na carteira do Criador do produto
                db.users.update_one(
                    {"username": produto['criador']},
                    {"$inc": {"saldo.disponivel": lucro_criador, "estatisticas.vendas": 1}},
                    session=mongo_session
                )
                
                # OPERAÇÃO 3: Creditar a comissão do Afiliado (Se houver indicação válida)
                if comissao_afiliado > 0 and ref_afiliado and ref_afiliado != comprador_username:
                    db.users.update_one(
                        {"username": ref_afiliado},
                        {"$inc": {"saldo.disponivel": comissao_afiliado}},
                        session=mongo_session
                    )
                
                # OPERAÇÃO 4: Atualizar a telemetria e o volume de vendas do próprio produto
                db.infoprodutos.update_one(
                    {"_id": ObjectId(produto_id)},
                    {"$inc": {"numero_vendas": 1}},
                    session=mongo_session
                )

                # OPERAÇÃO 5: Registar a movimentação no Livro Razão (Coleção transacoes)
                nova_transacao = {
                    "tipo": "compra_infoproduto",
                    "comprador": comprador_username,
                    "vendedor": produto['criador'],
                    "afiliado": ref_afiliado if comissao_afiliado > 0 else None,
                    "produto_id": ObjectId(produto_id),
                    "valores": {
                        "total": preco_total,
                        "comissao_afiliado": comissao_afiliado,
                        "lucro_criador": lucro_criador,
                        "taxa_plataforma": taxa_plataforma
                    },
                    "data": datetime.utcnow(),
                    "status": "concluida"
                }
                db.transacoes.insert_one(nova_transacao, session=mongo_session)

        return jsonify({"success": True, "message": "Nexo financeiro processado. Transação ACID concluída!"})

    except Exception as e:
        # Se qualquer uma das 5 operações falhar, o banco faz ROLLBACK automático e não mexe em nenhum saldo
        return jsonify({"error": f"Falha crítica na transação: {str(e)}"}), 500

# INITIALIZADOR DO SERVIDOR DO ECOSSISTEMA
if __name__ == '__main__':
    # Configurado para rodar localmente ou ler a porta dinâmica atribuída pelo Render
    porta = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=porta, debug=True)
