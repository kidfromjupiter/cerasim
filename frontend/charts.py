"""CeraSim Frontend - Chart Generation"""

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def create_production_chart(kpis: dict) -> Optional[go.Figure]:
    """
    Create a production breakdown pie chart by product.
    
    Parameters
    ----------
    kpis : dict
        Dictionary of computed KPIs
        
    Returns
    -------
    go.Figure or None
        Plotly pie chart, or None if no production data
    """
    prod_by_product = kpis.get("production_by_product", {})
    if not prod_by_product:
        return None

    df = pd.DataFrame(
        list(prod_by_product.items()),
        columns=["Product", "Units"],
    )
    fig = px.pie(
        df,
        values="Units",
        names="Product",
        title="Production by Product",
    )
    fig.update_layout(showlegend=True)
    return fig


def create_financial_chart(kpis: dict) -> Optional[go.Figure]:
    """
    Create a cost breakdown bar chart.
    
    Parameters
    ----------
    kpis : dict
        Dictionary of computed KPIs
        
    Returns
    -------
    go.Figure or None
        Plotly bar chart, or None if no cost data
    """
    costs = {
        "Raw Materials": kpis.get("raw_mat_cost_eur", 0),
        "Energy": kpis.get("energy_cost_eur", 0),
        "Labor": kpis.get("labor_cost_eur", 0),
        "Breakdowns": kpis.get("breakdown_cost_eur", 0),
        "Stockouts": kpis.get("stockout_cost_eur", 0),
    }
    
    # Filter out zero costs
    costs = {k: v for k, v in costs.items() if v > 0}
    
    if not costs:
        return None

    df = pd.DataFrame(list(costs.items()), columns=["Cost Type", "Amount"])
    fig = px.bar(
        df,
        x="Cost Type",
        y="Amount",
        title="Cost Breakdown",
        labels={"Amount": "Amount (€)", "Cost Type": ""},
    )
    fig.update_layout(
        yaxis_title="Amount (€)",
        xaxis_title="",
        showlegend=False,
    )
    return fig


def create_timeline_chart(stage_log: dict) -> Optional[go.Figure]:
    """
    Create a timeline chart showing production stages.
    
    Parameters
    ----------
    stage_log : dict
        Stage completion log from metrics
        
    Returns
    -------
    go.Figure or None
        Plotly figure, or None if no stage data
    """
    if not stage_log:
        return None
    
    # Flatten stage logs into a single dataset
    data = []
    for stage, entries in stage_log.items():
        if entries:
            times = [e[0] / 24 for e in entries]  # Convert hours to days
            cumulative = [sum(e[1] for e in entries[:i+1]) for i in range(len(entries))]
            for t, cum in zip(times, cumulative):
                data.append({"Day": t, "Stage": stage, "Cumulative Units": cum})
    
    if not data:
        return None
    
    df = pd.DataFrame(data)
    fig = px.line(
        df,
        x="Day",
        y="Cumulative Units",
        color="Stage",
        title="Production Timeline by Stage",
    )
    return fig
