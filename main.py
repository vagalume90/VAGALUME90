import os
from flask import Flask, render_template, request, redirect, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'vagalume90_chave_secreta_2026')

# Conexão Direta ao MongoDB Atlas
MONGO_URI = os.environ.get(
    'MONGO_URI', 
    'mongodb+srv://vagalume903_db_user:Vagalume90_2026!@cluster0.f8cltes.mongodb.net/?appName=Cluster0'
)

try:
    client = MongoClient(MONGO_URI)
    db = client['vagalume90_db']
    users_col = db['users']
    print("MongoDB conectado com sucesso!")
except Exception as e:
    print(f"Erro de conexão MongoDB: {e}")

@app.route('/')
def index():
    if 'user' in session:
        return redirect('/mundo/ruas')
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    
    if not username or not email or not password:
        return jsonify({"success": False, "message": "Por favor, preencha todos os campos."})
        
    if users_col.find_one({"$or": [{"username": username}, {"email": email}]}):
        return jsonify({"success": False, "message": "Este utilizador ou e-mail já existe."})

    user_profile = {
        "username": username,
        "email": email,
        "password": password,
        "rank": "Aventuriro"
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
        session['rank'] = user_profile.get('rank', 'Aventuriro')
        return jsonify({"success": True, "username": session['user'], "rank": session['rank']})
        
    return jsonify({"success": False, "message": "Nome de utilizador ou senha incorretos."})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Rota Integrada das Ruas + Saúde Yeto
@app.route('/mundo/ruas')
def mundo_ruas():
    if 'user' not in session:
        return redirect('/')
        
    user_profile = users_col.find_one({"username": session['user']})
    dados_saude = user_profile.get('saude_yeto', {
        "status_vital": "Estável",
        "pressao_art": "12/8",
        "oxigenio": "98%",
        "consultas": "Nenhuma triagem agendada"
    })
    
    return render_template('ruas.html', 
                           username=session['user'], 
                           rank=session['rank'], 
                           saude=dados_saude)

if __name__ == '__main__':
    porta = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=porta, debug=True)
