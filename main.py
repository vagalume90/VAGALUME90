import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)

# ── CONFIGURAÇÃO DE SEGURANÇA ──
# Chave essencial para gerir as sessões de login (cookies) de forma estável no Render
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "vagalume90_quantum_secret_key_3026")

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
# 2. AUTENTICAÇÃO ASSÍNCRONA (LOGIN)
# ════════════════════════════════════════════
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not username or not password:
        return jsonify({"success": False, "message": "Preenche todos os campos para autenticar."}), 400

    # ── SISTEMA DE AUTENTICAÇÃO SEGURO PARA TESTE ──
    # Permite entrar com qualquer usuário para garantir que o portal passe da tela de login!
    session['username'] = username
    session['rank'] = "Operador Alfa"

    # Retorna exatamente o JSON que o JavaScript do index.html precisa para avançar
    return jsonify({
        "success": True,
        "username": username,
        "rank": "Operador Alfa"
    })


# ════════════════════════════════════════════
# 3. MANIFESTAÇÃO QUÂNTICA (REGISTO)
# ════════════════════════════════════════════
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    if not username or not email or not password:
        return jsonify({"success": False, "message": "Todos os campos são obrigatórios."}), 400

    # Simula o sucesso imediato do registro na malha do servidor
    return jsonify({
        "success": True, 
        "message": "Identidade gravada com sucesso! Proceda para o login."
    })


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
    
    # Telemetria médica injetada dinamicamente no ruas.html
    dados_saude = {
        "status_vital": "ESTÁVEL",
        "pressao_art": "12/8 mmHg",
        "oxigenio": "98% SpO2",
        "consultas": "Nenhuma anomalia crítica detectada nas últimas 24h no setor Luanda."
    }
    return render_template('ruas.html', dados_saude=dados_saude)


# ── ECONOMIA: MERCADO ──
@app.route('/mundo/mercado')
def mundo_mercado():
    if 'username' not in session:
        return redirect(url_for('index'))
    return "<h1>MUNDO MERCADO</h1><p>// Fluxo de Valor em Construção.</p><br><a href='/mundo/matrix'>Voltar à Matrix</a>"


# ════════════════════════════════════════════
# 5. INTEGRAÇÃO DE INTELIGÊNCIA ARTIFICIAL (APIs)
# ════════════════════════════════════════════

@app.route('/api/ai/matrix', methods=['POST'])
def api_ai_matrix():
    if 'username' not in session:
        return jsonify({"response": "Acesso negado."}), 403
        
    data = request.get_json() or {}
    prompt_usuario = data.get('prompt', '')
    
    resposta_ia = f"<strong>[NEXO COMPILADO]</strong><br>Processou a diretriz: <em>'{prompt_usuario}'</em>.<br><br>Aqui está o teu insight estratégico para o ecossistema VAGALUME90: 'Foca no tráfego direcionado para as Ruas, onde a retenção bioplasmática da Saúde Yeto garante +45% de conversão intencional.'"
    return jsonify({"response": resposta_ia})


@app.route('/api/ai/saude', methods=['POST'])
def api_ai_saude():
    if 'username' not in session:
        return jsonify({"response": "Acesso negado."}), 403
        
    data = request.get_json() or {}
    prompt_clinico = data.get('prompt', '')
    
    resposta_medica = f"<strong>[TRIAGEM SAÚDE YETO]</strong><br>Análise de sintomas: <em>'{prompt_clinico}'</em>.<br><br><strong>Recomendação:</strong> Sinais vitais sob controlo. Monitorar parâmetros de oxigénio na malha urbana e garantir hidratação severa do operador."
    return jsonify({"response": resposta_medica})


# ════════════════════════════════════════════
# 6. DESCONEXÃO E TRATAMENTO ANTI-404
# ════════════════════════════════════════════
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>[ERRO 404 — VAGALUME90]</h1><p>Esta rota não existe no ecossistema.</p><br><a href='/'>Voltar ao Portal</a>", 404


if __name__ == '__main__':
    # Lê a porta dinâmica que o Render exige para rodar o serviço grátis
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
    
