import os
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Link exato do teu fluxo n8n para testes
N8N_WEBHOOK_URL = "https://vagalume90.onrender.com/webhook-test/dae66e7c-13b2-40a1-a1c7-07d49baf94d9"

# DESIGN DO MERCADO COM COMPORTAMENTO DE ABAS INTERLIGADAS
PAGINA_MERCADO = """
<!DOCTYPE html>
<html lang="pt-AO">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vagalume90 - Ecossistema Integrado</title>
    <!-- Importação das Fontes Oficiais da Marca -->
    <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Outfit:wght@400;600&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        /* Cores Oficiais da Identidade Visual Vagalume90 */
        :root {
            --preto-vaga: #07070A;
            --roxo-mistico: #3D1060;
            --ouro-africano: #F5C030;
            --rosa-olho: #E8407A;
            --ciano-tech: #00C8FF;
            --cinza-card: #0F0F16;
        }

        body {
            background-color: var(--preto-vaga);
            color: #FFFFFF;
            font-family: 'Outfit', sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }

        header {
            text-align: center;
            padding: 25px 20px 10px 20px;
            width: 100%;
            background: linear-gradient(180deg, var(--roxo-mistico) 0%, var(--preto-vaga) 100%);
        }

        header h1 {
            font-family: 'Bebas Neue', sans-serif;
            font-size: 3.5rem;
            color: var(--ouro-africano);
            margin: 0;
            letter-spacing: 2px;
        }

        /* ESTRATÉGIA DE ABAS: Menu de navegação entre os mundos */
        .abas-menu {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 15px;
            width: 100%;
            max-width: 500px;
        }

        .aba-link {
            flex: 1;
            text-align: center;
            padding: 10px 5px;
            background-color: var(--cinza-card);
            border: 1px solid var(--roxo-mistico);
            color: #FFFFFF;
            text-decoration: none;
            font-family: 'Bebas Neue', sans-serif;
            font-size: 1.1rem;
            border-radius: 6px;
            letter-spacing: 1px;
            transition: all 0.3s;
        }

        .aba-link.ativa {
            background-color: var(--roxo-mistico);
            border-color: var(--ouro-africano);
            color: var(--ouro-africano);
        }

        .container {
            width: 90%;
            max-width: 500px;
            margin: 10px auto 30px auto;
        }

        .card {
            background-color: var(--cinza-card);
            border: 2px solid var(--roxo-mistico);
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
            margin-bottom: 20px;
        }

        .card h2 {
            font-family: 'Bebas Neue', sans-serif;
            font-size: 2rem;
            color: var(--ciano-tech);
            margin-top: 0;
            letter-spacing: 1px;
        }

        .form-group {
            margin-bottom: 15px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-size: 0.9rem;
            color: #AAAAAA;
        }

        .form-group input {
            width: 100%;
            padding: 12px;
            box-sizing: border-box;
            background-color: var(--preto-vaga);
            border: 1px solid #333333;
            border-radius: 6px;
            color: #FFFFFF;
            font-family: 'Outfit', sans-serif;
            font-size: 1rem;
        }

        .form-group input:focus {
            border-color: var(--ciano-tech);
            outline: none;
        }

        .btn-enviar {
            width: 100%;
            padding: 14px;
            background-color: var(--ouro-africano);
            color: #000000;
            border: none;
            border-radius: 6px;
            font-family: 'Bebas Neue', sans-serif;
            font-size: 1.5rem;
            cursor: pointer;
            letter-spacing: 1px;
        }

        /* CAMINHO INTERLIGADO NO FUNDO DO CARD */
        .caminho-ponte {
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px dashed #333333;
            font-size: 0.9rem;
            color: #CCCCCC;
            text-align: center;
        }

        .caminho-ponte a {
            color: var(--rosa-olho);
            text-decoration: none;
            font-weight: bold;
        }

        .footer-link {
            text-align: center;
            font-size: 0.85rem;
        }

        .footer-link a {
            color: var(--ciano-tech);
            text-decoration: none;
            font-family: 'JetBrains Mono', sans-serif;
        }
    </style>
</head>
<body>

    <header>
        <h1>VAGALUME90</h1>
        <!-- ABAS QUE CONECTAM CADA MUNDO DA PLATAFORMA -->
        <div class="abas-menu">
            <a href="#" class="aba-link ativa" onclick="mudarAba('mercado')">🛒 Mercado</a>
            <a href="#" class="aba-link" onclick="mudarAba('afiliados')">👥 Afiliados</a>
            <a href="#" class="aba-link" onclick="mudarAba('automacao')">🤖 Robôs/IA</a>
        </div>
    </header>

    <div class="container">
        
        <!-- MUNDO 1: O MERCADO -->
        <div id="aba-mercado" class="card">
            <h2>Produtos Disponíveis</h2>
            <p style="font-size: 0.9rem; color: #BBBBBB; margin-bottom: 20px;">Escolhe um produto digital ou serviço para avançar na Arena.</p>
            
            <form action="/enviar-teste" method="POST">
                <div class="form-group">
                    <label for="nome">Teu Nome Completo</label>
                    <input type="text" id="nome" name="nome" placeholder="Ex: Ernesto Constantino" required>
                </div>
                <div class="form-group">
                    <label for="telefone">Teu WhatsApp</label>
                    <input type="tel" id="telefone" name="whatsapp" placeholder="Ex: 923000000" required>
                </div>
                <button type="submit" class="btn-enviar">Comprar Agora & Registar</button>
            </form>

            <!-- CAMINHO DIRETO PARA O OUTRO MUNDO -->
            <div class="caminho-ponte">
                Já compraste? <a href="#" onclick="mudarAba('afiliados')">Ir para a Aba de Afiliados para levantar comissões →</a>
            </div>
        </div>

        <!-- MUNDO 2: OS AFILIADOS -->
        <div id="aba-afiliados" class="card" style="display: none;">
            <h2>Painel de Revenda</h2>
            <p style="font-size: 0.9rem; color: #BBBBBB; margin-bottom: 20px;">Ganha dinheiro recomendando os nossos infoprodutos.</p>
            
            <div style="background: #07070A; padding: 15px; border-radius: 6px; border-left: 4px solid var(--ciano-tech); margin-bottom: 20px;">
                <span style="font-size: 0.8rem; color: #888;">TEU SALDO ATUAL:</span><br>
                <span style="font-family: 'JetBrains Mono', sans-serif; font-size: 1.8rem; color: var(--ciano-tech);">0,00 Kz</span>
            </div>

            <!-- CAMINHO DIRETO PARA OS OUTROS MUNDOS -->
            <div class="caminho-ponte">
                Precisas de produtos para vender? <a href="#" onclick="mudarAba('mercado')">Voltar ao Mercado ←</a><br><br>
                Queres automatizar os teus links? <a href="#" onclick="mudarAba('automacao')">Configurar Robôs de IA →</a>
            </div>
        </div>

        <!-- MUNDO 3: ROBÔS E INTEGRAÇÕES DE IA -->
        <div id="aba-automacao" class="card" style="display: none;">
            <h2>Central de Automação</h2>
            <p style="font-size: 0.9rem; color: #BBBBBB; margin-bottom: 20px;">Configura as conexões do teu n8n e servidores do Render aqui.</p>
            
            <p style="font-family: 'JetBrains Mono', sans-serif; font-size: 0.9rem; color: var(--rosa-olho);">Status do Webhook: CONECTADO À ARENA</p>

            <!-- CAMINHO DIRETO PARA VOLTAR -->
            <div class="caminho-ponte">
                Tudo pronto nas automações? <a href="#" onclick="mudarAba('mercado')">Ir para o Mercado Principal ↑</a>
            </div>
        </div>

        <div class="footer-link">
            <p>Infraestrutura Integrada Vagalume90 • Suporte via <a href="https://wa.me/923000000" target="_blank">WhatsApp 💬</a></p>
        </div>
    </div>

    <!-- Script simples para alternar as abas no ecrã sem recarregar a página -->
    <script>
        function mudarAba(nomeAba) {
            // Esconde todos os cards
            document.getElementById('aba-mercado').style.display = 'none';
            document.getElementById('aba-afiliados').style.display = 'none';
            document.getElementById('aba-automacao').style.display = 'none';
            
            // Remove a classe ativa de todos os botões do menu
            const links = document.querySelectorAll('.aba-link');
            links.forEach(l => l.classList.remove('ativa'));
            
            // Mostra o card selecionado e ativa o botão correspondente
            if(nomeAba === 'mercado') {
                document.getElementById('aba-mercado').style.display = 'block';
                event.currentTarget ? event.currentTarget.classList.add('ativa') : links[0].classList.add('ativa');
            } else if(nomeAba === 'afiliados') {
                document.getElementById('aba-afiliados').style.display = 'block';
                // Garante que o botão fica ativo mesmo quando clicado no link do fundo
                links[1].classList.add('ativa');
            } else if(nomeAba === 'automacao') {
                document.getElementById('aba-automacao').style.display = 'block';
                links[2].classList.add('ativa');
            }
        }
    </script>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(PAGINA_MERCADO)

@app.route('/enviar-teste', methods=['POST'])
def enviar_teste():
    try:
        dados_usuario = request.json if request.is_json else request.form.to_dict()
        if not dados_usuario:
            dados_usuario = {"teste": "Arena Vagalume90", "status": "Conectado"}
            
        print(f"[INFO] Enviando dados para o n8n: {dados_usuario}")
        
        resposta = requests.post(N8N_WEBHOOK_URL, json=dados_usuario, headers={"Content-Type": "application/json"}, timeout=10)
        
        if resposta.status_code == 200:
            return f'''
            <div style="background-color: #07070A; color: #FFFFFF; font-family: sans-serif; text-align: center; padding: 50px; min-height: 100vh;">
                <h1 style="color: #00C8FF;">Registo Efetuado com Sucesso! 🔥</h1>
                <p>Os teus dados cruzaram a ponte e chegaram ao n8n.</p>
                <br><br>
                <a href="/" style="color: #F5C030; text-decoration: none; font-weight: bold;"><- Voltar para a Arena Circular</a>
            </div>
            '''
        else:
            return jsonify({"status": "erro", "mensagem": f"Erro {resposta.status_code}", "detalhes": resposta.text}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({"status": "erro", "mensagem": f"Erro de rede: {str(e)}"}), 500

if __name__ == '__main__':
    porta = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=porta)
