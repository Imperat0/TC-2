🚑 Smart Medical Logistics: Otimização de Rotas (VRP) com Algoritmos Genéticos e GenAI

    Projeto Acadêmico - Pós-Graduação em IA para Devs (FIAP)

    Solução computacional aplicada ao Vehicle Routing Problem (VRP) com restrições de capacidade (CVRP) e janelas de prioridade, integrada a uma camada de análise preditiva via LLM (Google Gemini).

📋 Visão Geral da Arquitetura

O projeto foi desenhado para resolver problemas de logística hospitalar crítica, onde o tempo de entrega de insumos (sangue, órgãos, medicamentos) é vital. A solução opera em três camadas distintas:

    Motor de Otimização (Core): Utiliza Algoritmos Genéticos para encontrar soluções sub-ótimas em tempo polinomial para um problema NP-Hard.

    Camada de Inteligência (Analysis): Integração via API com Google Gemini 1.5 Flash para análise semântica de riscos, cruzando dados da rota gerada com zonas de tráfego simuladas.

    Camada de Visualização (Presentation): Simulação gráfica baseada em física (Pygame) para validação visual das rotas e monitoramento de KPIs.

⚙️ Detalhamento Técnico
1. Algoritmo Genético (Heurística Evolutiva)

Implementação pura em Python (sem bibliotecas de "caixa preta" para o GA), permitindo controle granular sobre os hiperparâmetros:

    Codificação: Permutação de inteiros (representação de caminhos).

    Função de Aptidão (Fitness): Minimização da distância Euclidiana total penalizada por excesso de capacidade.

    Operador de Seleção: Torneio (Tournament Selection) para preservação de diversidade.

    Crossover: Order Crossover (OX), garantindo a validade da permutação sem duplicatas.

    Mutação: Swap Mutation com decaimento dinâmico.

    Elitismo: Preservação dos top-N indivíduos para garantir a não-regressão da convergência.

2. Integração com Large Language Models (LLM)

Utilização do modelo Gemini 1.5 Flash para pós-processamento de dados logísticos.

    Prompt Engineering: Uso de técnicas de Chain of Thought e Few-Shot Prompting.

    Structured Output: A IA retorna dados estritamente em JSON, desacoplando a camada de inteligência do front-end e permitindo a estruturação de alertas (Risco Alto/Médio/Baixo).

🛠️ Stack Tecnológico

    Linguagem: Python 3.12

    Computação Científica: NumPy (vetorização de cálculos de distância).

    Visualização de Dados: Matplotlib (Gráficos de Convergência) e Pygame (Simulação em Tempo Real).

    GenAI SDK: Google GenAI (Integração com Gemini API).

    Qualidade: Unittest para validação de operadores genéticos e restrições de carga.