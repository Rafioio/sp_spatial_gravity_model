"""Recalcula C_col e C_ent convertendo a area de hectares para km2.

O script preserva coordenadas, fluxos e parametros da instancia atual. A area
original de cada regiao e recuperada do custo diagonal de coleta, no qual nao
existe distancia de acesso, e entao convertida por Ai_km2 = Ai_hectares / 100.
"""

import math
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utilidades import load_sp_instance  # noqa: E402


INSTANCE = PROJECT_ROOT / "data" / "SPdata" / "sp11_instancia_completa.txt"
BACKUP = INSTANCE.with_name("sp11_instancia_completa_backup_hectares.txt")
HECTARES_POR_KM2 = 100.0


def inferir_area_hectares(custo_diagonal, volume, rho, beta, custo_km):
    """Inverte C_diag = custo_km * beta * sqrt(A * volume/rho) / volume."""
    paradas = volume / rho
    distancia_interna = custo_diagonal * volume / custo_km
    return (distancia_interna / beta) ** 2 / paradas


def matriz_ca(nodes, volume, areas_km2, distance, rho, capacidade, beta, custo_km, coleta):
    matriz = {}
    for regiao in nodes:
        quantidade = volume[regiao]
        paradas = quantidade / rho
        viagens = math.ceil(quantidade / capacidade)
        distancia_interna = beta * math.sqrt(areas_km2[regiao] * paradas)
        for hub in nodes:
            distancia_acesso = 2 * distance[(regiao, hub)] * viagens
            custo_unitario = custo_km * (distancia_acesso + distancia_interna) / quantidade
            chave = (regiao, hub) if coleta else (hub, regiao)
            matriz[chave] = custo_unitario
    return matriz


def escrever_instancia(path, data, c_col, c_ent):
    nodes = data["nodes"]
    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(f"{len(nodes)}\n")
        for node in nodes:
            lat, lon = data["coords"][node]
            file.write(f"{lat:.6f} {lon:.6f}\n")

        matrizes = [
            {(i, j): data["flow"].get((i, j), 0.0) for i in nodes for j in nodes},
            c_col,
            c_ent,
        ]
        for matriz in matrizes:
            for i in nodes:
                file.write(" ".join(f"{matriz[(i, j)]:.6f}" for j in nodes) + "\n")

        ordem = [
            "gamma", "T", "rho_col", "Q_col", "beta_col", "c_col",
            "rho_ent", "Q_ent", "beta_ent", "c_ent",
        ]
        for nome in ordem:
            file.write(f"{nome} {data['params'][nome]:g}\n")


def main():
    data = load_sp_instance(INSTANCE)
    nodes, params = data["nodes"], data["params"]
    origem = {i: sum(data["flow"].get((i, j), 0.0) for j in nodes) for i in nodes}
    destino = {j: sum(data["flow"].get((i, j), 0.0) for i in nodes) for j in nodes}

    areas_hectares = {
        i: inferir_area_hectares(
            data["c_col"][(i, i)], origem[i], params["rho_col"],
            params["beta_col"], params["c_col"],
        )
        for i in nodes
    }
    areas_km2 = {i: area / HECTARES_POR_KM2 for i, area in areas_hectares.items()}

    c_col = matriz_ca(
        nodes, origem, areas_km2, data["distance"], params["rho_col"],
        params["Q_col"], params["beta_col"], params["c_col"], coleta=True,
    )
    c_ent = matriz_ca(
        nodes, destino, areas_km2, data["distance"], params["rho_ent"],
        params["Q_ent"], params["beta_ent"], params["c_ent"], coleta=False,
    )

    if not BACKUP.exists():
        shutil.copy2(INSTANCE, BACKUP)
    escrever_instancia(INSTANCE, data, c_col, c_ent)

    validacao = load_sp_instance(INSTANCE)
    print(f"Instancia substituida: {INSTANCE}")
    print(f"Backup preservado: {BACKUP}")
    print(f"Nos: {len(validacao['nodes'])}; fluxos positivos: {len(validacao['flow'])}")
    print("Conversao aplicada: Ai_km2 = Ai_hectares / 100")
    print(
        "Media diagonal C_col: "
        f"{sum(validacao['c_col'][(i, i)] for i in nodes) / len(nodes):.6f} R$/pacote"
    )
    print(
        "Media diagonal C_ent: "
        f"{sum(validacao['c_ent'][(i, i)] for i in nodes) / len(nodes):.6f} R$/pacote"
    )


if __name__ == "__main__":
    main()
