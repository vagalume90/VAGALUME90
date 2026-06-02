import os
from flask import Flask, render_template, request, redirect, session, jsonify
from pymongo import MongoClient
import firebase_admin
from firebase_admin import credentials, auth

app = Flask(__name__)

# Chave secreta para gerir as sessões dos utilizadores
app.secret_key = os.environ.get('SECRET_KEY', 'vagalume90_secret_key_2026_portal')

# 1. INICIALIZAÇÃO DO FIREBASE (Autenticação)
try:
    # Se já estiver inicializado (evita erros em reloads), usa a app existente
    if not firebase_admin._apps:
        # Tenta carregar o arquivo de credenciais local ou do Render
        cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH', 'firebase-sdk.json')
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            # Caso não encontre o arquivo, inicializa com as credenciais padrão do ambiente
            firebase_admin.initialize_app()
    print("Firebase Authentication inicializado com sucesso!")
except Exception as e:
    print(f"Aviso ao inicializar Firebase: {e}. Certifica-te de que o Firebase está configurado.")

# 2. LIGAÇÃO AO MONGODB ATLAS (Ranks e Dados do Ecossistema)
MONGO_URI = os.environ.get(
    'MONGO_URI', 
    'mongodb+srv://vagalume903_db_user:Vagalume90_2026!@cluster0.f8cltes.mongodb.net/?appName=Cluster0'
)

try:
    client = MongoClient(MONGO_URI)
    db = client['vagalume90_db']  # Nome da tua base de dados
    users_col = db['users']       # Coleção de perfis e ranks
    print("Conexão ao MongoDB Atlas estabelecida com sucesso!")
except Exception as e:
    print(f"Erro ao conectar ao MongoDB Atlas: {e}")


# --- ROTAS DO SISTEMA ---

# ROTA PRINCIPAL (INDEX) - O Portal dos Mundos
@app.route('/')
def index():
    if 'user' not in session:
        # Se não estiver logado, exibe o ecrã do Gatekeeper diretamente para fazer login/registro
        return render_template('index.html')
    
    # Se já estiver logado, mantém no portal injetando as variáveis do operador
    return render_template('index.html', usuario=session['user'], rank=session['rank'])


# ROTA DE INSCRIÇÃO / REGISTO (Criação de Nó operador no MongoDB)
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not username or not email or not password:
        return jsonify({"success": False, "message": "Preenche todos os campos da sinapse."}), 400
        
    # Verificar se o utilizador ou email já existem na base de dados
    if users_col.find_one({"$or": [{"username": username}, {"email": email}]}):
        return jsonify({"success": False, "message": "Operador ou Sinapse já manifestados no sistema."}), 400

    # Criar o perfil no MongoDB com o Rank Inicial de Aventuriro
    user_profile = {
        "username": username,
        "email": email,
        "password": password, # Chave neural de acesso
        "rank": "Aventuriro"
    }
    users_col.insert_one(user_profile)
    return jsonify({"success": True, "message": "Nódua manifestada com sucesso!"})


# ROTA DE LOGIN - Autenticação Tradicional Directa no MongoDB
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return jsonify({"success": False, "message": "Identificador e chave requeridos."}), 400

    # Procura pelo Identificador (Username) e valida a senha correspondente
    user_profile = users_col.find_one({"username": username, "password": password})
    
    if user_profile:
        session['user'] = user_profile['username']
        session['rank'] = user_profile.get('rank', 'Aventuriro')
        return jsonify({"success": True, "rank": session['rank'], "username": session['user']})
        
    return jsonify({"success": False, "message": "Chave neural ou Operador inválido."}), 401


# ROTA DE LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# --- ROTAS DE ACESSO AOS MUNDOS DO ECOSSISTEMA ---

@app.route('/mundo/mercado')
def mundo_mercado():
    if 'user' not in session:
        return redirect('/')
    return render_template('mercado.html', rank=session['rank'])

@app.route('/mundo/matrix')
def mundo_matrix():
    if 'user' not in session:
        return redirect('/')
    return render_template('matrix.html', rank=session['rank'])

@app.route('/mundo/ruas')
def mundo_ruas():
    if 'user' not in session:
        return redirect('/')
    return render_template('ruas.html', rank=session['rank'])


if __name__ == '__main__':
    porta = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=porta, debug=True)
