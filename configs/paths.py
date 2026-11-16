from pathlib import Path

def ensure_directories():
    for directory in [DATA_DIR, INPUT_DIR, OUTPUT_DIR, INSTANCIAS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
        
# Diretórios
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
DATA_DIR = ROOT_DIR / "data"
DATA_REGIOES_DIR = DATA_DIR / "regioes"
INPUT_DIR = ROOT_DIR / "input"
OUTPUT_DIR = ROOT_DIR / "output"
ASSETS_DIR = ROOT_DIR / "assets"
INSTANCIAS_DIR = ROOT_DIR / "output" / "instancias"

# Arquivos de entrada
ARQUIVO_PLANILHA_AREA = DATA_DIR / "area_municipios_sp.csv"
ARQUIVO_PLANILHA_POPULACAO = DATA_DIR / "populacao_municipios_sp.csv"
ARQUIVO_CENARIOS = INPUT_DIR / "cenarios.json"

# Arquivos intermediários
ARQUIVO_MUNICIPIOS_SP = DATA_REGIOES_DIR / "municipios_sp.json"
ARQUIVO_REGIOES_INTERMEDIARIAS_SP = DATA_REGIOES_DIR / "regioes_intermediarias_sp.json"
ARQUIVO_REGIOES_IMEDIATAS_SP = DATA_REGIOES_DIR / "regioes_imediatas_sp.json"

# Arquivos de saída
ARQUIVO_MATRIZ_CUSTO_COLETA = OUTPUT_DIR / "matriz_custo_coleta_sp.json"
ARQUIVO_MATRIZ_CUSTO_ENTREGA = OUTPUT_DIR / "matriz_custo_entrega_sp.json"

ARQUIVO_CUSTO_COLETA_CSV = OUTPUT_DIR / "custo_coleta_sp_detalhado.csv"
ARQUIVO_CUSTO_ENTREGA_CSV = OUTPUT_DIR / "custo_entrega_sp_detalhado.csv"

ARQUIVO_MATRIZ_DEMANDA_INTERMEDIARIAS = OUTPUT_DIR / "matriz_demanda_intermediarias.json"
ARQUIVO_MATRIZ_DEMANDA_IMEDIATAS = OUTPUT_DIR / "matriz_demanda_imediatas.json"
ARQUIVO_MATRIZ_DEMANDA_INTERMEDIARIAS_CSV = OUTPUT_DIR / "demanda_intermediarias_detalhada.csv"
ARQUIVO_MATRIZ_DEMANDA_IMEDIATAS_CSV = OUTPUT_DIR / "demanda_imediatas_detalhada.csv"

ARQUIVO_SAIDA_INSTANCIA = INSTANCIAS_DIR / "sp11_instancia_completa.txt"

NIVEIS_REGIOES = {
    "intermediarias": {
        "arquivo": ARQUIVO_REGIOES_INTERMEDIARIAS_SP,
        "coluna_nome": "Região Intermediária",
    },
    "imediatas": {
        "arquivo": ARQUIVO_REGIOES_IMEDIATAS_SP,
        "coluna_nome": "Região Imediata",
    },
}

def caminhos_saida(nivel):
    pasta = OUTPUT_DIR / nivel
    return {
        "pasta": pasta,
        "demanda_json": pasta / "matriz_demanda.json",
        "demanda_csv": pasta / "demanda_detalhada.csv",
        "coleta_json": pasta / "matriz_custo_coleta.json",
        "entrega_json": pasta / "matriz_custo_entrega.json",
        "coleta_csv": pasta / "custo_coleta_detalhado.csv",
        "entrega_csv": pasta / "custo_entrega_detalhado.csv",
    }
