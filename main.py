# main.py
from fastapi import FastAPI, Query
from ia_service import IAService
from pagamento_service import PagamentoService
from whatsapp_service import WhatsAppService

app = FastAPI(
    title="VAGALUME90 API",
    description="Backend oficial da plataforma VAGALUME90 - Angola",
    version="1.0.0"
)

@app.get("/")
def pagina_inicial():
    return {
        "status": "Online",
        "projeto": "VAGALUME90",
        "mensagem": "Sucesso! O backend esta a rodar com os ficheiros unificados!",
        "autor": "Enfermeiro Desenvolvedor"
    }

@app.get("/api/ia/gerar")
def gerar_conteudo(tema: str = Query(..., description="O assunto do texto"), tom: str = Query("profissional")):
    return IAService.gerar_conteudo_vagalume(tema=tema, tom_voz=tom)

@app.post("/api/pagamentos/solicitar")
def solicitar_pagamento(telefone: str, valor: float, metodo: str = Query("multicaixa", description="multicaixa ou unitel_money")):
    pagamento = PagamentoService.criar_intencao_pagamento(telefone=telefone, valor=valor, metodo=metodo)
    WhatsAppService.enviar_notificacao_pagamento(telefone=telefone, valor=valor, status="pendente")
    return pagamento

@app.get("/api/admin/pagamentos/pendentes")
def ver_pagamentos_pendentes():
    return PagamentoService.listar_pendentes()

@app.post("/api/admin/pagamentos/confirmar")
def confirmar_pagamento(id_pagamento: int, acao: str = Query(..., description="aprovar ou rejeitar")):
    pagamento_updated = PagamentoService.confirmar_pagamento(id_pagamento=id_pagamento, acao=acao)
    if "erro" not in pagamento_updated:
        WhatsAppService.enviar_notificacao_pagamento(
            telefone=pagamento_updated["telefone_cliente"],
            valor=pagamento_updated["valor_kz"],
            status=pagamento_updated["status"]
        )
    return pagamento_updated

@app.get("/api/admin/whatsapp/historico")
def ver_historico_whatsapp():
    return WhatsAppService.listar_historico()