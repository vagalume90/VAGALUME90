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
    # Conecta ao Neon usando SSL obrigatório para segurança
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def inicializar_banco():
    """Cria as tabelas estruturadas no Neon se elas ainda não existirem"""
    conn = obter_conexao()
    cur = conn.cursor()
    
    # 1. Tabela de Utilizadores / Pilotos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS perfis_utilizadores (
            id TEXT PRIMARY KEY,
            rank TEXT DEFAULT 'OPERADOR ALFA',
            saldo_disponivel NUMERIC(12, 2) DEFAULT 999649.00,
            codigo_afiliado TEXT UNIQUE
        );
    """)
    
    # 2. Tabela de Produtos / Ativos na Rede
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
    
    # 3. Tabela de Transações (Histórico do Fluxo que o Neon protege)
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
    
    # Garante que o teu perfil padrão existe na base de dados
    cur.execute("""
        INSERT INTO perfis_utilizadores (id, rank, saldo_disponivel, codigo_afiliado)
        VALUES ('USER_HASTA_90', 'OPERADOR ALFA', 999649.00, 'HASTA90')
        ON CONFLICT (id) DO NOTHING;
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("🚀 [Neon Core] Banco de dados verificado e pronto!")

# Inicializa o banco de dados do Neon ao arrancar o servidor
inicializar_banco()

# =======================================================
# ROTAS DE RENDERIZAÇÃO DO PORTAL
# =======================================================

@app.route('/')
def index():
    return redirect('/modulo/mercado')

@app.route('/modulo/mercado')
def renderizar_mercado():
    id_comprador_atual = "USER_HASTA_90"
    
    conn = obter_conexao()
    cur = conn.cursor()
    
    # Buscar os dados reais do teu utilizador salvos no Neon
    cur.execute("SELECT * FROM perfis_utilizadores WHERE id = %s", (id_comprador_atual,))
    perfil = cur.fetchone()
    
    # Buscar todos os infoprodutos cadastrados na rede
    cur.execute("SELECT * FROM produtos_ativos ORDER BY id DESC")
    lista_produtos = cur.fetchall()
    
    # Buscar os ativos que já foram LIBERADOS no teu cofre histórico
    cur.execute("""
        SELECT produto_titulo, download_url 
        FROM transacoes_fluxo 
        WHERE comprador_id = %s AND status = 'LIBERADO'
        ORDER BY id DESC
    """, (id_comprador_atual,))
    ativos_comprados = cur.fetchall()
    
    cur.close()
    conn.close()

    # Produto principal da montra (Estático por segurança de interface)
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
# API INTERNA: PROCESSAMENTO LOCAL E LOG NO NEON
# =======================================================

@app.route('/api/mercado/comprar', methods=['POST'])
def comprar_produto():
    try:
        dados = request.get_json() or {}
        produto_id = dados.get("produto_id")
        afiliado_cod = dados.get("afiliado_cod", "DIRETO")
        id_comprador_atual = request.headers.get("X-USER-ID", "USER_HASTA_90")
        
        print(f"📡 Ordem processada localmente -> Produto: {produto_id} | Comprador: {id_comprador_atual}")
        
        titulo_produto = "Fórmula Tráfego Angola"
        download_url = "#"
        
        conn = obter_conexao()
        cur = conn.cursor()
        
        # Se for um produto da lista dinâmica, busca os dados reais dele no Neon
        if produto_id != "PROD_DESTAQUE_01":
            cur.execute("SELECT titulo, download_url FROM produtos_ativos WHERE id = %s", (int(produto_id),))
            prod = cur.fetchone()
            if prod:
                titulo_produto = prod["titulo"]
                download_url = prod["download_url"]

        # Cria uma ID única para a transação baseada no timestamp
        transacao_id = f"TX_{int(datetime.utcnow().timestamp())}"

        # Grava o histórico do clique de forma permanente no teu Neon
        cur.execute("""
            INSERT INTO transacoes_fluxo (comprador_id, produto_id, produto_titulo, afiliado_cod, status, download_url)
            VALUES (%s, %s, %s, %s, 'AGUARDANDO PROVA', %s)
        """, (id_comprador_atual, str(produto_id), titulo_produto, afiliado_cod, download_url))
        
        conn.commit()
        cur.close()
        conn.close()

        # Constrói a mensagem direta do WhatsApp
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

        print(f"✅ Sucesso! Redirecionamento gerado para o WhatsApp.")
        return jsonify({
            "success": True, 
            "transacao_id": transacao_id, 
            "whatsapp_url": whatsapp_url
        })

    except Exception as e:
        print(f"❌ Erro crítico no fluxo de compra: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/mercado/gerar-infoproduto', methods=['POST'])
def gerar_infoproduto():
    try:
        dados = request.get_json() or {}
        tema = dados.get("tema", "Geral")
        
        conn = obter_conexao()
        cur = conn.cursor()
        
        # Insere um infoproduto novo diretamente nas tabelas estáveis do Neon
        cur.execute("""
            INSERT INTO produtos_ativos (titulo, criador, preco_sugerido, descricao, download_url)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            f"Império Digital: {tema.upper()}", 
            "CORE IA / HASTA", 
            3500.00, 
            f"Infoproduto gerado focado no nicho de {tema}.", 
            "https://vagalume90.com/downloads/pack"
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=False)
