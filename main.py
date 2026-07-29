from src.population_weighted_centroid import main as centroid_main
from src.gravity_model import main as gravity_main
from src.ca_data import main as ca_main


def main():
    centroid_main()
    gravity_main()
    ca_main()
    print("Fluxo concluído com sucesso!")


if __name__ == "__main__":
    main()