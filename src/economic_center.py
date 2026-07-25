import os
import pandas as pd
import time
from geopy.geocoders import Nominatim

def extrair_coordenadas_polos(lista_regioes):
    print("Buscando as coordenadas dos polos econômicos...\n")
    
    geolocator = Nominatim(user_agent="modelo_gravitacional_sp")
    dados_polos = []

    for regiao in lista_regioes:
        query = f"{regiao}, Estado de São Paulo, Brasil"
        
        try:
            location = geolocator.geocode(query)
            
            if location:
                lat = location.latitude
                lon = location.longitude
                print(f"Sucesso: {regiao} -> Lat: {lat:.4f}, Lon: {lon:.4f}")
                
                dados_polos.append({
                    'Região Intermediária': regiao,
                    'Latitude_Polo': lat,
                    'Longitude_Polo': lon
                })
            else:
                print(f"Atenção: Não foi possível localizar {regiao}")
                
        except Exception as e:
            print(f"Erro ao buscar {regiao}: {e}")
            
        # Pausa de 1 segundo para não sobrecarregar a API gratuita
        time.sleep(1)
        
    return pd.DataFrame(dados_polos)

if __name__ == "__main__":
    # 1. Configura os caminhos das pastas (lendo de 'output' e salvando em 'output')
    pasta_src = os.path.dirname(os.path.abspath(__file__))
    pasta_output = os.path.join(pasta_src, "..", "output")
    
    arquivo_entrada = os.path.join(pasta_output, "pib_regions_sp.json")
    arquivo_saida = os.path.join(pasta_output, "pib_with_coordinates_sp.json")
    
    # Verifica se o JSON do PIB existe antes de tentar abrir
    if not os.path.exists(arquivo_entrada):
        print(f"Erro: O arquivo {arquivo_entrada} não foi encontrado.")
        print("Rode o script extrator do PIB primeiro!")
        exit()

    print("1. Lendo os dados de PIB...")
    df_pib = pd.read_json(arquivo_entrada)
    
    # Transforma a coluna de regiões em uma lista do Python
    lista_de_regioes = df_pib['Região Intermediária'].tolist()

    # 2. Busca as coordenadas
    print("\n2. Processando as coordenadas na API do OpenStreetMap...")
    df_coordenadas = extrair_coordenadas_polos(lista_de_regioes)

    # 3. Junta as tabelas (Merge)
    print("\n3. Cruzando PIB com as Coordenadas...")
    # Faz o merge usando a coluna 'Região Intermediária' como chave para não misturar os dados
    df_final = pd.merge(df_pib, df_coordenadas, on='Região Intermediária', how='inner')

    print("\n--- TABELA FINAL PRONTA PARA O MODELO GRAVITACIONAL ---")
    print(df_final.to_string(index=False))

    # 4. Salva o JSON final
    df_final.to_json(
        arquivo_saida, 
        orient="records",
        force_ascii=False,
        indent=4
    )
    
    print(f"\nSucesso! Arquivo completo salvo em: {arquivo_saida}")