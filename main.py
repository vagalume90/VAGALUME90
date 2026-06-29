import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# URL do teu Webhook do n8n para onde a Engenharia de Funil vai disparar os dados
N8N_WEBHOOK_URL = "https://vagalume90.onrender.com/webhook-test/dae66e7c-13b2-40a1-a1c7-07d49baf94d9"

# HTML DO TEU MERCADO MATRIX ORIGINAL
INTERF_MERCADO = """
<!DOCTYPE html>
<html lang="pt-AO">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Módulo Mercado // Alavanca</title>
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-matrix: #0b0f12;
            --card-matrix: #11161b;
            --neon-green: #39ff14;
            --border-green: #1f3a23;
            --text-muted: #8a9ba8;
        }

        body {
            background-color: var(--bg-matrix);
            color: #ffffff;
            font-family: 'Share Tech Mono', monospace;
            margin: 0;
            padding: 20px;
        }

        .header-title {
            color: var(--neon-green);
            font-size: 2.2rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 30px;
        }

        .nexus-panel {
            text-align: right;
            margin-bottom: 20px;
            font-size: 1.1rem;
        }
        .nexus-status { color: var(--neon-green); }

        .grid-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        @media (max-width: 768px) {
            .grid-container { grid-template-columns: 1fr; }
        }

        .card {
            background-color: var(--card-matrix);
            border: 1px solid var(--border-green);
            border-radius: 4px;
            padding: 20px;
        }

        .card h2 {
            font-size: 1.5rem;
            border-left: 4px solid var(--neon-green);
            padding-left: 10px;
            margin-top: 0;
            letter-spacing: 1px;
        }

        .input-matrix {
            width: 100%;
            background-color: #070a0d;
            border: 1px solid var(--border-green);
            color: var(--neon-green);
            padding: 12px;
            box-sizing: border-box;
            font-family: 'Share Tech Mono', monospace;
            font-size: 1rem;
            margin-bottom: 15px;
        }

        .select-matrix {
            width: 100%;
            background-color: #070a0d;
            border: 1px solid var(--border-green);
            color: #ffffff;
            padding: 12px;
            margin-bottom: 20px;
            font-family: 'Share Tech Mono', monospace;
        }

        .btn-neon {
            width: 100%;
            background-color: var(--neon-green);
            color: #000000;
            border: none;
            padding: 15px;
            font-family: 'Share Tech Mono', monospace;
            font-size: 1.2rem;
            font-weight: bold;
            cursor: pointer;
            text-transform: uppercase;
            box-shadow: 0 0 10px rgba(57, 255, 20, 0.4);
        }

        .btn-adquirir {
            background-color: transparent;
            border: 1px solid var(--neon-green);
            color: var(--neon-green);
            padding: 10px 15px;
            cursor: pointer;
            font-family: 'Share Tech Mono', monospace;
        }

        .item-produto {
            background: #070a0d;
            border: 1px dashed var(--border-green);
            padding: 15px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .nav-footer {
            margin-top: 40px;
            border-top: 1px solid var(--border-green);
            padding-top: 20px;
            color: var(--text-muted);
            font-size: 1.2rem;
        }
    </style>
</head>
<body>

    <div class="header-title">Módulo Mercado // Alavanca</div>

    <div class="nexus-panel">
        NEXUS STATUS: <span class="nexus-status">OPERADOR ALFA</span><br>
        SALDO DISPONÍVEL: <span style="color: var(--neon-green);">999649.00 KZ</span><br>
        <span style="color: var(--text-muted); font-size: 0.85rem;">SALDO PENDENTE: 0.00 KZ</span>
    </div>

    <div class="grid-container">
        
        <!-- COLUNA 1: FÁBRICA DE ATIVOS -->
        <div class="card">
            <h2>FÁBRICA DE ATIVOS // CORE IA</h2>
            <form action="/modulo/mercado/disparar" method="POST">
                <input type="text" name="tema" class="input-matrix" placeholder="// Insira o tema ou nicho do Infoproto..." required>
                
                <select name="tipo_funil" class="select-matrix">
                    <option value="ebook_funil">E-Book Estruturado + Funil de Vendas</option>
                    <option value="venda_automatica">Automação de Tráfego Direto</option>
                </select>
                
                <button type="submit" class="btn-neon">Disparar Engenharia de Funil</button>
            </form>
            
            <div style="margin-top: 30px;" class="nav-footer">
                ANUNCIAR ITEM // CIRCULAR
            </div>
        </div>

        <!-- COLUNA 2: PRODUTOS ATIVOS -->
        <div class="card">
            <h2>PRODUTOS ATIVOS NA REDE</h2>
            
            <div class="item-produto">
                <div>
                    <strong>Império Digital: AFRICA</strong><br>
                    <span style="color: var(--text-muted); font-size: 0.85rem;">CRIADOR: HASTA | VENDAS: 1</span>
                </div>
                <button class="btn-adquirir">ADQUIRIR (3500.00 KZ)</button>
            </div>

            <div class="item-produto">
                <div>
                    <strong>Império Digital: AFRICA A MIL ANOS ATRAZ</strong><br>
                    <span style="color: var(--text-muted); font-size: 0.85rem;">CRIADOR: HASTA | VENDAS: 0</span>
                </div>
                <button class="btn-adquirir">ADQUIRIR (3500.00 KZ)</button>
            </div>

            <div class="nav-footer">
                MARKETPLACE DE USADOS // CIRCULAR
            </div>
        </div>

    </div>

</body>
</html>
"""

@app.route('/modulo/mercado')
def modulo_mercado():
    # Esta rota vai abrir exatamente o ecrã das tuas fotos!
    return render_template_string(INTERF_MERCADO)

@app.route('/')
def home():
    # Redireciona ou avisa para ir à rota certa
    return "<h1>Vagalume90 Ativo</h1><p>Acede à rota correta: <a href='/modulo/mercado'>/modulo/mercado</a></p>"

@app.route('/modulo/mercado/disparar', methods=['POST'])
def disparar_funil():
    try:
        tema = request.form.get('tema')
        tipo_funil = request.form.get('tipo_funil')
        
        payload = {
            "evento": "Disparo Engenharia de Funil",
            "tema_solicitado": tema,
            "tipo_estrutura": tipo_funil,
            "operador": "ALFA"
        }
        
        # Envia diretamente ao n8n
        resposta = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
        
        if resposta.status_code == 200:
            return f'''
            <body style="background-color: #0b0f12; color: #39ff14; font-family: monospace; padding: 50px; text-align: center;">
                <h2>ENGINE DISPARADO COM SUCESSO! 🟢</h2>
                <p>O n8n já está a processar a inteligência para o tema: "{tema}"</p>
                <br><a href="/modulo/mercado" style="color: white; text-decoration: none;">[ Voltar ao Painel ]</a>
            </body>
            '''
        else:
            return f"Erro no n8n: {resposta.status_code}", 500
    except Exception as e:
        return f"Falha na conexão: {str(e)}", 500

if __name__ == '__main__':
    porta = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=porta)
