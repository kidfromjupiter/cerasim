# AzulCer Tile Industries — Supply Chain Simulation
# All time units are HOURS; quantities in tonnes (raw materials) or m² (tiles).

# ── Simulation horizon ────────────────────────────────────────────────────────
SIM_DAYS      = 90
HOURS_PER_DAY = 24
SIM_DURATION  = SIM_DAYS * HOURS_PER_DAY   # 2 160 h

BATCH_SIZE_M2 = 250   # m² per production batch — fundamental granule of the sim

# ── Factory metadata ──────────────────────────────────────────────────────────
FACTORY_NAME     = "AzulCer Tile Industries"
FACTORY_LOCATION = "Aveiro, Portugal"
FACTORY_FOUNDED  = 1987
FACTORY_EMPLOYEES = 240

# ── Products ──────────────────────────────────────────────────────────────────
# price_eur_m2  : ex-works price to distributor
# body_kg_per_m2: unfired green body weight (includes moisture, pre-firing shrink)
# glaze_kg_per_m2: wet glaze applied (0 → unglazed / through-body colour)
# demand_share  : fraction of total m² ordered by customers
PRODUCTS = {
    "FLOOR-6060": {
        "name":            "Premium Glazed Floor Tile 60×60 cm",
        "price_eur_m2":    15.0,
        "body_kg_per_m2":  25.0,
        "glaze_kg_per_m2":  1.2,
        "needs_glaze":     True,
        "demand_share":    0.55,
        "color":           "#2E86AB",
    },
    "WALL-3045": {
        "name":            "Glazed Wall Tile 30×45 cm",
        "price_eur_m2":    12.0,
        "body_kg_per_m2":  18.0,
        "glaze_kg_per_m2":  0.9,
        "needs_glaze":     True,
        "demand_share":    0.30,
        "color":           "#A23B72",
    },
    "RUSTIC-4545": {
        "name":            "Rustic Outdoor Tile 45×45 cm",
        "price_eur_m2":    10.0,
        "body_kg_per_m2":  22.0,
        "glaze_kg_per_m2":  0.0,
        "needs_glaze":     False,
        "demand_share":    0.15,
        "color":           "#F18F01",
    },
}

# Weighted average body weight (kg/m²) across the product mix
AVG_BODY_KG_M2 = sum(
    PRODUCTS[p]["body_kg_per_m2"] * PRODUCTS[p]["demand_share"] for p in PRODUCTS
)  # ≈ 22.45 kg/m²

# Ceramic body composition (fraction of dry body weight)
BODY_COMPOSITION = {
    "clay":     0.45,
    "feldspar": 0.25,
    "silica":   0.20,
    "kaolin":   0.10,
}

# ── Production stages ─────────────────────────────────────────────────────────
# proc_mean_hr / proc_std_hr : processing time per BATCH_SIZE_M2 batch
# mtbf_hr                    : mean time between failures (hours of operation)
# mttr_hr                    : mean time to repair (hours), Exponential distribution
# Theoretical max throughput  = (count / proc_mean_hr) × 24  batches/day
#
# Designed so the KILN is the bottleneck:
#   body_prep  3 lines × 24/3.5  = 20.6 batches/day
#   forming    3 presses × 24/1.8 = 40   batches/day
#   glazing    2 lines  × 24/0.35 = 137  batches/day
#   kiln ★     2 kilns  × 24/4.0  = 12   batches/day  ← bottleneck
#   finishing  3 lines  × 24/0.60 = 120  batches/day
MACHINES = {
    "body_prep": {
        "name":         "Body Preparation Line",
        "detail":       "Batch mixer → ball mill → spray dryer",
        "count":        3,
        "proc_mean_hr": 3.5,
        "proc_std_hr":  0.45,
        "mtbf_hr":      340,
        "mttr_hr":      4.5,
        "capex_eur":    900_000,
    },
    "forming": {
        "name":         "Hydraulic Press & Roller Dryer",
        "detail":       "Isostatic press + continuous dryer tunnel",
        "count":        3,
        "proc_mean_hr": 1.8,
        "proc_std_hr":  0.25,
        "mtbf_hr":      480,
        "mttr_hr":      3.0,
        "capex_eur":    700_000,
    },
    "glazing": {
        "name":         "Glaze Application Line",
        "detail":       "Bell/disc glaze + inkjet digital printing",
        "count":        2,
        "proc_mean_hr": 0.35,
        "proc_std_hr":  0.05,
        "mtbf_hr":      720,
        "mttr_hr":      1.5,
        "capex_eur":    450_000,
    },
    "kiln": {
        "name":         "Roller Hearth Kiln",
        "detail":       "Fast-fire single-layer kiln, 1 200 °C peak",
        "count":        2,
        "proc_mean_hr": 4.0,
        "proc_std_hr":  0.20,
        "mtbf_hr":      220,   # Kilns break most often — complex refractory + drives
        "mttr_hr":      7.0,   # Longest repair — must cool before entry
        "capex_eur":    2_400_000,
    },
    "finishing": {
        "name":         "Sorting & Packaging Line",
        "detail":       "Optical sorter + palletiser",
        "count":        3,
        "proc_mean_hr": 0.60,
        "proc_std_hr":  0.08,
        "mtbf_hr":      900,
        "mttr_hr":      1.5,
        "capex_eur":    320_000,
    },
}

# ── Raw-material suppliers ────────────────────────────────────────────────────
# delivery_qty_t     : tonnes per triggered delivery
# lead_time_mean_hr  : average hours from order to gate arrival
# reliability        : probability the delivery is on-time (vs. delayed)
# reorder_point_t    : trigger a replenishment order when stock falls below this
SUPPLIERS = {
    "clay": {
        "name":               "ClayMin Lda",
        "country":            "Portugal",
        "delivery_qty_t":     50.0,
        "lead_time_mean_hr":  36,
        "lead_time_std_hr":    6,
        "reliability":        0.92,
        "unit_cost_eur_t":    85,
        "reorder_point_t":    65,
        "max_stock_t":        260,
    },
    "feldspar": {
        "name":               "FeldsparCo S.L.",
        "country":            "Spain",
        "delivery_qty_t":     30.0,
        "lead_time_mean_hr":  42,
        "lead_time_std_hr":    8,
        "reliability":        0.88,
        "unit_cost_eur_t":    120,
        "reorder_point_t":    40,
        "max_stock_t":        150,
    },
    "silica": {
        "name":               "SilicaTech Lda",
        "country":            "Portugal",
        "delivery_qty_t":     25.0,
        "lead_time_mean_hr":  36,
        "lead_time_std_hr":    6,
        "reliability":        0.91,
        "unit_cost_eur_t":    95,
        "reorder_point_t":    32,
        "max_stock_t":        120,
    },
    "kaolin": {
        "name":               "KaolinMine S.A.",
        "country":            "Brazil",           # Overseas → long lead time
        "delivery_qty_t":     20.0,
        "lead_time_mean_hr":  72,
        "lead_time_std_hr":   16,
        "reliability":        0.82,               # Less reliable — distant supplier
        "unit_cost_eur_t":    110,
        "reorder_point_t":    22,
        "max_stock_t":        100,
    },
    "glaze": {
        "name":               "ChemGlaze GmbH",
        "country":            "Germany",
        "delivery_qty_t":     12.0,
        "lead_time_mean_hr":  72,
        "lead_time_std_hr":   14,
        "reliability":        0.85,
        "unit_cost_eur_t":    280,
        "reorder_point_t":    10,
        "max_stock_t":        55,
    },
}

# Initial raw-material inventory (tonnes) — approx 3 days of production supply
INITIAL_INVENTORY = {
    "clay":     90.0,
    "feldspar": 50.0,
    "silica":   40.0,
    "kaolin":   25.0,
    "glaze":    10.0,
}

# ── Finished-goods warehouse ──────────────────────────────────────────────────
FG_INITIAL_M2 = {
    "FLOOR-6060":  3_000,
    "WALL-3045":   1_500,
    "RUSTIC-4545":   750,
}
FG_MAX_M2 = {k: 120_000 for k in PRODUCTS}

# ── Customer demand ───────────────────────────────────────────────────────────
DEMAND = {
    "mean_orders_per_day": 5,
    "mean_order_m2":       500,
    "std_order_m2":        160,
    "min_order_m2":        100,
    "std_lead_time_days":    7,    # standard service promise
    "express_lead_time_days": 3,
    "express_fraction":    0.20,
    "express_premium":     1.15,  # 15 % price uplift for express
}

CUSTOMERS = [
    "BuildCo Portugal", "Iberian Tiles Distribution", "ConstructMax S.A.",
    "Mediterranean Build", "Porto Renovations", "Atlantic Contracts Ltd",
    "HomeStyle Iberia", "TilesPro Europe", "Lisbon Interiors",
    "Douro Construction Group",
]

# ── Quality parameters ────────────────────────────────────────────────────────
QUALITY = {
    "grade_a_rate":         0.88,   # Prime quality — full price
    "grade_b_rate":         0.09,   # Seconds — sold at a discount
    "reject_rate":          0.03,   # Scrapped
    "grade_b_price_factor": 0.65,
}

# ── Financial parameters ──────────────────────────────────────────────────────
FINANCIAL = {
    "energy_cost_per_batch_eur":      160,   # Gas + electricity per 250 m² batch
    "labor_cost_per_shift_eur":     3_000,   # One 8-hour shift (all direct labour)
    "shifts_per_day":                   3,
    "breakdown_repair_cost_eur":    2_500,   # Average cost per incident
    "stockout_penalty_eur_m2":          5,   # Lost margin + expediting cost
    "holding_cost_pct_per_year":     0.20,   # 20 % of FG value per annum
}

# ── Scenario definitions ──────────────────────────────────────────────────────
SCENARIOS = {
    "baseline": {
        "label":       "Baseline",
        "description": "Normal 90-day operations — balanced supply & demand",
        "demand_factor":               1.0,
        "machine_reliability_factor":  1.0,
        "supplier_reliability_factor": 1.0,
        "extra_kilns":                 0,
        "safety_stock_factor":         1.0,
        "kaolin_disruption":           None,   # (start_hr, end_hr) or None
    },
    "supply_disruption": {
        "label":       "Supply Disruption",
        "description": "KaolinMine S.A. — 35-day Brazilian port strike (Day 15–50)",
        "demand_factor":               1.0,
        "machine_reliability_factor":  1.0,
        "supplier_reliability_factor": 1.0,
        "extra_kilns":                 0,
        "safety_stock_factor":         1.0,
        "kaolin_disruption":           (15 * HOURS_PER_DAY, 50 * HOURS_PER_DAY),
    },
    "demand_surge": {
        "label":       "Demand Surge",
        "description": "Summer construction boom — 30 % demand uplift across all products",
        "demand_factor":               1.30,
        "machine_reliability_factor":  1.0,
        "supplier_reliability_factor": 1.0,
        "extra_kilns":                 0,
        "safety_stock_factor":         1.0,
        "kaolin_disruption":           None,
    },
    "optimised": {
        "label":       "Optimised",
        "description": "3rd kiln installed + 50 % safety stock uplift across all raw materials",
        "demand_factor":               1.0,
        "machine_reliability_factor":  1.0,
        "supplier_reliability_factor": 1.0,
        "extra_kilns":                 1,      # Total kilns: 3
        "safety_stock_factor":         1.5,    # Reorder points × 1.5
        "kaolin_disruption":           None,
    },
}
