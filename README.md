# 🚑 Smart Medical Logistics (VRP-AI)

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![FIAP](https://img.shields.io/badge/FIAP-Pos_Graduacao-ed145b?style=for-the-badge)
![AI](https://img.shields.io/badge/GenAI-Google_Gemini-orange?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Concluido-success?style=for-the-badge)

> **Projeto Acadêmico - Pós-Graduação em IA para Devs (FIAP)**
>
> Solução computacional para o *Vehicle Routing Problem* (VRP) com restrições de capacidade e análise preditiva via LLM.

---

## 📋 Visão Geral

Este projeto aborda o desafio da logística hospitalar crítica, onde o tempo de entrega de insumos (sangue, órgãos, medicamentos) é vital. A solução não apenas calcula a rota matemática, mas "entende" o contexto da entrega.

O sistema opera em três camadas distintas:

1.  **Core (Otimização):** Resolve o problema matemático (NP-Hard) usando Algoritmos Genéticos para encontrar rotas eficientes.
2.  **Analysis (Inteligência):** Uma camada de GenAI (Google Gemini) que atua como um "Gerente de Logística", analisando riscos e sugerindo ações (ex: escolta policial para cargas críticas).
3.  **Presentation (Visualização):** Simulação gráfica baseada em física para validação das rotas e monitoramento em tempo real.

---

## ⚙️ Arquitetura Técnica

### 1. Algoritmo Genético (Heurística Evolutiva)
Implementação *from-scratch* (sem bibliotecas de caixa preta) para controle total dos hiperparâmetros.

* **Codificação:** Permutação de inteiros (Path Representation).
* **Fitness Function:** Minimização da distância Euclidiana + Penalidade por excesso de carga (Soft Constraint).
* **Seleção:** Torneio (Tournament Selection) com `k=3` para pressão seletiva.
* **Crossover:** Order Crossover (OX1), essencial para evitar cidades duplicadas no cromossomo.
* **Mutação:** Swap Mutation para introduzir diversidade e evitar ótimos locais.
* **Elitismo:** Preservação dos melhores indivíduos entre gerações.

### 2. Integração com LLM (GenAI)
Uso do modelo **`gemini-3-flash-preview`** via API para análise semântica.

* **Prompt Engineering:** Utiliza *Few-Shot Prompting* e regras de negócio explícitas no prompt.
* **Structured Output:** A IA é forçada a retornar um JSON estrito, permitindo que o sistema classifique riscos (🔴 Alto / 🟡 Médio / 🟢 Baixo) programaticamente.

---

## 🛠️ Stack Tecnológico

| Categoria | Tecnologia | Uso no Projeto |
| :--- | :--- | :--- |
| **Linguagem** | ![Python](https://img.shields.io/badge/-Python_3.12-black) | Core da aplicação |
| **Computação** | `NumPy` | Vetorização de cálculos de distância (Euclidiana) |
| **Visualização** | `Pygame` | Simulação visual interativa da frota |
| **Dados** | `Matplotlib` | Gráficos de convergência do algoritmo |
| **GenAI** | `Google Generative AI` | SDK para conexão com o Gemini |
| **API** | `FastAPI` | (Opcional) Exposição dos endpoints de otimização |

---

## 🚀 Como Executar

### Pré-requisitos
* Python 3.10 ou superior
* Chave de API do Google Gemini (Google AI Studio)

### Instalação

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/Imperat0/TC-2.git](https://github.com/Imperat0/TC-2)