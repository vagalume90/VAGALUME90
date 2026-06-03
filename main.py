import os
from flask import Flask, render_template, request, redirect, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# Chave secreta de sessão protegida contra invasões criptográficas
app.secret_key = os.environ.get('SECRET_KEY', 'vagalume90_quantum_secret_key_secure_102026')

# =================================================================
# CONEXÃO BLINDADA - A SENHA REAL FICA APENAS NO RENDER
# =================================================================
MONGO_URI = os.environ.get(
    'MONGO_URI',
    'mongodb+srv://vagalume903_db_user:CONFIGURADO_NO_RENDER@cluster0.f8cltes.mongodb.net/vagalume90_db?retryWrites=true&w=majority&appName=Cluster0'
)

try:
    client = MongoClient(MONGO_URI)
    db = client['vagalume90_db']
    users_col = db['users']
    print("Sincronizador Quântico do MongoDB Atlas inicializado e ativo!")
except Exception as e:
    print(f"Falha crítica na fenda quântica do MongoDB: {e}")

# =================================================================
# ROTAS DO PORTAL DO ECOSSISTEMA VG90
# =================================================================
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
        return jsonify({"success": False, "message": "Dados incompletos na manifestação quântica."})

    if users_col.find_one({"$or": [{"username": username}, {"email": email}]}):
        return jsonify({"success": False, "message": "Identificador ou E-mail já materializados na rede."})

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
        
    return jsonify({"success": False, "message": "Chave neural ou Identificador incorreto."})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# =================================================================
# ROTAS DE TELETRANSPORTE HOLOGRÁFICO (OS MUNDOS)
# =================================================================
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
    
    # Injeção Automática de Dados de Telemetria Médica (Saúde Yeto do Futuro)
    dados_saude = user_profile.get('saude_yeto', {
        "status_vital": "Imortal / Estável",
        "pressao_art": "144 Hz (Harmónica)",
        "oxigenio": "100% Bioplasmático",
        "consultas": "Nenhuma anomalia celular detetada."
    })
    return render_template('ruas.html', username=session['user'], rank=session['rank'], saude=dados_saude)

if __name__ == '__main__':
    porta = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=porta, debug=True)
