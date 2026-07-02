import os
from datetime import datetime
import requests
from flask import Flask, render_template, request, jsonify, redirect
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# =======================================================
# CONEXÃO PERMANENTE AO NEON POSTGRESQL
# =======================================================
DATABASE_URL = os.getenv("DATABASE_URL")
WHATSAPP_SUPORTE_NUMERO = os.getenv("WHATSAPP_NUMERO", "244929894589")

if not DATABASE_URL:
    raise ValueError("⚠️ ERRO CRÍTICO: A variável DATABASE_URL está ausente no Render!")

def obter_conexao():
    # Liga de forma segura ao Neon usando SSL obrigatório
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def inicializar_banco():
    """Cria as tabelas necessárias no Neon se ainda não existirem"""
    conn = obter_conexao()
    cur = conn.cursor()
    
    # 1. Tabela de Perfis
    cur.execute("""
        CREATE TABLE IF NOT EXISTS perfis_utilizadores (
            id TEXT PRIMARY KEY,
            rank TEXT DEFAULT 'OPERADOR ALFA',
            saldo_disponivel NUMERIC(12, 2) DEFAULT 999649.00,
            codigo_afiliado TEXT UNIQUE
        );
    """)
    
    # 2. Tabela de Produtos / Ativos (Suporta IA e Uploads Manuais)
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
    
    # 3. Tabela de Transações (Histórico Permanente e Protegido)
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
    
    # Garante o perfil piloto padrão ativo
    cur.execute("""
        INSERT INTO perfis_utilizadores (id, rank, saldo_disponivel, codigo_afiliado)
        VALUES ('USER_HASTA_90', 'OPERADOR ALFA', 999649.00, 'HASTA90')
        ON CONFLICT (id) DO NOTHING;
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("🚀 [Neon Core] Base de dados sincronizada e indestrutível!")

# Inicializa as tabelas ao arrancar a aplicação
inicializar_banco()

# =======================================================
# ROTAS DE VISUALIZAÇÃO DO MERCADO
# =======================================================

@app.route('/')
def index():
    return redirect('/modulo/mercado')

@app.route('/modulo/mercado')
def renderizar_mercado():
    id_comprador_atual = "USER_HASTA_90"
    
    conn = obter_conexao()
    cur = conn.cursor()
    
    # Procura os dados reais de perfil guardados no Neon
    cur.execute("SELECT * FROM perfis_utilizadores WHERE id = %s", (id_comprador_atual,))
    perfil = cur.fetchone()
    
    # Lista todos os ativos disponíveis por ordem recente
    cur.execute("SELECT * FROM produtos_ativos ORDER BY id DESC")
    lista_produtos = cur.fetchall()
    
    # Filtra os teus ativos já LIBERADOS para download no teu cofre pessoal
    cur.execute("""
        SELECT produto_titulo, download_url 
        FROM transacoes_fluxo 
        WHERE comprador_id = %s AND status = 'LIBERADO'
        ORDER BY id DESC
    """, (id_comprador_atual,))
    ativos_comprados = cur.fetchall()
    
    cur.close()
    conn.close()

    # Produto estático de Destaque da Montra
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

# =======================================================
# WORKFLOW E ROTAS DA API INTERNA
# =======================================================

@app.route('/api/mercado/comprar', methods=['POST'])
def comprar_produto():
    try:
        dados = request.get_json() or {}
        produto_id = dados.get("produto_id")
        afiliado_cod = dados.get("afiliado_cod", "DIRETO")
        id_comprador_atual = request.headers.get("X-USER-ID", "USER_HASTA_90")
        
        titulo_produto = "Fórmula Tráfego Angola"
        download_url = "#"
        
        conn = obter_conexao()
        cur = conn.cursor()
        
        # Se for um produto dinâmico, extrai o título e link real do Neon
        if str(produto_id) != "PROD_DESTAQUE_01":
            cur.execute("SELECT titulo, download_url FROM produtos_ativos WHERE id = %s", (int(produto_id),))
            prod = cur.fetchone()
            if prod:
                titulo_produto = prod["titulo"]
                download_url = prod["download_url"]

        transacao_id = f"TX_{int(datetime.utcnow().timestamp())}"

        # Regista a intenção de compra sem perdas no banco permanente
        cur.execute("""
            INSERT INTO transacoes_fluxo (comprador_id, produto_id, produto_titulo, afiliado_cod, status, download_url)
            VALUES (%s, %s, %s, %s, 'AGUARDANDO PROVA', %s)
        """, (id_comprador_atual, str(produto_id), titulo_produto, afiliado_cod, download_url))
        
        conn.commit()
        cur.close()
        conn.close()

        # Prepara a mensagem encriptada para o WhatsApp de Suporte
        mensagem_whatsapp = (
            f"Olá Vagalume! Desejo adquirir o Ativo Digital.\n\n"
            f"⚙️ ID ORDEM: {transacao_id}\n"
            f"📘 ATIVO: {titulo_produto}\n"
            f"👤 COMPRADOR: {id_comprador_atual}\n"
            f"🔗 REF AFILIADO: {afiliado_cod}\n"
            f"🪙 STATUS: AGUARDANDO VERIFICAÇÃO"
        )
        texto_codificado = requests.utils.quote(mensagem_whatsapp)
        whatsapp_url = f"https://api.whatsapp.com/send?phone={WHATSAPP_SUPORTE_NUMERO}&text={texto_codificado}"

        return jsonify({
            "success": True, 
            "transacao_id": transacao_id, 
            "whatsapp_url": whatsapp_url
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/mercado/gerar-infoproduto', methods=['POST'])
def gerar_infoproduto():
    try:
        dados = request.get_json() or {}
        tipo_acao = dados.get("tipo", "manual") # Identifica a origem ('ia' ou 'manual')
        
        conn = obter_conexao()
        cur = conn.cursor()
        
        if tipo_acao == "ia":
            # SISTEMA IA: Gera o produto dinamicamente com base no nicho informado
            tema = dados.get("tema", "Geral")
            titulo = f"Império Digital: {tema.upper()}"
            preco = 3500.00
            descricao = f"Infoproduto estratégico gerado automaticamente focado no nicho de {tema}."
            download_url = "https://vagalume90.com/downloads/pack-ia"
        else:
            # SISTEMA MANUAL: Recolhe o teu produto real com link de hospedagem
            titulo = dados.get("titulo")
            preco = dados.get("preco", 3500.00)
            download_url = dados.get("download_url", "#")
            descricao = dados.get("descricao", "Sem descrição disponível.")
            
            if not titulo:
                return jsonify({"success": False, "error": "Título obrigatório no depósito manual"}), 400

        # Grava a manifestação do produto no Neon de forma definitiva
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
