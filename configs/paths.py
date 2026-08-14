from pathlib import Path

def ensure_directories():
    for directory in [DATA_DIR, INPUT_DIR, OUTPUT_DIR, INSTANCIAS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
        
# Diretórios
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
DATA_DIR = ROOT_DIR / "data"
DATA_INTERMEDIARIA_DIR = DATA_DIR / "intermediaria"
INPUT_DIR = ROOT_DIR / "input"
OUTPUT_DIR = ROOT_DIR / "output"
ASSETS_DIR = ROOT_DIR / "assets"
INSTANCIAS_DIR = ROOT_DIR / "output" / "instancias"

# Arquivos de entrada
ARQUIVO_PLANILHA_AREA = DATA_DIR / "area_urbana_municipios_sp_2024.xlsx"
ARQUIVO_CENARIOS = INPUT_DIR / "cenarios.json"

# Arquivos intermediários
ARQUIVO_MUNICIPIOS_SP = DATA_INTERMEDIARIA_DIR / "municipios_sp.json"
ARQUIVO_REGIOES_SP = DATA_INTERMEDIARIA_DIR / "regioes_sp.json"

# Arquivos de saída
ARQUIVO_MATRIZ_DEMANDA = OUTPUT_DIR / "matriz_demanda.json"
ARQUIVO_MATRIZ_CUSTO_COLETA = OUTPUT_DIR / "matriz_custo_coleta_sp.json"

ARQUIVO_CUSTO_COLETA_CSV = OUTPUT_DIR / "custo_coleta_sp_detalhado.csv"
ARQUIVO_MATRIZ_DEMANDA_CSV = OUTPUT_DIR / "demanda_sp_detalhada.csv"

ARQUIVO_SAIDA_INSTANCIA = INSTANCIAS_DIR / "sp11_instancia_completa.txt"


