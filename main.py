import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Link exato do teu fluxo n8n para testes
N8N_WEBHOOK_URL = "https://vagalume90.onrender.com/webhook-test/dae66e7c-13b2-40a1-a1c7-07d49baf94d9"

@app.route('/')
def home():
    return "<h1>Vagalume90 - Sistema Ativo</h1><p>A Arena de testes está ligada e pronta para enviar dados para o n8n!</p>"

@app.route('/enviar-teste', methods=['POST'])
def enviar_teste():
    try:
        # Captura os dados que o utilizador enviar (seja em JSON ou formulário)
        dados_usuario = request.json if request.is_json else request.form.to_dict()
        
        if not dados_usuario:
            # Envia um dado padrão de teste caso vá vazio, só para o n8n receber algo
            dados_usuario = {"teste": "Arena Vagalume90", "status": "Conectado"}
            
        print(f"[INFO] Enviando dados para o n8n: {dados_usuario}")
        
        # Envia os dados diretamente para o teu webhook do n8n
        resposta = requests.post(
            N8N_WEBHOOK_URL, 
            json=dados_usuario, 
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        # Retorna o resultado para o ecrã
        if resposta.status_code == 200:
            return jsonify({
                "status": "sucesso", 
                "mensagem": "O n8n recebeu os teus dados com sucesso!",
                "resposta_do_n8n": resposta.text
            }), 200
        else:
            return jsonify({
                "status": "erro", 
                "mensagem": f"O n8n respondeu com o código de erro {resposta.status_code}",
                "detalhes": resposta.text
            }), 500

    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha de rede: {str(e)}")
        return jsonify({"status": "erro", "mensagem": f"Erro ao conectar ao n8n: {str(e)}"}), 500

if __name__ == '__main__':
    # Configuração de porta automática para o Render
    porta = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=porta)
