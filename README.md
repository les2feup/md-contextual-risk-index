![Figure 1](./data/figures/les2banner.png)

# Multi-domain Contextual Risk Index

## Description

This repository contains the implementation of a comprehensive multilayer assessment framework for generating contextual risk indices in urban environments. The system integrates multiple geospatial data layers including risk, spatiotemporal vulnerability, response capacity, and socioeconomic indicators to produce a unified contextual risk assessment. Experiments were conducted for Lisbon and Porto, Portugal.

The framework employs hexagonal grid-based spatial analysis with 100-meter edge length cells, combining:
- **Response Layer (L1-Response)**: Mitigation zones and emergency response capacity
- **Risk Layer (L2-Flood)**: Flood zones and environmental hazards  
- **Vulnerability Layer (L3-Vulnerability)**: Spatiotemporal vulnerability assessment across 4 scenarios
- **Socioeconomic Layers (L4-L5)**: Gini index and median income distribution

## Article Information

[TBD]

## Repository Structure

```plaintext
/md-contextual-risk-index
├── data/                          # Geospatial datasets and processed layers
│   ├── cities/                    # City boundary files (Lisbon, Porto)
│   ├── figures/                   # Generated visualizations and plots
│   ├── multi_layers/              # Integrated multi-layer datasets
│   ├── poti/                      # POTI (Points of Interest) datasets
│   ├── response_layer/            # Mitigation zones data
│   ├── risk_layer/                # Flood zones and environmental risk data
│   ├── socioeconomic_layer/       # Gini index and income data
│   ├── time_windows/              # Temporal analysis configurations
│   ├── vulnerability_layer/       # Spatiotemporal vulnerability 
├── notebook/                      # Jupyter notebooks for analysis pipeline
├── requirements.txt               # Python dependencies
├── .gitignore                     # Git ignore patterns
├── LICENSE                        # Repository license
└── README.md                      # This documentation
```

## Installation

### Prerequisites
- Python 3.8 or higher
- Jupyter Notebook/Lab
- Git

### Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone git@github.com:les2feup/md-contextual-risk-index.git
   cd md-contextual-risk-index
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch Jupyter Notebook**:
   ```bash
   jupyter notebook
   ```

## Reproducing Results

Follow these notebooks in sequence to reproduce the complete analysis pipeline:

### 1. Spatiotemporal Vulnerability Assessment
```bash
jupyter notebook notebook/01-spatiotemporal_vulnerability_assessment.ipynb
```
Generates vulnerability layers for 4 temporal scenarios using POTI data and time windows. The scenarios and the time-window table are defined in `data/time_windows/scenarios_T1g.csv` and `data/time_windows/time_windows_T1g.csv` (see `docs/thesis/README.md`); requires `verus>=1.1.1`. The article's original setup and results are in git commit `7cef902`.

### 2. Data Layer Preparation
```bash
# Convert city zones data
jupyter notebook notebook/02-convert_from_cityzones.ipynb

# Process air quality indices (Lisbon)
jupyter notebook notebook/03-lisbon_air_quality_index.ipynb

# Generate socioeconomic layers (Porto)
jupyter notebook notebook/04_gini_index_porto.ipynb
jupyter notebook notebook/05_median_income_porto.ipynb
```

### 3. Integrated Grid Generation
```bash
jupyter notebook notebook/06-integrated_hexagonal_grid_porto.ipynb
```
Creates grid maps integrating all data layers for spatial analysis.

### 4. Multi-layer Assessment and CRI Calculation
```bash
# Multi-layer integration
jupyter notebook notebook/07_multi_layer_assessment.ipynb

# Contextual Risk Index analysis
jupyter notebook notebook/08_CRI_Analysis_All_Scenarios.ipynb

# Tables for the thesis (docs/thesis/)
jupyter notebook notebook/10-thesis_tables.ipynb
```

`notebook/09-time_window_selection.ipynb` is a separate sensitivity analysis (time-window candidates and entropy-weighting variants) and is not needed to reproduce the results.

### Expected Outputs
- Integrated grid maps with all layers
- Contextual Risk Index calculations for all vulnerability scenarios
- Comparative visualizations and statistical analyses
- Geospatial datasets in GeoJSON format

## Usage

### Single Scenario Example - Load Integrated Dataset
```python
import geopandas as gpd
import matplotlib.pyplot as plt

# Load integrated multi-layer dataset
lisbon_data = gpd.read_file('data/multi_layers/Lisbon_multi_layer_all_scenarios_with_CRI.geojson')

# Plot CRI for scenario 1
fig, ax = plt.subplots(figsize=(12, 10))
lisbon_data.plot(column='s1_cri', cmap='RdYlGn_r', ax=ax, legend=True)
plt.title('Contextual Risk Index - Scenario 1 (Lisbon)')
plt.show()
```

### Multi-scenario Analysis
```python
# Compare CRI across all scenarios
scenarios = ['s1', 's2', 's3', 's4']
cri_columns = [f'{s}_cri' for s in scenarios]

# Calculate correlation matrix
correlation_matrix = lisbon_data[cri_columns].corr()
print("CRI Correlation Matrix Across Scenarios:")
print(correlation_matrix)
```

## Key Features

- **Hexagonal Grid Analysis**: 100m edge length hexagonal spatial discretization for more localized assessment
- **Multi-layer Integration**: Seamless combination of multiple data layers
- **Temporal Scenarios**: allow different spatiotemporal scenarios
- **Multi City Analysis**: Examples of analysis for Lisbon and Porto, Portugal
- **Reproducible Pipeline**: End-to-end Jupyter notebook workflow avaliable
- **Geospatial Outputs**: Standards-compliant GeoJSON format exports

## Dependencies

Key Python packages:
- `geopandas`: Geospatial data processing
- `matplotlib`: Data visualization
- `pandas`: Data manipulation
- `shapely`: Geometric operations
- `contextily`: Basemap integration
- `seaborn`: Statistical visualizations
- `verus`: Hexagonal grid generation
- `osmnx`: OpenStreetMap data access

See `requirements.txt` for complete dependency list.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- LES2 FEUP Research Group
- Portuguese cities of Lisbon and Porto for data availability
- OpenStreetMap contributors for geospatial data

---

**Research Group**: Laboratory of Software Engineering and Engineering (LES2)  
**Institution**: Faculty of Engineering, University of Porto (FEUP)  
**Contact**: [Contact information to be added]
