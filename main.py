@app.route('/api/mercado/comprar', methods=['POST'])
def processar_compra_v2_gratis():
    if 'username' not in session:
        return jsonify({"error": "Acesso negado. Autenticação necessária."}), 403
        
    data = request.get_json() or {}
    produto_id = data.get('produto_id')
    ref_afiliado = data.get('ref')
    comprador_username = session['username']
    
    if not produto_id:
        return jsonify({"error": "Parâmetro 'produto_id' em falta."}), 400

    # 1. Buscar Configurações de Comissões (Funciona no plano grátis)
    config = db.configuracoes.find_one({"_id": "sistema_config"})
    if not config:
        pct_afiliado, pct_criador, pct_plataforma = 40, 50, 10
    else:
        pct_afiliado = config['comissoes_percentual']['afiliado']
        pct_criador = config['comissoes_percentual']['criador']
        pct_plataforma = config['comissoes_percentual']['plataforma']

    # 2. Buscar documentos normalmente (Sem travar sessões pagas)
    comprador = db.users.find_one({"username": comprador_username})
    produto = db.infoprodutos.find_one({"_id": ObjectId(produto_id)})
    
    if not produto:
        return jsonify({"error": "O infoproduto solicitado não existe."}), 404
        
    preco_total = produto.get('preco_sugerido', 0.0)
    
    # Validação de Saldo
    if comprador.get('saldo', {}).get('disponivel', 0.0) < preco_total:
        return jsonify({"error": "Saldo Vagalume insuficiente."}), 400

    # Divisão dos valores
    comissao_afiliado = (preco_total * pct_afiliado) / 100 if ref_afiliado else 0.0
    lucro_criador = (preco_total * pct_criador) / 100 if ref_afiliado else (preco_total * (pct_criador + pct_afiliado)) / 100
    taxa_plataforma = (preco_total * pct_plataforma) / 100

    # EXECUÇÃO DIRETA (Compatível com MongoDB Atlas Grátis)
    # OPERAÇÃO 1: Deduzir saldo do comprador
    db.users.update_one(
        {"username": comprador_username},
        {"$inc": {"saldo.disponivel": -preco_total, "estatisticas.compras": 1}}
    )
    
    # OPERAÇÃO 2: Creditar Criador
    db.users.update_one(
        {"username": produto['criador']},
        {"$inc": {"saldo.disponivel": lucro_criador, "estatisticas.vendas": 1}}
    )
    
    # OPERAÇÃO 3: Creditar Afiliado
    if comissao_afiliado > 0 and ref_afiliado and ref_afiliado != comprador_username:
        db.users.update_one(
            {"username": ref_afiliado},
            {"$inc": {"saldo.disponivel": comissao_afiliado}}
        )
    
    # OPERAÇÃO 4: Atualizar volume do produto
    db.infoprodutos.update_one(
        {"_id": ObjectId(produto_id)},
        {"$inc": {"numero_vendas": 1}}
    )

    # OPERAÇÃO 5: Registar no Livro Razão para auditoria
    nova_transacao = {
        "tipo": "compra_infoproduto",
        "comprador": comprador_username,
        "vendedor": produto['criador'],
        "afiliado": ref_afiliado if comissao_afiliado > 0 else None,
        "produto_id": ObjectId(produto_id),
        "valores": {
            "total": preco_total,
            "comissao_afiliado": comissao_afiliado,
            "lucro_criador": lucro_criador,
            "taxa_plataforma": taxa_plataforma
        },
        "data": datetime.utcnow(),
        "status": "concluida"
    }
    db.transacoes.insert_one(nova_transacao)

    return jsonify({"success": True, "message": "Movimentação processada com sucesso no plano gratuito!"})
