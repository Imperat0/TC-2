import unittest
import algoritmo_genetico as ag


class TestLogistica(unittest.TestCase):
    def setUp(self):
        self.pontos = [
            {"id": 0, "coord": (0, 0), "tipo": "deposito", "carga": 0},
            {"id": 1, "coord": (1, 1), "tipo": "entrega", "carga": 150},
            {"id": 2, "coord": (2, 2), "tipo": "entrega", "carga": 60},
        ]

    def test_estouro_capacidade(self):
        # Com 150kg + 60kg e limite de 200, deve gerar 2 veículos
        rotas = ag.separar_rotas_por_capacidade([1, 2], self.pontos, 200)
        self.assertEqual(len(rotas), 2)

    def test_formato_rota(self):
        # A rota deve sempre começar e terminar no depósito (0)
        rotas = ag.separar_rotas_por_capacidade([1], self.pontos, 200)
        self.assertEqual(rotas[0][0], 0)
        self.assertEqual(rotas[0][-1], 0)


if __name__ == "__main__":
    unittest.main()
