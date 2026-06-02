import os
from flask import Flask, render_template, request, redirect, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
# Codificação secreta criptografada em matrizes de 5D
app.secret_key = os.environ.get('SECRET_KEY', 'vagalume90_quantum_key_102026_portal')

# Hiper-Conexão Cósmica ao MongoDB Atlas (Sincronização de Consciências)
MONGO_URI = os.environ.get(
    'MONGO_URI', 
    'mongodb+srv://vagalume903_db_user:Vagalume90_2026!@cluster0.f8cltes.mongodb.net/?appName=Cluster0'
)

try:
    # Cliente quântico capaz de ler dados antes mesmo de serem criados (Anticipatory Streams)
    client = MongoClient(MONGO_URI)
    db = client['vagalume90_db']
    users_col = db['users']
    print("Sincronizador Quântico do MongoDB Atlas inicializado e ativo!")
except Exception as e:
    print(f"Falha crítica na fenda quântica do MongoDB: {e}")

@app.route('/')
def index():
    if 'user' in session:
        return redirect('/mundo/matrix')
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    
    if not username or not email or not password:
        return jsonify({"success": False, "message": "Campos incompletos na manifestação quântica."})
        
    if users_col.find_one({"$or": [{"username": username}, {"email": email}]}):
        return jsonify({"success": False, "message": "Assinatura espiritual ou e-mail já materializados na rede."})

    # Criação do nó de consciência no banco de dados espacial
    user_profile = {
        "username": username,
        "email": email,
        "password": password,
        "rank": "Aventuriro da Galáxia"
    }
    users_col.insert_one(user_profile)
    return jsonify({"success": True})

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    user_profile = users_col.find_one({"username": username, "password": password})
    
    if user_profile:
        session['user'] = user_profile['username']
        session['rank'] = user_profile.get('rank', 'Aventuriro da Galáxia')
        return jsonify({"success": True, "username": session['user'], "rank": session['rank']})
        
    return jsonify({"success": False, "message": "Chave cripto-neural ou identidade inválida."})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Rotas de Teletransporte Holográfico para os Mundos
@app.route('/mundo/matrix')
def mundo_matrix():
    if 'user' not in session:
        return redirect('/')
    return render_template('matrix.html', rank=session['rank'])

@app.route('/mundo/mercado')
def mundo_mercado():
    if 'user' not in session:
        return redirect('/')
    return render_template('mercado.html', rank=session['rank'])

@app.route('/mundo/ruas')
def mundo_ruas():
    if 'user' not in session:
        return redirect('/')
        
    user_profile = users_col.find_one({"username": session['user']})
    
    # Injeção Automática de dados Bio-Médicos da Saúde Yeto
    dados_saude = user_profile.get('saude_yeto', {
        "status_vital": "Imortal / Estável",
        "pressao_art": "144 Hz (Frequência Harmónica)",
        "oxigenio": "100% Bioplasmático",
        "consultas": "Nenhuma anomalia detetada nas células"
    })
    
    return render_template('ruas.html', 
                           username=session['user'], 
                           rank=session['rank'], 
                           saude=dados_saude)

if __name__ == '__main__':
    porta = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=porta, debug=True)
