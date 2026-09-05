import json
from math import ceil, sqrt
import numpy as np
import pandas as pd
from src.utils.calcular_distancia import calcular_distancia
import configs.paths as paths
import configs.params as params
 
 
def ler_regioes(arquivo_regioes):
    """
    Lê o JSON de regiões. Espera as colunas:
    - 'Região Intermediária'
    - 'Latitude_Centroide', 'Longitude_Centroide'
    - alguma coluna de área urbana (Ai): tenta alguns nomes comuns.
    """
    df = pd.read_json(arquivo_regioes)
 
    campo_area = None
    for candidato in ["Area_Urbana_Total", "Ai", "Area_Urbana_2024"]:
        if candidato in df.columns:
            campo_area = candidato
            break
    if campo_area is None:
        raise ValueError(
            "Nenhuma coluna de área (Ai) encontrada em regioes_sp.json. "
            "Rode antes o script que adiciona a área urbana às regiões "
            "(campo esperado: 'Area_Urbana_Total')."
        )
 
    df = df.rename(columns={campo_area: "Ai"})
    return df
 
 
def ler_matriz_wij(arquivo_json, n_esperado):
    with open(arquivo_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    matriz_wij = np.array(dados["matriz_demanda_Wij"], dtype=float)

    if matriz_wij.shape != (n_esperado, n_esperado):
        raise ValueError(
            f"Esperava uma matriz {n_esperado}x{n_esperado}, "
            f"mas encontrei {matriz_wij.shape}."
        )

    return matriz_wij
 
def calcular_custos(df_regioes, matriz_wij):
    """
    Calcula os custos unitários de coleta e entrega.

    Retorna:
    - custo_coleta: matriz n x n
      custo_coleta[i][k] = C^col_ik
      Custo unitário de coleta da região i considerando hub em k.

    - custo_entrega: matriz n x n
      custo_entrega[j][k] = C^ent_jk
      Custo unitário de entrega na região j considerando hub em k.

    - df_detalhes_coleta: DataFrame com as grandezas intermediárias da coleta.

    - df_detalhes_entrega: DataFrame com as grandezas intermediárias da entrega.
    """

    n = len(df_regioes)

    Ai = df_regioes["Ai"].values
    lats = df_regioes["Latitude_Centroide"].values
    lons = df_regioes["Longitude_Centroide"].values
    nomes = df_regioes["Região Intermediária"].values

    # ============================================================
    # DISTÂNCIAS ENTRE TODAS AS REGIÕES
    # ============================================================

    dist = np.zeros((n, n))

    for i in range(n):
        for k in range(n):
            dist[i][k] = calcular_distancia(
                lats[i],
                lons[i],
                lats[k],
                lons[k]
            )

    # ============================================================
    # COLETA
    # ============================================================

    # Volume originado em cada região
    O = matriz_wij.sum(axis=1)

    custo_coleta = np.zeros((n, n))
    detalhes_coleta = []

    for i in range(n):

        if O[i] <= 0:
            print(
                f"Aviso: região '{nomes[i]}' tem O_i = 0, "
                "custo de coleta não calculado."
            )
            continue

        # Passo 2
        N_col_i = O[i] / params.RHO_COL

        # Passo 3
        R_col_i = ceil(O[i] / params.Q_COL)

        # Passo 5
        L_interno_col_i = (
            params.BETA_COL *
            sqrt(Ai[i] * N_col_i)
        )

        for k in range(n):

            # Passo 4
            L_acesso_col_ik = (
                2 * dist[i][k] * R_col_i
            )

            # Passo 6
            Dist_col_ik = (
                L_acesso_col_ik +
                L_interno_col_i
            )

            # Passo 7
            TC_col_ik = (
                params.C_COL *
                Dist_col_ik
            )

            # Passo 8
            C_col_ik = TC_col_ik / O[i]

            custo_coleta[i][k] = C_col_ik

            detalhes_coleta.append({
                "Regiao_i": nomes[i],
                "Hub_k": nomes[k],
                "O_i": O[i],
                "N_col_i": N_col_i,
                "R_col_i": R_col_i,
                "d_ik_km": dist[i][k],
                "L_acesso_col_ik_km": L_acesso_col_ik,
                "L_interno_col_i_km": L_interno_col_i,
                "Dist_col_ik_km": Dist_col_ik,
                "TC_col_ik_reais": TC_col_ik,
                "C_col_ik_reais_por_pacote": C_col_ik,
                "L_interno_coleta_ik_km": L_interno_col_i,
                "L_acesso_coleta_ik_km": L_acesso_col_ik,
                
            })

    # ============================================================
    # ENTREGA
    # ============================================================

    # Volume destinado a cada região
    D = matriz_wij.sum(axis=0)

    custo_entrega = np.zeros((n, n))
    detalhes_entrega = []

    for j in range(n):

        if D[j] <= 0:
            print(
                f"Aviso: região '{nomes[j]}' tem D_j = 0, "
                "custo de entrega não calculado."
            )
            continue

        # Número de paradas de entrega
        N_ent_j = D[j] / params.RHO_ENT

        # Número de rotas de entrega
        R_ent_j = ceil(D[j] / params.Q_ENT)

        # Distância interna de entrega
        L_interno_ent_j = (
            params.BETA_ENT *
            sqrt(Ai[j] * N_ent_j)
        )

        for k in range(n):

            # Distância de acesso:
            # ida e volta entre hub k e região destino j
            L_acesso_ent_kj = (
                2 * dist[j][k] * R_ent_j
            )

            # Distância total de entrega
            Dist_ent_kj = (
                L_acesso_ent_kj +
                L_interno_ent_j
            )

            # Custo total diário de entrega
            TC_ent_kj = (
                params.C_ENT *
                Dist_ent_kj
            )

            # Custo unitário de entrega
            C_ent_kj = TC_ent_kj / D[j]

            custo_entrega[j][k] = C_ent_kj

            detalhes_entrega.append({
                "Regiao_j": nomes[j],
                "Hub_k": nomes[k],
                "D_j": D[j],
                "N_ent_j": N_ent_j,
                "R_ent_j": R_ent_j,
                "d_jk_km": dist[j][k],
                "L_acesso_ent_kj_km": L_acesso_ent_kj,
                "L_interno_ent_j_km": L_interno_ent_j,
                "Dist_ent_kj_km": Dist_ent_kj,
                "TC_ent_kj_reais": TC_ent_kj,
                "C_ent_kj_reais_por_pacote": C_ent_kj,
                "L_interno_entrega_jk_km": L_interno_ent_j,
                "L_acesso_entrega_jk_km": L_acesso_ent_kj,
            })

    return (
        detalhes_coleta,
        detalhes_entrega,
        pd.DataFrame(detalhes_coleta),
        pd.DataFrame(detalhes_entrega)
    )

def salvar_resultado(df_regioes, coleta, entrega):
    nomes = df_regioes["Região Intermediária"].tolist()

    # Converte listas de dicionários em DataFrames
    df_col = pd.DataFrame(coleta)
    df_ent = pd.DataFrame(entrega)

    # ============================================================
    # 1. PROCESSAMENTO DE COLETA (Mapeamento correto de chaves_ik)
    # ============================================================
    matriz_c_col = df_col.pivot(index="Regiao_i", columns="Hub_k", values="C_col_ik_reais_por_pacote").values.tolist()
    matriz_l_int_col = df_col.pivot(index="Regiao_i", columns="Hub_k", values="L_interno_col_i_km").values.tolist()
    matriz_l_ace_col = df_col.pivot(index="Regiao_i", columns="Hub_k", values="L_acesso_col_ik_km").values.tolist()

    resultado_coleta = {
        "regioes": nomes,
        "parametros": {
            "rho_col": params.RHO_COL,
            "Q_col": params.Q_COL,
            "beta_col": params.BETA_COL,
            "c_col": params.C_COL,
        },
        "matriz_custo_coleta_C_col_ik": matriz_c_col,
        "L_interno_coleta_ik_km": matriz_l_int_col,
        "L_acesso_coleta_ik_km": matriz_l_ace_col,
    }

    with open(paths.ARQUIVO_MATRIZ_CUSTO_COLETA, "w", encoding="utf-8") as f:
        json.dump(resultado_coleta, f, ensure_ascii=False, indent=4)
    print(f"Matriz de custo de coleta salva em: {paths.ARQUIVO_MATRIZ_CUSTO_COLETA}")

    # ============================================================
    # 2. PROCESSAMENTO DE ENTREGA (Mapeamento correto de chaves_jk)
    # ============================================================
    matriz_c_ent = df_ent.pivot(index="Regiao_j", columns="Hub_k", values="C_ent_kj_reais_por_pacote").values.tolist()
    matriz_l_int_ent = df_ent.pivot(index="Regiao_j", columns="Hub_k", values="L_interno_ent_j_km").values.tolist()
    matriz_l_ace_ent = df_ent.pivot(index="Regiao_j", columns="Hub_k", values="L_acesso_ent_kj_km").values.tolist()

    resultado_entrega = {
        "regioes": nomes,
        "parametros": {
            "rho_ent": params.RHO_ENT,
            "Q_ent": params.Q_ENT,
            "beta_ent": params.BETA_ENT,
            "c_ent": params.C_ENT,
        },
        "matriz_custo_entrega_C_ent_ik": matriz_c_ent,
        "L_interno_entrega_jk_km": matriz_l_int_ent,
        "L_acesso_entrega_jk_km": matriz_l_ace_ent,
    }

    with open(paths.ARQUIVO_MATRIZ_CUSTO_ENTREGA, "w", encoding="utf-8") as f:
        json.dump(resultado_entrega, f, ensure_ascii=False, indent=4)
    print(f"Matriz de custo de entrega salva em: {paths.ARQUIVO_MATRIZ_CUSTO_ENTREGA}")

def main():
    df_regioes = ler_regioes(paths.ARQUIVO_REGIOES_SP)
    matriz_wij = ler_matriz_wij(paths.ARQUIVO_MATRIZ_DEMANDA, len(df_regioes))
 
    coleta, entrega, df_detalhes_coleta, df_detalhes_entrega = calcular_custos(df_regioes, matriz_wij)
 
    df_coleta = pd.DataFrame(coleta)

    # Cria a matriz 2D (Regiao_i x Hub_k) a partir das colunas da tabela
    df_matriz = df_coleta.pivot(
        index="Regiao_i", 
        columns="Hub_k", 
        values="C_col_ik_reais_por_pacote"
    ).round(4)

    print("\n--- RESUMO: Custo unitário de coleta C^col_ik (R$/pacote) ---")
    print(df_matriz)
    
    salvar_resultado(df_regioes, coleta, entrega)
 
    df_detalhes_coleta.to_csv(paths.ARQUIVO_CUSTO_COLETA_CSV, index=False)
    df_detalhes_entrega.to_csv(paths.ARQUIVO_CUSTO_ENTREGA_CSV, index=False)
    print(f"Detalhamento linha a linha salvo em: {paths.ARQUIVO_CUSTO_COLETA_CSV}")
    print(f"Detalhamento linha a linha salvo em: {paths.ARQUIVO_CUSTO_ENTREGA_CSV}")
    return True