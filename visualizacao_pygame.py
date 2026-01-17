import pygame
import sys

# --- CONFIGURAÇÕES VISUAIS E PALETA DE CORES ---
LARGURA, ALTURA = 1300, 750
COR_FUNDO = (242, 244, 247)  # Cinza muito claro (clean)
COR_PAINEL = (33, 47, 61)  # Azul escuro (dashboard)
COR_TRANSITO = (231, 76, 60, 60)  # Vermelho com transparência (zonas de risco)

# Cores de Status
VERDE_HUB = (46, 204, 113)  # Depósito/Sucesso
VERMELHO_CRITICO = (231, 76, 60)  # Prioridade Alta
AZUL_NORMAL = (52, 152, 219)  # Prioridade Normal
BRANCO = (255, 255, 255)
PRETO = (28, 40, 51)
CINZA_TEXTO = (171, 178, 185)

# Paleta de cores para diferenciar as rotas de cada veículo
CORES_ROTAS = [
    (243, 156, 18),  # Laranja
    (142, 68, 173),  # Roxo
    (22, 160, 133),  # Verde Mar
    (255, 20, 147),  # Rosa
    (241, 196, 15),  # Amarelo
    (211, 84, 0),  # Marrom
    (41, 128, 185),  # Azul
]


def normalizar_coordenadas(pontos, largura, altura, margem=80):
    """
    Converte coordenadas geográficas (Latitude/Longitude) em pixels da tela (X, Y).
    Utiliza normalização Min-Max para garantir que todos os pontos caibam na tela.

    Args:
        pontos (list): Lista de locais.
        largura, altura (int): Dimensões da janela.
        margem (int): Espaço vazio nas bordas para estética.

    Returns:
        dict: Mapeamento {id_ponto: (pixel_x, pixel_y)}.
        tuple: Limites geográficos calculados (para uso posterior).
    """
    lats = [p["coord"][0] for p in pontos]
    lons = [p["coord"][1] for p in pontos]

    # Encontra os extremos do mapa
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    # Evita divisão por zero se houver apenas 1 ponto
    lat_range = max_lat - min_lat if max_lat != min_lat else 1
    lon_range = max_lon - min_lon if max_lon != min_lon else 1

    mapa_pixels = {}
    for p in pontos:
        # Fórmula de normalização: (Valor - Min) / (Max - Min)
        # Invertemos o Y (latitude) pois em telas o Y cresce para baixo
        y_norm = (p["coord"][0] - min_lat) / lat_range
        x_norm = (p["coord"][1] - min_lon) / lon_range

        # Escala para o tamanho da tela (descontando o painel lateral de 300px)
        x = int(margem + x_norm * (largura - 300 - 2 * margem))
        y = int(altura - margem - y_norm * (altura - 2 * margem))
        mapa_pixels[p["id"]] = (x, y)

    return mapa_pixels, (min_lat, max_lat, lat_range, min_lon, max_lon, lon_range)


def visualizar_rotas_pygame(rotas, pontos_dados, zonas_transito=[]):
    """
    Inicializa o loop principal da simulação visual.
    Renderiza o mapa, veículos em movimento e painel de telemetria.
    """
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Smart Logistics VRP - Monitoramento em Tempo Real")
    clock = pygame.time.Clock()  # Controle de FPS

    # --- SETUP DE FONTES ---
    fonte_p = pygame.font.SysFont("Segoe UI", 12, bold=True)  # Textos pequenos
    fonte_m = pygame.font.SysFont("Segoe UI", 15, bold=True)  # Títulos médios
    fonte_g = pygame.font.SysFont("Segoe UI", 22, bold=True)  # Títulos grandes
    fonte_relogio = pygame.font.SysFont("Consolas", 32, bold=True)  # Relógio digital

    # --- PREPARAÇÃO DE DADOS ---
    # Converte lat/lon para pixels
    coords_pixel, bounds = normalizar_coordenadas(pontos_dados, LARGURA, ALTURA)
    min_lat, max_lat, lat_range, min_lon, max_lon, lon_range = bounds

    # Processa as zonas de trânsito (converte raio km para pixels)
    for z in zonas_transito:
        y_n = (z["coord"][0] - min_lat) / lat_range
        x_n = (z["coord"][1] - min_lon) / lon_range
        z["px"] = int(80 + x_n * (LARGURA - 300 - 160))
        z["py"] = int(ALTURA - 80 - y_n * (ALTURA - 160))
        z["raio_px"] = int(z["raio_km"] * 8500)  # Fator de escala visual

    # --- INICIALIZAÇÃO DA FROTA ---
    veiculos = []
    for i, rota in enumerate(rotas):
        # Calcula carga total do veículo para exibir na barra de progresso
        carga_total = sum(
            next(p["carga"] for p in pontos_dados if p["id"] == pid)
            for pid in rota
            if pid != 0
        )
        veiculos.append(
            {
                "id": i + 1,
                "rota": rota,
                "idx": 0,  # Índice do ponto atual na rota
                "progresso": 0.0,  # Porcentagem do trajeto entre dois pontos (0.0 a 1.0)
                "cor": CORES_ROTAS[i % len(CORES_ROTAS)],
                "v_base": 0.012
                + (i * 0.001),  # Velocidade base (leve variação para realismo)
                "carga_total": carga_total,
                "concluido": False,
                "no_transito": False,  # Flag de estado (se está em área de risco)
                # Variáveis para cálculo de velocidade média
                "soma_v": 0,
                "f_count": 0,
            }
        )

    telemetria_pontos = {}  # Armazena dados para o Tooltip (mouse hover)
    frames_totais = 0

    # --- LOOP PRINCIPAL (GAME LOOP) ---
    while True:
        mouse_pos = pygame.mouse.get_pos()
        ponto_hover = None  # Reseta o ponto sob o mouse

        # 1. Tratamento de Eventos (Teclado/Mouse)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # Tecla ESPAÇO reinicia a simulação
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
                for v in veiculos:
                    v["idx"] = 0
                    v["progresso"] = 0.0
                    v["concluido"] = False
                    v["soma_v"] = 0
                    telemetria_pontos.clear()
                frames_totais = 0

        # 2. Renderização do Fundo
        tela.fill(COR_FUNDO)
        frames_totais += 1

        # 3. Desenho das Zonas de Trânsito (Círculos vermelhos transparentes)
        for z in zonas_transito:
            # Cria uma superfície temporária para suportar canal Alpha (transparência)
            s = pygame.Surface((z["raio_px"] * 2, z["raio_px"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                s, COR_TRANSITO, (z["raio_px"], z["raio_px"]), z["raio_px"]
            )
            tela.blit(s, (z["px"] - z["raio_px"], z["py"] - z["raio_px"]))

        # 4. Desenho do Painel Lateral (Dashboard)
        pygame.draw.rect(tela, COR_PAINEL, (LARGURA - 300, 0, 300, ALTURA))

        # Relógio Simulado
        minutos_sim = (frames_totais // 30) % 60
        horas_sim = (8 + (frames_totais // 1800)) % 24  # Começa as 08:00
        tempo_str = f"{horas_sim:02d}:{minutos_sim:02d}"

        tela.blit(fonte_relogio.render(tempo_str, True, VERDE_HUB), (LARGURA - 190, 30))
        tela.blit(
            fonte_p.render("TEMPO DE OPERAÇÃO", True, CINZA_TEXTO), (LARGURA - 190, 15)
        )
        tela.blit(fonte_g.render("FROTA ATIVA", True, BRANCO), (LARGURA - 270, 90))

        # Lista de Veículos no Painel
        for i, v in enumerate(veiculos):
            y_off = 140 + (i * 70)
            # Ícone do veículo
            pygame.draw.rect(tela, v["cor"], (LARGURA - 280, y_off, 12, 50), 0, 3)

            # Texto identificador
            tela.blit(
                fonte_m.render(f"Veículo #{v['id']}", True, BRANCO),
                (LARGURA - 260, y_off),
            )

            # Status (Em Trânsito / Congestionado / Finalizado)
            status_txt = "EM OPERAÇÃO" if not v.get("concluido") else "FINALIZADO"
            status_cor = AZUL_NORMAL if not v.get("concluido") else CINZA_TEXTO

            if v["no_transito"] and not v.get("concluido"):
                status_txt = "REDUÇÃO VELOCIDADE"
                status_cor = VERMELHO_CRITICO

            tela.blit(
                fonte_p.render(status_txt, True, status_cor),
                (LARGURA - 260, y_off + 20),
            )

            # Barra de Capacidade de Carga
            pygame.draw.rect(
                tela, (50, 50, 50), (LARGURA - 260, y_off + 40, 180, 6), 0, 3
            )  # Fundo
            largura_barra = int(
                180 * (v["carga_total"] / 200)
            )  # Exemplo: 200kg cap max
            pygame.draw.rect(
                tela, v["cor"], (LARGURA - 260, y_off + 40, largura_barra, 6), 0, 3
            )  # Frente

        # 5. Desenho das Rotas (Linhas)
        for i, rota in enumerate(rotas):
            pts = [coords_pixel[pid] for pid in rota]
            if len(pts) > 1:
                pygame.draw.lines(
                    tela, CORES_ROTAS[i % len(CORES_ROTAS)], False, pts, 2
                )

        # 6. Desenho dos Pontos (Hospitais/Depósito)
        for p in pontos_dados:
            px, py = coords_pixel[p["id"]]

            # Desenha Depósito (Quadrado) ou Hospital (Círculo)
            if p["tipo"] == "deposito":
                pygame.draw.rect(tela, VERDE_HUB, (px - 15, py - 15, 30, 30), 0, 5)
            else:
                cor = (
                    VERMELHO_CRITICO
                    if p.get("prioridade") == "crítica"
                    else AZUL_NORMAL
                )
                pygame.draw.circle(
                    tela, cor, (px, py), 8 if p.get("prioridade") == "crítica" else 6
                )

            # Detecção de Mouse Hover (Interatividade)
            dist_mouse = ((px - mouse_pos[0]) ** 2 + (py - mouse_pos[1]) ** 2) ** 0.5
            if dist_mouse < 15:
                ponto_hover = p

        # 7. Lógica de Animação dos Veículos (Interpolação Linear)
        todos_concluidos = True
        for v in veiculos:
            # Verifica se chegou ao fim da rota
            if v["idx"] >= len(v["rota"]) - 1:
                v["concluido"] = True
                continue

            todos_concluidos = False

            # Pega coordenada atual (p1) e próxima (p2)
            p1 = coords_pixel[v["rota"][v["idx"]]]
            p2 = coords_pixel[v["rota"][v["idx"] + 1]]

            # Fórmula de Interpolação: Posição = Inicio + (Fim - Inicio) * Progresso
            x = p1[0] + (p2[0] - p1[0]) * v["progresso"]
            y = p1[1] + (p2[1] - p1[1]) * v["progresso"]

            # Verifica impacto do trânsito
            fator_velocidade = 1.0
            v["no_transito"] = False
            for z in zonas_transito:
                dist_zona = ((x - z["px"]) ** 2 + (y - z["py"]) ** 2) ** 0.5
                if dist_zona < z["raio_px"]:
                    fator_velocidade = (
                        1.0 - z["intensidade"]
                    )  # Reduz velocidade (ex: -70%)
                    v["no_transito"] = True

            # Desenha o veículo (Ponto colorido sobre a linha)
            pygame.draw.circle(tela, BRANCO, (int(x), int(y)), 9)  # Borda
            pygame.draw.circle(tela, v["cor"], (int(x), int(y)), 6)  # Núcleo

            # Atualiza Telemetria
            v["soma_v"] += (v["v_base"] * fator_velocidade) * 5000  # Simulação de KM/H
            v["f_count"] += 1

            # Atualiza Progresso
            v["progresso"] += v["v_base"] * fator_velocidade

            # Se completou o trecho, passa para o próximo ponto
            if v["progresso"] >= 1.0:
                id_destino = v["rota"][v["idx"] + 1]
                telemetria_pontos[id_destino] = (
                    v["soma_v"] / v["f_count"] if v["f_count"] > 0 else 0
                )

                v["progresso"] = 0.0
                v["idx"] += 1
                v["soma_v"] = 0
                v["f_count"] = 0

        # Para o relógio se a simulação acabou
        if todos_concluidos:
            frames_totais -= 1

        # 8. Desenho do Tooltip (Caixa de Informação Flutuante)
        if ponto_hover:
            box_w, box_h = 240, 85
            # Fundo branco com borda preta
            pygame.draw.rect(
                tela, BRANCO, (mouse_pos[0] + 15, mouse_pos[1] + 15, box_w, box_h), 0, 8
            )
            pygame.draw.rect(
                tela, PRETO, (mouse_pos[0] + 15, mouse_pos[1] + 15, box_w, box_h), 2, 8
            )

            # Dados do local
            vel = telemetria_pontos.get(ponto_hover["id"], 0)
            status_v = f"{vel:.1f} km/h" if vel > 0 else "---"

            tela.blit(
                fonte_m.render(ponto_hover["nome"], True, PRETO),
                (mouse_pos[0] + 25, mouse_pos[1] + 25),
            )
            tela.blit(
                fonte_p.render(
                    f"Carga: {ponto_hover.get('carga',0)}kg", True, (80, 80, 80)
                ),
                (mouse_pos[0] + 25, mouse_pos[1] + 45),
            )
            tela.blit(
                fonte_p.render(f"Velocidade Média: {status_v}", True, AZUL_NORMAL),
                (mouse_pos[0] + 25, mouse_pos[1] + 62),
            )

        # Atualiza a tela e limita a 60 FPS
        pygame.display.flip()
        clock.tick(60)
