import json
import os
import numpy as np
import pandas as pd
import configs.params as params
import configs.paths as paths
from src.utils.calcular_distancia import calcular_distancia


def gerar_matriz_fluxo(df_dados, gamma, T):
    """
    Gera uma matriz N x N com os fluxos normalizados baseados no modelo gravitacional exponencial.
    
    Parâmetros:
    - gamma: Parâmetro de decaimento/penalização da distância (γ).
    - T: Volume total de pacotes por dia a ser distribuído na matriz.
    """
    n_nos = len(df_dados)
    matriz_forca_bruta = np.zeros((n_nos, n_nos))
    
    # Identifica a coluna de massa (População ou PIB)
    colunas_massa = [col for col in df_dados.columns if 'POP' in col.upper() or 'PIB' in col.upper()]
    if not colunas_massa:
        raise ValueError("Nenhuma coluna contendo 'Pop' ou 'PIB' foi encontrada no DataFrame.")
    nome_coluna_massa = colunas_massa[0]

    # Extrai os dados para arrays (mais rápido)
    massas = df_dados[nome_coluna_massa].values
    lats = df_dados['Latitude_Centroide'].values # Ajuste o nome da coluna se necessário
    lons = df_dados['Longitude_Centroide'].values # Ajuste o nome da coluna se necessário
    
    soma_fluxo_bruto = 0.0

    # 1. Calcula os fluxos brutos (g_ij)
    for i in range(n_nos):
        for j in range(n_nos):
            if i != j:
                # Passo 4 e 5: Prod_i e Atra_j (No caso simples, ambos são a população/massa do nó)
                prod_i = massas[i]
                atra_j = massas[j]
                
                dist = calcular_distancia(lats[i], lons[i], lats[j], lons[j])
                
                # Passo 6: Propensão bruta de fluxo (g_ij = Prod_i * Atra_j * e^(-gamma * d_ij))
                # Usa-se np.exp para a função exponencial
                g_ij = prod_i * atra_j * np.exp(-gamma * dist)
                
                matriz_forca_bruta[i][j] = g_ij
                soma_fluxo_bruto += g_ij

    # Passo 8: Normalização da matriz (w_ij)
    matriz_fluxo_normalizada = np.zeros((n_nos, n_nos))
    
    # Para evitar divisão por zero caso a soma bruta seja 0 (o que é muito improvável com populações positivas)
    if soma_fluxo_bruto > 0:
        for i in range(n_nos):
            for j in range(n_nos):
                if i != j:
                    # w_ij = T * (g_ij / sum(g_ab))
                    matriz_fluxo_normalizada[i][j] = T * (matriz_forca_bruta[i][j] / soma_fluxo_bruto)
                    
    return matriz_fluxo_normalizada

def salvar_resultado(df_regioes, demanda):
    nomes = df_regioes["Região Intermediária"].tolist()
    resultado = {
        "regioes": nomes,
        "parametros": {
            "gamma": params.GAMMA,
            "T": params.T,
        },
        "matriz_demanda_Wij": demanda.tolist(),
    }
    with open(paths.ARQUIVO_MATRIZ_DEMANDA, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=4)
    print(f"Matriz de demanda salva em: {paths.ARQUIVO_MATRIZ_DEMANDA}")

def main():
    
    if not os.path.exists(paths.ARQUIVO_REGIOES_SP):
        print(f"Erro: Arquivo base {paths.ARQUIVO_REGIOES_SP} não encontrado.")
        exit()

    # Lê os dados processados
    df_regioes = pd.read_json(paths.ARQUIVO_REGIOES_SP)

    # Gera a instância limpa
    matriz_fluxo = gerar_matriz_fluxo(df_regioes, params.GAMMA, params.T)

    salvar_resultado(df_regioes, matriz_fluxo)

    return True