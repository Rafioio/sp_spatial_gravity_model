import requests
import pandas as pd
import os

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

try:
    print("1. Puxando PIB dos Municípios de SP (SIDRA)...")
    url_pib = "https://apisidra.ibge.gov.br/values/t/5938/n6/in%20n3%2035/p/last/v/37"
    resp_pib = requests.get(url_pib, headers=headers)
    
    if resp_pib.status_code != 200:
        print("Erro na API do SIDRA.")
        exit()

    data_pib = resp_pib.json()
    
    # Identificar qual coluna tem o código do município e qual tem o valor
    header_dict = data_pib[0]
    chave_mun_cod = None
    chave_valor = 'V'
    
    for key, value in header_dict.items():
        if 'MUNICÍPIO (CÓDIGO)' in value.upper():
            chave_mun_cod = key

    # Criar DataFrame com o PIB dos municípios
    df_pib = pd.DataFrame(data_pib[1:], columns=header_dict.keys())
    df_pib = df_pib[[chave_mun_cod, chave_valor]].copy()
    df_pib.columns = ['Cod_IBGE', 'PIB']
    df_pib['PIB'] = pd.to_numeric(df_pib['PIB'], errors='coerce')


    print("2. Puxando malha de Regiões Intermediárias (API de Localidades do IBGE)...")
    url_local = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/35/municipios"
    resp_local = requests.get(url_local, headers=headers)
    
    if resp_local.status_code != 200:
        print("Erro na API de Localidades.")
        exit()

    dados_localidades = resp_local.json()
    
    # Extrair o código do município e o nome da sua Região Intermediária
    lista_municipios = []
    for mun in dados_localidades:
        cod_ibge = str(mun['id'])
        regiao_intermediaria = mun['regiao-imediata']['regiao-intermediaria']['nome']
        lista_municipios.append({
            'Cod_IBGE': cod_ibge, 
            'Região Intermediária': regiao_intermediaria
        })
        
    df_local = pd.DataFrame(lista_municipios)


    print("3. Cruzando os dados e calculando o PIB das 11 Regiões...\n")
    # Juntar a tabela de PIB com a tabela de Regiões baseando-se no Código do IBGE
    df_completo = pd.merge(df_pib, df_local, on='Cod_IBGE', how='inner')

    # Agrupar pelas Regiões Intermediárias e somar o PIB
    df_regioes = df_completo.groupby('Região Intermediária', as_index=False)['PIB'].sum()

    # Ordenar do maior para o menor PIB
    df_regioes = df_regioes.sort_values(by='PIB', ascending=False).reset_index(drop=True)

    print("--- PIB POR REGIÃO GEOGRÁFICA INTERMEDIÁRIA (IBGE - SP) ---")
    print(df_regioes.to_string(index=False))

    #Salvando os dados em um arquivo JSON
    
    pasta_src = os.path.dirname(os.path.abspath(__file__))

    pasta_output = os.path.join(pasta_src, "..", "output")
    
    # Cria a pasta 'output' caso ela ainda não exista
    os.makedirs(pasta_output, exist_ok=True)

    nome_arquivo = os.path.join(pasta_output, "pib_regions_sp.json")
    
    # Exporta o DataFrame para JSON
    df_regioes.to_json(
        nome_arquivo, 
        orient="records",      # Formata como uma lista de objetos (padrão em APIs e Banco de Dados)
        force_ascii=False,     # Permite que acentos (como "São Paulo") fiquem corretos no arquivo
        indent=4               # Quebra as linhas e indenta para o arquivo ficar fácil de ler
    )
    
    print(f"\nSucesso! Arquivo '{nome_arquivo}' criado na mesma pasta do script.")

except Exception as e:
    print(f"\nOcorreu um erro inesperado: {e}")