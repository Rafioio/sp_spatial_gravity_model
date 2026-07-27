import requests
import pandas as pd
import os

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

try:
    print("1. Puxando População dos Municípios de SP (SIDRA - Censo 2022)...")
    # Tabela 4709 = População Residente (Censo 2022) | Variável 93 = População residente
    url_pop = "https://apisidra.ibge.gov.br/values/t/4709/n6/in%20n3%2035/p/last/v/93"
    resp_pop = requests.get(url_pop, headers=headers)
    
    if resp_pop.status_code != 200:
        print("Erro na API do SIDRA.")
        exit()

    data_pop = resp_pop.json()
    
    # Identificar qual coluna tem o código do município e qual tem o valor
    header_dict = data_pop[0]
    chave_mun_cod = None
    chave_valor = 'V'
    
    for key, value in header_dict.items():
        if 'MUNICÍPIO (CÓDIGO)' in value.upper():
            chave_mun_cod = key

    # Criar DataFrame com a população dos municípios
    df_pop = pd.DataFrame(data_pop[1:], columns=header_dict.keys())
    df_pop = df_pop[[chave_mun_cod, chave_valor]].copy()
    df_pop.columns = ['Cod_IBGE', 'Populacao']
    
    # Converter para numérico (população não tem decimal, então podemos tratar os nulos e converter)
    df_pop['Populacao'] = pd.to_numeric(df_pop['Populacao'], errors='coerce').fillna(0).astype(int)


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


    print("3. Cruzando os dados e calculando a População das 11 Regiões...\n")
    # Juntar a tabela de População com a tabela de Regiões baseando-se no Código do IBGE
    df_completo = pd.merge(df_pop, df_local, on='Cod_IBGE', how='inner')

    # Agrupar pelas Regiões Intermediárias e somar a População
    df_regioes = df_completo.groupby('Região Intermediária', as_index=False)['Populacao'].sum()

    # Ordenar da maior para a menor População
    df_regioes = df_regioes.sort_values(by='Populacao', ascending=False).reset_index(drop=True)

    print("--- POPULAÇÃO POR REGIÃO GEOGRÁFICA INTERMEDIÁRIA (IBGE - SP) ---")
    print(df_regioes.to_string(index=False))

    # Salvando os dados em um arquivo JSON
    pasta_src = os.path.dirname(os.path.abspath(__file__))
    pasta_output = os.path.join(pasta_src, "..", "output")
    
    # Cria a pasta 'output' caso ela ainda não exista
    os.makedirs(pasta_output, exist_ok=True)

    # Mudei o nome do arquivo de saída para refletir a nova métrica
    nome_arquivo = os.path.join(pasta_output, "pop_regions_sp.json")
    
    # Exporta o DataFrame para JSON
    df_regioes.to_json(
        nome_arquivo, 
        orient="records",      
        force_ascii=False,     
        indent=4               
    )
    
    print(f"\nSucesso! Arquivo '{nome_arquivo}' criado.")

except Exception as e:
    print(f"\nOcorreu um erro inesperado: {e}")