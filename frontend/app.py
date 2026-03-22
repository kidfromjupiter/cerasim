#!/usr/bin/env python3
"""
CeraSim Streamlit Frontend - Main Application
==============================================

Interactive web interface for running supply chain simulations.
Allows users to select scenarios, configure parameters, run simulations,
and view KPI outputs.

Modular architecture:
  - config.py      → Configuration and constants
  - utils.py       → Helper functions (formatting, simulation runner)
  - charts.py      → Chart visualization functions
  - components.py  → Streamlit UI components
  - app.py         → Main orchestration (this file)
"""

import sys
import time
from pathlib import Path

import streamlit as st

# Add parent directory to path for cerasim imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    PAGE_CONFIG, STREAMLIT_CSS, TABS, SESSION_DEFAULTS,
    SCENARIOS,
)
from utils import run_simulation
from components import (
    display_top_metrics, display_charts,
    tab_summary, tab_production, tab_orders,
    tab_financial, tab_machines,
)


# ─────────────────────────────────────────────────────────────────────────────
# Page Setup
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(**PAGE_CONFIG)
st.markdown(STREAMLIT_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Session State Initialization
# ─────────────────────────────────────────────────────────────────────────────

for key, default_value in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default_value


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────

st.title("CeraSim — Supply Chain Simulator")
st.markdown("**SaniCer Sanitary Ware Industries** | 90-day discrete-event simulation")
st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar Configuration
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Simulation Configuration")

    # Scenario selection
    scenario_names = list(SCENARIOS.keys())
    scenario_idx = scenario_names.index(st.session_state.selected_scenario)
    selected_scenario = st.selectbox(
        "Select Scenario",
        scenario_names,
        index=scenario_idx,
        format_func=lambda x: SCENARIOS[x]["label"],
    )
    st.session_state.selected_scenario = selected_scenario

    # Scenario description
    scenario_desc = SCENARIOS[selected_scenario]["description"]
    st.info(scenario_desc, icon=None)

    # Advanced options
    with st.expander("Advanced Options"):
        seed = st.number_input("Random Seed", value=42, min_value=0, max_value=10000)
        generate_charts = st.checkbox("Generate charts", value=True)
    
    st.divider()

    # Run button
    run_button = st.button(
        "Run Simulation",
        use_container_width=True,
        type="primary",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Simulation Execution
# ─────────────────────────────────────────────────────────────────────────────

if run_button:
    with st.spinner("Running simulation..."):
        try:
            start_time = time.time()
            factory, kpis = run_simulation(selected_scenario, seed=seed)
            elapsed = time.time() - start_time

            st.session_state.sim_results = {
                "factory": factory,
                "kpis": kpis,
                "scenario": selected_scenario,
                "seed": seed,
                "elapsed": elapsed,
            }
            st.success(f"Simulation completed in {elapsed:.2f} seconds")

        except Exception as e:
            st.error(f"Simulation failed: {str(e)}")
            st.exception(e)


# ─────────────────────────────────────────────────────────────────────────────
# Results Display
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.sim_results:
    results = st.session_state.sim_results
    kpis = results["kpis"]
    scenario = results["scenario"]

    # Results header
    st.subheader(f"Results — {SCENARIOS[scenario]['label']}")
    st.caption(f"Seed: {results['seed']} | Computed in {results['elapsed']:.2f}s")
    st.divider()

    # Key metrics at the top
    display_top_metrics(kpis)
    st.divider()

    # Charts
    display_charts(kpis, generate_charts)

    # Detailed tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(TABS)

    with tab1:
        tab_summary(kpis)

    with tab2:
        tab_production(kpis)

    with tab3:
        tab_orders(kpis)

    with tab4:
        tab_financial(kpis)

    with tab5:
        tab_machines(kpis)

else:
    st.info(
        "Configure the simulation in the sidebar and click Run Simulation to begin.",
        icon=None,
    )
