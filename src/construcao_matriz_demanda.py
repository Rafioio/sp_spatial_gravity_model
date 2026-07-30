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
                    
    return matriz_fluxo_normalizada.tolist()

# --- GERADOR DA INSTÂNCIA ---

def escrever_arquivo_instancia(df_dados, arquivo_saida):
    n_nos = len(df_dados)
    # Aqui pode ajustar o valor de T (pacotes diários) e gamma (penalidade da distância)
    matriz_fluxo = gerar_matriz_fluxo(df_dados, params.GAMMA, params.T)
    
    print(f"Escrevendo instância em: {arquivo_saida}")
    
    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        # 1. Tamanho da rede (n)
        f.write(f"{n_nos}\n")
        
        # 2. Coordenadas (Lat e Lon) - Atualize para 'Latitude_Centroide' se for a saída do script anterior
        for _, row in df_dados.iterrows():
            f.write(f"{row['Latitude_Centroide']:.6f} {row['Longitude_Centroide']:.6f}\n")
            
        # 3. Matriz de Fluxo Normalizada (n x n)
        for i in range(n_nos):
            linha_formatada = " ".join([f"{valor:.6f}" for valor in matriz_fluxo[i]])
            f.write(f"{linha_formatada}\n")

def main():
    
    # Agora lendo os centroides populacionais gerados no script anterior
    arquivo_entrada = paths.ARQUIVO_REGIOES_SP

    # Nome do arquivo da instância
    arquivo_instancia = paths.ARQUIVO_INSTANCIA_GRAVIDADE

    if not os.path.exists(arquivo_entrada):
        print(f"Erro: Arquivo base {arquivo_entrada} não encontrado.")
        exit()

    # Lê os dados processados
    df_dados = pd.read_json(arquivo_entrada)

    # Gera a instância limpa
    escrever_arquivo_instancia(df_dados, arquivo_instancia)
    
    print("\nInstância gerada com sucesso! Matriz normalizada para 100.000 pacotes.")