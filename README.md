# SIDRA Spatial Gravity Model

This project downloads economic data from SIDRA, aggregates it by São Paulo intermediate regions, geocodes the regions, and generates a flow matrix for a gravitational model.

## Project structure

- `src/sidra_data.py` - fetches PIB data from SIDRA and saves it as JSON.
- `src/economic_center.py` - geocodes the intermediate regions and joins them with PIB data.
- `src/gravity_model.py` - generates the flow matrix instance file for the model.
- `output/` - generated JSON and text files.

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

1. `src/sidra_data.py`
2. `src/economic_center.py`
3. `src/gravity_model.py`

## Output files

- `output/pib_regions_sp.json`
- `output/pib_with_coordinates_sp.json`
- `output/sp11_flow_only.txt`
