import google.generativeai as genai
import json
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")


def gerar_instrucoes_llm_v2(rotas_finais, pontos_dados, zonas_transito):
    print("\n🤖 PROCESSANDO INTELIGÊNCIA LOGÍSTICA...")

    try:
        genai.configure(api_key=API_KEY)

        # AJUSTE 1: Use um modelo válido e configure para JSON
        # O 'response_mime_type' força a saída em JSON nativo (muito mais seguro)
        model = genai.GenerativeModel(
            "gemini-3-flash-preview",
            generation_config={"response_mime_type": "application/json"},
        )

        # Preparação dos dados (Mantive sua lógica, apenas formatando para o prompt)
        dados_input = {"rotas": [], "transito": zonas_transito}

        for i, rota in enumerate(rotas_finais):
            detalhes_rota = []
            carga_rota = 0
            tem_critico = False

            for id_ponto in rota:
                if id_ponto == 0:
                    continue
                ponto = next(p for p in pontos_dados if p["id"] == id_ponto)
                detalhes_rota.append(ponto["nome"])
                carga_rota += ponto["carga"]
                if ponto.get("prioridade") == "crítica":
                    tem_critico = True

            dados_input["rotas"].append(
                {
                    "veiculo_id": i + 1,
                    "paradas": detalhes_rota,
                    "carga_total_kg": carga_rota,
                    "carga_critica": tem_critico,
                }
            )

        prompt = f"""
        Você é um algoritmo de Inteligência Logística Hospitalar (VRP).
        Analise a frota inteira fornecida abaixo.
        
        INPUT DATA:
        {json.dumps(dados_input, indent=2)}

        REGRA DE CLASSIFICAÇÃO DE RISCO:
        - ALTO (🔴): Trânsito > 70% E Carga Crítica.
        - MEDIO (🟡): Trânsito > 50% OU Carga Crítica em rota limpa.
        - BAIXO (🟢): Operação normal.

        REGRA DE OTIMIZAÇÃO (NUNCA RETORNE NULL):
        1. Se Veículo com Risco ALTO: Sugira "Solicitar Transbordo" ou "Escolta".
        2. Se Veículo com Carga < 30%: Sugira "Veículo Ocioso - Disponível para Apoio".
        3. Se Veículo com Carga > 90%: Sugira "Operação Eficiente (Capacidade Máxima)".
        4. Se não houver nada especial: Sugira "Rota Otimizada - Manter Plano".

        SAÍDA ESPERADA (JSON):
        Lista de objetos com:
        - "veiculo_id": int
        - "nivel_risco": "ALTO" | "MEDIO" | "BAIXO"
        - "acao_imediata": "string curta"
        - "justificativa": "string explicativa"
        - "sugestao_otimizacao": "String obrigatória (Siga as regras acima)"
        """

        response = model.generate_content(prompt)

        analise_estruturada = json.loads(response.text)
        return analise_estruturada

    except Exception as e:
        return {"erro": f"Falha na IA: {e}"}
