import random
import numpy as np
import copy

# --- Funções Auxiliares ---


def calcular_distancia(ponto1, ponto2):
    """
    Calcula a distância Euclidiana (linha reta) entre dois pontos.

    Args:
        ponto1 (tuple): Coordenadas (x, y) ou (lat, lon) do primeiro ponto.
        ponto2 (tuple): Coordenadas (x, y) ou (lat, lon) do segundo ponto.

    Returns:
        float: A distância calculada.
    """
    return np.sqrt((ponto1[0] - ponto2[0]) ** 2 + (ponto1[1] - ponto2[1]) ** 2)


def separar_rotas_por_capacidade(cromossomo, pontos, cap_max):
    """
    Decodifica o cromossomo (sequência linear de IDs) em rotas reais,
    respeitando a capacidade máxima do veículo.

    Lógica: Adiciona pontos a um veículo até que ele esteja cheio,
    então inicia um novo veículo (retorna ao depósito '0').

    Args:
        cromossomo (list): Lista de IDs representando a ordem de visita.
        pontos (list): Lista de dicionários contendo os dados dos locais.
        cap_max (float): Capacidade máxima de carga de cada veículo.

    Returns:
        list: Lista de listas, onde cada sublista é uma rota válida (ex: [0, 1, 5, 0]).
    """
    rotas_finais = []
    # Inicia a primeira rota saindo do depósito (ID 0)
    rota_atual = [0]
    carga_atual = 0

    for id_ponto in cromossomo:
        # Busca o objeto ponto correspondente ao ID
        ponto = next(p for p in pontos if p["id"] == id_ponto)
        peso_entrega = ponto.get("carga", 0)

        # Verifica se cabe no veículo atual
        if carga_atual + peso_entrega > cap_max:
            # Se não couber, finaliza a rota atual voltando ao depósito
            rota_atual.append(0)
            rotas_finais.append(rota_atual)

            # Inicia nova rota com o ponto atual
            rota_atual = [0, id_ponto]
            carga_atual = peso_entrega
        else:
            # Se couber, adiciona o ponto à rota atual
            rota_atual.append(id_ponto)
            carga_atual += peso_entrega

    # Finaliza a última rota pendente retornando ao depósito
    rota_atual.append(0)
    rotas_finais.append(rota_atual)

    return rotas_finais


def aplicar_2opt(rota, pontos):
    """
    Aplica a heurística de busca local 2-opt para otimizar uma única rota.
    O objetivo é remover cruzamentos no caminho trocando arestas.

    Args:
        rota (list): Lista de IDs representando uma rota (ex: [0, 1, 5, 0]).
        pontos (dict): Dicionário de pontos indexado por ID para acesso rápido.

    Returns:
        list: A rota otimizada.
    """
    melhor_rota = rota[:]
    otimizou = True

    while otimizou:
        otimizou = False
        # Itera sobre todos os pares de arestas possíveis na rota
        for i in range(1, len(melhor_rota) - 2):
            for j in range(i + 1, len(melhor_rota) - 1):
                # Calcula a distância da configuração atual
                ponto_i_minus = pontos[melhor_rota[i - 1]]["coord"]
                ponto_i = pontos[melhor_rota[i]]["coord"]
                ponto_j = pontos[melhor_rota[j]]["coord"]
                ponto_j_plus = pontos[melhor_rota[j + 1]]["coord"]

                d_atual = calcular_distancia(
                    ponto_i_minus, ponto_i
                ) + calcular_distancia(ponto_j, ponto_j_plus)

                # Calcula a distância se trocarmos as conexões (cruzamento das arestas)
                d_nova = calcular_distancia(
                    ponto_i_minus, ponto_j
                ) + calcular_distancia(ponto_i, ponto_j_plus)

                # Se a nova configuração for mais curta, aplica a inversão
                if d_nova < d_atual:
                    # Inverte o segmento entre i e j
                    melhor_rota[i : j + 1] = reversed(melhor_rota[i : j + 1])
                    otimizou = True

    return melhor_rota


def funcao_fitness_vrp(cromossomo, pontos, cap_max, custo_por_km=1):
    """
    Calcula a aptidão (fitness) de um indivíduo baseada no custo total das rotas.

    Args:
        cromossomo (list): Sequência de genes (IDs dos locais).
        pontos (list): Dados dos locais.
        cap_max (float): Capacidade do veículo.
        custo_por_km (float): Multiplicador de custo.

    Returns:
        float: O custo total da solução (quanto menor, melhor).
    """
    rotas = separar_rotas_por_capacidade(cromossomo, pontos, cap_max)
    custo_total = 0

    for rota in rotas:
        dist_rota = 0
        ponto_anterior = next(p for p in pontos if p["id"] == 0)

        for id_ponto in rota:
            ponto_atual = next(p for p in pontos if p["id"] == id_ponto)
            dist_trecho = calcular_distancia(
                ponto_anterior["coord"], ponto_atual["coord"]
            )

            # Regra de Negócio: Pontos críticos têm "desconto" virtual na distância
            # para incentivar o algoritmo a priorizá-los em rotas mais curtas.
            if ponto_atual.get("prioridade") == "crítica":
                dist_trecho *= 0.5

            dist_rota += dist_trecho
            ponto_anterior = ponto_atual

        custo_total += dist_rota

    return custo_total * custo_por_km


# --- Operadores Genéticos ---


def criar_individuo(lista_ids_locais):
    """
    Gera um indivíduo aleatório (permutação dos locais de entrega).
    O depósito (ID 0) é excluído da permutação pois é fixo no início/fim.
    """
    entregas = [x for x in lista_ids_locais if x != 0]
    random.shuffle(entregas)
    return entregas


def selecao_torneio(populacao, pontos, cap_veiculo, k=3):
    """
    Seleciona o melhor indivíduo entre 'k' competidores escolhidos aleatoriamente.
    Preserva a diversidade genética.
    """
    competidores = random.sample(populacao, k)
    # Retorna aquele que tiver o menor custo (função fitness)
    return min(
        competidores, key=lambda ind: funcao_fitness_vrp(ind, pontos, cap_veiculo)
    )


def crossover(pai1, pai2):
    """
    Realiza o Crossover de Ordem (Order Crossover - OX).
    Preserva a ordem relativa dos genes e evita duplicatas.

    1. Copia um segmento aleatório do Pai 1 para o Filho.
    2. Preenche o restante com os genes do Pai 2, na ordem em que aparecem,
       pulando os que já estão no filho.
    """
    tamanho = len(pai1)
    if tamanho == 0:
        return pai1

    # Define o segmento de corte
    inicio, fim = sorted(random.sample(range(tamanho), 2))

    # Inicializa filho com marcadores
    filho = [-1] * tamanho

    # Herança do Pai 1 (cópia do segmento)
    filho[inicio:fim] = pai1[inicio:fim]

    # Herança do Pai 2 (preenchimento circular)
    pos_atual = fim
    for gene in pai2:
        if gene not in filho:
            if pos_atual >= tamanho:
                pos_atual = 0
            filho[pos_atual] = gene
            pos_atual += 1

    return filho


def mutacao(individuo, taxa_mutacao=0.2):
    """
    Mutação por troca (Swap Mutation).
    Troca dois genes de lugar aleatoriamente para introduzir diversidade.
    """
    if random.random() < taxa_mutacao:
        idx1, idx2 = random.sample(range(len(individuo)), 2)
        individuo[idx1], individuo[idx2] = individuo[idx2], individuo[idx1]
    return individuo


def executar_ga(pontos, cap_veiculo, geracoes=200, tam_populacao=50):
    """
    Executa o Algoritmo Genético principal para o problema de roteamento.

    Args:
        pontos (list): Lista de locais (incluindo depósito).
        cap_veiculo (float): Capacidade dos caminhões.
        geracoes (int): Número de iterações do algoritmo.
        tam_populacao (int): Tamanho da população por geração.

    Returns:
        tuple: (rotas_otimizadas, historico_fitness)
    """
    ids_locais = [p["id"] for p in pontos]

    # Cria um dicionário para acesso O(1) no algoritmo 2-opt (performance)
    dict_pontos = {p["id"]: p for p in pontos}

    # 1. Inicialização da População
    populacao = [criar_individuo(ids_locais) for _ in range(tam_populacao)]

    melhor_global = None
    melhor_fitness_global = float("inf")
    historico_fitness = []

    # Loop Principal (Evolução)
    for g in range(geracoes):
        # Avaliação de toda a população
        scores = [
            (ind, funcao_fitness_vrp(ind, pontos, cap_veiculo)) for ind in populacao
        ]
        # Ordena do melhor (menor custo) para o pior
        scores.sort(key=lambda x: x[1])

        # Elitismo: Atualiza a melhor solução encontrada até agora
        if scores[0][1] < melhor_fitness_global:
            melhor_fitness_global = scores[0][1]
            melhor_global = copy.deepcopy(scores[0][0])

        historico_fitness.append(melhor_fitness_global)

        # Conversão aproximada para KM (assumindo coordenadas geográficas lat/lon)
        # Nota: 111.139 km é aprox. 1 grau de latitude.
        distancia_km = melhor_fitness_global * 111.139
        print(
            f"[Geração {g:03}] Melhor Rota: {distancia_km:.2f} km (Custo Técnico: {melhor_fitness_global:.4f})"
        )

        # Reprodução
        nova_populacao = [melhor_global]  # Mantém o melhor (Elitismo)
        while len(nova_populacao) < tam_populacao:
            pai1 = selecao_torneio(populacao, pontos, cap_veiculo)
            pai2 = selecao_torneio(populacao, pontos, cap_veiculo)
            filho = mutacao(crossover(pai1, pai2))
            nova_populacao.append(filho)

        populacao = nova_populacao

    # Pós-processamento: Refinamento Local
    print("\n[INFO] Aplicando Busca Local 2-opt para refinamento final...")

    # Transforma o melhor cromossomo em rotas separadas
    rotas_finais = separar_rotas_por_capacidade(melhor_global, pontos, cap_veiculo)

    # Aplica 2-opt em cada rota individualmente
    rotas_otimizadas = [aplicar_2opt(r, dict_pontos) for r in rotas_finais]

    return rotas_otimizadas, historico_fitness
