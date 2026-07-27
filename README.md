# SIDRA Spatial Gravity Model

This project downloads municipality population data, geocodes São Paulo municipalities, computes population-weighted centroids for São Paulo intermediate regions, and generates a normalized flow matrix for a spatial gravity model.

## Project structure

- `src/population_weighted_centroid.py` - fetches IBGE municipality population and location data, geocodes municipalities with Nominatim, and calculates population-weighted centroids by intermediate region.
- `src/gravity_model.py` - reads the generated centroid data and writes a normalized flow matrix instance file using a gravity model.
- `main.py` - runs the full pipeline in sequence.
- `output/` - stores generated JSON and text outputs.

## Requirements

Install the dependencies with:

```bash
pip install -r requirements.txt
```

## How to run

Run the full pipeline with a single command:

```bash
python main.py
```

This will execute, in order:

1. `src/population_weighted_centroid.py`
2. `src/gravity_model.py`

## Output files

- `output/municipios_sp_coordenadas.json` - cached municipality coordinates.
- `output/centroides_populacionais_sp.json` - population-weighted centroids by intermediate region.
- `output/sp11_flow_only.txt` - gravity model flow matrix instance.
