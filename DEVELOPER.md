# CeraSim — Developer Guide

**AzulCer Tile Industries · Supply Chain Discrete-Event Simulator**

---

## Using the simulation

### Running it

```bash
# Run all 4 scenarios (default)
python main.py

# Single scenario
python main.py --scenario baseline
python main.py --scenario supply_disruption
python main.py --scenario demand_surge
python main.py --scenario optimised

# Reproducible run with a specific random seed
python main.py --seed 99

# Skip chart generation (faster, terminal-only output)
python main.py --no-charts
```

Output goes to the terminal (Rich tables) and `reports/*.png` (Matplotlib dashboards).

---

## Architecture

```
cerasim/
├── config.py     ← All parameters (products, machines, suppliers, scenarios)
├── models.py     ← Data classes (ProductionBatch, CustomerOrder, …)
├── factory.py    ← SimPy processes — the actual simulation engine
├── metrics.py    ← KPI computation from collected events
└── reports.py    ← Rich console tables + Matplotlib charts

main.py           ← CLI entrypoint — orchestrates runs and output
reports/          ← Generated PNG dashboards
```

### Data flow

```
config.py (parameters)
     │
     ▼
factory.py  ──registers──►  SimPy processes:
     │                         supply_monitor()        → triggers _supplier_delivery()
     │                         body_preparation()      → powder_buf (Container)
     │                         forming_and_drying()    → unglazed_store (Store)
     │                         surface_treatment()     → ready_to_fire (Store)
     │                         kiln_firing()  ★        → fired_store (Store)
     │                         finishing()             → fg[product] (Container)
     │                         demand_generator()      → order_queue (Store)
     │                         order_fulfilment()
     │                         daily_recorder()
     │
     ▼
metrics.py  ──computes──►  KPI dict
     │
     ▼
reports.py  ──renders──►  Rich tables + PNG charts
```

---

## How to extend it

### 1. Add a new product

Open `cerasim/config.py` and append to `PRODUCTS`:

```python
PRODUCTS["OUTDOOR-2020"] = {
    "name":            "Anti-Slip Outdoor Paver 20×20 cm",
    "price_eur_m2":    18.0,
    "body_kg_per_m2":  30.0,
    "glaze_kg_per_m2":  0.0,
    "needs_glaze":     False,
    "demand_share":    0.10,   # all demand_shares should sum to 1.0
    "color":           "#6A994E",
}
```

Also add it to `FG_INITIAL_M2` and `FG_MAX_M2`. Everything else (production routing, demand, metrics, charts) picks it up automatically.

---

### 2. Add a new scenario

In `config.py`, add a key to `SCENARIOS`:

```python
SCENARIOS["dual_disruption"] = {
    "label":       "Dual Disruption",
    "description": "Kaolin strike + 20% machine reliability drop",
    "demand_factor":               1.0,
    "machine_reliability_factor":  0.80,   # degrades all MTBF values
    "supplier_reliability_factor": 1.0,
    "extra_kilns":                 0,
    "safety_stock_factor":         1.0,
    "kaolin_disruption":           (15 * HOURS_PER_DAY, 50 * HOURS_PER_DAY),
}
```

Then run it:

```bash
python main.py --scenario dual_disruption
```

No other files need to change.

---

### 3. Add a new production stage

**Step 1 — Add the machine to `config.py`:**

```python
MACHINES["polishing"] = {
    "name":         "Tile Polishing Line",
    "detail":       "Multi-head planetary polisher",
    "count":        2,
    "proc_mean_hr": 0.5,
    "proc_std_hr":  0.06,
    "mtbf_hr":      600,
    "mttr_hr":      2.0,
    "capex_eur":    250_000,
}
```

**Step 2 — Add a buffer Store between stages in `factory.py __init__`:**

```python
self.polished_store = simpy.Store(env)
```

**Step 3 — Write the process method:**

```python
def polishing(self):
    while True:
        batch = yield self.fired_store.get()     # pull from upstream
        with self.machines["polishing"].request() as req:
            yield req
            t, _ = self._proc_time("polishing")
            yield self.env.timeout(t)
            self._machine_busy_hr["polishing"] += t
        batch.polishing_done = self.env.now
        yield self.polished_store.put(batch)     # push downstream
        self.metrics.record_stage("polishing", batch.quantity_m2)
```

**Step 4 — Wire `finishing()` to read from `polished_store` instead of `fired_store`, and register the process in `register_processes()`:**

```python
for _ in range(MACHINES["polishing"]["count"]):
    env.process(self.polishing())
```

**Step 5 — Add the stage to `metrics.py stage_log`:**

```python
self.stage_log: Dict[str, List[...]] = {
    "body_prep": [], "forming": [], "glazing": [],
    "kiln": [], "polishing": [], "finishing": [],   # ← add here
}
```

---

### 4. Add a new supplier

In `config.py`:

```python
SUPPLIERS["pigment"] = {
    "name":               "ColorMix Italia S.r.l.",
    "country":            "Italy",
    "delivery_qty_t":     5.0,
    "lead_time_mean_hr":  56,
    "lead_time_std_hr":   10,
    "reliability":        0.87,
    "unit_cost_eur_t":    450,
    "reorder_point_t":    4,
    "max_stock_t":        25,
}
INITIAL_INVENTORY["pigment"] = 8.0
```

Then consume it in a production stage the same way `glaze` is consumed in `surface_treatment()`.

---

### 5. Add a new KPI

All raw event data is stored on `factory.metrics`:

| Attribute | Type | Contents |
|---|---|---|
| `metrics.completed_batches` | `list[ProductionBatch]` | Every finished 250 m² batch |
| `metrics.orders` | `list[CustomerOrder]` | Every customer order placed |
| `metrics.deliveries` | `list[SupplierDelivery]` | Every supplier delivery received |
| `metrics.breakdowns` | `list[BreakdownEvent]` | Every machine failure |
| `metrics.daily_snapshots` | `list[dict]` | System state snapshot, once per day |

Add your computation in `metrics.py → compute_kpis()`:

```python
# Example: kiln first-pass yield
kiln_batches = [b for b in batches if b.firing_done is not None]
k["kiln_yield_pct"] = (
    sum(b.grade_a_m2 for b in kiln_batches) /
    max(1, sum(b.quantity_m2 for b in kiln_batches)) * 100
)
```

Then reference `kpis["kiln_yield_pct"]` in `reports.py` to display it.

---

### 6. Run programmatically (no CLI)

```python
import simpy
from cerasim.config import SIM_DAYS, SIM_DURATION, HOURS_PER_DAY
from cerasim.factory import CeramicFactory

env     = simpy.Environment()
factory = CeramicFactory(env, scenario="optimised", seed=7)
factory.register_processes()
env.run(until=SIM_DURATION)

kpis = factory.metrics.compute_kpis(SIM_DAYS)
print(f"Net profit: €{kpis['net_profit_eur']:,.0f}")
print(f"Fill rate:  {kpis['fill_rate_pct']:.1f}%")

# Access raw event logs
for b in factory.metrics.breakdowns:
    print(f"  Breakdown: {b.machine_name} at day {b.occurred_at/24:.1f}, "
          f"repair {b.repair_duration:.1f}h")
```

---

## Key SimPy concepts used

| Concept | Where used | Why |
|---|---|---|
| `simpy.Resource` | Each machine group | Models capacity — processes queue when all machines busy |
| `simpy.Container` | Raw materials, powder buffer, finished goods | Continuous quantity (tonnes / m²) with get/put |
| `simpy.Store` | Inter-stage batch queues, order queue | Discrete objects (batches, orders) pass between processes |
| `env.process()` | Every stage, supplier, demand generator | Registers a generator as a concurrent SimPy process |
| `env.timeout()` | Processing times, poll loops | Advances simulation clock |
