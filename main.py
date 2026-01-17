import algoritmo_genetico as ag
import visualizacao_pygame as vis_pg
import ia_relatorios as ia
import random
import json
import matplotlib.pyplot as plt


# --- CARGA DE CONFIGURAÇÕES ---
def carregar_configuracoes():
    """
    Lê os parâmetros do projeto a partir do arquivo 'config.json'.
    Caso o arquivo não exista, retorna None e exibe erro.
    """
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[ERRO] O arquivo 'config.json' não foi encontrado.")
        return None


# --- GERADOR DE CENÁRIO ---
def gerar_cenario(config):
    """
    Cria a lista de pontos (HUB + Entregas) com base nas configurações.
    Gera coordenadas aleatórias em torno de um ponto central (SP).

    Args:
        config (dict): Dicionário com configurações carregadas.

    Returns:
        list: Lista de dicionários representando os locais.
    """
    pontos = []
    centro_lat, centro_lon = config["centro_sp"]

    # 1. Criação do Depósito Central (HUB)
    # O ID 0 é reservado obrigatoriamente para o ponto de partida/chegada.
    pontos.append(
        {
            "id": 0,
            "nome": "CENTRAL DE LOGÍSTICA (Hosp. das Clínicas)",
            "coord": (centro_lat, centro_lon),
            "tipo": "deposito",
            "carga": 0,
        }
    )

    # 2. Geração de Entregas (Hospitais/Pacientes)
    for i in range(1, config["qtd_pontos"]):
        # Gera uma dispersão aleatória em torno do centro (simulação de endereços)
        lat = centro_lat + random.uniform(-0.08, 0.08)
        lon = centro_lon + random.uniform(-0.08, 0.08)

        # Define aleatoriamente se a entrega é urgente (20% de chance)
        eh_critico = random.random() < 0.2
        nome_base = random.choice(config["nomes_locais"])

        pontos.append(
            {
                "id": i,
                "nome": f"{nome_base} - Unidade {i}",
                "coord": (lat, lon),
                "prioridade": "crítica" if eh_critico else "regular",
                "carga": random.randint(5, 25),  # Peso aleatório entre 5kg e 25kg
                "tipo": "entrega",
            }
        )
    return pontos


# --- ORQUESTRADOR DO PROJETO ---
def executar_projeto():
    """
    Função principal (Main Loop).
    Coordena a execução sequencial: Config -> GA -> Gráficos -> IA -> Simulação Visual.
    """
    print("\n" + "=" * 60)
    print("      SISTEMA DE OTIMIZAÇÃO LOGÍSTICA HOSPITALAR (VRP)")
    print("=" * 60)

    # 1. Setup inicial e carregamento de dados
    config = carregar_configuracoes()
    if not config:
        return

    pontos_entrega = gerar_cenario(config)

    # 2. Execução do Algoritmo Genético (Motor Matemático)
    print(
        f"\n[INFO] Otimizando {config['qtd_pontos']} locais para veículos de {config['capacidade_veiculo']}kg..."
    )

    # Chama o módulo algoritmo_genetico.py
    rotas_finais, historico = ag.executar_ga(
        pontos_entrega, config["capacidade_veiculo"], geracoes=config["geracoes"]
    )

    # 3. Geração do Gráfico de Performance
    print("\n[GRAFICO] Gerando curva de convergencia (convergencia_logistica.png)...")
    plt.figure(figsize=(10, 5))
    plt.plot(historico, color="#2c3e50", linewidth=2)
    plt.title("Curva de Aprendizado - Otimização de Rotas")
    plt.xlabel("Geração (Iteração)")
    plt.ylabel("Custo Total (Distância)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.savefig("convergencia_logistica.png")
    plt.close()

    # 4. Relatório Estratégico com Google Gemini (Inteligência Artificial)
    print("\n[IA] Solicitando analise de risco e otimização à API Gemini...")

    try:
        # Chama o módulo ia_relatorios.py
        relatorio_ia = ia.gerar_instrucoes_llm_v2(
            rotas_finais, pontos_entrega, config["zonas_transito"]
        )

        print("\n" + "-" * 40)
        print("RELATORIO DE INTELIGENCIA (JSON):")

        # Exibe o resultado formatado no terminal para conferência
        print(json.dumps(relatorio_ia, indent=2, ensure_ascii=False))
        print("-" * 40)

    except AttributeError:
        print("[ERRO] Função de IA não encontrada. Verifique 'ia_relatorios.py'.")
    except Exception as e:
        print(f"[ERRO] Falha ao conectar com o serviço de IA: {e}")

    # 5. Visualização Interativa (Pygame)
    print("\n[VISUALIZACAO] Iniciando simulador de mapa...")
    print(f" -> Frota Ativa: {len(rotas_finais)} veículos.")

    # Chama o módulo visualizacao_pygame.py
    vis_pg.visualizar_rotas_pygame(
        rotas_finais, pontos_entrega, config["zonas_transito"]
    )


if __name__ == "__main__":
    executar_projeto()
