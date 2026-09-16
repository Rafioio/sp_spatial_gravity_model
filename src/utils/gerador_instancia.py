import json
import configs.paths as paths
import configs.params as params

def carregar_jsons():
    with open(paths.ARQUIVO_REGIOES_SP, "r", encoding="utf-8") as f:
        regioes = json.load(f)
    with open(paths.ARQUIVO_MATRIZ_DEMANDA, "r", encoding="utf-8") as f:
        demanda = json.load(f)
    with open(paths.ARQUIVO_MATRIZ_CUSTO_COLETA, "r", encoding="utf-8") as f:
        coleta = json.load(f)
    with open(paths.ARQUIVO_MATRIZ_CUSTO_ENTREGA, "r", encoding="utf-8") as f:
        entrega = json.load(f)
    return regioes, demanda, coleta, entrega
 
 
def validar_consistencia(regioes, demanda, coleta, entrega):
    """
    Garante que os 4 arquivos se referem às mesmas 11 regiões, na mesma
    ordem — senão a instância sairia com coordenadas e matrizes desalinhadas.
    """
    nomes_regioes = [r["Região Intermediária"] for r in regioes]
    nomes_demanda = demanda["regioes"]
    nomes_coleta = coleta["regioes"]
    nomes_entrega = entrega["regioes"]

    if nomes_regioes != nomes_demanda:
        raise ValueError(
            "A ordem/lista de regiões de regioes_sp.json não bate com "
            "matriz_demanda.json. Confira se são da mesma execução do pipeline."
        )
    if nomes_regioes != nomes_coleta:
        raise ValueError(
            "A ordem/lista de regiões de regioes_sp.json não bate com "
            "custo_coleta_sp.json. Confira se são da mesma execução do pipeline."
        )
    return nomes_regioes
 
 
def escrever_instancia(regioes, demanda, coleta, entrega, arquivo_saida):
    nomes = validar_consistencia(regioes, demanda, coleta, entrega)
    n = len(nomes)
 
    matriz_demanda = demanda["matriz_demanda_Wij"]
    matriz_coleta = coleta["matriz_custo_coleta_C_col_ik"]
    matriz_acesso_coleta = coleta["L_acesso_coleta_ik_km"]
    matriz_interno_coleta = coleta["L_interno_coleta_ik_km"]
    matriz_entrega = entrega["matriz_custo_entrega_C_ent_ik"]
    matriz_acesso_entrega = entrega["L_acesso_entrega_jk_km"]
    matriz_interno_entrega = entrega["L_interno_entrega_jk_km"]

    with open(arquivo_saida, "w", encoding="utf-8") as f:
        # 1. Tamanho da rede (n)
        f.write(f"{n}\n")
 
        # 2. Coordenadas dos centroides, na mesma ordem das regiões
        for regiao in regioes:
            f.write(
                f"{regiao['Latitude_Centroide']:.6f} "
                f"{regiao['Longitude_Centroide']:.6f}\n"
            )
 
        # 3. Matriz de demanda (wij) — n x n
        for linha in matriz_demanda:
            f.write(" ".join(f"{v:.6f}" for v in linha) + "\n")

        for linha in matriz_coleta:
            f.write(" ".join(f"{v:.6f}" for v in linha) + "\n")

        for linha in matriz_entrega:
            f.write(" ".join(f"{v:.6f}" for v in linha) + "\n")

        for linha in matriz_acesso_coleta:
            f.write(" ".join(f"{v:.6f}" for v in linha) + "\n")

        for linha in matriz_acesso_entrega:
            f.write(" ".join(f"{v:.6f}" for v in linha) + "\n")

        for linha in matriz_interno_coleta:
            f.write(" ".join(f"{v:.6f}" for v in linha) + "\n")

        for linha in matriz_interno_entrega:
            f.write(" ".join(f"{v:.6f}" for v in linha) + "\n")

        # 5. Parâmetros usados para gerar as duas matrizes acima
        params_demanda = demanda["parametros"]
        params_coleta = coleta["parametros"]
        params_entrega = entrega["parametros"]
 
        f.write(f"gamma {params_demanda['gamma']}\n")
        f.write(f"T {params_demanda['T']}\n")

        f.write(f"rho_col {params_coleta['rho_col']}\n")
        f.write(f"Q_col {params_coleta['Q_col']}\n")
        f.write(f"beta_col {params_coleta['beta_col']}\n")
        f.write(f"c_col {params_coleta['c_col']}\n")

        f.write(f"rho_ent {params_entrega['rho_ent']}\n")
        f.write(f"Q_ent {params_entrega['Q_ent']}\n")
        f.write(f"beta_ent {params_entrega['beta_ent']}\n")
        f.write(f"c_ent {params_entrega['c_ent']}\n")
        f.write(f"Q_hub {params.Q_HUB}\n")
        f.write(f"ckm_hub {params.CKM_HUB}\n")
        f.write(f"c_hub {params.C_HUB}\n")


    print(f"Instância completa escrita em: {arquivo_saida}")
    print(f"  - {n} regiões")
    print(f"  - matriz de demanda {n}x{n}")
    print(f"  - matriz de custo de coleta {n}x{n}")
    print(f"  - matriz de custo de entrega {n}x{n}")
    print(f"  - matriz de custo interno de coleta {n}x{n}")
    print(f"  - matriz de custo interno de entrega {n}x{n}")
    print(f"  - 7 parâmetros (gamma, T, rho_col, Q_col, beta_col, c_col, C_hub)")


def main():
    regioes, demanda, coleta, entrega = carregar_jsons()
    escrever_instancia(regioes, demanda, coleta, entrega, paths.ARQUIVO_SAIDA_INSTANCIA)
    return True