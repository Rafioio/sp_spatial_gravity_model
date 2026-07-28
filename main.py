import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run_step(script_name: str) -> None:
    script_path = ROOT / "src" / script_name
    print(f"\n=== Executando {script_name} ===")
    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=ROOT,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(f"Falha ao executar {script_name} (código {completed.returncode}).")


def main() -> None:
    run_step("population_weighted_centroid.py")
    run_step("gravity_model.py")
    run_step("ca_data.py")
    print("\nFluxo concluído com sucesso!")


if __name__ == "__main__":
    main()
