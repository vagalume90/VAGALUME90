from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from pymongo import MongoClient
from bson.objectid import ObjectId  # IMPORTAÇÃO CORRIGIDA PARA EVITAR CRASH NO RENDER
from datetime import datetime
import os
import requests  # Garante a comunicação com o n8n

app = Flask(__name__)

# CHAVE SECRETA DA SESSÃO
app.secret_key = os.environ.get('SECRET_KEY', 'VAGALUME90_CHAVE_NEURAL_SECRETA')

# CONEXÃO LÓGICA AO MONGODB ATLAS
# O Render vai ler a tua senha real direto do painel (Environment -> MONGO_URI)
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://usuario:senha@cluster.mongodb.net/vagalume90_db')
client = MongoClient(MONGO_URI)
db = client['vagalume90_db'] # Seleciona a base de dados activa explicitamente

# =================================================================
# 1. ROTAS DE AUTENTICAÇÃO E ENTRADA
# =================================================================

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('modulo_mercado'))
    return "<h1>PORTAL VAGALUME90</h1><p>Ecrã de Login Central. Autenticação Neural Requerida.</p>"

# ROTA DE LOGIN DE TESTE (Alinhada corretamente)
@app.route('/login-teste')
def login_teste():
    # Define o utilizador que criaste com saldo na tua base de dados
    session['username'] = 'HASTA'  
    session['rank'] = 'OPERADOR ALFA'
    return "<h3>Sessão Neural Ativada com Sucesso!</h3><p><a href='/modulo/mercado'>Entrar no Módulo Mercado</a></p>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# =================================================================
# 2. MÓDULO MERCADO - ROTAS VISUAIS (BLINDADO CONTRA ERRO 500)
# =================================================================

@app.route('/modulo/mercado')
def modulo_mercado():
    if 'username' not in session:
        return redirect(url_for('index'))
        
    ref_url = request.args.get('ref')
    if ref_url:
        session['ref_afiliado'] = ref_url
        
    comprador_atual = session['username']
    user_data = db.users.find_one({"username": comprador_atual})
    if not user_data:
        return f"Erro Crítico: Operador '{comprador_atual}' não detetado.", 404
    
    # Puxa os infoprodutos ativos da base de dados
    produtos_cru = list(db.infoprodutos.find({"status": "ativo"}))
    
    # 🛡️ BLINDAGEM AUTOMÁTICA: Garante que nenhum produto antigo sem o atributo preco_sugerido quebre o Jinja2
    produtos_ia = []
    for prod in produtos_cru:
        if 'preco_sugerido' not in prod:
            # Se tiver o campo 'preco', usa-o. Caso contrário, define o padrão de 3500.0
            prod['preco_sugerido'] = prod.get('preco', 3500.0)
        produtos_ia.append(prod)
        
    itens_usados = list(db.marketplace_usados.find({"status": "disponivel"}))
    
    # BUSCA OS ATIVOS ADQUIRIDOS: Procura transações concluídas deste utilizador
    transacoes_usuario = list(db.transacoes.find({
        "comprador": comprador_atual,
        "status": "concluida"
    }))
    
    # Extrai os IDs dos produtos comprados para encontrar os detalhes deles
    ids_comprados = [t['produto_id'] for t in transacoes_usuario if 'produto_id' in t]
    
    # Busca os dados reais dos infoprodutos que foram comprados
    ativos_adquiridos = list(db.infoprodutos.find({"_id": {"$in": ids_comprados}}))
    
    return render_template(
        'mercado.html',
        rank=session.get('rank', 'OPERADOR ALFA'),
        saldo_disponivel=user_data.get('saldo', {}).get('disponivel', 0.0),
        saldo_pendente=user_data.get('saldo', {}).get('pendente', 0.0),
        codigo_afiliado=user_data.get('afiliacao', {}).get('codigo', 'VAGALUME90-ALFA'),
        produtos=produtos_ia,  # Passa a lista corrigida e segura para o ecrã HTML
        usados=itens_usados,
        ativos_comprados=ativos_adquiridos  
    )

# =================================================================
# 3. ENDPOINTS DA API - TRANSAÇÕES
# =================================================================

@app.route('/api/mercado/comprar', methods=['POST'])
def processar_compra_v2_gratis():
    if 'username' not in session:
        return jsonify({"error": "Acesso negado. Autenticação necessária."}), 403
        
    data = request.get_json() or {}
    produto_id = data.get('produto_id')
    ref_afiliado = data.get('ref')
    comprador_username = session['username']
    
    if not produto_id:
        return jsonify({"error": "Parâmetro 'produto_id' em falta no payload."}), 400

    config = db.configuracoes.find_one({"_id": "sistema_config"})
    if not config:
        pct_afiliado, pct_criador, pct_plataforma = 40, 50, 10
    else:
        pct_afiliado = config['comissoes_percentual']['afiliado']
        pct_criador = config['comissoes_percentual']['criador']
        pct_plataforma = config['comissoes_percentual']['plataforma']

    comprador = db.users.find_one({"username": comprador_username})
    produto = db.infoprodutos.find_one({"_id": ObjectId(produto_id)})
    
    if not produto:
        return jsonify({"error": "O infoproduto solicitado não existe."}), 404
        
    preco_total = produto.get('preco_sugerido', 0.0)
    
    if comprador.get('saldo', {}).get('disponivel', 0.0) < preco_total:
        return jsonify({"error": "Saldo Vagalume insuficiente."}), 400
        
    if ref_afiliado == produto['criador']:
        ref_afiliado = None

    comissao_afiliado = (preco_total * pct_afiliado) / 100 if ref_afiliado else 0.0
    lucro_criador = (preco_total * pct_criador) / 100 if ref_afiliado else (preco_total * (pct_criador + pct_afiliado)) / 100
    taxa_plataforma = (preco_total * pct_plataforma) / 100

    try:
        db.users.update_one(
            {"username": comprador_username},
            {"$inc": {"saldo.disponivel": -preco_total, "estatisticas.compras": 1}}
        )
        
        db.users.update_one(
            {"username": produto['criador']},
            {"$inc": {"saldo.disponivel": lucro_criador, "estatisticas.vendas": 1}}
        )
        
        if comissao_afiliado > 0 and ref_afiliado and ref_afiliado != comprador_username:
            db.users.update_one(
                {"username": ref_afiliado},
                {"$inc": {"saldo.disponivel": comissao_afiliado}}
            )
        
        db.infoprodutos.update_one(
            {"_id
