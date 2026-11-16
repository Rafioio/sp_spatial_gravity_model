import os
import unicodedata
import pandas as pd
import requests
import configs.paths as paths

CAMPO_AREA_URBANA_MUNICIPIO = "Area_Urbana_Municipio"
CAMPO_AREA_TOTAL_MUNICIPIO = "Area_Total_Municipio"

CAMPO_AREA_URBANA_REGIAO = "Area_Urbana_Regiao"
CAMPO_AREA_TOTAL_REGIAO = "Area_Total_Regiao"

NIVEIS = {
    "intermediarias": {
        "arquivo": paths.ARQUIVO_REGIOES_INTERMEDIARIAS_SP,
        "chave": "Região Intermediária",
    },
    "imediatas": {
        "arquivo": paths.ARQUIVO_REGIOES_IMEDIATAS_SP,
        "chave": "Cod_Regiao_Imediata",
    },
}

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
            "Cod_Regiao_Imediata": str(m["regiao-imediata"]["id"]),
            "Região Imediata": m["regiao-imediata"]["nome"],
            "Região Intermediária": m["regiao-imediata"]["regiao-intermediaria"]["nome"],
        }
        for m in resp_local
    ]
    df_mapa = pd.DataFrame(lista_mun)
    df_mapa["Nome_Normalizado"] = df_mapa["Nome_Municipio"].apply(normalizar_nome)
    return df_mapa


def ler_planilha_area(arquivo_planilha):
    print(f"Lendo planilha de área urbana e total: {arquivo_planilha}")
    # A planilha usa vírgula como separador decimal ("11,64"); sem decimal=","
    # os valores viram texto e o to_numeric abaixo os transformaria em NaN.
    df_area = pd.read_csv(arquivo_planilha, decimal=",")

    # Colunas: 'Município', 'Área Urbana Km²' e 'Área Total Km²' (ambas em km²).
    # A área total já inclui a área urbana, então não deve ser somada a ela.
    df_area = df_area.rename(
        columns={
            df_area.columns[0]: "Nome_Municipio_Planilha",
            df_area.columns[1]: CAMPO_AREA_URBANA_MUNICIPIO,
            df_area.columns[2]: CAMPO_AREA_TOTAL_MUNICIPIO,
        }
    )
    df_area = df_area.dropna(subset=["Nome_Municipio_Planilha"])
    df_area[CAMPO_AREA_URBANA_MUNICIPIO] = (
        pd.to_numeric(df_area[CAMPO_AREA_URBANA_MUNICIPIO], errors="coerce")
    )
    df_area[CAMPO_AREA_TOTAL_MUNICIPIO] = (
        pd.to_numeric(df_area[CAMPO_AREA_TOTAL_MUNICIPIO], errors="coerce")
    )
    df_area["Nome_Normalizado"] = df_area["Nome_Municipio_Planilha"].apply(normalizar_nome)
    return df_area


def atualizar_municipios_sp(df_area, df_mapa):
    if not os.path.exists(paths.ARQUIVO_MUNICIPIOS_SP):
        print(f"Aviso: {paths.ARQUIVO_MUNICIPIOS_SP} não encontrado, pulando atualização de municípios.")
        return None

    df_municipios = pd.read_json(paths.ARQUIVO_MUNICIPIOS_SP)
    df_municipios["Nome_Normalizado"] = df_municipios["Nome_Municipio"].apply(normalizar_nome)

    # Remove as colunas antigas, se existirem
    campos_municipio = [CAMPO_AREA_URBANA_MUNICIPIO, CAMPO_AREA_TOTAL_MUNICIPIO]
    colunas_antigas = [c for c in campos_municipio if c in df_municipios.columns]
    if colunas_antigas:
        df_municipios = df_municipios.drop(columns=colunas_antigas)

    # Junta as áreas da planilha diretamente pelo nome normalizado
    df_municipios = df_municipios.merge(
        df_area[["Nome_Normalizado"] + campos_municipio],
        on="Nome_Normalizado",
        how="left",
    )

    for campo in campos_municipio:
        faltantes = df_municipios[df_municipios[campo].isna()]
        if len(faltantes) > 0:
            print(f"Atenção: {len(faltantes)} município(s) sem {campo} encontrada:")
            print(faltantes["Nome_Municipio"].tolist())

    df_municipios = df_municipios.drop(columns=["Nome_Normalizado"])
    df_municipios.to_json(paths.ARQUIVO_MUNICIPIOS_SP, orient="records", force_ascii=False, indent=4)
    print(f"Atualizado: {paths.ARQUIVO_MUNICIPIOS_SP}")
    return df_municipios

def atualizar_regioes_sp(df_area, df_mapa, nivel):
    cfg = NIVEIS[nivel]
    arquivo = cfg["arquivo"]
    chave = cfg["chave"]

    if not os.path.exists(arquivo):
        print(f"Aviso: {arquivo} não encontrado, pulando atualização de regiões ({nivel}).")
        return None

    # 1. Cruza a planilha com o mapa e agrupa as áreas pela chave do nível
    df_join = df_area.merge(df_mapa, on="Nome_Normalizado", how="left")

    faltantes = df_join[df_join[chave].isna()]
    if len(faltantes) > 0:
        print(f"Atenção: {len(faltantes)} município(s) da planilha não encontrados na API do IBGE:")
        print(faltantes["Nome_Municipio_Planilha"].tolist())

    df_area_por_regiao = (
        df_join.dropna(subset=[chave])
        .groupby(chave)
        .agg(**{
            CAMPO_AREA_URBANA_REGIAO: (CAMPO_AREA_URBANA_MUNICIPIO, "sum"),
            CAMPO_AREA_TOTAL_REGIAO: (CAMPO_AREA_TOTAL_MUNICIPIO, "sum"),
        })
        .reset_index()
    )

    # 2. Lê o arquivo de regiões
    df_regioes = pd.read_json(arquivo)

    # 3. Remove as colunas antigas, se existirem
    campos_regiao = [CAMPO_AREA_URBANA_REGIAO, CAMPO_AREA_TOTAL_REGIAO]
    colunas_antigas = [c for c in campos_regiao if c in df_regioes.columns]
    if colunas_antigas:
        df_regioes = df_regioes.drop(columns=colunas_antigas)

    # 4. Garante o mesmo tipo na chave (read_json converte código para int)
    df_regioes[chave] = df_regioes[chave].astype(str)
    df_area_por_regiao[chave] = df_area_por_regiao[chave].astype(str)

    df_regioes = df_regioes.merge(df_area_por_regiao, on=chave, how="left")

    for campo in campos_regiao:
        faltantes_regiao = df_regioes[df_regioes[campo].isna()]
        if len(faltantes_regiao) > 0:
            print(f"Atenção: {len(faltantes_regiao)} região(ões) sem {campo}:")
            print(faltantes_regiao[chave].tolist())

    # 5. Salva
    df_regioes.to_json(arquivo, orient="records", force_ascii=False, indent=4)
    print(f"Atualizado: {arquivo}")

    return df_regioes


def main():
    df_area = ler_planilha_area(paths.ARQUIVO_PLANILHA_AREA)
    df_mapa = buscar_mapa_municipio_regiao()

    print("\n--- Atualizando municipios_sp.json ---")
    atualizar_municipios_sp(df_area, df_mapa)

    for nivel in NIVEIS:
        print(f"\n--- Atualizando regiões ({nivel}) ---")
        atualizar_regioes_sp(df_area, df_mapa, nivel)

    print("\nConcluído.")
    return True