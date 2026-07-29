import os
import json
import math
import numpy as np
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
import configs.paths as paths
import configs.params as params
 
 
def calcular_distancia(lat1, lon1, lat2, lon2):
    """Distância de Haversine em km (mesma fórmula do gravity_model.py)."""
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return 6371.0 * c
 
 
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
 
 
def ler_matriz_wij(arquivo_instancia, n_esperado):
    """
    Lê a matriz wij do arquivo de instância no formato escrito pelo gravity_model.py:
      linha 1:      n
      linhas 2..n+1: lat lon (por região)
      linhas seguintes: matriz wij (n x n)
    """
    with open(arquivo_instancia, "r", encoding="utf-8") as f:
        linhas = f.readlines()
 
    n = int(linhas[0].strip())
    if n != n_esperado:
        print(
            f"Aviso: a instância tem n={n} regiões, mas regioes_sp.json tem "
            f"{n_esperado}. Confira se os dois arquivos estão na mesma ordem/versão."
        )
 
    linhas_matriz = linhas[1 + n: 1 + n + n]
    matriz_wij = np.array(
        [[float(valor) for valor in linha.split()] for linha in linhas_matriz]
    )
    return matriz_wij
 
 
def calcular_custo_coleta(df_regioes, matriz_wij):
    """
    Implementa os Passos 1 a 8 da Seção 4 do documento.
 
    Retorna:
    - custo_coleta: matriz n x n onde custo_coleta[i][k] = C^col_ik
      (custo unitário de coleta da região i, considerando hub instalado em k)
    - df_detalhes: DataFrame linha a linha com todas as grandezas intermediárias,
      útil para conferência/depuração.
    """
    n = len(df_regioes)
    Ai = df_regioes["Ai"].values
    lats = df_regioes["Latitude_Centroide"].values
    lons = df_regioes["Longitude_Centroide"].values
    nomes = df_regioes["Região Intermediária"].values
 
    # Passo 1: Oi = soma da linha i da matriz wij (todo volume originado em i,
    # independente do destino j)
    O = matriz_wij.sum(axis=1)
 
    # Distância dik entre todas as regiões (o hub pode ser instalado em
    # qualquer uma das regiões candidatas, aqui as mesmas 11 regiões)
    dist = np.zeros((n, n))
    for i in range(n):
        for k in range(n):
            if i != k:
                dist[i][k] = calcular_distancia(lats[i], lons[i], lats[k], lons[k])
 
    custo_coleta = np.zeros((n, n))
    detalhes = []
 
    for i in range(n):
        if O[i] <= 0:
            # Região sem volume originado: custo unitário indefinido (evita divisão por zero)
            print(f"Aviso: região '{nomes[i]}' tem O_i = 0, custo de coleta não calculado.")
            continue
 
        # Passo 2: número de paradas de coleta (Ncol_i = Oi / rho_col)
        N_col_i = O[i] / params.RHO_COL
 
        # Passo 3: número de rotas de coleta (Rcol_i = ceil(Oi / Qcol))
        R_col_i = math.ceil(O[i] / params.Q_COL)
 
        # Passo 5: distância interna de coleta (aproximação contínua)
        # L_interno_col_i = beta_col * sqrt(Ai * Ncol_i)
        L_interno_col_i = params.BETA_COL * sqrt(Ai[i] * N_col_i)
 
        for k in range(n):
            if i == k:
                # Hub na própria região: distância de acesso é zero (dik = 0)
                continue
 
            # Passo 4: distância de acesso (ida e volta hub k <-> região i)
            # L_acesso_col_ik = 2 * dik * Rcol_i
            L_acesso_col_ik = 2 * dist[i][k] * R_col_i
 
            # Passo 6: distância total de coleta
            # Dist_col_ik = L_acesso_col_ik + L_interno_col_i
            Dist_col_ik = L_acesso_col_ik + L_interno_col_i
 
            # Passo 7: custo total diário de coleta
            # TC_col_ik = c_col * Dist_col_ik
            TC_col_ik = params.C_COL * Dist_col_ik
 
            # Passo 8: custo unitário de coleta
            # C_col_ik = TC_col_ik / Oi
            C_col_ik = TC_col_ik / O[i]
 
            custo_coleta[i][k] = C_col_ik
            detalhes.append({
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
            })
 
    return custo_coleta, pd.DataFrame(detalhes)
 
 
def salvar_resultado(df_regioes, custo_coleta):
    nomes = df_regioes["Região Intermediária"].tolist()
    resultado = {
        "regioes": nomes,
        "parametros": {
            "rho_col": params.RHO_COL,
            "Q_col": params.Q_COL,
            "beta_col": params.BETA_COL,
            "c_col": params.C_COL,
        },
        "matriz_custo_coleta_C_col_ik": custo_coleta.tolist(),
    }
    with open(paths.ARQUIVO_SAIDA_CUSTO_COLETA, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=4)
    print(f"Matriz de custo de coleta salva em: {paths.ARQUIVO_SAIDA_CUSTO_COLETA}")
 
 
def main():
    df_regioes = ler_regioes(paths.ARQUIVO_REGIOES_SP)
    matriz_wij = ler_matriz_wij(paths.ARQUIVO_INSTANCIA_GRAVIDADE, len(df_regioes))
 
    custo_coleta, df_detalhes = calcular_custo_coleta(df_regioes, matriz_wij)
 
    print("\n--- RESUMO: Custo unitário de coleta C^col_ik (R$/pacote) ---")
    print(
        pd.DataFrame(
            custo_coleta,
            index=df_regioes["Região Intermediária"],
            columns=df_regioes["Região Intermediária"],
        ).round(4)
    )
 
    salvar_resultado(df_regioes, custo_coleta)
 
    df_detalhes.to_csv(paths.ARQUIVO_SAIDA_DETALHADO, index=False)
    print(f"Detalhamento linha a linha salvo em: {paths.ARQUIVO_SAIDA_DETALHADO}")