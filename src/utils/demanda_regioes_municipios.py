"""
Demanda total de entrada/saída por região e rateio por município.

Lê as matrizes de demanda W_ij geradas por `construcao_matriz_demanda.py` e:

1. Calcula, para cada região i:
     - Demanda de saída   O_i = sum_j W_ij   (soma da linha i: o que a região envia)
     - Demanda de entrada D_i = sum_j W_ji   (soma da coluna i: o que a região recebe)
   e grava os dois valores nos JSONs das regiões (intermediárias e imediatas).

2. Distribui a demanda de cada região entre os seus municípios, proporcionalmente
   à população do município em relação à população total da região:
     demanda_m = demanda_regiao * Pop_m / Pop_regiao
   e grava os valores no JSON dos municípios. Como cada município pertence a uma
   região intermediária e a uma imediata, são gravados os dois conjuntos de campos.

A soma das demandas dos municípios de uma região reproduz exatamente a demanda
da região (a população da região é recalculada a partir dos próprios municípios,
de modo que o rateio sempre fecha).

Deve rodar DEPOIS de `construcao_matriz_demanda` (para os dois níveis) e depois
de `centroide_ponderado`, que recria os JSONs de regiões e municípios do zero.
"""
import json
import os

import configs.paths as paths

# Campos adicionados aos JSONs das regiões
CAMPO_DEMANDA_SAIDA_REGIAO = "Demanda_Saida_Regiao"
CAMPO_DEMANDA_ENTRADA_REGIAO = "Demanda_Entrada_Regiao"

NIVEIS = {
    "intermediarias": {
        "coluna_nome": "Região Intermediária",
        # chave que liga o município à sua região, no JSON de municípios
        "chave_municipio": "Região Intermediária",
        # campos adicionados ao JSON de municípios
        "campo_saida_municipio": "Demanda_Saida_Municipio_Intermediaria",
        "campo_entrada_municipio": "Demanda_Entrada_Municipio_Intermediaria",
    },
    "imediatas": {
        "coluna_nome": "Região Imediata",
        "chave_municipio": "Cod_Regiao_Imediata",
        "campo_saida_municipio": "Demanda_Saida_Municipio_Imediata",
        "campo_entrada_municipio": "Demanda_Entrada_Municipio_Imediata",
    },
}


def _ler_json(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def _salvar_json(dados, caminho):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)


def _chave(valor):
    """Normaliza a chave de região (o código vem como str num JSON e int no outro)."""
    return str(valor)


def calcular_demanda_regioes(matriz_wij):
    """
    Retorna (saida, entrada), duas listas com a demanda total de saída
    (soma das linhas) e de entrada (soma das colunas) de cada região.
    """
    n = len(matriz_wij)
    for i, linha in enumerate(matriz_wij):
        if len(linha) != n:
            raise ValueError(
                f"Matriz de demanda não é quadrada: linha {i} tem {len(linha)} "
                f"colunas, esperado {n}."
            )

    saida = [sum(linha) for linha in matriz_wij]
    entrada = [sum(matriz_wij[i][j] for i in range(n)) for j in range(n)]
    return saida, entrada


def carregar_matriz_demanda(nivel, regioes):
    """
    Lê a matriz de demanda do nível e confere que ela se refere às mesmas
    regiões, na mesma ordem, do JSON de regiões (mesma validação usada
    em gerador_instancia).
    """
    cfg = NIVEIS[nivel]
    caminho = paths.caminhos_saida(nivel)["demanda_json"]

    if not os.path.exists(caminho):
        raise FileNotFoundError(
            f"Matriz de demanda não encontrada: {caminho}. "
            f"Rode antes construcao_matriz_demanda('{nivel}')."
        )

    dados = _ler_json(caminho)
    nomes_regioes = [r[cfg["coluna_nome"]] for r in regioes]

    if dados["regioes"] != nomes_regioes:
        raise ValueError(
            f"A ordem/lista de regiões de {paths.NIVEIS_REGIOES[nivel]['arquivo'].name} "
            f"não bate com {caminho.name} ({nivel}). Confira se são da mesma "
            f"execução do pipeline."
        )

    return dados["matriz_demanda_Wij"]


def atualizar_regioes(nivel):
    """
    Adiciona a demanda total de saída e de entrada ao JSON das regiões do nível.
    Retorna {chave_da_regiao: (saida, entrada)} para o rateio dos municípios,
    junto com a lista de regiões atualizada.
    """
    cfg = NIVEIS[nivel]
    arquivo = paths.NIVEIS_REGIOES[nivel]["arquivo"]

    if not os.path.exists(arquivo):
        raise FileNotFoundError(f"Arquivo de regiões não encontrado: {arquivo}")

    regioes = _ler_json(arquivo)
    matriz = carregar_matriz_demanda(nivel, regioes)
    saida, entrada = calcular_demanda_regioes(matriz)

    # Mesma chave usada para ligar os municípios à região
    chave_regiao = cfg["chave_municipio"]
    demanda_por_regiao = {}

    for regiao, s, e in zip(regioes, saida, entrada):
        regiao[CAMPO_DEMANDA_SAIDA_REGIAO] = s
        regiao[CAMPO_DEMANDA_ENTRADA_REGIAO] = e
        demanda_por_regiao[_chave(regiao[chave_regiao])] = (s, e)

    _salvar_json(regioes, arquivo)
    print(f"Demanda de entrada/saída adicionada às regiões ({nivel}): {arquivo}")
    return demanda_por_regiao


def ratear_demanda_municipios(municipios, nivel, demanda_por_regiao):
    """
    Distribui a demanda de cada região entre seus municípios, proporcionalmente
    à população (Pop_m / Pop_regiao). Altera `municipios` in-place.
    """
    cfg = NIVEIS[nivel]
    chave = cfg["chave_municipio"]
    campo_saida = cfg["campo_saida_municipio"]
    campo_entrada = cfg["campo_entrada_municipio"]

    # População da região = soma da população dos seus municípios
    pop_regiao = {}
    for m in municipios:
        k = _chave(m[chave])
        pop_regiao[k] = pop_regiao.get(k, 0) + (m.get("Populacao") or 0)

    sem_regiao = sorted(set(pop_regiao) - set(demanda_por_regiao))
    if sem_regiao:
        raise ValueError(
            f"Municípios pertencem a regiões ({nivel}) ausentes na matriz de demanda: "
            f"{sem_regiao}"
        )

    for m in municipios:
        k = _chave(m[chave])
        saida_regiao, entrada_regiao = demanda_por_regiao[k]
        pop_total = pop_regiao[k]

        if pop_total > 0:
            fracao = (m.get("Populacao") or 0) / pop_total
        else:
            fracao = 0.0

        m[campo_saida] = saida_regiao * fracao
        m[campo_entrada] = entrada_regiao * fracao


def atualizar_municipios(demandas_por_nivel):
    """
    Adiciona ao JSON dos municípios a demanda de entrada/saída rateada de cada
    nível processado. Reescreve os campos antigos, então pode rodar mais de uma vez.
    """
    arquivo = paths.ARQUIVO_MUNICIPIOS_SP
    if not os.path.exists(arquivo):
        raise FileNotFoundError(f"Arquivo de municípios não encontrado: {arquivo}")

    municipios = _ler_json(arquivo)

    for nivel, demanda_por_regiao in demandas_por_nivel.items():
        ratear_demanda_municipios(municipios, nivel, demanda_por_regiao)

    _salvar_json(municipios, arquivo)
    print(f"Demanda de entrada/saída adicionada aos municípios: {arquivo}")
    return municipios


def validar_rateio(municipios, nivel, demanda_por_regiao, tolerancia=1e-6):
    """Confere se a soma dos municípios de cada região fecha com a demanda da região."""
    cfg = NIVEIS[nivel]
    chave = cfg["chave_municipio"]

    soma_saida, soma_entrada = {}, {}
    for m in municipios:
        k = _chave(m[chave])
        soma_saida[k] = soma_saida.get(k, 0.0) + m[cfg["campo_saida_municipio"]]
        soma_entrada[k] = soma_entrada.get(k, 0.0) + m[cfg["campo_entrada_municipio"]]

    for k, (saida, entrada) in demanda_por_regiao.items():
        if abs(soma_saida.get(k, 0.0) - saida) > tolerancia * max(1.0, saida) or \
           abs(soma_entrada.get(k, 0.0) - entrada) > tolerancia * max(1.0, entrada):
            raise ValueError(
                f"Rateio não fecha na região {k} ({nivel}): "
                f"saída {soma_saida.get(k, 0.0)} vs {saida}, "
                f"entrada {soma_entrada.get(k, 0.0)} vs {entrada}."
            )


def main(niveis=("intermediarias", "imediatas")):
    demandas_por_nivel = {}

    for nivel in niveis:
        print(f"\n--- Demanda por região ({nivel}) ---")
        demandas_por_nivel[nivel] = atualizar_regioes(nivel)

    print("\n--- Demanda por município ---")
    municipios = atualizar_municipios(demandas_por_nivel)

    for nivel, demanda_por_regiao in demandas_por_nivel.items():
        validar_rateio(municipios, nivel, demanda_por_regiao)

    print("\nConcluído.")
    return True


if __name__ == "__main__":
    main()