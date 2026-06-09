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
# 3. ENDPOINTS DA API - TRANSAÇÕES COMPATÍVEIS COM PLANO GRÁTIS
# =================================================================

@app.route('/api/mercado/comprar', methods=['POST'])
def processar_compra_v2_gratis():
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

    # Buscar documentos normalmente (Sem travar sessões multi-documentos pagas)
    comprador = db.users.find_one({"username": comprador_username})
    produto = db.infoprodutos.find_one({"_id": ObjectId(produto_id)})
    
    if not produto:
        return jsonify({"error": "O infoproduto solicitado não existe."}), 404
        
    preco_total = produto.get('preco_sugerido', 0.0)
    
    # Validação de Saldo contra o Ledger do utilizador
    if comprador.get('saldo', {}).get('disponivel', 0.0) < preco_total:
        return jsonify({"error": "Saldo Vagalume insuficiente para esta operação."}), 400
        
    # Impedir que o criador ganhe comissão de afiliado comprando o seu próprio produto
    if ref_afiliado == produto['criador']:
        ref_afiliado = None

    # Divisão analítica dos valores com base nas configurações da BD
    comissao_afiliado = (preco_total * pct_afiliado) / 100 if ref_afiliado else 0.0
    lucro_criador = (preco_total * pct_criador) / 100 if ref_afiliado else (preco_total * (pct_criador + pct_afiliado)) / 100
    taxa_plataforma = (preco_total * pct_plataforma) / 100

    try:
        # OPERAÇÃO 1: Deduzir o valor total do saldo do comprador
        db.users.update_one(
            {"username": comprador_username},
            {"$inc": {"saldo.disponivel": -preco_total, "estatisticas.compras": 1}}
        )
        
        # OPERAÇÃO 2: Creditar o lucro na carteira do Criador do produto
        db.users.update_one(
            {"username": produto['criador']},
            {"$inc": {"saldo.disponivel": lucro_criador, "estatisticas.vendas": 1}}
        )
        
        # OPERAÇÃO 3: Creditar a comissão do Afiliado (Se houver indicação válida)
        if comissao_afiliado > 0 and ref_afiliado and ref_afiliado != comprador_username:
            db.users.update_one(
                {"username": ref_afiliado},
                {"$inc": {"saldo.disponivel": comissao_afiliado}}
            )
        
        # OPERAÇÃO 4: Atualizar a telemetria e o volume de vendas do infoproduto
        db.infoprodutos.update_one(
            {"_id": ObjectId(produto_id)},
            {"$inc": {"numero_vendas": 1}}
        )

        # OPERAÇÃO 5: Registar a movimentação no Livro Razão (Coleção transacoes) para auditoria
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
        db.transacoes.insert_one(nova_transacao)

        return jsonify({"success": True, "message": "Movimentação processada com sucesso no plano gratuito!"})

    except Exception as e:
        return jsonify({"error": f"Falha ao processar a movimentação: {str(e)}"}), 500

# =================================================================
# 4. FÁBRICA DE ATIVOS - CORE IA MULTIFACETADA
# =================================================================

@app.route('/api/mercado/gerar-infoproduto', methods=['POST'])
def gerar_infoproduto_ia():
    if 'username' not in session:
        return jsonify({"error": "Acesso negado. Autenticação necessária."}), 403
        
    data = request.get_json() or {}
    tema = data.get('tema', '').strip()
    tipo = data.get('tipo', 'ebook') # ebook ou curso
    criador_username = session['username']
    
    if not tema:
        return jsonify({"error": "Insira um tema válido para ativar a IA."}), 400
        
    # Payload Gerado pela IA (Simulação completa do Funil de Vendas)
    novo_infoproduto = {
        "titulo": f"Império Digital: {tema}",
        "descricao": f"O guia definitivo focado em {tema}, gerado e otimizado pela inteligência do ecossistema Vagalume90.",
        "categoria": "Estratégia Digital",
        "tags": [tipo, "Vagalume90", tema[:10]],
        "criador": criador_username,
        "preco_sugerido": 3500.00, # Valor padrão em Kwanzas
        "conteudo": {
            "tipo": tipo,
            "modulos_ou_capitulos": [
                "Fase 01: O Despertar e Mindset de Operador",
                f"Fase 02: Engenharia Prática Aplicada a {tema}",
                "Fase 03: Escala Automática e Distribuição na Malha"
            ]
        },
        "funil_vendas": {
            "pagina_vendas_draft": f"<h1>Domine {tema}</h1><p>Ativo digital gerado automaticamente...</p>",
            "emails_marketing": [
                {"gatilho": "Dia 1 - Boas-vindas", "conteudo": f"Olá! Aqui está o segredo sobre {tema}..."},
                {"gatilho": "Dia 3 - Escassez", "conteudo": "As vagas para o nexo de afiliados estão a fechar."}
            ]
        },
        "numero_vendas": 0,
        "status": "ativo",
        "data_criacao": datetime.utcnow()
    }
    
    # Injetar o infoproduto gerado pela IA diretamente no MongoDB Atlas
    db.infoprodutos.insert_one(novo_infoproduto)
    
    return jsonify({
        "success": True, 
        "message": f"Core IA: Funil e {tipo.upper()} sobre '{tema}' gerados com sucesso!",
        "produto": novo_infoproduto["titulo"]
    })

# INITIALIZADOR DO SERVIDOR DO ECOSSISTEMA
if __name__ == '__main__':
    # Configurado para rodar localmente ou ler a porta dinâmica atribuída pelo Render
    porta = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=porta, debug=True)
