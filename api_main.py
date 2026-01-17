from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import algoritmo_genetico as ag
import ia_relatorios as ia
import uvicorn

app = FastAPI(title="Smart Medical Logistics API")


# --- SCHEMAS DE DADOS (Pydantic) ---
class Ponto(BaseModel):
    id: int
    nome: str
    coord: List[float]  # [lat, lon]
    tipo: str
    carga: int = 0
    prioridade: str = "regular"


class ConfigOtimizacao(BaseModel):
    pontos: List[Ponto]
    capacidade_veiculo: int
    geracoes: int = 100
    zonas_transito: List[Dict[str, Any]] = []



@app.get("/")
def read_root():
    return {"status": "Online", "service": "Logistics Optimizer"}


@app.post("/otimizar")
async def otimizar_rota(config: ConfigOtimizacao):
    try:
        # Converte os modelos Pydantic para o formato esperado pelo GA
        pontos_processados = [p.dict() for p in config.pontos]

        rotas, historico = ag.executar_ga(
            pontos_processados, config.capacidade_veiculo, geracoes=config.geracoes
        )

        return {"rotas": rotas, "custo_final": historico[-1], "convergencia": historico}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/relatorio")
async def gerar_relatorio_ia(dados: Dict[str, Any]):
    try:
        relatorio = ia.gerar_instrucoes_llm(
            dados["rotas"], dados["pontos"], dados["zonas"]
        )
        return {"relatorio": relatorio}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao processar IA")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
