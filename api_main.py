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
    description="API para otimização de rotas hospitalares e análise via GenAI.",
    version="2.0",
)

# --- CONFIGURAÇÃO DE CORS (Essencial para Angular) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, troque "*" pelo URL do seu Angular
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- SCHEMAS DE DADOS (Modelos) ---
class ZonaTransito(BaseModel):
    nome: str
    intensidade: float
    raio_km: float


class Ponto(BaseModel):
    id: int
    nome: str
    coord: List[float] = Field(..., description="[Latitude, Longitude]")
    tipo: str
    carga: int = 0
    prioridade: str = "regular"


class ConfigOtimizacao(BaseModel):
    pontos: List[Ponto]
    capacidade_veiculo: int
    geracoes: int = 100
    zonas_transito: List[ZonaTransito] = []


class RequestRelatorio(BaseModel):
    rotas: List[List[int]]
    pontos: List[Ponto]
    zonas: List[ZonaTransito]


# --- ENDPOINTS ---


@app.get("/", tags=["Status"])
def read_root():
    return {"status": "Online", "service": "Smart Medical Logistics VRP"}


@app.post("/otimizar", tags=["Core"])
async def otimizar_rota(config: ConfigOtimizacao):
    """
    Executa apenas o Algoritmo Genético e retorna as rotas numéricas.
    """
    try:
        # Pydantic V2 usa model_dump() ao invés de dict()
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
        raise HTTPException(status_code=500, detail=f"Erro no GA: {str(e)}")


@app.post("/relatorio", tags=["AI Analysis"])
async def gerar_relatorio_ia(dados: RequestRelatorio):
    """
    Gera apenas a análise textual/JSON da IA com base em rotas já existentes.
    """
    try:
        # Converte para dicionários para passar para a função legada
        pontos_dict = [p.model_dump() for p in dados.pontos]
        zonas_dict = [z.model_dump() for z in dados.zonas]

        # IMPORTANTE: Verifique se no seu arquivo ia_relatorios a função é v2 ou a normal
        relatorio = ia.gerar_instrucoes_llm_v2(dados.rotas, pontos_dict, zonas_dict)
        return relatorio  # Já retorna o JSON estruturado da IA
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na IA: {str(e)}")


@app.post("/solucao-completa", tags=["Full Flow"])
async def executar_processo_completo(config: ConfigOtimizacao):
    """
    🚀 ENDPOINT MÁGICO: Executa Otimização + Análise de IA em uma única chamada.
    Ideal para o Front-end chamar apenas uma vez.
    """
    try:
        # 1. Executa GA
        pontos_processados = [p.model_dump() for p in config.pontos]
        rotas, historico = ag.executar_ga(
            pontos_processados, config.capacidade_veiculo, geracoes=config.geracoes
        )

        # 2. Executa IA
        zonas_dict = [z.model_dump() for z in config.zonas_transito]
        analise_ia = ia.gerar_instrucoes_llm_v2(rotas, pontos_processados, zonas_dict)

        # 3. Retorna tudo junto
        return {
            "meta_info": {"custo_rota": historico[-1], "geracoes": config.geracoes},
            "rotas": rotas,
            "analise_inteligente": analise_ia,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no fluxo completo: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
