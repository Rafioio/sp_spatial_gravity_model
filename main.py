from src.utils.centroide_ponderado import main as centroide_ponderado
from src.construcao_matriz_demanda import main as construcao_matriz_demanda
from src.utils.area_urbana import main as area_urbana
from src.construcao_matriz_custo_de_coleta import main as construcao_custo_de_coleta
from src.utils.gerador_instancia import main as gerar_instancia
from src.utils.demanda_regioes_municipios import main as demanda_regioes_municipios

NIVEIS = ["intermediarias", "imediatas"]


def main():
    # Etapas que geram os dois níveis de uma vez
    centroide_ponderado()
    area_urbana()

    # Etapas que dependem do nível
    for nivel in NIVEIS:
        print(f"\n===== {nivel.upper()} =====")
        construcao_matriz_demanda(nivel)
        construcao_custo_de_coleta(nivel)
        gerar_instancia(nivel)

    # Depende das matrizes de demanda dos dois níveis (e escreve nos JSONs de
    # regiões e municípios recriados por centroide_ponderado/area_urbana)
    demanda_regioes_municipios(NIVEIS)

    print("\nFluxo concluído com sucesso!")


if __name__ == "__main__":
    main()