from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
ASSETS_DIR = ROOT_DIR / "assets"

# Arquivos de entrada
ARQUIVO_PLANILHA_AREA = DATA_DIR / "area_urbana_municipios_sp_2024.xlsx"

# Arquivos intermediários e de saída
ARQUIVO_MUNICIPIOS_SP = OUTPUT_DIR / "municipios_sp.json"
ARQUIVO_REGIOES_SP = OUTPUT_DIR / "regioes_sp.json"
ARQUIVO_BASE_MUNICIPIOS = OUTPUT_DIR / "municipios_sp_base.json"
ARQUIVO_MATRIZ_DEMANDA = OUTPUT_DIR / "matriz_demanda.json"
ARQUIVO_SAIDA_CUSTO_COLETA = OUTPUT_DIR / "custo_coleta_sp.json"
ARQUIVO_SAIDA_DETALHADO = OUTPUT_DIR / "custo_coleta_sp_detalhado.csv"

def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR
