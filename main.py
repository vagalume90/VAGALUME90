import os
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Configuração da Arena: Link de Teste do teu n8n
N8N_WEBHOOK_URL = "https://vagalume90.onrender.com/webhook-test/dae66e7c-13b2-40a1-a1c7-07d49baf94d9"

@app.route('/')
def home():
    return "<h1>Vagalume90 - Arena de Testes Online!</h1><p>O site está a rodar perfeitamente no Render.</p>"

@app.route('/enviar-teste', methods=['POST'])
def enviar_teste():
    try:
        # Pega os dados enviados pelo utilizador no site
        dados_usuario = request.json if request.is_json else request.form.to_dict()
        
        if not dados_usuario:
            return jsonify({"status": "erro", "mensagem": "Nenhum dado enviado"}), 400
            
        print(f"[INFO] A enviar dados para o n8n: {dados_usuario}")
        
        # Dispara os dados para o teu novo caminho de testes do n8n
        resposta = requests.post(
            N8N_WEBHOOK_URL, 
            json=dados_usuario, 
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        # Verifica se o n8n recebeu com sucesso
        if resposta.status_code == 200:
            return jsonify({
                "status": "sucesso", 
                "mensagem": "Dados enviados para o n8n com sucesso!",
                "n8n_resposta": resposta.text
            }), 200
        else:
            return jsonify({
                "status": "erro", 
                "mensagem": f"O n8n respondeu com erro {resposta.status_code}",
                "detalhes": resposta.text
            }), 500

    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao ligar ao n8n: {str(e)}")
        return jsonify({"status": "erro", "mensagem": f"Erro de rede ao ligar ao n8n: {str(e)}"}), 500

if __name__ == '__main__':
    # Porta padrão que o Render utiliza
    porta = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=porta)
