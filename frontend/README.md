# CeraSim Frontend

Streamlit-based web interface for the CeraSim supply chain simulator.

## Setup

### 1. Install Dependencies

```bash
pip install -r ../requirements.txt
```

### 2. Run the App

Navigate to the frontend directory and run:

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

## Features

### Simulation Configuration

- **Scenario Selection**: Choose from 4 predefined scenarios:
  - **Baseline**: Normal operations with balanced supply & demand
  - **Supply Disruption**: Kaolin shortage during port strike (Day 15-50)
  - **Demand Surge**: 30% demand uplift across all products
  - **Optimised**: 2nd tunnel kiln + 50% safety stock increase

- **Advanced Options**:
  - **Random Seed**: Set for reproducible results (default: 42)
  - **Chart Generation**: Toggle visualization generation on/off

### Output Metrics

#### Summary Tab
- All key KPIs in a single table
- Production, orders, financial, and machine metrics

#### Production Tab
- Grade A, B, and reject units
- Production by product breakdown
- Average cycle time and daily output

#### Orders Tab
- Order fulfillment statistics
- Fill rate and on-time delivery metrics
- Lead times and stockout events

#### Financial Tab
- Revenue, costs, and profit
- Cost breakdown (materials, energy, labor, breakdowns, stockouts)
- Gross and net margins

#### Machines Tab
- Machine breakdown counts and hours
- Supplier lead times and on-time delivery rates
- Disruption analysis

### Visualizations

- **Production Pie Chart**: Sales mix by product
- **Cost Breakdown Bar Chart**: Cost distribution across categories

## How to Use

1. **Configure Simulation**:
   - Select a scenario from the dropdown
   - Optionally adjust the random seed for different outcomes
   - Toggle chart generation if desired

2. **Run Simulation**:
   - Click the **Run Simulation** button
   - Wait for the progress bar to reach 100%

3. **Analyze Results**:
   - View high-level metrics in the top row
   - Explore detailed breakdowns in the tabs below
   - Compare visualizations with KPI tables

## Technical Details

- **Framework**: Streamlit 1.40+
- **Visualization**: Plotly for interactive charts
- **Data Processing**: Pandas
- **Backend**: SimPy discrete-event simulation

## Architecture

```
frontend/
├── app.py              # Main Streamlit application
├── README.md          # This file
└── .streamlit/        # Streamlit configuration
```

The frontend imports the core simulation engine from the parent `cerasim/` directory and runs full 90-day simulations with configurable parameters.
