import os
import time
import sys
import json
import pandas as pd
import requests
from geopy.geocoders import Nominatim
from configs import paths
from geopy.geocoders import Nominatim
from configs import paths
from playwright.sync_api import sync_playwright

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

        time.sleep(1.1)

    df_mun['Latitude'] = lats
    df_mun['Longitude'] = lons

    df_mun.to_json(arquivo_cache, orient="records", force_ascii=False, indent=4)
    return df_mun


def calcular_centroide_ponderado(df_mun):
    """
    Aplica a modelagem matemática exata:
    lat_r = sum(Pop_m * lat_m) / sum(Pop_m)
    lon_r = sum(Pop_m * lon_m) / sum(Pop_m)
    """
    print("\nCalculando os centroides ponderados por população...")

    df_calc = df_mun.dropna(subset=['Latitude', 'Longitude']).copy()

    df_calc['Lat_Ponderada'] = df_calc['Latitude'] * df_calc['Populacao']
    df_calc['Lon_Ponderada'] = df_calc['Longitude'] * df_calc['Populacao']

    df_regioes = df_calc.groupby('Região Intermediária').agg(
        Pop_Total=('Populacao', 'sum'),
        Soma_Lat_Pond=('Lat_Ponderada', 'sum'),
        Soma_Lon_Pond=('Lon_Ponderada', 'sum')
    ).reset_index()

    df_regioes['Latitude_Centroide'] = df_regioes['Soma_Lat_Pond'] / df_regioes['Pop_Total']
    df_regioes['Longitude_Centroide'] = df_regioes['Soma_Lon_Pond'] / df_regioes['Pop_Total']

    df_final = df_regioes[['Região Intermediária', 'Pop_Total', 'Latitude_Centroide', 'Longitude_Centroide']]
    df_final = df_final.sort_values(by='Pop_Total', ascending=False).reset_index(drop=True)

    return df_final


def buscar_json_via_browser(url, browser, tentativas=3, timeout_ms=20000):
    """
    Usa uma aba do Chromium (via Playwright) para acessar a URL e extrair o JSON,
    contornando a proteção anti-bot (Cloudflare) do apisidra.ibge.gov.br.
    """
    ultima_excecao = None
    for tentativa in range(1, tentativas + 1):
        page = browser.new_page()
        try:
            page.goto(url, timeout=timeout_ms)
            # dá um tempo para o Cloudflare validar e a página assentar
            page.wait_for_timeout(4000)

            conteudo = page.inner_text("body").strip()

            if not conteudo:
                raise ValueError("Resposta vazia do servidor (via navegador)")

            return json.loads(conteudo)

        except Exception as e:
            ultima_excecao = e
            print(f"[Tentativa {tentativa}/{tentativas}] Falha em {url}: {e}")
            if tentativa < tentativas:
                time.sleep(3)
        finally:
            page.close()

    raise ultima_excecao

def carregar_populacao_de_csv(caminho_csv):
    """
    Carrega população, código do município e coordenadas já geocodificadas
    a partir do CSV local, evitando a chamada ao SIDRA (bloqueada por
    Cloudflare) e a geocodificação via Nominatim.
    """
    print(f"CSV de população encontrado em '{caminho_csv}'. Usando dados locais...")
    df = pd.read_csv(caminho_csv, dtype={"codigo_municipio": str})
    df = df.rename(columns={
        "codigo_municipio": "Cod_IBGE",
        "populacao": "Populacao",
        "lat": "Latitude",
        "lon": "Longitude",
    })
    df["Populacao"] = pd.to_numeric(df["Populacao"], errors="coerce").fillna(0).astype(int)
    return df[["Cod_IBGE", "Populacao", "Latitude", "Longitude"]]


def main():

    paths.ensure_directories()

    arquivo_cache_coord = paths.ARQUIVO_MUNICIPIOS_SP
    arquivo_saida = paths.ARQUIVO_REGIOES_SP

    usar_csv = os.path.exists(paths.ARQUIVO_PLANILHA_POPULACAO) 

    try:
        print("1. Coletando Base de Municípios e População do IBGE...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            # Região Intermediária sempre vem da API (não é bloqueada pelo Cloudflare)
            resp_local = buscar_json_via_browser(
                "https://servicodados.ibge.gov.br/api/v1/localidades/estados/35/municipios",
                browser,
            )

            if usar_csv:
                df_pop_coords = carregar_populacao_de_csv(paths.ARQUIVO_PLANILHA_POPULACAO) 
            else:
                resp_pop = buscar_json_via_browser(
                    "https://apisidra.ibge.gov.br/values/t/4709/n6/in%20n3%2035/p/last/v/93",
                    browser,
                )
                chave_mun_cod = [k for k, v in resp_pop[0].items() if 'MUNICÍPIO (CÓDIGO)' in v.upper()][0]
                df_pop_coords = pd.DataFrame(resp_pop[1:])
                df_pop_coords = df_pop_coords[[chave_mun_cod, 'V']].rename(
                    columns={chave_mun_cod: 'Cod_IBGE', 'V': 'Populacao'}
                )
                df_pop_coords['Populacao'] = pd.to_numeric(
                    df_pop_coords['Populacao'], errors='coerce'
                ).fillna(0).astype(int)

            browser.close()

        lista_mun = [
            {
                "Cod_IBGE": str(m["id"]),
                "Nome_Municipio": m["nome"],
                "Região Intermediária": m["regiao-imediata"]["regiao-intermediaria"]["nome"],
            }
            for m in resp_local
        ]

    except requests.exceptions.ConnectionError as e:
        print("\n[ERRO FATAL DE CONEXÃO]")
        print(f"Detalhes técnicos: {e}")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("\n[ERRO DE TEMPO LIMITE]")
        sys.exit(1)
    except Exception as e:
        print("\n[ERRO NA API DO IBGE]")
        print(f"Ocorreu um problema ao comunicar com o servidor após várias tentativas: {e}")
        sys.exit(1)

    df_local = pd.DataFrame(lista_mun)
    df_completo_mun = pd.merge(df_pop_coords, df_local, on='Cod_IBGE', how='inner')

    if usar_csv:
        # já temos Latitude/Longitude do CSV, pula a geocodificação via Nominatim
        df_com_coordenadas = df_completo_mun
    else:
        print("\n2. Iniciando Motor de Geocodificação (Nominatim)...")
        df_com_coordenadas = buscar_coordenadas_municipios(df_completo_mun, arquivo_cache_coord)

    print("\n3. Aplicando Modelagem Matemática...")
    df_centroides = calcular_centroide_ponderado(df_com_coordenadas)

    print("\n--- RESULTADO FINAL: CENTROIDES PONDERADOS (CENTRO DE MASSA) ---")
    print(df_centroides.to_string(index=False))

    df_centroides.to_json(arquivo_saida, orient="records", force_ascii=False, indent=4)
    print(f"\nSucesso! Arquivo completo salvo em: {arquivo_saida}")
    return True