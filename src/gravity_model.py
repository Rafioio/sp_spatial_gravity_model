import os
import pandas as pd
from math import radians, sin, cos, sqrt, atan2

# --- FUNÇÕES MATEMÁTICAS ---

def calcular_distancia(lat1, lon1, lat2, lon2):
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return 6371.0 * c

def gerar_matriz_fluxo(df_dados, beta=2.0):
    """Gera uma matriz N x N com os valores da força gravitacional."""
    n_nos = len(df_dados)
    matriz_fluxo = [[0.0 for _ in range(n_nos)] for _ in range(n_nos)]
    nome_coluna_pib = [col for col in df_dados.columns if 'PIB' in col.upper()][0]

    
    for i in range(n_nos):
        for j in range(n_nos):
            if i != j:
                pib_i = df_dados.iloc[i][nome_coluna_pib]
                pib_j = df_dados.iloc[j][nome_coluna_pib]
                lat_i, lon_i = df_dados.iloc[i]['Latitude_Polo'], df_dados.iloc[i]['Longitude_Polo']
                lat_j, lon_j = df_dados.iloc[j]['Latitude_Polo'], df_dados.iloc[j]['Longitude_Polo']
                
                dist = calcular_distancia(lat_i, lon_i, lat_j, lon_j)
                
                # Escalando o valor para evitar números gigantescos no solver
                forca = (pib_i * pib_j) / (dist ** beta)
                matriz_fluxo[i][j] = forca / 1e9 
                
    return matriz_fluxo

# --- GERADOR DA INSTÂNCIA ---

def escrever_arquivo_instancia(df_dados, arquivo_saida):
    n_nos = len(df_dados)
    matriz_fluxo = gerar_matriz_fluxo(df_dados)
    
    print(f"Escrevendo instância em: {arquivo_saida}")
    
    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        # 1. Tamanho da rede (n)
        f.write(f"{n_nos}\n")
        
        # 2. Coordenadas (Lat e Lon)
        for _, row in df_dados.iterrows():
            f.write(f"{row['Latitude_Polo']:.6f} {row['Longitude_Polo']:.6f}\n")
            
        # 3. Matriz de Fluxo (n x n)
        for i in range(n_nos):
            linha_formatada = " ".join([f"{valor:.6f}" for valor in matriz_fluxo[i]])
            f.write(f"{linha_formatada}\n")

if __name__ == "__main__":
    # Configurações de pastas
    pasta_src = os.path.dirname(os.path.abspath(__file__))
    pasta_output = os.path.join(pasta_src, "..", "output")
    arquivo_entrada = os.path.join(pasta_output, "pib_with_coordinates_sp.json")
    
    # Nome do arquivo da instância
    arquivo_instancia = os.path.join(pasta_output, "sp11_flow_only.txt")
    
    if not os.path.exists(arquivo_entrada):
        print(f"Erro: Arquivo base {arquivo_entrada} não encontrado.")
        exit()

    # Lê os dados processados
    df_dados = pd.read_json(arquivo_entrada)

    # Gera a instância limpa (apenas nós, coordenadas e fluxo)
    escrever_arquivo_instancia(df_dados, arquivo_instancia)
    
    print("\nInstância gerada com sucesso! Sem parâmetros de hubs ou custos.")