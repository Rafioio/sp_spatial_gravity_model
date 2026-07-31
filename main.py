from src.utils.centroide_ponderado import main as centroide_ponderado
from src.construcao_matriz_demanda import main as construcao_matriz_demanda
from src.utils.area_urbana import main as area_urbana
from src.construcao_matriz_custo_de_coleta import main as construcao_custo_de_coleta
from src.utils.gerador_instancia import main as gerar_instancia

def main():
    centroide_ponderado()
    construcao_matriz_demanda()
    area_urbana()
    construcao_custo_de_coleta()
    gerar_instancia()
    print("Fluxo concluído com sucesso!")


if __name__ == "__main__":
    main()