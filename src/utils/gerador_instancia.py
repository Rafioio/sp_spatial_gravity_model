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