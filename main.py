import os
import hashlib
import subprocess
import shutil
import tempfile
import secrets
import hashlib
import smtplib
from email.message import EmailMessage
from pathlib import Path
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from flask import Flask, render_template, request, jsonify, redirect, session, url_for
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, DuplicateKeyError
from bson import ObjectId
import re
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

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
    colecao_repositorios = db["repositorios"]
    colecao_utilizadores = db["utilizadores"]
    colecao_tokens_password = db["tokens_password"]
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

# ===================== AUTENTICAÇÃO E PERMISSÕES =====================
def utilizador_atual():
    utilizador_id = session.get("utilizador_id")
    if not utilizador_id:
        return None
    try:
        return colecao_utilizadores.find_one({"_id": ObjectId(utilizador_id)})
    except Exception:
        return None

def login_obrigatorio(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if utilizador_atual() is None:
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "Inicia sessão para continuar."}), 401
            return redirect(url_for("pagina_login"))
        return view(*args, **kwargs)
    return wrapped

def projeto_pode_ser_lido(projeto):
    if projeto.get("visibilidade", "privado") == "publico":
        return True
    utilizador = utilizador_atual()
    return utilizador is not None and projeto.get("proprietario_id") == utilizador["_id"]

def projeto_pode_ser_gerido(projeto):
    utilizador = utilizador_atual()
    return utilizador is not None and projeto.get("proprietario_id") == utilizador["_id"]

def projeto_id_a_objectid(valor):
    try:
        return ObjectId(valor)
    except Exception:
        return None

def exigir_leitura(projeto):
    if projeto is None:
        return jsonify({"success": False, "error": "Projeto não encontrado."}), 404
    if not projeto_pode_ser_lido(projeto):
        return jsonify({"success": False, "error": "Este projeto é privado."}), 403
    return None

def exigir_gestao(projeto):
    if projeto is None:
        return jsonify({"success": False, "error": "Projeto não encontrado."}), 404
    if not projeto_pode_ser_gerido(projeto):
        return jsonify({"success": False, "error": "Não tens permissão para alterar este projeto."}), 403
    return None

@app.route('/registo', methods=['GET', 'POST'])
def pagina_registo():
    if request.method == 'GET':
        return render_template('auth.html', modo='registo')
    dados = request.get_json(silent=True) or request.form
    nome = str(dados.get('nome', '')).strip()
    email = str(dados.get('email', '')).strip().lower()
    password = str(dados.get('password', ''))
    if len(nome) < 2 or len(nome) > 80:
        return jsonify({"success": False, "error": "O nome deve ter entre 2 e 80 caracteres."}), 400
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return jsonify({"success": False, "error": "Indica um email válido."}), 400
    if len(password) < 8:
        return jsonify({"success": False, "error": "A palavra-passe deve ter pelo menos 8 caracteres."}), 400
    if colecao_utilizadores.find_one({"email": email}):
        return jsonify({"success": False, "error": "Este email já está registado."}), 409
    utilizador = {"nome": sanitizar_string(nome), "email": email, "password_hash": generate_password_hash(password), "criado_em": datetime.utcnow()}
    resultado = colecao_utilizadores.insert_one(utilizador)
    session["utilizador_id"] = str(resultado.inserted_id)
    return jsonify({"success": True, "mensagem": "Conta criada com sucesso."}), 201

@app.route('/login', methods=['GET', 'POST'])
def pagina_login():
    if request.method == 'GET':
        return render_template('auth.html', modo='login')
    dados = request.get_json(silent=True) or request.form
    email = str(dados.get('email', '')).strip().lower()
    password = str(dados.get('password', ''))
    utilizador = colecao_utilizadores.find_one({"email": email})
    if utilizador is None or not check_password_hash(utilizador.get("password_hash", ""), password):
        return jsonify({"success": False, "error": "Email ou palavra-passe incorretos."}), 401
    session.clear()
    session["utilizador_id"] = str(utilizador["_id"])
    return jsonify({"success": True, "mensagem": "Sessão iniciada.", "utilizador": {"nome": utilizador.get("nome", ""), "email": utilizador.get("email", "")}})

@app.route('/alterar-password', methods=['GET', 'POST'])
@login_obrigatorio
def alterar_password():
    utilizador = utilizador_atual()
    if request.method == 'GET':
        return render_template('password.html', utilizador=utilizador)

    dados = request.get_json(silent=True) or request.form
    password_atual = str(dados.get('password_atual', ''))
    password_nova = str(dados.get('password_nova', ''))
    password_confirmacao = str(dados.get('password_confirmacao', ''))

    if not check_password_hash(utilizador.get('password_hash', ''), password_atual):
        return jsonify({"success": False, "error": "A palavra-passe atual está incorreta."}), 400
    if len(password_nova) < 8:
        return jsonify({"success": False, "error": "A nova palavra-passe deve ter pelo menos 8 caracteres."}), 400
    if password_nova != password_confirmacao:
        return jsonify({"success": False, "error": "As palavras-passe novas não coincidem."}), 400
    if password_nova == password_atual:
        return jsonify({"success": False, "error": "A nova palavra-passe deve ser diferente."}), 400

    colecao_utilizadores.update_one(
        {"_id": utilizador["_id"]},
        {"$set": {"password_hash": generate_password_hash(password_nova), "password_atualizada_em": datetime.utcnow()}}
    )
    return jsonify({"success": True, "mensagem": "Palavra-passe alterada com sucesso."})

def enviar_email_recuperacao(destinatario, url):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    remetente = os.getenv("SMTP_FROM", smtp_user or "no-reply@vagalume90.local")
    if not all([smtp_host, smtp_user, smtp_password]):
        logger.warning("SMTP não configurado. Link local de recuperação: %s", url)
        return False
    mensagem = EmailMessage()
    mensagem["Subject"] = "Recuperação da palavra-passe — VAGALUME90"
    mensagem["From"] = remetente
    mensagem["To"] = destinatario
    mensagem.set_content(f"Abre este link nos próximos 30 minutos para redefinir a palavra-passe:\n\n{url}\n\nSe não foste tu, ignora este email.")
    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as servidor:
        servidor.starttls()
        servidor.login(smtp_user, smtp_password)
        servidor.send_message(mensagem)
    return True

@app.route('/esqueci-password', methods=['GET', 'POST'])
def pedir_recuperacao_password():
    if request.method == 'GET':
        return render_template('password_recovery.html', modo='pedido')
    dados = request.get_json(silent=True) or request.form
    email = str(dados.get('email', '')).strip().lower()
    utilizador = colecao_utilizadores.find_one({"email": email})
    # Resposta igual para email existente ou inexistente, evitando descoberta de contas.
    resposta = {"success": True, "mensagem": "Se o email existir, receberás instruções de recuperação."}
    if utilizador is None:
        return jsonify(resposta)
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    colecao_tokens_password.delete_many({"utilizador_id": utilizador["_id"], "usado": False})
    colecao_tokens_password.insert_one({
        "utilizador_id": utilizador["_id"],
        "token_hash": token_hash,
        "usado": False,
        "criado_em": datetime.utcnow(),
        "expira_em": datetime.utcnow() + timedelta(minutes=30)
    })
    base_url = os.getenv("APP_BASE_URL", "http://127.0.0.1:5000")
    link = f"{base_url.rstrip('/')}/redefinir-password/{token}"
    try:
        enviar_email_recuperacao(email, link)
    except Exception as erro:
        logger.error("Falha no envio do email de recuperação: %s", erro)
    return jsonify(resposta)

@app.route('/redefinir-password/<token>', methods=['GET', 'POST'])
def redefinir_password(token):
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    registro = colecao_tokens_password.find_one({
        "token_hash": token_hash,
        "usado": False,
        "expira_em": {"$gt": datetime.utcnow()}
    })
    if registro is None:
        if request.method == 'GET':
            return "Link inválido ou expirado.", 400
        return jsonify({"success": False, "error": "Link inválido ou expirado."}), 400
    if request.method == 'GET':
        return render_template('password_recovery.html', modo='redefinir', token=token)
    dados = request.get_json(silent=True) or request.form
    nova = str(dados.get('password_nova', ''))
    confirmacao = str(dados.get('password_confirmacao', ''))
    if len(nova) < 8:
        return jsonify({"success": False, "error": "A palavra-passe deve ter pelo menos 8 caracteres."}), 400
    if nova != confirmacao:
        return jsonify({"success": False, "error": "As palavras-passe não coincidem."}), 400
    colecao_utilizadores.update_one({"_id": registro["utilizador_id"]}, {"$set": {"password_hash": generate_password_hash(nova), "password_atualizada_em": datetime.utcnow()}})
    colecao_tokens_password.update_one({"_id": registro["_id"]}, {"$set": {"usado": True, "usado_em": datetime.utcnow()}})
    return jsonify({"success": True, "mensagem": "Palavra-passe redefinida com sucesso."})

@app.route('/logout', methods=['GET', 'POST'])
def terminar_sessao():
    session.clear()
    if request.path.startswith('/api/'):
        return jsonify({"success": True, "mensagem": "Sessão terminada."})
    return redirect(url_for('pagina_login'))

@app.route('/api/auth/me', methods=['GET'])
def estado_sessao():
    utilizador = utilizador_atual()
    if utilizador is None:
        return jsonify({"success": True, "autenticado": False, "utilizador": None})
    return jsonify({"success": True, "autenticado": True, "utilizador": {"id": str(utilizador["_id"]), "nome": utilizador.get("nome", ""), "email": utilizador.get("email", "")}})

# ===================== ROTAS PRINCIPAIS =====================
@app.route('/')
def index():
    return redirect('/modulo/mercado')

@app.route('/mundo/matrix/projeto/<project_id>')
def pagina_publica_projeto_matrix(project_id):
    try:
        projeto = colecao_projetos.find_one({"_id": ObjectId(project_id)})
    except Exception:
        projeto = None
    if projeto is None or projeto.get("estado") == "apagado":
        return "Projeto não encontrado.", 404
    if projeto.get("visibilidade", "privado") != "publico":
        utilizador = utilizador_atual()
        if utilizador is None or projeto.get("proprietario_id") != utilizador["_id"]:
            return "Este projeto é privado.", 403
    return render_template("project_public.html", project_id=str(projeto["_id"]), projeto=projeto)

@app.route('/mundo/matrix')
def renderizar_matrix():
    utilizador = utilizador_atual()
    dados_contexto = {
        "rank": "OPERADOR ALFA",
        "utilizador": utilizador
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

def criar_ficheiros_iniciais(projeto):
    existentes = {f.get("nome") for f in colecao_ficheiros.find({"projeto_id": projeto["_id"]}, {"nome": 1})}
    iniciais = {
        "README.md": f"# {projeto.get('nome', 'Projeto Matrix')}\n\n{projeto.get('descricao') or 'Projeto criado na Matrix da VAGALUME90.'}\n",
        ".gitignore": "# Ficheiros locais\n.env\n.venv/\n__pycache__/\n"
    }
    criados = []
    for nome, conteudo in iniciais.items():
        if nome in existentes:
            continue
        colecao_ficheiros.insert_one({
            "projeto_id": projeto["_id"],
            "nome": nome,
            "conteudo": conteudo,
            "criado_em": datetime.utcnow()
        })
        criados.append(nome)
    return criados

@app.route('/api/matrix/projetos', methods=['POST'])
@login_obrigatorio
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

    utilizador = utilizador_atual()
    projeto = {
        "proprietario_id": utilizador["_id"],
        "nome": sanitizar_string(nome),
        "descricao": sanitizar_string(descricao),
        "visibilidade": visibilidade,
        "estado": "ativo",
        "criado_em": datetime.utcnow()
    }

    resultado = colecao_projetos.insert_one(projeto)
    projeto["_id"] = resultado.inserted_id
    ficheiros_iniciais = criar_ficheiros_iniciais(projeto)

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
    pesquisa = str(request.args.get("q", "")).strip().lower()[:100]
    visibilidade_filtro = str(request.args.get("visibilidade", "todos")).strip().lower()
    estado_filtro = str(request.args.get("estado", "ativo")).strip().lower()
    if visibilidade_filtro not in {"todos", "publico", "privado"}:
        return jsonify({"success": False, "error": "Filtro de visibilidade inválido."}), 400
    if estado_filtro not in {"todos", "ativo"}:
        return jsonify({"success": False, "error": "Filtro de estado inválido."}), 400

    filtro_mongo = {}
    if estado_filtro != "todos":
        filtro_mongo["estado"] = estado_filtro
    else:
        filtro_mongo["estado"] = {"$ne": "apagado"}
    if visibilidade_filtro != "todos":
        filtro_mongo["visibilidade"] = visibilidade_filtro

    projetos = []
    for projeto in colecao_projetos.find(filtro_mongo).sort("_id", -1):
        if not projeto_pode_ser_lido(projeto):
            continue
        nome = projeto.get("nome", "")
        descricao = projeto.get("descricao", "")
        if pesquisa and pesquisa not in f"{nome} {descricao}".lower():
            continue
        projetos.append({
            "id": str(projeto["_id"]),
            "nome": nome,
            "descricao": descricao,
            "visibilidade": projeto.get("visibilidade", "privado"),
            "estado": projeto.get("estado", "ativo")
        })

    return jsonify({
        "success": True,
        "total": len(projetos),
        "projetos": projetos,
        "filtros": {"q": pesquisa, "visibilidade": visibilidade_filtro, "estado": estado_filtro}
    })

@app.route('/api/matrix/projetos/<project_id>', methods=['PUT'])
@login_obrigatorio
def editar_projeto_matrix(project_id):
    try:
        projeto = colecao_projetos.find_one({"_id": ObjectId(project_id)})
    except Exception:
        projeto = None
    erro_acesso = exigir_gestao(projeto)
    if erro_acesso:
        return erro_acesso

    dados = request.get_json(silent=True) or {}
    nome = str(dados.get("nome", projeto.get("nome", ""))).strip()
    descricao = str(dados.get("descricao", projeto.get("descricao", ""))).strip()
    visibilidade = str(dados.get("visibilidade", projeto.get("visibilidade", "privado"))).strip().lower()
    if not nome or len(nome) > 100:
        return jsonify({"success": False, "error": "O nome do projeto deve ter entre 1 e 100 caracteres."}), 400
    if visibilidade not in {"publico", "privado"}:
        return jsonify({"success": False, "error": "A visibilidade deve ser publico ou privado."}), 400

    atualizacao = {"nome": sanitizar_string(nome), "descricao": sanitizar_string(descricao), "visibilidade": visibilidade, "atualizado_em": datetime.utcnow()}
    colecao_projetos.update_one({"_id": projeto["_id"]}, {"$set": atualizacao})
    return jsonify({"success": True, "mensagem": "Projeto atualizado com sucesso.", "projeto": {"id": str(projeto["_id"]), **atualizacao}})

@app.route('/api/matrix/projetos/<project_id>', methods=['DELETE'])
@login_obrigatorio
def apagar_projeto_matrix(project_id):
    try:
        projeto = colecao_projetos.find_one({"_id": ObjectId(project_id)})
    except Exception:
        projeto = None
    erro_acesso = exigir_gestao(projeto)
    if erro_acesso:
        return erro_acesso

    # Apagamento lógico: mantém dados e Git recuperáveis nesta fase do MVP.
    colecao_projetos.update_one(
        {"_id": projeto["_id"]},
        {"$set": {"estado": "apagado", "apagado_em": datetime.utcnow()}}
    )
    return jsonify({"success": True, "mensagem": "Projeto apagado. Os dados foram preservados para recuperação."})

@app.route('/api/matrix/projetos/apagados', methods=['GET'])
@login_obrigatorio
def listar_projetos_apagados_matrix():
    utilizador = utilizador_atual()
    projetos = []
    for projeto in colecao_projetos.find({"proprietario_id": utilizador["_id"], "estado": "apagado"}).sort("apagado_em", -1):
        projetos.append({
            "id": str(projeto["_id"]),
            "nome": projeto.get("nome", ""),
            "descricao": projeto.get("descricao", ""),
            "visibilidade": projeto.get("visibilidade", "privado"),
            "estado": projeto.get("estado", "apagado"),
            "apagado_em": projeto.get("apagado_em").isoformat() if projeto.get("apagado_em") else None
        })
    return jsonify({"success": True, "total": len(projetos), "projetos": projetos})

@app.route('/api/matrix/projetos/<project_id>/restaurar', methods=['POST'])
@login_obrigatorio
def restaurar_projeto_matrix(project_id):
    try:
        projeto = colecao_projetos.find_one({"_id": ObjectId(project_id), "estado": "apagado"})
    except Exception:
        projeto = None
    erro_acesso = exigir_gestao(projeto)
    if erro_acesso:
        return erro_acesso
    colecao_projetos.update_one(
        {"_id": projeto["_id"]},
        {"$set": {"estado": "ativo", "restaurado_em": datetime.utcnow()}, "$unset": {"apagado_em": ""}}
    )
    return jsonify({"success": True, "mensagem": "Projeto restaurado com sucesso."})

@app.route('/api/matrix/projetos/<project_id>/inicializar', methods=['POST'])
@login_obrigatorio
def inicializar_ficheiros_matrix(project_id):
    try:
        projeto = colecao_projetos.find_one({"_id": ObjectId(project_id), "estado": {"$ne": "apagado"}})
    except Exception:
        projeto = None
    erro_acesso = exigir_gestao(projeto)
    if erro_acesso:
        return erro_acesso
    criados = criar_ficheiros_iniciais(projeto)
    return jsonify({"success": True, "mensagem": "Ficheiros iniciais preparados.", "criados": criados})

@app.route('/api/matrix/projetos/<project_id>', methods=['GET'])
def obter_projeto_matrix(project_id):
    try:
        projeto = colecao_projetos.find_one({"_id": ObjectId(project_id)})
    except Exception:
        projeto = None

    erro_acesso = exigir_leitura(projeto)
    if erro_acesso:
        return erro_acesso

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

    erro_acesso = exigir_gestao(projeto)
    if erro_acesso:
        return erro_acesso

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

    erro_acesso = exigir_leitura(projeto)
    if erro_acesso:
        return erro_acesso

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
    erro_acesso = exigir_gestao(projeto)
    if erro_acesso:
        return erro_acesso

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
        projeto = colecao_projetos.find_one({"_id": ObjectId(project_id)})
        erro_acesso = exigir_gestao(projeto)
        if erro_acesso:
            return erro_acesso
        resultado = colecao_ficheiros.delete_one({"_id": ObjectId(file_id), "projeto_id": ObjectId(project_id)})
    except Exception:
        resultado = None

    if resultado is None or resultado.deleted_count == 0:
        return jsonify({"success": False, "error": "Ficheiro não encontrado."}), 404

    return jsonify({"success": True, "mensagem": "Ficheiro apagado com sucesso."})

@app.route('/api/matrix/projetos/<project_id>/repositorio', methods=['POST'])
def criar_repositorio_matrix(project_id):
    try:
        projeto = colecao_projetos.find_one({"_id": ObjectId(project_id)})
    except Exception:
        projeto = None

    erro_acesso = exigir_gestao(projeto)
    if erro_acesso:
        return erro_acesso

    existente = colecao_repositorios.find_one({"projeto_id": projeto["_id"]})
    if existente is not None:
        return jsonify({
            "success": False,
            "error": "Este projeto já tem um repositório Git."
        }), 409

    base = Path(os.getenv("MATRIX_GIT_STORAGE", "matrix_git_repositories"))
    caminho = base / str(projeto["_id"])
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        resultado_git = subprocess.run(
            ["git", "init", "--bare", "--initial-branch=main", str(caminho)],
            capture_output=True, text=True, timeout=15, check=False
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as erro:
        logger.error("Erro ao criar repositório Git: %s", erro)
        return jsonify({"success": False, "error": "Git não está disponível no servidor."}), 500

    if resultado_git.returncode != 0:
        logger.error("git init falhou: %s", resultado_git.stderr)
        return jsonify({"success": False, "error": "Não foi possível criar o repositório Git."}), 500

    repositorio = {
        "projeto_id": projeto["_id"],
        "nome": projeto.get("nome", "projeto"),
        "ramo_principal": "main",
        "caminho_local": str(caminho),
        "tipo": "git-bare-local",
        "criado_em": datetime.utcnow()
    }
    resultado = colecao_repositorios.insert_one(repositorio)

    return jsonify({
        "success": True,
        "mensagem": "Repositório Git criado com sucesso.",
        "repositorio": {
            "id": str(resultado.inserted_id),
            "nome": repositorio["nome"],
            "ramo_principal": repositorio["ramo_principal"],
            "tipo": repositorio["tipo"]
        }
    }), 201

@app.route('/api/matrix/projetos/<project_id>/repositorio', methods=['GET'])
def obter_repositorio_matrix(project_id):
    try:
        projeto = colecao_projetos.find_one({"_id": ObjectId(project_id)})
    except Exception:
        projeto = None

    erro_acesso = exigir_leitura(projeto)
    if erro_acesso:
        return erro_acesso

    repositorio = colecao_repositorios.find_one({"projeto_id": projeto["_id"]})
    if repositorio is None:
        return jsonify({"success": True, "repositorio": None})

    return jsonify({
        "success": True,
        "repositorio": {
            "id": str(repositorio["_id"]),
            "nome": repositorio.get("nome", projeto.get("nome", "projeto")),
            "ramo_principal": repositorio.get("ramo_principal", "main"),
            "tipo": repositorio.get("tipo", "git-bare-local")
        }
    })

@app.route('/api/matrix/projetos/<project_id>/ficheiros/<file_id>/commit', methods=['POST'])
def criar_commit_ficheiro_matrix(project_id, file_id):
    try:
        projeto_id = ObjectId(project_id)
        ficheiro_id = ObjectId(file_id)
    except Exception:
        return jsonify({"success": False, "error": "Identificador inválido."}), 400

    projeto = colecao_projetos.find_one({"_id": projeto_id})
    ficheiro = colecao_ficheiros.find_one({"_id": ficheiro_id, "projeto_id": projeto_id})
    repositorio = colecao_repositorios.find_one({"projeto_id": projeto_id})
    if projeto is None or ficheiro is None:
        return jsonify({"success": False, "error": "Projeto ou ficheiro não encontrado."}), 404
    erro_acesso = exigir_gestao(projeto)
    if erro_acesso:
        return erro_acesso
    if repositorio is None:
        return jsonify({"success": False, "error": "Cria primeiro o repositório Git."}), 409

    caminho_bare = Path(repositorio["caminho_local"])
    if not caminho_bare.exists():
        return jsonify({"success": False, "error": "O repositório Git local não existe."}), 500

    mensagem = request.get_json(silent=True) or {}
    mensagem_commit = str(mensagem.get("mensagem", "")).strip()[:160]
    if len(mensagem_commit) < 3:
        return jsonify({"success": False, "error": "A mensagem do commit deve ter pelo menos 3 caracteres."}), 400
    utilizador = utilizador_atual()
    autor_nome = sanitizar_string(utilizador.get("nome", "Utilizador Matrix")) if utilizador else "Utilizador Matrix"
    autor_email = utilizador.get("email", "matrix@vagalume90.local") if utilizador else "matrix@vagalume90.local"

    try:
        pasta_temp = tempfile.mkdtemp(prefix="matrix-commit-")
        try:
            clone = subprocess.run(
                ["git", "clone", str(caminho_bare), pasta_temp],
                capture_output=True, text=True, timeout=30, check=False
            )
            if clone.returncode != 0:
                logger.error("git clone falhou: %s", clone.stderr)
                return jsonify({"success": False, "error": "Não foi possível preparar o commit."}), 500

            trabalho = Path(pasta_temp)
            arquivo = trabalho / ficheiro["nome"]
            arquivo.parent.mkdir(parents=True, exist_ok=True)
            arquivo.write_text(ficheiro.get("conteudo", ""), encoding="utf-8")

            comandos = [
                ["git", "-C", str(trabalho), "config", "user.name", autor_nome],
                ["git", "-C", str(trabalho), "config", "user.email", autor_email],
                ["git", "-C", str(trabalho), "add", "--", ficheiro["nome"]],
                ["git", "-C", str(trabalho), "commit", "-m", mensagem_commit],
                ["git", "-C", str(trabalho), "push", "origin", "HEAD:main"]
            ]
            for comando in comandos:
                resultado = subprocess.run(comando, capture_output=True, text=True, timeout=30, check=False)
                if resultado.returncode != 0:
                    if "commit" in comando and "nothing to commit" in (resultado.stdout + resultado.stderr).lower():
                        return jsonify({"success": False, "error": "Não existem alterações novas para criar um commit."}), 409
                    logger.error("Comando Git falhou: %s", resultado.stderr)
                    return jsonify({"success": False, "error": "O Git não conseguiu criar o commit."}), 500

            sha = subprocess.run(
                ["git", "-C", str(trabalho), "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=15, check=False
            ).stdout.strip()
            return jsonify({"success": True, "mensagem": "Commit criado com sucesso.", "commit": {"sha": sha, "mensagem": mensagem_commit, "autor": autor_nome}}), 201
        finally:
            shutil.rmtree(pasta_temp, ignore_errors=True)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as erro:
        logger.error("Erro no commit Git: %s", erro)
        return jsonify({"success": False, "error": "Não foi possível concluir o commit."}), 500

@app.route('/api/matrix/projetos/<project_id>/commits', methods=['GET'])
def listar_commits_matrix(project_id):
    try:
        projeto_id = ObjectId(project_id)
    except Exception:
        return jsonify({"success": False, "error": "Identificador inválido."}), 400

    try:
        limite = min(max(int(request.args.get("limite", 20)), 1), 100)
        offset = max(int(request.args.get("offset", 0)), 0)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Paginação inválida."}), 400

    projeto = colecao_projetos.find_one({"_id": projeto_id})
    erro_acesso = exigir_leitura(projeto)
    if erro_acesso:
        return erro_acesso
    repositorio = colecao_repositorios.find_one({"projeto_id": projeto_id})
    if repositorio is None:
        return jsonify({"success": False, "error": "Repositório não encontrado."}), 404

    try:
        # Pedimos mais um commit para saber se existe uma página seguinte.
        resultado = subprocess.run(
            ["git", "--git-dir", repositorio["caminho_local"], "log", "main",
             f"-{limite + 1}", f"--skip={offset}",
             "--pretty=format:%H%x09%an%x09%aI%x09%s"],
            capture_output=True, text=True, timeout=15, check=False
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return jsonify({"success": False, "error": "Git não está disponível."}), 500

    if resultado.returncode != 0 and "does not have any commits" not in resultado.stderr.lower():
        logger.error("git log falhou: %s", resultado.stderr)
        return jsonify({"success": False, "error": "Não foi possível ler o histórico."}), 500

    linhas = [linha for linha in resultado.stdout.splitlines() if linha.strip()]
    tem_mais = len(linhas) > limite
    commits = []
    for linha in linhas[:limite]:
        partes = linha.split("\t", 3)
        if len(partes) == 4:
            sha, autor, data, mensagem = partes
            commits.append({"sha": sha, "autor": autor, "data": data, "mensagem": mensagem})

    return jsonify({
        "success": True,
        "commits": commits,
        "offset": offset,
        "limite": limite,
        "tem_mais": tem_mais
    })

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
