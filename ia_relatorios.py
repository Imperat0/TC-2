import google.generativeai as genai

# --- CONFIGURAÇÃO DA IA ---
# Insira sua chave grátis obtida em: https://aistudio.google.com/
API_KEY = "COLE_SUA_CHAVE_AQUI"


def gerar_instrucoes_llm(rotas_finais, pontos_dados, zonas_transito):
    """
    Recebe os dados das rotas, dos pontos e do trânsito para gerar um
    relatório logístico estratégico via Google Gemini.
    """
    print("\n🤖 CONECTANDO AO CÉREBRO DA IA (GEMINI)...")

    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        # 1. Prepara o Resumo das Rotas e Cargas
        texto_dados = "DADOS TÉCNICOS DA OPERAÇÃO:\n"
        for i, rota in enumerate(rotas_finais):
            nomes_destinos = []
            carga_total = 0
            qtd_criticos = 0

            for id_ponto in rota:
                if id_ponto == 0:
                    continue
                ponto = next(p for p in pontos_dados if p["id"] == id_ponto)
                nomes_destinos.append(ponto["nome"])
                carga_total += ponto["carga"]
                if ponto.get("prioridade") == "crítica":
                    qtd_criticos += 1

            texto_dados += f"- VEÍCULO {i+1}: {len(nomes_destinos)} paradas | Carga: {carga_total}kg | Críticos: {qtd_criticos}\n"
            texto_dados += f"  Trajeto: {' -> '.join(nomes_destinos)}\n"

        # 2. Prepara os Dados de Trânsito (O novo parâmetro)
        texto_transito = "\nCONDIÇÕES DE TRÁFEGO ATUAIS:\n"
        for z in zonas_transito:
            texto_transito += f"- {z['nome']}: Lentidão de {z['intensidade']*100}% em um raio de {z['raio_km']}km\n"

        # 3. Prompt Estratégico
        prompt = f"""
        Atue como um Gerente de Logística Hospitalar Sênior.
        Analise os dados de entrega e trânsito abaixo para gerar um relatório executivo.
        
        {texto_dados}
        {texto_transito}
        
        SEU RELATÓRIO DEVE CONTER:
        1. 📢 AVISO DE TRÂNSITO: Identifique quais veículos podem sofrer atrasos baseados nas zonas de lentidão.
        2. 🚨 PRIORIDADE MÉDICA: Dê uma instrução de segurança para as entregas críticas.
        3. 💡 INSIGHT OPERACIONAL: Sugira uma melhoria simples baseada nos dados (ex: horários ou divisão de carga).
        
        Use uma linguagem profissional e técnica. Evite formatação complexa.
        """

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"⚠️ Erro ao gerar relatório com IA: {e}"
