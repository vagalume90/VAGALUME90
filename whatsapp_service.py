# whatsapp_service.py

class WhatsAppService:
    mensagens_enviadas = []

    @classmethod
    def enviar_notificacao_pagamento(cls, telefone: str, valor: float, status: str):
        if status.lower() == "pendente":
            texto = f"Olá! Recebemos o seu pedido de adesão ao VAGALUME90. Por favor, envie o comprovativo de {valor} Kz para este número."
        elif status.lower() == "aprovado":
            texto = f"Prezado Cliente, o seu pagamento de {valor} Kz foi confirmado com sucesso! O seu acesso à plataforma já está libertado."
        else:
            texto = f"Atenção: O seu pagamento de {valor} Kz não pôde ser validado. Por favor, contacte o suporte."

        log_mensagem = {
            "id_envio": len(cls.mensagens_enviadas) + 1,
            "destino": telefone,
            "mensagem": texto,
            "status_entrega": "Enviado (Simulado)"
        }
        cls.mensagens_enviadas.append(log_mensagem)
        return log_mensagem

    @classmethod
    def listar_historico(cls):
        return cls.mensagens_enviadas