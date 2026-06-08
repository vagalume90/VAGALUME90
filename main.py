import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ── 1. SEGURANÇA E SESSÃO ──
# Chave essencial para criptografar os cookies de login do utilizador
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "vagalume90_secret_key_quantum_3026")

# ── 2. CONEXÃO COM MONGODB ATLAS ──
# O Render vai ler o link real direto do painel Environment.
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://USUARIO:SENHA@cluster.mongodb.net/vagalume90?retryWrites=true&w=majority")
client = MongoClient(MONGO_URI)
db = client['vagalume90']
users_collection = db['users']


# ════════════════════════════════════════════
# RAÍZ: PORTAL DE ENTRADA (INDEX)
# ════════════════════════════════════════════
@app.route('/')
def index():
    # Se o operador já tiver uma sessão ativa, pula o login e joga direto na Matrix
    if 'username' in session:
        return redirect(url_for('mundo_matrix'))
    return render_template('index.html')


# ════════════════════════════════════════════
# AUTENTICAÇÃO NEURAL (ROTAS VIA FETCH API)
# ════════════════════════════════════════════

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not username or not password:
        return jsonify({"success": False, "message": "Preenche todos os campos para autenticar."}), 400

    # Busca o operador na base de dados (independente de maiúsculas/minúsculas)
    user = users_collection.find_one({"username_lowercase": username.lower()})

    if user and check_password_hash(user['password_hash'], password):
        # Grava os dados na sessão do servidor
        session['username'] = user['username']
        session['rank'] = user.get('rank', 'Operador Alfa')

        # Resposta JSON idêntica à que o index.html precisa para avançar
        return jsonify({
            "success": True,
            "username": user['username'],
            "rank": session['rank']
        })
    
    return jsonify({"success": False, "message": "Sequência de acesso incorreta ou inexistente."}), 401


@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    if not username or not email or not password:
        return jsonify({"success": False, "message": "Todos os campos são obrigatórios para manifestar."}), 400

    # Evita duplicações na malha do MongoDB Atlas
    if users_collection.find_one({"username_lowercase": username.lower()}):
        return jsonify({"success": False, "message": "Esta designação já se encontra ativa no nexo."}), 400
        
    if users_collection.find_one({"email": email.lower()}):
        return jsonify({"success": False, "message": "Este endereço biomórfico já está vinculado a outra consciência."}), 400

    # Criptografia de segurança cibernética para a senha
    password_hash = generate_password_hash(password)

    new_user = {
        "username": username,
        "username_lowercase": username.lower(),
        "email": email.lower(),
        "password_hash": password_hash,
        "rank": "Operador Alfa"
    }
    
    users_collection.insert_one(new_user)
    return jsonify({"success": True, "message": "Identidade manifestada com sucesso no bloco quântico."})


# ════════════════════════════════════════════
# ROTAS DOS MUNDOS (INTERMUNDOS)
# ════════════════════════════════════════════

@app.route('/mundo/matrix')
def mundo_matrix():
    # Proteção de Rota: Se tentar entrar direto sem login, volta para o index
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('matrix.html', rank=session.get('rank', 'Operador Alfa'))


@app.route('/mundo/ruas')
def mundo_ruas():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    # Dados injetados dinamicamente no template ruas.html (Saúde Yeto)
    dados_saude = {
        "status_vital": "ESTÁVEL",
        "pressao_art": "12/8 mmHg",
        "oxigenio": "98% SpO2",
        "consultas": "Nenhuma anomalia crítica detectada nas últimas 24h no setor Luanda
