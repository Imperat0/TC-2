import google.generativeai as genai
import json
from dotenv import load_dotenv
import os

# Carrega as variáveis de ambiente (API KEY)
load_dotenv()
API_KEY = os.getenv("API_KEY")


def gerar_instrucoes_llm_v2(rotas_finais, pontos_dados, zonas_transito):
    """
    Utiliza a IA do Google Gemini para analisar as rotas geradas e fornecer
    insights logísticos, avaliação de risco e sugestões de otimização.

    Args:
        rotas_finais (list): Lista de listas com IDs dos pontos (ex: [[0, 1, 0]]).
        pontos_dados (list): Dicionários com detalhes de cada ponto (nome, carga, prioridade).
        zonas_transito (list): Dados sobre áreas de risco ou trânsito intenso.

    Returns:
        list: Uma lista de dicionários contendo a análise da IA para cada veículo.
    """
    print("\n[INFO] Iniciando analise de Inteligencia Artificial...")

    try:
        # Configuração do cliente Google Generative AI
        genai.configure(api_key=API_KEY)

        # Inicializa o modelo específico solicitado (gemini-3-flash-preview)
        # Configurado para retornar JSON nativo
        model = genai.GenerativeModel(
            "gemini-3-flash-preview",
            generation_config={"response_mime_type": "application/json"},
        )

        # --- PREPARAÇÃO DO CONTEXTO (INPUT) ---
        # Filtra e organiza os dados para enviar apenas o necessário para a IA
        dados_input = {"rotas": [], "transito": zonas_transito}

        for i, rota in enumerate(rotas_finais):
            detalhes_rota = []
            carga_rota = 0
            tem_critico = False

            # Reconstrói os dados da rota a partir dos IDs
            for id_ponto in rota:
                if id_ponto == 0:
                    continue  # Ignora o depósito para a lista de nomes

                # Busca os dados do ponto pelo ID
                ponto = next(p for p in pontos_dados if p["id"] == id_ponto)

                detalhes_rota.append(ponto["nome"])
                carga_rota += ponto["carga"]

                if ponto.get("prioridade") == "crítica":
                    tem_critico = True

            # Adiciona o resumo deste veículo ao input da IA
            dados_input["rotas"].append(
                {
                    "veiculo_id": i + 1,
                    "paradas": detalhes_rota,
                    "carga_total_kg": carga_rota,
                    "carga_critica": tem_critico,
                }
            )

        # --- ENGENHARIA DE PROMPT ---
        # Definição estrita do papel da IA e das regras de negócio
        prompt = f"""
        Você é um algoritmo especialista em Inteligência Logística Hospitalar.
        Sua tarefa é analisar a frota e identificar riscos baseados nos dados fornecidos.
        
        INPUT DATA (Contexto da Frota):
        {json.dumps(dados_input, indent=2)}

        REGRA DE CLASSIFICAÇÃO DE RISCO:
        - ALTO: Se houver Trânsito > 70% E a rota contiver Carga Crítica.
        - MEDIO: Se houver Trânsito > 50% OU Carga Crítica mesmo sem trânsito.
        - BAIXO: Operação normal, sem incidentes.

        REGRA DE OTIMIZAÇÃO (Logica de Decisão):
        1. Risco ALTO: Sugira estritamente "Solicitar Transbordo" ou "Escolta Policial".
        2. Carga Baixa (< 30%): Sugira "Veículo Ocioso - Disponível para Apoio".
        3. Carga Alta (> 90%): Sugira "Operação Eficiente (Capacidade Máxima)".
        4. Padrão: Se nenhuma anterior se aplicar, sugira "Rota Otimizada - Manter Plano".

        FORMATO DE SAÍDA (JSON ARRAY):
        Retorne APENAS uma lista de objetos JSON com as chaves exatas:
        - "veiculo_id": (inteiro)
        - "nivel_risco": "ALTO" | "MEDIO" | "BAIXO"
        - "acao_imediata": (resumo curto da ação)
        - "justificativa": (explicação baseada nas regras)
        - "sugestao_otimizacao": (texto baseado nas Regras de Otimização acima)
        """

        # Envia para a IA processar
        response = model.generate_content(prompt)

        # Converte a resposta textual da IA em objeto Python (Lista/Dict)
        analise_estruturada = json.loads(response.text)
        return analise_estruturada

    except Exception as e:
        print(f"[ERRO] Falha na comunicação com a IA: {e}")
        # Retorna uma estrutura de erro amigável para não quebrar a aplicação
        return [{"erro": "Serviço de IA indisponível", "detalhes": str(e)}]
