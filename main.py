from src.utils.centroide_ponderado import main as centroide_ponderado
from src.construcao_matriz_demanda import main as construcao_matriz_demanda
from src.utils.area_urbana import main as area_urbana
from src.custo_de_coleta import main as custo_de_coleta


def main():
    centroide_ponderado()
    construcao_matriz_demanda()
    area_urbana()
    custo_de_coleta()
    print("Fluxo concluído com sucesso!")


if __name__ == "__main__":
    main()