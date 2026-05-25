# app/services/pagamento_service.py

class PagamentoService:
    pagamentos_db = []

    @classmethod
    def criar_intencao_pagamento(cls, telefone: str, valor: float, metodo: str):
        id_pagamento = len(cls.pagamentos_db) + 1
        novo_pagamento = {
            "id": id_pagamento,
            "telefone_cliente": telefone,
            "valor_kz": valor,
            "metodo": metodo,
            "status": "Pendente",
            "mensagem": "Envie o comprovativo via WhatsApp para validacao."
        }
        cls.pagamentos_db.append(novo_pagamento)
        return novo_pagamento

    @classmethod
    def listar_pendentes(cls):
        return [p for p in cls.pagamentos_db if p["status"] == "Pendente"]

    @classmethod
    def confirmar_pagamento(cls, id_pagamento: int, acao: str):
        for p in cls.pagamentos_db:
            if p["id"] == id_pagamento:
                if acao.lower() == "aprovar":
                    p["status"] = "Aprovado"
                    p["mensagem"] = "Acesso libertado! Obrigado pelo pagamento."
                else:
                    p["status"] = "Rejeitado"
                    p["mensagem"] = "Pagamento nao verificado."
                return p
        return {"erro": "Pagamento nao encontrado"}