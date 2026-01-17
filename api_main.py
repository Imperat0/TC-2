from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import algoritmo_genetico as ag
import ia_relatorios as ia
import uvicorn

# --- INICIALIZAÇÃO DA API ---
app = FastAPI(
    title="Smart Medical Logistics API",
    description="API para otimização de rotas hospitalares e análise via Inteligência Artificial.",
    version="2.0",
)


# --- MODELOS DE DADOS (DTOs) ---
class ZonaTransito(BaseModel):
    """
    Define áreas de trânsito ou zonas de risco que podem influenciar a análise da IA.
    """

    nome: str
    intensidade: float
    raio_km: float


class Ponto(BaseModel):
    """
    Representa um local (nó) no mapa, seja um hospital, paciente ou depósito.
    """

    id: int
    nome: str
    coord: List[float] = Field(
        ..., description="Coordenadas geográficas [Latitude, Longitude]"
    )
    tipo: str
    carga: int = 0
    prioridade: str = "regular"  # Pode ser 'critica', 'alta' ou 'regular'


class ConfigOtimizacao(BaseModel):
    """
    Estrutura de entrada para o pedido de otimização de rotas.
    Contém todos os pontos a serem visitados e as restrições do veículo.
    """

    pontos: List[Ponto]
    capacidade_veiculo: int
    geracoes: int = 100
    zonas_transito: List[ZonaTransito] = []


class RequestRelatorio(BaseModel):
    """
    Estrutura de entrada para solicitar apenas a análise da IA sobre rotas já existentes.
    """

    rotas: List[List[int]]
    pontos: List[Ponto]
    zonas: List[ZonaTransito]


# --- ENDPOINTS (ROTAS DA API) ---


@app.get("/", tags=["Status"])
def read_root():
    """
    Verificação de saúde da API (Health Check).
    """
    return {"status": "Online", "service": "Smart Medical Logistics VRP"}


@app.post("/otimizar", tags=["Otimizacao"])
async def otimizar_rota(config: ConfigOtimizacao):
    """
    Executa exclusivamente o Algoritmo Genético (VRP).

    Entrada: Lista de pontos e capacidade do veículo.
    Saída: As rotas otimizadas (listas de IDs) e o histórico de convergência.
    """
    try:
        # Serializa os objetos Pydantic para dicionários Python
        pontos_processados = [p.model_dump() for p in config.pontos]

        rotas, historico = ag.executar_ga(
            pontos_processados, config.capacidade_veiculo, geracoes=config.geracoes
        )

        return {
            "rotas_otimizadas": rotas,
            "custo_final": historico[-1],
            "historico_convergencia": historico,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro interno no Algoritmo Genético: {str(e)}"
        )


@app.post("/relatorio", tags=["Analise IA"])
async def gerar_relatorio_ia(dados: RequestRelatorio):
    """
    Executa exclusivamente a análise de Inteligência Artificial.
    Útil quando já se tem as rotas e deseja-se apenas gerar os insights textuais.
    """
    try:
        pontos_dict = [p.model_dump() for p in dados.pontos]
        zonas_dict = [z.model_dump() for z in dados.zonas]

        # Chama o módulo de IA para gerar insights sobre as rotas fornecidas
        relatorio = ia.gerar_instrucoes_llm_v2(dados.rotas, pontos_dict, zonas_dict)
        return relatorio
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro interno no módulo de IA: {str(e)}"
        )


@app.post("/solucao-completa", tags=["Fluxo Completo"])
async def executar_processo_completo(config: ConfigOtimizacao):
    """
    Executa o fluxo completo: Otimização Matemática + Análise de IA.

    1. O Algoritmo Genético cria as melhores rotas.
    2. A IA analisa essas rotas considerando zonas de trânsito e prioridades.
    3. Retorna um objeto consolidado com rotas e relatórios.
    """
    try:
        # Passo 1: Otimização (Algoritmo Genético)
        pontos_processados = [p.model_dump() for p in config.pontos]
        rotas, historico = ag.executar_ga(
            pontos_processados, config.capacidade_veiculo, geracoes=config.geracoes
        )

        # Passo 2: Análise (Inteligência Artificial)
        zonas_dict = [z.model_dump() for z in config.zonas_transito]
        analise_ia = ia.gerar_instrucoes_llm_v2(rotas, pontos_processados, zonas_dict)

        # Passo 3: Retorno Consolidado
        return {
            "meta_info": {"custo_rota": historico[-1], "geracoes": config.geracoes},
            "rotas": rotas,
            "analise_inteligente": analise_ia,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro no processamento completo: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
