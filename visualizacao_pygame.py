import pygame
import sys

# --- CONFIGURAÇÕES VISUAIS ---
LARGURA, ALTURA = 1300, 750
COR_FUNDO = (242, 244, 247)
COR_PAINEL = (33, 47, 61)
COR_TRANSITO = (231, 76, 60, 60)

# Cores Temáticas
VERDE_HUB = (46, 204, 113)
VERMELHO_CRITICO = (231, 76, 60)
AZUL_NORMAL = (52, 152, 219)
BRANCO = (255, 255, 255)
PRETO = (28, 40, 51)
CINZA_TEXTO = (171, 178, 185)

CORES_ROTAS = [
    (243, 156, 18),
    (142, 68, 173),
    (22, 160, 133),
    (255, 20, 147),
    (241, 196, 15),
    (211, 84, 0),
    (41, 128, 185),
]


def normalizar_coordenadas(pontos, largura, altura, margem=80):
    lats = [p["coord"][0] for p in pontos]
    lons = [p["coord"][1] for p in pontos]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    lat_range = max_lat - min_lat if max_lat != min_lat else 1
    lon_range = max_lon - min_lon if max_lon != min_lon else 1

    mapa_pixels = {}
    for p in pontos:
        y_norm = (p["coord"][0] - min_lat) / lat_range
        x_norm = (p["coord"][1] - min_lon) / lon_range
        x = int(margem + x_norm * (largura - 300 - 2 * margem))
        y = int(altura - margem - y_norm * (altura - 2 * margem))
        mapa_pixels[p["id"]] = (x, y)
    return mapa_pixels, (min_lat, max_lat, lat_range, min_lon, max_lon, lon_range)


def visualizar_rotas_pygame(rotas, pontos_dados, zonas_transito=[]):
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Smart Logistics Dashboard - Daniel Imperato")
    clock = pygame.time.Clock()

    fonte_p = pygame.font.SysFont("Segoe UI", 12, bold=True)
    fonte_m = pygame.font.SysFont("Segoe UI", 15, bold=True)
    fonte_g = pygame.font.SysFont("Segoe UI", 22, bold=True)
    fonte_relogio = pygame.font.SysFont(
        "Consolas", 32, bold=True
    )  # Fonte estilo digital

    coords_pixel, bounds = normalizar_coordenadas(pontos_dados, LARGURA, ALTURA)
    min_lat, max_lat, lat_range, min_lon, max_lon, lon_range = bounds

    # Processamento visual das zonas de trânsito
    for z in zonas_transito:
        y_n = (z["coord"][0] - min_lat) / lat_range
        x_n = (z["coord"][1] - min_lon) / lon_range
        z["px"] = int(80 + x_n * (LARGURA - 300 - 160))
        z["py"] = int(ALTURA - 80 - y_n * (ALTURA - 160))
        z["raio_px"] = int(z["raio_km"] * 8500)

    # Variáveis de Tempo e Telemetria
    telemetria_pontos = {}
    frames_totais = 0  # Contador para o relógio

    veiculos = []
    for i, rota in enumerate(rotas):
        carga_total = sum(
            next(p["carga"] for p in pontos_dados if p["id"] == pid)
            for pid in rota
            if pid != 0
        )
        veiculos.append(
            {
                "id": i + 1,
                "rota": rota,
                "idx": 0,
                "progresso": 0.0,
                "cor": CORES_ROTAS[i % len(CORES_ROTAS)],
                "v_base": 0.012 + (i * 0.001),
                "carga_total": carga_total,
                "soma_v": 0,
                "f_count": 0,
                "no_transito": False,
            }
        )

    while True:
        mouse_pos = pygame.mouse.get_pos()
        ponto_hover = None

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_SPACE:
                for v in veiculos:
                    v["idx"] = 0
                    v["progresso"] = 0.0
                    telemetria_pontos.clear()
                frames_totais = 0  # Reinicia o relógio

        tela.fill(COR_FUNDO)
        frames_totais += 1  # Incrementa o tempo

        # 1. ZONAS DE TRÂNSITO
        for z in zonas_transito:
            s = pygame.Surface((z["raio_px"] * 2, z["raio_px"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                s, COR_TRANSITO, (z["raio_px"], z["raio_px"]), z["raio_px"]
            )
            tela.blit(s, (z["px"] - z["raio_px"], z["py"] - z["raio_px"]))

        # 2. PAINEL LATERAL
        pygame.draw.rect(tela, COR_PAINEL, (LARGURA - 300, 0, 300, ALTURA))

        # --- NOVO: RELÓGIO DE SIMULAÇÃO ---
        # Lógica: 30 frames = 1 minuto de simulação. Início às 08:00
        minutos_sim = (frames_totais // 30) % 60
        horas_sim = (8 + (frames_totais // 1800)) % 24
        tempo_str = f"{horas_sim:02d}:{minutos_sim:02d}"

        relogio_surf = fonte_relogio.render(tempo_str, True, VERDE_HUB)
        tela.blit(relogio_surf, (LARGURA - 190, 30))
        tela.blit(
            fonte_p.render("TEMPO DE OPERAÇÃO", True, CINZA_TEXTO), (LARGURA - 190, 15)
        )

        tela.blit(fonte_g.render("FROTA ATIVA", True, BRANCO), (LARGURA - 270, 90))

        for i, v in enumerate(veiculos):
            y_off = 140 + (i * 70)
            pygame.draw.rect(tela, v["cor"], (LARGURA - 280, y_off, 12, 50), 0, 3)
            tela.blit(
                fonte_m.render(f"Veículo #{v['id']}", True, BRANCO),
                (LARGURA - 260, y_off),
            )

            status_txt = "EM TRÂNSITO" if not v.get("concluido") else "FINALIZADO"
            status_cor = AZUL_NORMAL if not v.get("concluido") else CINZA_TEXTO
            if v["no_transito"]:
                status_txt = "CONGESTIONADO"
                status_cor = VERMELHO_CRITICO

            tela.blit(
                fonte_p.render(status_txt, True, status_cor),
                (LARGURA - 260, y_off + 20),
            )

            # Barra de Carga
            pygame.draw.rect(
                tela, (50, 50, 50), (LARGURA - 260, y_off + 40, 180, 6), 0, 3
            )
            pygame.draw.rect(
                tela,
                v["cor"],
                (LARGURA - 260, y_off + 40, int(180 * (v["carga_total"] / 200)), 6),
                0,
                3,
            )

        # 3. ROTAS E ENTREGAS
        for i, rota in enumerate(rotas):
            pts = [coords_pixel[pid] for pid in rota]
            if len(pts) > 1:
                pygame.draw.lines(
                    tela, CORES_ROTAS[i % len(CORES_ROTAS)], False, pts, 2
                )

        for p in pontos_dados:
            px, py = coords_pixel[p["id"]]
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

            if ((px - mouse_pos[0]) ** 2 + (py - mouse_pos[1]) ** 2) ** 0.5 < 15:
                ponto_hover = p

        # 4. ANIMAÇÃO E TELEMETRIA
        todos_concluidos = True
        for v in veiculos:
            if v["idx"] >= len(v["rota"]) - 1:
                v["concluido"] = True
                continue

            todos_concluidos = False
            p1, p2 = (
                coords_pixel[v["rota"][v["idx"]]],
                coords_pixel[v["rota"][v["idx"] + 1]],
            )
            x = p1[0] + (p2[0] - p1[0]) * v["progresso"]
            y = p1[1] + (p2[1] - p1[1]) * v["progresso"]

            fator = 1.0
            v["no_transito"] = False
            for z in zonas_transito:
                if ((x - z["px"]) ** 2 + (y - z["py"]) ** 2) ** 0.5 < z["raio_px"]:
                    fator = 1.0 - z["intensidade"]
                    v["no_transito"] = True

            pygame.draw.circle(tela, BRANCO, (int(x), int(y)), 9)
            pygame.draw.circle(tela, v["cor"], (int(x), int(y)), 6)

            # Acumula telemetria
            v["soma_v"] += (v["v_base"] * fator) * 5000
            v["f_count"] += 1

            v["progresso"] += v["v_base"] * fator
            if v["progresso"] >= 1.0:
                telemetria_pontos[v["rota"][v["idx"] + 1]] = v["soma_v"] / v["f_count"]
                v["progresso"] = 0.0
                v["idx"] += 1
                v["soma_v"] = 0
                v["f_count"] = 0

        # Para o relógio se todos acabarem
        if todos_concluidos:
            frames_totais -= 1

        # 5. TOOLTIP
        if ponto_hover:
            box_w, box_h = 240, 85
            pygame.draw.rect(
                tela, BRANCO, (mouse_pos[0] + 15, mouse_pos[1] + 15, box_w, box_h), 0, 8
            )
            pygame.draw.rect(
                tela, PRETO, (mouse_pos[0] + 15, mouse_pos[1] + 15, box_w, box_h), 2, 8
            )

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

        pygame.display.flip()
        clock.tick(60)
