import os
import hashlib
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
from flask import Flask, render_template, request, jsonify, redirect, session
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, DuplicateKeyError
from bson import ObjectId
import re
from functools import wraps

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "vagalume90-super-secret-key-change-in-production")

# ===================== CONFIGURAÇÕES =====================
MONGO_URI = os.getenv("MONGO_URI")
FASTAPI_URL = os.getenv("FASTAPI_URL")
WHATSAPP_SUPORTE_NUMERO = os.getenv("WHATSAPP_NUMERO", "244929894589")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "VAGALUME90_ADMIN_2026")

if not MONGO_URI:
    logger.error("⚠️ ERRO CRÍTICO: A variável MONGO_URI está ausente!")
    raise ValueError("MONGO_URI é obrigatória")

# ===================== CONEXÃO MONGODB =====================
def obter_conexao_mongo(uri: str, max_tentativas: int = 5) -> MongoClient:
    for i in range(max_tentativas):
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=3000, maxPoolSize=10)
            client.server_info()
            logger.info(f"✅ Conexão com MongoDB estabelecida (tentativa {i+1})")
            return client
        except ServerSelectionTimeoutError as e:
            logger.warning(f"⚠️ Tentativa {i+1}/{max_tentativas} falhou: {e}")
            if i < max_tentativas - 1:
                time.sleep(2)
            else:
                logger.error("❌ Falha ao conectar ao MongoDB após todas as tentativas")
                raise e

try:
    client = obter_conexao_mongo(MONGO_URI)
    db = client[os.getenv("MONGO_DATABASE", "vagalume_db")]
    colecao_produtos = db["produtos"]
    colecao_compras = db["compras"]
    colecao_projetos = db["projetos"]
    colecao_ficheiros = db["ficheiros"]
    logger.info("✅ Coleções do MongoDB mapeadas com sucesso")
except Exception as e:
    logger.error(f"❌ Erro ao inicializar MongoDB: {e}")
    raise

def sanitizar_string(texto: str) -> str:
    if not texto:
        return ""
    texto = re.sub(r'[<>]', '', texto)
    texto = re.sub(r'[^\w\s\-.,!?]', '', texto)
    return texto[:200]

# ===================== ROTAS PRINCIPAIS =====================
@app.route('/')
def index():
    return redirect('/modulo/mercado')

@app.route('/mundo/matrix')
def renderizar_matrix():
    dados_contexto = {
        "rank": "OPERADOR ALFA"
    }
    return render_template('matrix.html', **dados_contexto)

@app.route('/api/ai/matrix', methods=['POST'])
def api_ai_matrix():
    dados = request.get_json(silent=True) or {}
    prompt = str(dados.get('prompt', '')).strip()

    if not prompt:
        return jsonify({
            "success": False,
            "error": "Escreve uma mensagem para a Matrix."
        }), 400

    return jsonify({
        "success": True,
        "response": f"A Matrix recebeu a tua mensagem: {prompt}"
    })

@app.route('/api/matrix/projetos', methods=['POST'])
def criar_projeto_matrix():
    dados = request.get_json(silent=True) or {}
    nome = str(dados.get('nome', '')).strip()
    descricao = str(dados.get('descricao', '')).strip()
    visibilidade = str(dados.get('visibilidade', 'privado')).strip().lower()

    if not nome:
        return jsonify({
            "success": False,
            "error": "O nome do projeto é obrigatório."
        }), 400

    if len(nome) > 100:
        return jsonify({
            "success": False,
            "error": "O nome do projeto é demasiado longo."
        }), 400

    if visibilidade not in {"publico", "privado"}:
        return jsonify({
            "success": False,
            "error": "A visibilidade deve ser publico ou privado."
        }), 400

    projeto = {
        "nome": sanitizar_string(nome),
        "descricao": sanitizar_string(descricao),
        "visibilidade": visibilidade,
        "estado": "ativo",
        "criado_em": datetime.utcnow()
    }

    resultado = colecao_projetos.insert_one(projeto)

    return jsonify({
        "success": True,
        "mensagem": "Projeto criado com sucesso.",
        "projeto_id": str(resultado.inserted_id),
        "projeto": {
            "nome": projeto["nome"],
            "descricao": projeto["descricao"],
            "visibilidade": projeto["visibilidade"],
            "estado": projeto["estado"]
        }
    }), 201

@app.route('/api/matrix/projetos', methods=['GET'])
def listar_projetos_matrix():
    projetos = []

    for projeto in colecao_projetos.find().sort("_id", -1):
        projetos.append({
            "id": str(projeto["_id"]),
            "nome": projeto.get("nome", ""),
            "descricao": projeto.get("descricao", ""),
            "visibilidade": projeto.get("visibilidade", "privado"),
            "estado": projeto.get("estado", "ativo")
        })

    return jsonify({
        "success": True,
        "total": len(projetos),
        "projetos": projetos
    })

@app.route('/api/matrix/projetos/<project_id>', methods=['GET'])
def obter_projeto_matrix(project_id):
    try:
        projeto = colecao_projetos.find_one({"_id": ObjectId(project_id)})
    except Exception:
        projeto = None

    if projeto is None:
        return jsonify({
            "success": False,
            "error": "Projeto não encontrado."
        }), 404

    return jsonify({
        "success": True,
        "projeto": {
            "id": str(projeto["_id"]),
            "nome": projeto.get("nome", ""),
            "descricao": projeto.get("descricao", ""),
            "visibilidade": projeto.get("visibilidade", "privado"),
            "estado": projeto.get("estado", "ativo"),
            "criado_em": projeto.get("criado_em").isoformat() if projeto.get("criado_em") else None
        }
    })

@app.route('/api/matrix/projetos/<project_id>/ficheiros', methods=['POST'])
def criar_ficheiro_matrix(project_id):
    try:
        projeto = colecao_projetos.find_one({"_id": ObjectId(project_id)})
    except Exception:
        projeto = None

    if projeto is None:
        return jsonify({"success": False, "error": "Projeto não encontrado."}), 404

    dados = request.get_json(silent=True) or {}
    nome = str(dados.get('nome', '')).strip()
    conteudo = str(dados.get('conteudo', ''))

    if not nome or len(nome) > 120:
        return jsonify({"success": False, "error": "Indica um nome de ficheiro válido."}), 400
    if len(conteudo.encode('utf-8')) > 100000:
        return jsonify({"success": False, "error": "O ficheiro não pode ultrapassar 100 KB nesta versão."}), 400

    nome_seguro = re.sub(r'[^A-Za-z0-9_.-]', '_', nome)
    if nome_seguro in {"", ".", ".."}:
        return jsonify({"success": False, "error": "Nome de ficheiro inválido."}), 400

    ficheiro = {
        "projeto_id": projeto["_id"],
        "nome": nome_seguro[:120],
        "conteudo": conteudo,
        "criado_em": datetime.utcnow()
    }
    resultado = colecao_ficheiros.insert_one(ficheiro)

    return jsonify({
        "success": True,
        "mensagem": "Ficheiro guardado com sucesso.",
        "ficheiro_id": str(resultado.inserted_id),
        "ficheiro": {"nome": ficheiro["nome"]}
    }), 201

@app.route('/api/matrix/projetos/<project_id>/ficheiros', methods=['GET'])
def listar_ficheiros_matrix(project_id):
    try:
        projeto = colecao_projetos.find_one({"_id": ObjectId(project_id)})
    except Exception:
        projeto = None

    if projeto is None:
        return jsonify({"success": False, "error": "Projeto não encontrado."}), 404

    ficheiros = []
    for ficheiro in colecao_ficheiros.find({"projeto_id": projeto["_id"]}).sort("_id", 1):
        ficheiros.append({
            "id": str(ficheiro["_id"]),
            "nome": ficheiro.get("nome", ""),
            "conteudo": ficheiro.get("conteudo", "")
        })

    return jsonify({"success": True, "total": len(ficheiros), "ficheiros": ficheiros})

@app.route('/api/matrix/projetos/<project_id>/ficheiros/<file_id>', methods=['PUT'])
def editar_ficheiro_matrix(project_id, file_id):
    try:
        projeto = colecao_projetos.find_one({"_id": ObjectId(project_id)})
        ficheiro = colecao_ficheiros.find_one({"_id": ObjectId(file_id), "projeto_id": ObjectId(project_id)})
    except Exception:
        projeto = None
        ficheiro = None

    if projeto is None or ficheiro is None:
        return jsonify({"success": False, "error": "Projeto ou ficheiro não encontrado."}), 404

    dados = request.get_json(silent=True) or {}
    nome = str(dados.get('nome', '')).strip()
    conteudo = str(dados.get('conteudo', ''))
    if not nome or len(nome) > 120:
        return jsonify({"success": False, "error": "Indica um nome de ficheiro válido."}), 400
    if len(conteudo.encode('utf-8')) > 100000:
        return jsonify({"success": False, "error": "O ficheiro não pode ultrapassar 100 KB nesta versão."}), 400

    nome_seguro = re.sub(r'[^A-Za-z0-9_.-]', '_', nome)
    if nome_seguro in {"", ".", ".."}:
        return jsonify({"success": False, "error": "Nome de ficheiro inválido."}), 400

    colecao_ficheiros.update_one(
        {"_id": ficheiro["_id"]},
        {"$set": {"nome": nome_seguro[:120], "conteudo": conteudo, "atualizado_em": datetime.utcnow()}}
    )
    return jsonify({"success": True, "mensagem": "Ficheiro atualizado com sucesso."})

@app.route('/api/matrix/projetos/<project_id>/ficheiros/<file_id>', methods=['DELETE'])
def apagar_ficheiro_matrix(project_id, file_id):
    try:
        resultado = colecao_ficheiros.delete_one({"_id": ObjectId(file_id), "projeto_id": ObjectId(project_id)})
    except Exception:
        resultado = None

    if resultado is None or resultado.deleted_count == 0:
        return jsonify({"success": False, "error": "Ficheiro não encontrado."}), 404

    return jsonify({"success": True, "mensagem": "Ficheiro apagado com sucesso."})

@app.route('/modulo/mercado')
def renderizar_mercado():
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        produtos_cursor = colecao_produtos.find().sort("_id", -1).skip(offset).limit(limit)
        produtos = []
        for p in produtos_cursor:
            p["_id"] = str(p["_id"])
            p["titulo"] = sanitizar_string(p.get("titulo", ""))
            p["descricao"] = sanitizar_string(p.get("descricao", ""))
            produtos.append(p)
            
        logger.info(f"✅ Renderizando mercado com {len(produtos)} produtos")
    except Exception as e:
        logger.error(f"❌ Erro ao buscar produtos: {e}")
        produtos = []

    dados_contexto = {
        "rank": "OPERADOR ALFA",
        "saldo_disponivel": 999649.00,
        "codigo_afiliado": "HASTA90",
        "produto_destaque": {
            "_id": "PROD_DESTAQUE_01",
            "titulo": "Fórmula Tráfego Angola (Acesso Vitalício)",
            "preco_sugerido": 7500.00,
            "descricao": "O mapa completo para dominar anúncios e escala digital no mercado angolano."
        },
        "produtos": produtos,
        "total_produtos": len(produtos)
    }
    return render_template('mercado.html', **dados_contexto)

@app.route('/api/mercado/comprar', methods=['POST'])
def comprar_produto():
    try:
        dados = request.get_json() or {}
        produto_id = dados.get("produto_id")
        codigo_afiliado = dados.get("afiliado_cod", "HASTA90").strip()
        
        if not produto_id:
            return jsonify({"success": False, "error": "ID do produto é obrigatório"}), 400
        
        # Cria um ID de comprador fictício baseado no IP para o ecossistema
        comprador_ficticio = f"OP_{hashlib.md5(request.remote_addr.encode()).hexdigest()[:6].upper()}"

        # 1. Tentar localizar o produto no Mongo local para validar
        if produto_id == "PROD_DESTAQUE_01":
            titulo_produto = "Fórmula Tráfego Angola (Acesso Vitalício)"
            preco_produto = 7500.00
        else:
            prod = colecao_produtos.find_one({"_id": ObjectId(produto_id) if ObjectId.is_valid(produto_id) else produto_id})
            if not prod:
                return jsonify({"success": False, "error": "Produto não encontrado no catálogo"}), 404
            titulo_produto = prod.get("titulo")
            preco_produto = prod.get("preco_sugerido")

        # 2. Guardar log local na coleção de compras do Flask
        compra_local = {
            "produto_id": produto_id,
            "produto_titulo": titulo_produto,
            "preco": preco_produto,
            "afiliado_cod": codigo_afiliado,
            "comprador_id": comprador_ficticio,
            "status": "AGUARDANDO PROVA",
            "created_at": datetime.utcnow()
        }
        colecao_compras.insert_one(compra_local)

        # 3. Disparar para o Gestor de Aquisição na FastAPI
        if FASTAPI_URL:
            try:
                url_fastapi = f"{FASTAPI_URL.rstrip('/')}/api/mercado/comprar"
                payload_fastapi = {
                    "produto_id": produto_id,
                    "comprador_id": comprador_ficticio,
                    "afiliado_cod": codigo_afiliado
                }
                resposta = requests.post(url_fastapi, json=payload_fastapi, timeout=8)
                
                if resposta.status_code == 200:
                    return jsonify(resposta.json())
            except Exception as e:
                logger.error(f"⚠️ Gestor FastAPI indisponível, usando Fallback Direct Link: {e}")

        # Fallback local caso a FastAPI falhe
        mensagem_whatsapp = f"Olá! Quero validar o meu Ativo Digital.\n\n📘 INFOPRODUTO: {titulo_produto}\n👤 OPERADOR: {comprador_ficticio}\n🎯 REF: {codigo_afiliado}"
        link_whatsapp = f"https://api.whatsapp.com/send?phone={WHATSAPP_SUPORTE_NUMERO}&text={requests.utils.quote(mensagem_whatsapp)}"
        return jsonify({
            "success": True,
            "whatsapp_url": link_whatsapp,
            "mensagem": "Encaminhado via link direto de contingência."
        })
        
    except Exception as e:
        logger.error(f"❌ Erro na rota de compra: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/mercado/gerar-infoproduto', methods=['POST'])
def gerar_infoproduto():
    try:
        dados = request.get_json() or {}
        tipo_acao = dados.get("tipo", "manual")
        
        if tipo_acao == "ia":
            tema = dados.get("tema", "").strip()
            formato = dados.get("formato", "Ebook").upper()
            preco = float(dados.get("preco", 3500))
            
            if not tema or len(tema) < 3:
                return jsonify({"success": False, "error": "Tema muito curto!"}), 400
                
            produto = {
                "titulo": f"{formato}: {sanitizar_string(tema).upper()}",
                "preco_sugerido": preco,
                "descricao": f"Infoproduto magnético do tipo [{formato}] gerado por IA focado no mercado de {sanitizar_string(tema)}.",
                "criador_id": "VAGALUME_CORE_AI",
                "download_url": "https://vagalume90.com/downloads/pack-ia",
                "tipo_geracao": "ia",
                "created_at": datetime.utcnow()
            }
        else:
            titulo = dados.get("titulo", "").strip()
            preco = float(dados.get("preco", 0))
            url = dados.get("download_url", "").strip()
            desc = dados.get("descricao", "").strip()
            
            if not titulo or not url:
                return jsonify({"success": False, "error": "Campos obrigatórios em falta!"}), 400
                
            produto = {
                "titulo": sanitizar_string(titulo),
                "preco_sugerido": preco,
                "descricao": sanitizar_string(desc) or "Sem descrição.",
                "download_url": url,
                "criador_id": "USER_HASTA_90",
                "tipo_geracao": "manual",
                "created_at": datetime.utcnow()
            }

        colecao_produtos.insert_one(produto)
        return jsonify({"success": True, "mensagem": "Produto registado com sucesso!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
