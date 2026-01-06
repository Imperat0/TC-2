import random
import numpy as np
import copy


# --- Funções Auxiliares ---
def calcular_distancia(ponto1, ponto2):
    return np.sqrt((ponto1[0] - ponto2[0]) ** 2 + (ponto1[1] - ponto2[1]) ** 2)


def separar_rotas_por_capacidade(cromossomo, pontos, cap_max):
    rotas_finais = []
    rota_atual = [0]
    carga_atual = 0

    for id_ponto in cromossomo:
        ponto = next(p for p in pontos if p["id"] == id_ponto)
        peso_entrega = ponto.get("carga", 0)

        if carga_atual + peso_entrega > cap_max:
            rota_atual.append(0)
            rotas_finais.append(rota_atual)
            rota_atual = [0, id_ponto]
            carga_atual = peso_entrega
        else:
            rota_atual.append(id_ponto)
            carga_atual += peso_entrega

    rota_atual.append(0)
    rotas_finais.append(rota_atual)
    return rotas_finais


# --- NOVO: HEURÍSTICA DE BUSCA LOCAL 2-OPT ---
def aplicar_2opt(rota, pontos):
    """
    Refina uma rota individual eliminando cruzamentos.
    """
    melhor_rota = rota[:]
    otimizou = True

    while otimizou:
        otimizou = False
        for i in range(1, len(melhor_rota) - 2):
            for j in range(i + 1, len(melhor_rota) - 1):
                # Se inverter o trecho entre i e j diminuir a distância, inverte
                # Distâncias atuais
                d1 = calcular_distancia(
                    pontos[melhor_rota[i - 1]]["coord"], pontos[melhor_rota[i]]["coord"]
                )
                d2 = calcular_distancia(
                    pontos[melhor_rota[j]]["coord"], pontos[melhor_rota[j + 1]]["coord"]
                )

                # Distâncias se trocarmos as conexões
                d3 = calcular_distancia(
                    pontos[melhor_rota[i - 1]]["coord"], pontos[melhor_rota[j]]["coord"]
                )
                d4 = calcular_distancia(
                    pontos[melhor_rota[i]]["coord"], pontos[melhor_rota[j + 1]]["coord"]
                )

                if (d3 + d4) < (d1 + d2):
                    melhor_rota[i : j + 1] = reversed(melhor_rota[i : j + 1])
                    otimizou = True
    return melhor_rota


def funcao_fitness_vrp(cromossomo, pontos, cap_max):
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
            if ponto_atual.get("prioridade") == "crítica":
                dist_trecho *= 0.5
            dist_rota += dist_trecho
            ponto_anterior = ponto_atual
        custo_total += dist_rota
    return custo_total


# --- Operadores Genéticos ---
def criar_individuo(lista_ids_locais):
    entregas = [x for x in lista_ids_locais if x != 0]
    random.shuffle(entregas)
    return entregas


def selecao_torneio(populacao, pontos, cap_veiculo, k=3):
    competidores = random.sample(populacao, k)
    return min(
        competidores, key=lambda ind: funcao_fitness_vrp(ind, pontos, cap_veiculo)
    )


def crossover(pai1, pai2):
    tamanho = len(pai1)
    if tamanho == 0:
        return pai1
    inicio, fim = sorted(random.sample(range(tamanho), 2))
    filho = [-1] * tamanho
    filho[inicio:fim] = pai1[inicio:fim]
    pos_atual = fim
    for gene in pai2:
        if gene not in filho:
            if pos_atual >= tamanho:
                pos_atual = 0
            filho[pos_atual] = gene
            pos_atual += 1
    return filho


def mutacao(individuo, taxa_mutacao=0.2):
    if random.random() < taxa_mutacao:
        idx1, idx2 = random.sample(range(len(individuo)), 2)
        individuo[idx1], individuo[idx2] = individuo[idx2], individuo[idx1]
    return individuo


def executar_ga(pontos, cap_veiculo, geracoes=200, tam_populacao=50):
    ids_locais = [p["id"] for p in pontos]
    # Mapeamento rápido para o 2-opt
    dict_pontos = {p["id"]: p for p in pontos}

    populacao = [criar_individuo(ids_locais) for _ in range(tam_populacao)]
    melhor_global = None
    melhor_fitness_global = float("inf")
    historico_fitness = []

    for g in range(geracoes):
        scores = [
            (ind, funcao_fitness_vrp(ind, pontos, cap_veiculo)) for ind in populacao
        ]
        scores.sort(key=lambda x: x[1])

        if scores[0][1] < melhor_fitness_global:
            melhor_fitness_global = scores[0][1]
            melhor_global = copy.deepcopy(scores[0][0])

        historico_fitness.append(melhor_fitness_global)
        print(f"Geração {g}: Custo = {melhor_fitness_global:.4f}")

        nova_populacao = [melhor_global]
        while len(nova_populacao) < tam_populacao:
            pai1 = selecao_torneio(populacao, pontos, cap_veiculo)
            pai2 = selecao_torneio(populacao, pontos, cap_veiculo)
            filho = mutacao(crossover(pai1, pai2))
            nova_populacao.append(filho)
        populacao = nova_populacao

    # --- REFINAMENTO FINAL COM 2-OPT ---
    print("\n[INFO] Aplicando Busca Local 2-opt para refinamento final...")
    rotas_finais = separar_rotas_por_capacidade(melhor_global, pontos, cap_veiculo)
    rotas_otimizadas = [aplicar_2opt(r, dict_pontos) for r in rotas_finais]

    return rotas_otimizadas, historico_fitness
