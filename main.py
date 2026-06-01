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
        return redirect('/login')
    
    # Renderiza o portal passando o utilizador e o rank vindo do MongoDB
    return render_template('index.html', usuario=session['user'], rank=session['rank'])


# ROTA DE LOGIN - Firebase + MongoDB
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # O Firebase gera um "idToken" no frontend (JavaScript) após o login ter sucesso lá
        # ou podes receber o email/username e a senha para validar via API do Firebase
        id_token = request.form.get('idToken')
        email = request.form.get('email')
        username = request.form.get('username')
        
        # Fluxo A: Autenticação via Token do Firebase (Mais seguro para Frontend)
        if id_token:
            try:
                decoded_token = auth.verify_id_token(id_token)
                uid = decoded_token['uid']
                user_email = decoded_token.get('email', '')
                
                # Procurar ou criar o perfil deste utilizador no MongoDB para ler o Rank
                user_profile = users_col.find_one({"firebase_uid": uid})
                if not user_profile:
                    # Se for o primeiro login, regista-o no MongoDB como Aventuriro
                    user_profile = {
                        "firebase_uid": uid,
                        "username": username if username else user_email.split('@')[0],
                        "email": user_email,
                        "rank": "Aventuriro"
                    }
                    users_col.insert_one(user_profile)
                
                # Salva os dados na sessão do Flask
                session['user'] = user_profile['username']
                session['rank'] = user_profile.get('rank', 'Aventuriro')
                return redirect('/')
                
            except Exception as e:
                return render_template('login.html', erro=f"Erro de autenticação no Firebase: {e}")
        
        # Fluxo B: Formulário Tradicional de Teste (Caso ainda não uses Tokens no JS)
        elif email or username:
            search_query = {"email": email} if email else {"username": username}
            user_profile = users_col.find_one(search_query)
            
            if user_profile:
                session['user'] = user_profile['username']
                session['rank'] = user_profile.get('rank', 'Aventuriro')
                return redirect('/')
            
            return render_template('login.html', erro="Utilizador não encontrado no sistema.")
            
    return render_template('login.html')


# ROTA DE LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# --- ROTAS DE ACESSO AOS MUNDOS DO ECOSSISTEMA ---

@app.route('/mundo/mercado')
def mundo_mercado():
    if 'user' not in session:
        return redirect('/login')
    return render_template('mercado.html', rank=session['rank'])

@app.route('/mundo/matrix')
def mundo_matrix():
    if 'user' not in session:
        return redirect('/login')
    return render_template('matrix.html', rank=session['rank'])

@app.route('/mundo/ruas')
def mundo_ruas():
    if 'user' not in session:
        return redirect('/login')
    return render_template('ruas.html', rank=session['rank'])


if __name__ == '__main__':
    porta = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=porta, debug=True)
    
