import os
import unicodedata

import pandas as pd
import requests
import configs.paths as paths


CAMPO_AREA_MUNICIPIO = "Area_Urbana_2024"
CAMPO_AREA_REGIAO = "Area_Urbana_Total"

def normalizar_nome(nome):
    """Remove acentos e caixa para permitir casamento robusto de nomes de município."""
    if nome is None:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(nome))
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.strip().lower()


def buscar_mapa_municipio_regiao():
    """
    Usa a mesma API do IBGE do script de centroides para obter, para cada
    município de SP, o Cod_IBGE e a Região Intermediária a que pertence.
    """
    print("Buscando mapa Município -> Região Intermediária na API do IBGE...")
    headers = {"User-Agent": "modelo_gravitacional_sp"}
    resp_local = requests.get(
        "https://servicodados.ibge.gov.br/api/v1/localidades/estados/35/municipios",
        headers=headers,
    ).json()

    lista_mun = [
        {
            "Cod_IBGE": str(m["id"]),
            "Nome_Municipio": m["nome"],
            "Região Intermediária": m["regiao-imediata"]["regiao-intermediaria"]["nome"],
        }
        for m in resp_local
    ]
    df_mapa = pd.DataFrame(lista_mun)
    df_mapa["Nome_Normalizado"] = df_mapa["Nome_Municipio"].apply(normalizar_nome)
    return df_mapa


def ler_planilha_area(arquivo_planilha):
    print(f"Lendo planilha de área urbana: {arquivo_planilha}")
    df_area = pd.read_excel(arquivo_planilha)

    # A planilha tem colunas 'Município' e 'Área Urbana em 2024'
    df_area = df_area.rename(
        columns={
            df_area.columns[0]: "Nome_Municipio_Planilha",
            df_area.columns[1]: CAMPO_AREA_MUNICIPIO,
        }
    )
    df_area = df_area.dropna(subset=["Nome_Municipio_Planilha"])
    df_area["Nome_Normalizado"] = df_area["Nome_Municipio_Planilha"].apply(normalizar_nome)
    return df_area


def atualizar_municipios_sp(df_area, df_mapa):
    if not os.path.exists(paths.ARQUIVO_MUNICIPIOS_SP):
        print(f"Aviso: {paths.ARQUIVO_MUNICIPIOS_SP} não encontrado, pulando atualização de municípios.")
        return None

    df_municipios = pd.read_json(paths.ARQUIVO_MUNICIPIOS_SP)
    df_municipios["Nome_Normalizado"] = df_municipios["Nome_Municipio"].apply(normalizar_nome)


    if CAMPO_AREA_MUNICIPIO in df_municipios.columns:
        df_municipios = df_municipios.drop(columns=[CAMPO_AREA_MUNICIPIO])
    # ----------------------------

    # Junta a área da planilha diretamente pelo nome normalizado
    df_municipios = df_municipios.merge(
        df_area[["Nome_Normalizado", CAMPO_AREA_MUNICIPIO]],
        on="Nome_Normalizado",
        how="left",
    )

    faltantes = df_municipios[df_municipios[CAMPO_AREA_MUNICIPIO].isna()]
    if len(faltantes) > 0:
        print(f"Atenção: {len(faltantes)} município(s) sem área urbana encontrada:")
        print(faltantes["Nome_Municipio"].tolist())

    df_municipios = df_municipios.drop(columns=["Nome_Normalizado"])
    df_municipios.to_json(paths.ARQUIVO_MUNICIPIOS_SP, orient="records", force_ascii=False, indent=4)
    print(f"Atualizado: {paths.ARQUIVO_MUNICIPIOS_SP}")
    return df_municipios


def atualizar_regioes_sp(df_area, df_mapa):
    if not os.path.exists(paths.ARQUIVO_REGIOES_SP):
        print(f"Aviso: {paths.ARQUIVO_REGIOES_SP} não encontrado, pulando atualização de regiões.")
        return None

    # 1. Faz o cruzamento com o mapa e agrupa as áreas
    df_join = df_area.merge(df_mapa, on="Nome_Normalizado", how="left")

    faltantes = df_join[df_join["Região Intermediária"].isna()]
    if len(faltantes) > 0:
        print(f"Atenção: {len(faltantes)} município(s) da planilha não encontrados na API do IBGE:")
        print(faltantes["Nome_Municipio_Planilha"].tolist())

    df_area_por_regiao = (
        df_join.dropna(subset=["Região Intermediária"])
        .groupby("Região Intermediária")
        .agg(**{CAMPO_AREA_REGIAO: (CAMPO_AREA_MUNICIPIO, "sum")})
        .reset_index()
    )

    # 2. LÊ o arquivo antigo PRIMEIRO
    df_regioes = pd.read_json(paths.ARQUIVO_REGIOES_SP)

    # 3. DEPOIS de ler, apaga a coluna antiga se ela já existir
    if CAMPO_AREA_REGIAO in df_regioes.columns:
        df_regioes = df_regioes.drop(columns=[CAMPO_AREA_REGIAO])

    # 4. Faz o merge seguro com os novos dados
    df_regioes = df_regioes.merge(df_area_por_regiao, on="Região Intermediária", how="left")

    faltantes_regiao = df_regioes[df_regioes[CAMPO_AREA_REGIAO].isna()]
    if len(faltantes_regiao) > 0:
        print(f"Atenção: {len(faltantes_regiao)} região(ões) sem área urbana total:")
        print(faltantes_regiao["Região Intermediária"].tolist())

    # 5. Salva o arquivo atualizado
    df_regioes.to_json(paths.ARQUIVO_REGIOES_SP, orient="records", force_ascii=False, indent=4)
    print(f"Atualizado: {paths.ARQUIVO_REGIOES_SP}")
    
    return df_regioes


def main():

    df_area = ler_planilha_area(paths.ARQUIVO_PLANILHA_AREA)
    df_mapa = buscar_mapa_municipio_regiao()

    print("\n--- Atualizando municipios_sp.json ---")
    atualizar_municipios_sp(df_area, df_mapa)

    print("\n--- Atualizando regioes_sp.json ---")
    atualizar_regioes_sp(df_area, df_mapa)

    print("\nConcluído.")
    return True

