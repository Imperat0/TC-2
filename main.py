import algoritmo_genetico as ag
import visualizacao_pygame as vis_pg
import ia_relatorios as ia
import random
import json
import matplotlib.pyplot as plt


# --- CARGA DE CONFIGURAÇÕES ---
def carregar_configuracoes():
    """Lê os parâmetros do projeto a partir do arquivo config.json."""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Erro: O arquivo 'config.json' não foi encontrado.")
        return None


# --- GERADOR DE CENÁRIO ---
def gerar_cenario(config):
    """Cria a lista de pontos (HUB + Entregas) com base nas configurações."""
    pontos = []
    centro_lat, centro_lon = config["centro_sp"]

    # 1. Depósito Central (HUB)
    pontos.append(
        {
            "id": 0,
            "nome": "CENTRAL DE LOGÍSTICA (Hosp. das Clínicas)",
            "coord": (centro_lat, centro_lon),
            "tipo": "deposito",
            "carga": 0,
        }
    )

    # 2. Geração de Entregas (Hospitais)
    for i in range(1, config["qtd_pontos"]):
        lat = centro_lat + random.uniform(-0.08, 0.08)
        lon = centro_lon + random.uniform(-0.08, 0.08)
        eh_critico = random.random() < 0.2
        nome_base = random.choice(config["nomes_locais"])

        pontos.append(
            {
                "id": i,
                "nome": f"{nome_base} - Unidade {i}",
                "coord": (lat, lon),
                "prioridade": "crítica" if eh_critico else "regular",
                "carga": random.randint(5, 25),
                "tipo": "entrega",
            }
        )
    return pontos


# --- ORQUESTRADOR DO PROJETO ---
def executar_projeto():
    print("\n" + "=" * 60)
    print("      SISTEMA DE OTIMIZAÇÃO VRP")
    print("=" * 60)

    # 1. Setup inicial
    config = carregar_configuracoes()
    if not config:
        return

    pontos_entrega = gerar_cenario(config)

    # 2. Execução do Algoritmo Genético
    print(
        f"\n[1/4] Otimizando {config['qtd_pontos']} locais para veículos de {config['capacidade_veiculo']}kg..."
    )
    rotas_finais, historico = ag.executar_ga(
        pontos_entrega, config["capacidade_veiculo"], geracoes=config["geracoes"]
    )

    # 3. Geração do Gráfico
    print("\n[2/4] Gerando gráfico de performance (convergencia_logistica.png)...")
    plt.figure(figsize=(10, 5))
    plt.plot(historico, color="#2c3e50", linewidth=2)
    plt.title("Curva de Aprendizado - Algoritmo Genético")
    plt.xlabel("Geração")
    plt.ylabel("Custo (Distância Otimizada)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.savefig("convergencia_logistica.png")
    plt.close()

    # 4. Relatório Estratégico com Google Gemini
    print("\n[3/4] Solicitando parecer técnico à Inteligência Artificial...")

    # --- CORREÇÃO AQUI ---
    # Certifique-se que no arquivo ia_relatorios.py a função se chama gerar_instrucoes_llm_v2
    try:
        relatorio_ia = ia.gerar_instrucoes_llm_v2(
            rotas_finais, pontos_entrega, config["zonas_transito"]
        )

        print("\n" + "-" * 40)
        print("🤖 INSIGHTS DA IA (ESTRUTURADO):")

        # Formata o JSON para ficar bonito no terminal (Indentação de 2 espaços)
        print(json.dumps(relatorio_ia, indent=2, ensure_ascii=False))
        print("-" * 40)

    except AttributeError:
        print(
            "⚠️ Erro: Verifique se o nome da função no arquivo ia_relatorios.py é 'gerar_instrucoes_llm_v2'"
        )
    except Exception as e:
        print(f"⚠️ Erro na IA: {e}")

    # 5. Visualização no Pygame
    print("\n[4/4] Iniciando Simulador Visual Interativo...")
    print(f"      -> Frota: {len(rotas_finais)} veículos operando.")
    vis_pg.visualizar_rotas_pygame(
        rotas_finais, pontos_entrega, config["zonas_transito"]
    )


if __name__ == "__main__":
    executar_projeto()
