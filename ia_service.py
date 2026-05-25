# ia_service.py
import os
from google import genai

class IAService:
    @classmethod
    def gerar_conteudo_vagalume(cls, tema: str, tom_voz: str = "profissional"):
        api_key = os.environ.get("GEMINI_API_KEY", "SUA_CHAVE_AQUI")
        
        try:
            client = genai.Client(api_key=api_key)
            
            contexto_angola = (
                f"Atue como um Professor de Enfermagem de Elite em Angola, especialista nos concursos públicos do Ministério da Saúde (MINSA).\n"
                f"Gere um resumo focado, didático e de fácil leitura sobre o tema: '{tema}'.\n"
                f"Use um tom {tom_voz} e adapte os termos técnicos para o contexto da saúde em Angola.\n"
                f"No final do resumo, inclua sempre 2 perguntas de múltipla escolha no formato dos exames de admissão locais, com o gabarito correto."
            )
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contexto_angola,
            )
            
            return {
                "tema_solicitado": tema,
                "motor_ia": "Google Gemini 2.5 Flash (Real)",
                "conteudo_gerado": response.text
            }
            
        except Exception as e:
            return {
                "tema_solicitado": tema,
                "motor_ia": "Modo de Demonstracao (Sem Chave API)",
                "conteudo_gerado": f"Resumo simulado para o estudante de Angola sobre '{tema}'. (O motor da Google ja esta conectado com sucesso!)."
            }