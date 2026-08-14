# Modelo gravitacional espacial para as regiões intermediárias de São Paulo

Este repositório cria uma instância do modelo gravitacional para as 11 regiões intermediárias de São Paulo, gerando centroides populacionais, uma matriz origem-destino (OD) e matrizes de custo para uso em modelos de localização de hubs.

Resumo conciso do modelo (contexto útil):

- Construção da matriz de demanda (W_ij):
  - Calcular população por região (soma das populações municipais).
  - Estimar área atendida por região (soma das áreas urbanizadas municipais).
  - Calcular centroide populacional ponderado por população.
  - Definir produção e atratividade simples como população: Prodi = Popi, Atraj = Popj.
  - Propensão bruta de fluxo: gij = Prodi * Atraj * exp(-γ · dij), com γ penalizando distância.
  - Normalizar os fluxos para um total T (por exemplo, T = 100000) para obter wij.

- Cálculo de custos por caminho i → k → m → j (resumo):
  - Coleta (i ← k): inclui distância de acesso (ida e volta: 2·d_ik por rota) e distância interna aproximada na região (com termo contínuo β_col · sqrt(A_i · N_col_i)). O custo unitário de coleta é obtido dividindo o custo total diário pelo volume O_i gerado em i.
  - Transporte inter-hub (k → m): custo por km por unidade de carga C_hub_km = c_hub · d_km, normalmente com fator de desconto 0 < α ≤ 1 (economia de escala).
  - Entrega (m → j): análogo à coleta, considerando acesso do hub m à região j.
  - Custo unitário total do caminho: c_ijkm = C_col_ik + α · C_hub_km + C_ent_mj.

Esses custos unitários são multiplicados pelos fluxos wij e usados na função objetivo de minimização do custo total.

Principais scripts e estrutura

- [main.py](</home/rafael/Área de trabalho/SIDRA/main.py>) - pipeline que executa todo o processo.
- [src/construcao_matriz_demanda.py](</home/rafael/Área de trabalho/SIDRA/src/construcao_matriz_demanda.py>)
- [src/construcao_matriz_custo_de_coleta.py](</home/rafael/Área de trabalho/SIDRA/src/construcao_matriz_custo_de_coleta.py>)
- [src/utils/centroide_ponderado.py](</home/rafael/Área de trabalho/SIDRA/src/utils/centroide_ponderado.py>)
- [configs/params.py](</home/rafael/Área de trabalho/SIDRA/configs/params.py>) - parâmetros (γ, β_col, c_col, c_hub, Qcol, ρ_col, T, α, etc.).
- [data/](</home/rafael/Área de trabalho/SIDRA/data/>) - entradas (área urbana, populações).
- [output/](</home/rafael/Área de trabalho/SIDRA/output/>) - resultados gerados.

Como executar (rápido)

1. Criar/ativar um ambiente virtual (recomendado) e instalar dependências (exemplo para Linux/macOS):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Executar a pipeline:

```bash
python main.py
```

Saídas principais (geradas em [output/](</home/rafael/Área de trabalho/SIDRA/output/>)):

- [output/municipios_sp.json](</home/rafael/Área de trabalho/SIDRA/output/municipios_sp.json>)
- [output/regioes_sp.json](</home/rafael/Área de trabalho/SIDRA/output/regioes_sp.json>)
- [output/matriz_demanda.json](</home/rafael/Área de trabalho/SIDRA/output/matriz_demanda.json>)
- [output/matriz_custo_coleta_sp.json](</home/rafael/Área de trabalho/SIDRA/output/matriz_custo_coleta_sp.json>)
- [output/sp11_instancia_completa.txt](</home/rafael/Área de trabalho/SIDRA/output/sp11_instancia_completa.txt>)

Observações e boas práticas

- O projeto consulta APIs externas (IBGE, Nominatim); internet é necessária na primeira execução. O arquivo de municípios funciona como cache para evitar repetição da geocodificação.
- Recomenda-se criar o ambiente virtual no diretório do projeto com nome `.venv` e adicioná-lo ao `.gitignore` para não versionar dependências geradas.

Adicionar a venv ao .gitignore (exemplo)

```bash
# adiciona .venv/ ao .gitignore se ainda não existir
grep -qxF ".venv/" .gitignore || echo ".venv/" >> .gitignore
git add .gitignore
git commit -m "Add .venv to .gitignore" || true
```

Notas finais

O conteúdo deste README é intencionalmente conciso. Para detalhes matemáticos e fórmulas completas, consulte as funções em [src/construcao_matriz_demanda.py](</home/rafael/Área de trabalho/SIDRA/src/construcao_matriz_demanda.py>) e [src/construcao_matriz_custo_de_coleta.py](</home/rafael/Área de trabalho/SIDRA/src/construcao_matriz_custo_de_coleta.py>).
