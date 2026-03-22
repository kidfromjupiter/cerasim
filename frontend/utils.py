"""CeraSim Frontend - Utility Functions"""

import sys
import time
from pathlib import Path
from typing import Tuple

import streamlit as st
import pandas as pd
import simpy

# Add parent directory to path for cerasim imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cerasim.factory import CeramicFactory
from cerasim.config import SIM_DAYS, HOURS_PER_DAY


def run_simulation(scenario_id: str, seed: int = 42) -> Tuple[CeramicFactory, dict]:
    """
    Run a single scenario simulation and return factory & KPIs.
    
    Parameters
    ----------
    scenario_id : str
        The scenario to run (e.g., 'baseline', 'supply_disruption')
    seed : int
        Random seed for reproducibility (default: 42)
        
    Returns
    -------
    tuple
        (factory object, KPI dictionary)
    """
    env = simpy.Environment()
    factory = CeramicFactory(env, scenario=scenario_id, seed=seed)
    factory.register_processes()

    # Simulate with progress tracking
    progress_bar = st.progress(0)
    for day in range(SIM_DAYS):
        env.run(until=(day + 1) * HOURS_PER_DAY)
        progress_bar.progress((day + 1) / SIM_DAYS)

    kpis = factory.metrics.compute_kpis(SIM_DAYS)
    return factory, kpis


def format_currency(value: float) -> str:
    """Format a value as EUR currency."""
    return f"€{value:,.0f}"


def format_percentage(value: float) -> str:
    """Format a value as percentage."""
    return f"{value:.1f}%"


def create_kpi_summary(kpis: dict) -> pd.DataFrame:
    """
    Create a summary table of key KPIs.
    
    Parameters
    ----------
    kpis : dict
        Dictionary of computed KPIs
        
    Returns
    -------
    pd.DataFrame
        Summary table with KPI names and values
    """
    return pd.DataFrame({
        "KPI": [
            "Total Production (units)",
            "Average Daily Output",
            "Total Orders",
            "Total Fulfilled",
            "Fill Rate",
            "On-Time Delivery Rate",
            "Average Cycle Time (hours)",
            "Total Revenue",
            "Total Cost",
            "Net Profit",
            "Net Margin",
            "Machine Breakdowns",
            "Breakdown Hours",
        ],
        "Value": [
            f"{kpis.get('total_production_units', 0):.0f}",
            f"{kpis.get('avg_daily_m2', 0):.1f}",
            f"{kpis.get('total_orders', 0):.0f}",
            f"{kpis.get('total_fulfilled_m2', 0):.0f}",
            f"{kpis.get('fill_rate_pct', 0):.1f}%",
            f"{kpis.get('otd_rate_pct', 0):.1f}%",
            f"{kpis.get('avg_cycle_time_hr', 0):.1f}",
            format_currency(kpis.get("revenue_eur", 0)),
            format_currency(kpis.get("total_cost_eur", 0)),
            format_currency(kpis.get("net_profit_eur", 0)),
            f"{kpis.get('net_margin_pct', 0):.1f}%",
            f"{kpis.get('total_breakdowns', 0):.0f}",
            f"{kpis.get('breakdown_hours', 0):.1f}",
        ]
    })
