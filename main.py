import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ── CONFIGURAÇÃO DE SEGURANÇA ──
# Define uma chave secreta para gerir as sessões do utilizador (cookies criptografados)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "vagalume90_quantum_secret_key_3026")

# ── CONEXÃO COM MONGODB ATLAS ──
# O Render vai buscar a string de conexão diretamente das variáveis de ambiente (Environment Variables)
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://USUARIO:SENHA@cluster.mongodb.net/vagalume90?retryWrites=true&w=majority")
client = MongoClient(MONGO_URI)
db = client['vagalume90']
users_collection = db['users']


# ════════════════════════════════════════════
# 1. PORTAL DE ENTRADA (INDEX)
# ════════════════════════════════════════════
@app.route('/')
def index():
    # Se o operador já estiver logado, teletransporta direto para a Matrix
    if 'username' in session:
        return redirect(url_for('mundo_matrix'))
    return render_template('index.html')


# ════════════════════════════════════════════
# 2. AUTENTICAÇÃO NEURAL (LOGIN)
# ════════════════════════════════════════════
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not username or not password:
        return jsonify({"success": False, "message": "Preenche todos os campos para autenticar."}), 400

    # Procura o utilizador no MongoDB Atlas
    user = users_collection.find_one({"username_lowercase": username.lower()})

    if user and check_password_hash(user['password_hash'], password):
        # Registra a sessão do utilizador
        session['username'] = user['username']
        session['rank'] = user.get('rank', 'Operador Alfa')

        # Retorna o JSON que o JavaScript do index.html espera para fazer o redirecionamento
        return jsonify({
            "success": True,
            "username": user['username'],
            "rank": session['rank']
        })
    
    return jsonify({"success": False, "message": "Sequência de acesso incorreta ou inexistente."}), 401


# ════════════════════════════════════════════
# 3. MANIFESTAÇÃO QUÂNTICA (REGISTO)
# ════════════════════════════════════════════
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    if not username or not email or not password:
        return jsonify({"success": False, "message": "Todos os campos são obrigatórios para manifestar."}), 400

    # Verifica se a designação única ou e-mail já existem no nexo
    if users_collection.find_one({"username_lowercase": username.lower()}):
        return jsonify({"success": False, "message": "Esta designação já se encontra ativa no nexo."}), 400
        
    if users_collection.find_one({"email": email.lower()}):
        return jsonify({"success": False, "message": "Este endereço biomórfico já está vinculado a uma consciência."}), 400

    # Criptografa a senha antes de salvar por questões de segurança cibernética
    password_hash = generate_password_hash(password)

    # Cria o novo registro para o ecossistema
    new_user = {
        "username": username,
        "username_lowercase": username.lower(),
        "email": email.lower(),
        "password_hash": password_hash,
        "rank": "Operador Alfa"  # Rank inicial padrão
    }
    
    users_collection.insert_one(new_user)

    return jsonify({"success": True, "message": "Identidade manifestada com sucesso no bloco quântico."})


# ════════════════════════════════════════════
# 4. ROTAS DOS MUNDOS (INTERMUNDOS)
# ════════════════════════════════════════════

# ── SUBSTRATO: MATRIX ──
@app.route('/mundo/matrix')
def mundo_matrix():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    return render_template('matrix.html', rank=session.get('rank', 'Operador Alfa'))


# ── URBANIDADE: RUAS (SAÚDE YETO) ──
@app.route('/mundo/ruas')
def mundo_ruas():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    # Simulação de telemetria médica em tempo real para a interface Saúde Yeto
    dados_saude = {
        "status_vital": "ESTÁVEL",
        "pressao_art": "12/8 mmHg",
        "oxigenio": "98% SpO2",
        "consultas": "Nenhuma anomalia crítica detectada nas últimas 24h no setor Luanda."
    }
    
    return render_template('ruas.html', dados_saude=dados_saude)


# ── ECONOMIA: MERCADO (FLUXO DE VALOR) ──
@app.route('/mundo/mercado')
def mundo_mercado():
    if 'username' not in session:
        return redirect(url_for('index'))
        
    # Placeholder para a rota do Mercado Mundo
    return "<h1>MUNDO MERCADO</h1><p>// Fluxo de Valor e Afiliações em Construção.</p><br><a href='/mundo/matrix'>Voltar à Matrix</a>"


# ════════════════════════════════════════════
# 5. DESCONEXÃO NEURAL (LOGOUT)
# ════════════════════════════════════════════
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Configuração correta para rodar localmente ou ler a porta dinâmica do Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
