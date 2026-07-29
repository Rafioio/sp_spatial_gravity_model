from src.utils.centroide_ponderado import main as centroid_main
from src.construcao_matriz_demanda import main as gravity_main
from src.utils.area_urbana import main as ca_main
from src.custo_de_coleta import main as custo_main


def main():
    centroid_main()
    gravity_main()
    ca_main()
    custo_main()
    print("Fluxo concluído com sucesso!")


if __name__ == "__main__":
    main()