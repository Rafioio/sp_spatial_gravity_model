# Modelo gravitacional espacial para as regiões intermediárias de São Paulo

Este projeto monta uma instância de modelo gravitacional espacial para as regiões intermediárias de São Paulo a partir de dados de população municipal, geocodificação de municípios e dados de área urbana. O fluxo principal cria:

- centroides populacionais ponderados por município;
- uma matriz de demanda normalizada via modelo gravitacional exponencial;
- uma matriz de custo de coleta por região;
- uma instância completa em formato texto para uso em solver.

## O que o projeto faz

A pipeline é executada por [main.py](main.py) e segue estes passos:

1. coleta população municipal e informações de localização do IBGE;
2. geocodifica os municípios de São Paulo com o Nominatim;
3. calcula centroides ponderados por população para cada região intermediária;
4. gera a matriz de demanda `W_ij` a partir do modelo gravitacional;
5. calcula o custo unitário de coleta `C_col_ik`;
6. escreve a instância final em um arquivo de texto.

## Estrutura do repositório

- [main.py](main.py) - executa o pipeline completo em sequência.
- [src/construcao_matriz_demanda.py](src/construcao_matriz_demanda.py) - gera a matriz de demanda normalizada.
- [src/construcao_matriz_custo_de_coleta.py](src/construcao_matriz_custo_de_coleta.py) - calcula os custos de coleta.
- [src/utils/centroide_ponderado.py](src/utils/centroide_ponderado.py) - busca população e coordenadas e calcula os centroides.
- [src/utils/area_urbana.py](src/utils/area_urbana.py) - integra a área urbana dos municípios à base de regiões.
- [src/utils/gerador_instancia.py](src/utils/gerador_instancia.py) - consolida as matrizes e gera a instância final.
- [configs/params.py](configs/params.py) - parâmetros do modelo gravitacional e do custo de coleta.
- [configs/paths.py](configs/paths.py) - caminhos dos arquivos de entrada, intermediários e saída.
- [data/](data/) - dados de entrada, como a planilha de área urbana.
- [output/](output/) - arquivos gerados pela execução.

## Requisitos

Instale as dependências com:

```bash
pip install -r requirements.txt
```

## Como executar

Rode o pipeline completo com:

```bash
python main.py
```

O comando cria automaticamente a pasta [output/](output/) e gera os arquivos abaixo.

## Arquivos de saída

- [output/municipios_sp.json](output/municipios_sp.json) - cache dos municípios com população e coordenadas geocodificadas.
- [output/regioes_sp.json](output/regioes_sp.json) - centroides ponderados por região intermediária.
- [output/matriz_demanda.json](output/matriz_demanda.json) - matriz de demanda `W_ij`.
- [output/matriz_custo_coleta_sp.json](output/matriz_custo_coleta_sp.json) - matriz de custo de coleta `C_col_ik`.
- [output/custo_coleta_sp_detalhado.csv](output/custo_coleta_sp_detalhado.csv) - detalhes linha a linha do cálculo de coleta.
- [output/sp11_instancia_completa.txt](output/sp11_instancia_completa.txt) - instância final completa em formato texto.

## Observações importantes

- A execução depende de conexão com a internet, pois o projeto consulta APIs do IBGE e do Nominatim.
- A primeira execução pode levar alguns minutos, principalmente na geocodificação dos municípios.
- O arquivo [output/municipios_sp.json](output/municipios_sp.json) funciona como cache para evitar refazer a geocodificação em execuções subsequentes.
