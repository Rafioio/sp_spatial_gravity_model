import pandas as pd
import os
import time
from geopy.geocoders import Nominatim


def buscar_coordenadas_municipios(df_mun, arquivo_cache):
    """
    Busca as coordenadas de cada município na API do Nominatim.
    Utiliza um arquivo de cache para não ter que esperar 12 minutos toda vez que rodar o código.
    """
    if os.path.exists(arquivo_cache):
        print("Arquivo de coordenadas dos municípios já existe. Lendo do cache...")
        return pd.read_json(arquivo_cache)

    print("Buscando coordenadas para os municípios (Isso levará ~12 minutos)...")
    geolocator = Nominatim(user_agent="modelo_gravitacional_sp_v2")
    lats, lons = [], []

    for index, row in df_mun.iterrows():
        municipio = row['Nome_Municipio']
        # Adicionamos "Estado de São Paulo" para evitar que ele pegue cidades homônimas em outros estados
        query = f"{municipio}, Estado de São Paulo, Brasil"
        
        try:
            location = geolocator.geocode(query, timeout=10)
            if location:
                lats.append(location.latitude)
                lons.append(location.longitude)
                print(f"[{index+1}/{len(df_mun)}] Sucesso: {municipio}")
            else:
                lats.append(None)
                lons.append(None)
                print(f"[{index+1}/{len(df_mun)}] Atenção: Não localizado -> {municipio}")
        except Exception as e:
            lats.append(None)
            lons.append(None)
            print(f"[{index+1}/{len(df_mun)}] Erro em {municipio}: {e}")
            
        time.sleep(1.1) # Pausa obrigatória da API gratuita
        
    df_mun['Latitude'] = lats
    df_mun['Longitude'] = lons
    
    # Salva o cache para usos futuros
    df_mun.to_json(arquivo_cache, orient="records", force_ascii=False, indent=4)
    return df_mun