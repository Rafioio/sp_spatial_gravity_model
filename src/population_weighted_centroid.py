import os
import pandas as pd
import requests
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


def calcular_centroide_ponderado(df_mun):
    """
    Aplica a modelagem matemática exata:
    lat_r = sum(Pop_m * lat_m) / sum(Pop_m)
    lon_r = sum(Pop_m * lon_m) / sum(Pop_m)
    """
    print("\nCalculando os centroides ponderados por população...")
    
    # Remove municípios que por acaso não retornaram coordenada da API
    df_calc = df_mun.dropna(subset=['Latitude', 'Longitude']).copy()

    # PASSO 3 da Fórmula: Numerador (População * Coordenada)
    df_calc['Lat_Ponderada'] = df_calc['Latitude'] * df_calc['Populacao']
    df_calc['Lon_Ponderada'] = df_calc['Longitude'] * df_calc['Populacao']

    # PASSO 1 e 2: Agrupando por região (Somatórios)
    df_regioes = df_calc.groupby('Região Intermediária').agg(
        Pop_Total=('Populacao', 'sum'),
        Soma_Lat_Pond=('Lat_Ponderada', 'sum'),
        Soma_Lon_Pond=('Lon_Ponderada', 'sum')
    ).reset_index()

    # PASSO 3 FINAL: Divisão pela População Total da Região (Denominador)
    df_regioes['Latitude_Centroide'] = df_regioes['Soma_Lat_Pond'] / df_regioes['Pop_Total']
    df_regioes['Longitude_Centroide'] = df_regioes['Soma_Lon_Pond'] / df_regioes['Pop_Total']

    # Limpando a tabela para o formato final que vai para o Solver/Matriz
    df_final = df_regioes[['Região Intermediária', 'Pop_Total', 'Latitude_Centroide', 'Longitude_Centroide']]
    
    # Ordenar por população para ficar bonito
    df_final = df_final.sort_values(by='Pop_Total', ascending=False).reset_index(drop=True)
    
    return df_final

if __name__ == "__main__":
    # --- CONFIGURAÇÃO DE PASTAS ---
    pasta_src = os.path.dirname(os.path.abspath(__file__))
    pasta_output = os.path.join(pasta_src, "..", "output")
    os.makedirs(pasta_output, exist_ok=True)
    
    arquivo_base_mun = os.path.join(pasta_output, "municipios_sp_base.json")
    arquivo_cache_coord = os.path.join(pasta_output, "municipios_sp_coordenadas.json")
    arquivo_saida = os.path.join(pasta_output, "centroides_populacionais_sp.json")
    
    headers = {"User-Agent": "modelo_gravitacional_sp"}

    print("1. Coletando Base de Municípios e População do IBGE...")
    # Puxando População (Tabela 4709 - Censo 2022)
    resp_pop = requests.get("https://apisidra.ibge.gov.br/values/t/4709/n6/in%20n3%2035/p/last/v/93", headers=headers).json()
    chave_mun_cod = [k for k, v in resp_pop[0].items() if 'MUNICÍPIO (CÓDIGO)' in v.upper()][0]
    
    df_pop = pd.DataFrame(resp_pop[1:])
    df_pop = df_pop[[chave_mun_cod, 'V']].rename(columns={chave_mun_cod: 'Cod_IBGE', 'V': 'Populacao'})
    df_pop['Populacao'] = pd.to_numeric(df_pop['Populacao'], errors='coerce').fillna(0).astype(int)

    # Puxando Malha e Nomes
    resp_local = requests.get("https://servicodados.ibge.gov.br/api/v1/localidades/estados/35/municipios", headers=headers).json()
    lista_mun = [{'Cod_IBGE': str(m['id']), 'Nome_Municipio': m['nome'], 'Região Intermediária': m['regiao-imediata']['regiao-intermediaria']['nome']} for m in resp_local]
    df_local = pd.DataFrame(lista_mun)

    # Juntando Dados do Município
    df_completo_mun = pd.merge(df_pop, df_local, on='Cod_IBGE', how='inner')

    print("\n2. Iniciando Motor de Geocodificação (Nominatim)...")
    # Busca as coordenadas de cada município (usa cache se já existir)
    df_com_coordenadas = buscar_coordenadas_municipios(df_completo_mun, arquivo_cache_coord)

    print("\n3. Aplicando Modelagem Matemática...")

    df_centroides = calcular_centroide_ponderado(df_com_coordenadas)

    print("\n--- RESULTADO FINAL: CENTROIDES PONDERADOS (CENTRO DE MASSA) ---")
    print(df_centroides.to_string(index=False))

    # 4. Salva o JSON final
    df_centroides.to_json(arquivo_saida, orient="records", force_ascii=False, indent=4)
    print(f"\nSucesso! Arquivo completo salvo em: {arquivo_saida}")