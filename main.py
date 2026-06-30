import os
import urllib.parse
from datetime import datetime
import requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# URL do teu Webhook do n8n para a Engenharia de Funil
N8N_WEBHOOK_URL = "https://vagalume90.onrender.com/webhook-test/dae66e7c-13b2-40a1-a1c7-07d49baf94d9"

# --- OBJETO DE CONEXÃO DAS TUAS BASES DE DADOS ---
# (Mantém as tuas inicializações reais aqui caso os nomes das variáveis mudem)
# Exemplo: db_mongo = MongoClient(os.getenv("MONGO_URI")).vagalume_db
# Exemplo: db_firestore = firestore.client()

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

        <div class="card">
            <h2>PRODUTOS ATIVOS NA REDE</h2>
            
            <div class="item-produto">
                <div>
                    <strong>Império Digital: AFRICA</strong><br>
                    <span style="color: var(--text-muted); font-size: 0.85rem;">CRIADOR: HASTA | VENDAS: 1</span>
                </div>
                <button class="btn-adquirir" onclick="executarCompra('PROD_AFRICA_01', 'USER_TESTE', 'DIRETO')">ADQUIRIR (3500.00 KZ)</button>
            </div>

            <div class="item-produto">
                <div>
                    <strong>Império Digital: AFRICA A MIL ANOS ATRAZ</strong><br>
                    <span style="color: var(--text-muted); font-size: 0.85rem;">CRIADOR: HASTA | VENDAS: 0</span>
                </div>
                <button class="btn-adquirir" onclick="executarCompra('PROD_AFRICA_02', 'USER_TESTE', 'DIRETO')">ADQUIRIR (3500.00 KZ)</button>
            </div>

            <div class="nav-footer">
                MARKETPLACE DE USADOS // CIRCULAR
            </div>
        </div>

    </div>

    <script>
        function executarCompra(produtoId, compradorId, afiliadoCod) {
            fetch('/api/mercado/comprar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    produto_id: produtoId,
                    comprador_id: compradorId,
                    afiliado_cod: afiliadoCod
                })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    window.location.href = data.whatsapp_url;
                } else {
                    alert('Erro na geração da ordem: ' + data.error);
                }
            })
            .catch(err => console.error('Erro de rede:', err));
        }
    </script>
</body>
</html>
"""

# --- ROTAS DE INTERFACE ---

@app.route('/modulo/mercado')
def modulo_mercado():
    return render_template_string(INTERF_MERCADO)

@app.route('/')
def home():
    return "<h1>Vagalume90 Ativo</h1><p>Acede à rota correta: <a href='/modulo/mercado'>/modulo/mercado</a></p>"


# --- ENGINE FINANCEIRO DE COMPRA (PENDENTE COMPROVATIVO) ---

@app.route('/api/mercado/comprar', methods=['POST'])
def processar_compra_real():
    try:
        dados_requisicao = request.get_json()
        produto_id = dados_requisicao.get("produto_id")
        comprador_id = dados_requisicao.get("comprador_id")
        afiliado_cod = dados_requisicao.get("afiliado_cod", "DIRETO")

        # SEGURANÇA SÉNIOR: Buscar dados e preço direto na base MongoDB para mitigar fraudes no front
        produto = db_mongo.produtos.find_one({"_id": produto_id})
        if not produto:
            return jsonify({"success": False, "error": "Ativo digital não localizado na malha."}), 404
            
        preco_total = float(produto.get("preco_sugerido", 3500.00))
        produtor_id = produto.get("criador_id", "HASTA")
        
        # Divisão de Lucros (20% Plataforma / 20% Afiliado / 60% Produtor)
        taxa_plataforma = preco_total * 0.20
        comissao_afiliado = 0.0
        ganho_produtor = preco_total * 0.80  # Fallback se for venda direta
        
        afiliado_valido = False
        id_dono_afiliado = None

        if afiliado_cod and afiliado_cod != "DIRETO":
            doc_afiliado = db_firestore.collection("afiliados").document(afiliado_cod).get()
            if doc_afiliado.exists:
                dados_afiliado = doc_afiliado.to_dict()
                id_dono_afiliado = dados_afiliado.get("utilizador_id")
                
                if id_dono_afiliado != produtor_id:
                    comissao_afiliado = preco_total * 0.20
                    ganho_produtor = preco_total * 0.60
                    afiliado_valido = True

        # Grava a transação temporária pendente
        transacao = {
            "produto_id": produto_id,
            "titulo_produto": produto.get("titulo", "Império Digital"),
            "comprador_id": comprador_id,
            "afiliado_aplicado": afiliado_cod if afiliado_valido else "DIRETO",
            "valores": {
                "total_pago": preco_total,
                "plataforma_vagalume": taxa_plataforma,
                "afiliado": comissao_afiliado,
                "produtor": ganho_produtor
            },
            "status_pagamento": "PENDENTE_COMPROVATIVO",
            "data_criacao": datetime.utcnow()
        }
        
        resultado = db_mongo.transacoes.insert_one(transacao)
        transacao_id = str(resultado.inserted_id)

        # Dispara o canal de suporte via WhatsApp para conferência manual de saldo
        msg_whatsapp = (
            f"🔥 *QUERO ADQUIRIR UM ATIVO - VAGALUME90*\n\n"
            f"🆔 *Transação:* {transacao_id}\n"
            f"📦 *Produto:* {produto.get('titulo', 'Império Digital')}\n"
            f"💰 *Preço:* {preco_total:,.2f} KZ\n"
            f"👥 *Afiliado:* {afiliado_cod if afiliado_valido else 'DIRETO'}\n\n"
            f"Por favor, envie-me os dados de pagamento (IBAN/Multicaixa) para libertar o meu acesso!"
        )
        
        texto_codificado = urllib.parse.quote(msg_whatsapp)
        whatsapp_num = os.getenv("WHATSAPP_SUPORTE_NUM", "244923000000") 
        whatsapp_url = f"https://api.whatsapp.com/send?phone={whatsapp_num}&text={texto_codificado}"
        
        return jsonify({"success": True, "transacao_id": transacao_id, "whatsapp_url": whatsapp_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --- ENGINE FINANCEIRO DE CONFIRMAÇÃO (LIQUIDAÇÃO DE WALLETS) ---

@app.route('/api/mercado/confirmar', methods=['POST'])
def confirmar_pagamento_real():
    try:
        dados_requisicao = request.get_json()
        transacao_id = dados_requisicao.get("transacao_id")
        
        transacao = db_mongo.transacoes.find_one({"_id": transacao_id})
        if not transacao:
            return jsonify({"success": False, "error": "Transação não encontrada no Ledger."}), 404
            
        if transacao.get("status_pagamento") == "CONFIRMADO":
            return jsonify({"success": True, "message": "Pagamento já foi processado anteriormente."})
            
        valores = transacao.get("valores", {})
        ganho_produtor = valores.get("produtor", 0)
        comissao_afiliado = valores.get("afiliado", 0)
        taxa_plataforma = valores.get("plataforma_vagalume", 0)
        
        produto_id = transacao.get("produto_id")
        comprador_id = transacao.get("comprador_id")
        afiliado_cod = transacao.get("afiliado_aplicado")
        
        produto = db_mongo.produtos.find_one({"_id": produto_id})
        produtor_id = produto.get("criador_id") if produto else None

        # 1. Aloca os fundos na carteira disponível do Produtor
        if produtor_id:
            db_mongo.utilizadores.update_one({"_id": produtor_id}, {"$inc": {"saldo_disponivel": ganho_produtor}})

        # 2. Aloca os fundos na carteira disponível do Afiliado
        if afiliado_cod and afiliado_cod != "DIRETO":
            doc_afiliado = db_firestore.collection("afiliados").document(afiliado_cod).get()
            if doc_afiliado.exists:
                id_dono_afiliado = doc_afiliado.to_dict().get("utilizador_id")
                if id_dono_afiliado:
                    db_mongo.utilizadores.update_one({"_id": id_dono_afiliado}, {"$inc": {"saldo_disponivel": comissao_afiliado}})

        # 3. Liberta o infoproduto para o inventário do comprador
        db_mongo.utilizadores.update_one(
            {"_id": comprador_id},
            {"$addToSet": {"ativos_comprados": {"produto_id": produto_id, "titulo": transacao.get("titulo_produto"), "data": datetime.utcnow()}}}
        )

        # 4. Grava a imutabilidade do status
        db_mongo.transacoes.update_one({"_id": transacao_id}, {"$set": {"status_pagamento": "CONFIRMADO", "data_confirmacao": datetime.utcnow()}})

        return jsonify({"success": True, "message": "Balanços liquidados com sucesso no Ledger Vagalume."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --- INTEGRAÇÃO EXISTENTE COM WEBHOOK N8N ---

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
