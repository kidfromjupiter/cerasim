"""CeraSim Frontend - Streamlit Components"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import format_currency
from charts import create_production_chart, create_financial_chart
from utils import create_kpi_summary


def display_top_metrics(kpis: dict) -> None:
    """
    Display 4 key metrics at the top of the results.
    
    Parameters
    ----------
    kpis : dict
        Dictionary of computed KPIs
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "📦 Total Production",
            f"{kpis.get('total_production_units', 0):.0f} units",
            f"{kpis.get('avg_daily_m2', 0):.1f} units/day",
        )

    with col2:
        st.metric(
            "📋 Orders Fulfilled",
            f"{kpis.get('fill_rate_pct', 0):.1f}%",
            f"{kpis.get('total_fulfilled_m2', 0):.0f} / {kpis.get('total_ordered_m2', 0):.0f} units",
        )

    with col3:
        st.metric(
            "💰 Net Profit",
            format_currency(kpis.get("net_profit_eur", 0)),
            f"{kpis.get('net_margin_pct', 0):.1f}% margin",
        )

    with col4:
        st.metric(
            "⏱️ Avg Cycle Time",
            f"{kpis.get('avg_cycle_time_hr', 0):.1f} hours",
            f"{kpis.get('avg_cycle_time_hr', 0) / 24:.1f} days",
        )


def display_charts(kpis: dict, generate_charts: bool) -> None:
    """
    Display visualization charts.
    
    Parameters
    ----------
    kpis : dict
        Dictionary of computed KPIs
    generate_charts : bool
        Whether to generate and display charts
    """
    if not generate_charts:
        return

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        prod_chart = create_production_chart(kpis)
        if prod_chart:
            st.plotly_chart(prod_chart, use_container_width=True)

    with chart_col2:
        fin_chart = create_financial_chart(kpis)
        if fin_chart:
            st.plotly_chart(fin_chart, use_container_width=True)

    st.divider()


def tab_summary(kpis: dict) -> None:
    """Display summary tab with all KPIs."""
    st.subheader("Key Performance Indicators")
    summary_df = create_kpi_summary(kpis)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)


def tab_production(kpis: dict) -> None:
    """Display production metrics tab."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Grade A Units", f"{kpis.get('grade_a_units', 0):.0f}")
        st.metric("Avg Daily Output", f"{kpis.get('avg_daily_m2', 0):.1f} units")

    with col2:
        st.metric("Grade B Units", f"{kpis.get('grade_b_units', 0):.0f}")
        st.metric("Total Batches", f"{kpis.get('total_batches', 0):.0f}")

    with col3:
        st.metric("Reject Units", f"{kpis.get('reject_units', 0):.0f}")
        st.metric("Avg Cycle Time", f"{kpis.get('avg_cycle_time_hr', 0):.1f} hours")

    st.subheader("Production by Product")
    prod_df = pd.DataFrame(
        list(kpis.get("production_by_product", {}).items()),
        columns=["Product", "Units"],
    )
    if not prod_df.empty:
        st.dataframe(prod_df, use_container_width=True, hide_index=True)


def tab_orders(kpis: dict) -> None:
    """Display order fulfillment metrics tab."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Orders", f"{kpis.get('total_orders', 0):.0f}")
        st.metric("Complete Orders", f"{kpis.get('complete_pct', 0):.1f}%")

    with col2:
        st.metric("Total Ordered", f"{kpis.get('total_ordered_m2', 0):.0f} units")
        st.metric("On-Time Delivery", f"{kpis.get('otd_rate_pct', 0):.1f}%")

    with col3:
        st.metric("Total Fulfilled", f"{kpis.get('total_fulfilled_m2', 0):.0f} units")
        st.metric("Avg Lead Time", f"{kpis.get('avg_lead_time_days', 0):.1f} days")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Stockout Events", f"{kpis.get('stockout_events', 0):.0f}")
    with col2:
        st.metric("Partial Fulfillments", f"{kpis.get('partial_fulfils', 0):.0f}")


def tab_financial(kpis: dict) -> None:
    """Display financial metrics tab."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Revenue", format_currency(kpis.get("revenue_eur", 0)))
        st.metric("Raw Material Cost", format_currency(kpis.get("raw_mat_cost_eur", 0)))

    with col2:
        st.metric("Total Cost", format_currency(kpis.get("total_cost_eur", 0)))
        st.metric("Energy Cost", format_currency(kpis.get("energy_cost_eur", 0)))

    with col3:
        st.metric("Net Profit", format_currency(kpis.get("net_profit_eur", 0)))
        st.metric("Labor Cost", format_currency(kpis.get("labor_cost_eur", 0)))

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Gross Margin", f"{kpis.get('gross_margin_pct', 0):.1f}%")
        st.metric("Breakdown Cost", format_currency(kpis.get("breakdown_cost_eur", 0)))
    with col2:
        st.metric("Net Margin", f"{kpis.get('net_margin_pct', 0):.1f}%")
        st.metric("Stockout Cost", format_currency(kpis.get("stockout_cost_eur", 0)))


def tab_machines(kpis: dict) -> None:
    """Display machine reliability metrics tab."""
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Breakdowns", f"{kpis.get('total_breakdowns', 0):.0f}")
        st.metric("Breakdown Hours", f"{kpis.get('breakdown_hours', 0):.1f} hours")

    with col2:
        st.metric("Disruption Hours", f"{kpis.get('disruption_hours', 0):.1f} hours")
        st.metric("Supplier Lead Time", f"{kpis.get('avg_supplier_lead_time_hr', 0):.1f} hours")

    st.subheader("Breakdowns by Machine")
    breakdown_df = pd.DataFrame(
        list(kpis.get("breakdowns_by_machine", {}).items()),
        columns=["Machine", "Breakdowns"],
    )
    if not breakdown_df.empty:
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

    st.metric(
        "On-Time Delivery (Supplier)",
        f"{kpis.get('on_time_delivery_pct', 0):.1f}%",
    )
