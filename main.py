import os
import time
from datetime import datetime
import requests
from flask import Flask, render_template, request, jsonify, redirect
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# =======================================================
# CONFIGURAÇÕES DE AMBIENTE (SISTEMA INTEGRADO NEON)
# =======================================================
DATABASE_URL = os.getenv("DATABASE_URL")
WHATSAPP_SUPORTE_NUMERO = os.getenv("WHATSAPP_NUMERO", "244929894589")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")

if not DATABASE_URL:
    raise ValueError("⚠️ ERRO CRÍTICO: A variável DATABASE_URL está ausente no Render!")

def obter_conexao():
    """Tenta ligar ao Neon com sistema de tentativas para mitigar o Cold Start"""
    tentativas = 5
    for i in range(tentativas):
        try:
            return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        except psycopg2.OperationalError as e:
            if i < tentativas - 1:
                print(f"⏳ [Neon Core] Banco de dados a acordar... Nova tentativa em 1.5s (Tentativa {i+1}/{tentativas})")
                time.sleep(1.5)
            else:
                raise e

def inicializar_banco():
    """Garante a infraestrutura estável no Neon PostgreSQL"""
    try:
        conn = obter_conexao()
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS perfis_utilizadores (
                id TEXT PRIMARY KEY,
                rank TEXT DEFAULT 'OPERADOR ALFA',
                saldo_disponivel NUMERIC(12, 2) DEFAULT 999649.00,
                codigo_afiliado TEXT UNIQUE
            );
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS produtos_ativos (
                id SERIAL PRIMARY KEY,
                titulo TEXT NOT NULL,
                criador TEXT NOT NULL,
                preco_sugerido NUMERIC(12, 2) NOT NULL,
                descricao TEXT,
                download_url TEXT DEFAULT '#'
            );
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transacoes_fluxo (
                id SERIAL PRIMARY KEY,
                comprador_id TEXT NOT NULL,
                produto_id TEXT NOT NULL,
                produto_titulo TEXT,
                afiliado_cod TEXT DEFAULT 'DIRETO',
                status TEXT DEFAULT 'AGUARDANDO PROVA',
                download_url TEXT DEFAULT '#',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        cur.execute("""
            INSERT INTO perfis_utilizadores (id, rank, saldo_disponivel, codigo_afiliado)
            VALUES ('USER_HASTA_90', 'OPERADOR ALFA', 999649.00, 'HASTA90')
            ON CONFLICT (id) DO NOTHING;
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("🚀 [Neon Core] Sincronização e tabelas validadas com sucesso.")
    except Exception as e:
        print(f"⚠️ Erro ao iniciar base de dados: {str(e)}")

# Inicializa o banco de dados de forma segura
inicializar_banco()

# =======================================================
# ROTAS DE INTERAÇÃO
# =======================================================

@app.route('/')
def index():
    return redirect('/modulo/mercado')

@app.route('/modulo/mercado')
def renderizar_mercado():
    id_comprador_atual = "USER_HASTA_90"
    try:
        conn = obter_conexao()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM perfis_utilizadores WHERE id = %s", (id_comprador_atual,))
        perfil = cur.fetchone()
        
        cur.execute("SELECT * FROM produtos_ativos ORDER BY id DESC")
        lista_produtos = cur.fetchall()
        
        cur.execute("""
            SELECT produto_titulo, download_url 
            FROM transacoes_fluxo 
            WHERE comprador_id = %s AND status = 'LIBERADO'
            ORDER BY id DESC
        """, (id_comprador_atual,))
        ativos_comprados = cur.fetchall()
        
        cur.close()
        conn.close()
    except Exception as e:
        # Se mesmo com o retry falhar, envia uma resposta amigável em vez de quebrar a app
        return jsonify({"code": 503, "message": "O Neon está a demorar mais tempo a responder. Atualiza a página dentro de momentos.", "details": str(e)}), 503

    produto_destaque = {
        "id": "PROD_DESTAQUE_01",
        "titulo": "Fórmula Tráfego Angola (Acesso Vitalício)",
        "preco_sugerido": 7500.00,
        "descricao": "O mapa completo para dominar anúncios e escala digital no mercado angolano."
    }

    dados_contexto = {
        "rank": perfil["rank"] if perfil else "OPERADOR ALFA",
        "saldo_disponivel": float(perfil["saldo_disponivel"]) if perfil else 999649.00,
        "codigo_afiliado": perfil["codigo_afiliado"] if perfil else "HASTA90",
        "produto_destaque": produto_destaque,
        "produtos": lista_produtos,
        "ativos_comprados": ativos_comprados
    }
    return render_template('mercado.html', **dados_contexto)
@app.route('/api/mercado/comprar', methods=['POST'])
def comprar_produto():
    try:
        dados = request.get_json() or {}
        produto_id = dados.get("produto_id")
        afiliado_cod = dados.get("afiliado_cod", "DIRETO")
        id_comprador_atual = "USER_HASTA_90"

        if not produto_id:
            return jsonify({"success": False, "error": "produto_id é obrigatório"}), 400

        FASTAPI_URL = os.getenv("FASTAPI_URL")

        if not FASTAPI_URL:
            return jsonify({"success": False, "error": "FASTAPI_URL não configurado"}), 500

        endpoint = f"{FASTAPI_URL.rstrip('/')}/api/mercado/comprar"

        payload = {
            "produto_id": produto_id,
            "comprador_id": id_comprador_atual,
            "afiliado_cod": afiliado_cod
        }

        try:
            resposta = requests.post(endpoint, json=payload, timeout=10)
            data = resposta.json()
        except Exception as e:
            return jsonify({"success": False, "error": f"Erro ao comunicar com FastAPI: {str(e)}"}), 502

        if not data.get("success"):
            return jsonify({"success": False, "error": data.get("error", "Erro no motor financeiro")}), 400

        return jsonify({
            "success": True,
            "transacao_id": data.get("transacao_id"),
            "whatsapp_url": data.get("whatsapp_url")
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

        if N8N_WEBHOOK_URL:
            try:
                requests.post(N8N_WEBHOOK_URL, json={
                    "transacao_id": transacao_id,
                    "produto": titulo_produto,
                    "comprador": id_comprador_atual,
                    "afiliado": afiliado_cod
                }, timeout=2)
            except Exception:
                pass

        mensagem_whatsapp = (
            f"Olá! Quero validar o meu Ativo Digital.\n\n"
            f"⚙️ ORDEM ID: {transacao_id}\n"
            f"📘 INFOPRODUTO: {titulo_produto}\n"
            f"👤 OPERADOR: {id_comprador_atual}"
        )
        texto_codificado = requests.utils.quote(mensagem_whatsapp)
        whatsapp_url = f"https://api.whatsapp.com/send?phone={WHATSAPP_SUPORTE_NUMERO}&text={texto_codificado}"

        return jsonify({"success": True, "whatsapp_url": whatsapp_url})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/mercado/gerar-infoproduto', methods=['POST'])
def gerar_infoproduto():
    try:
        dados = request.get_json() or {}
        tipo_acao = dados.get("tipo", "manual")
        
        conn = obter_conexao()
        cur = conn.cursor()
        
        if tipo_acao == "ia":
            tema = dados.get("tema", "Geral")
            titulo = f"Império Digital: {tema.upper()}"
            preco = 3500.00
            descricao = f"Infoproduto gerado automaticamente no nicho de {tema}."
            download_url = "https://vagalume90.com/downloads/pack-ia"
        else:
            titulo = dados.get("titulo")
            preco = dados.get("preco", 3500.00)
            download_url = dados.get("download_url", "#")
            descricao = dados.get("descricao", "Sem descrição disponível.")
            
            if not titulo:
                return jsonify({"success": False, "error": "Título em falta"}), 400

        cur.execute("""
            INSERT INTO produtos_ativos (titulo, criador, preco_sugerido, descricao, download_url)
            VALUES (%s, %s, %s, %s, %s)
        """, (titulo, "VAGALUME CORE", preco, descricao, download_url))
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=False)
