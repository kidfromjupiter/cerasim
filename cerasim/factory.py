"""
CeramicFactory — SimPy discrete-event simulation of AzulCer's supply chain.

Production pipeline (left → right):

  Raw materials (clay, feldspar, silica, kaolin)
        │
   [Body Prep Lines]  ──────────────────── powder_buf (Container)
        │
   [Press & Dryer]    ──────────────────── unglazed_store (Store of ProductionBatch)
        │
   [Glaze Line]  ←── glaze raw-mat         ready_to_fire (Store)
   (RUSTIC skips)
        │
   [Roller Kiln] ★ bottleneck ─────────── fired_store (Store)
        │
   [Sort & Pack]  ──────────────────────── finished_goods[product] (Container)
        │
   Customer orders  ←── order_queue (Store)
"""

from __future__ import annotations

import math
import random
from typing import Dict, Tuple

import simpy

from .config import (
    BATCH_SIZE_M2, BODY_COMPOSITION, AVG_BODY_KG_M2,
    CUSTOMERS, DEMAND, FINANCIAL, FG_INITIAL_M2, FG_MAX_M2,
    HOURS_PER_DAY, INITIAL_INVENTORY, MACHINES, PRODUCTS,
    QUALITY, SCENARIOS, SUPPLIERS,
)
from .metrics import MetricsCollector
from .models import BreakdownEvent, CustomerOrder, ProductionBatch, SupplierDelivery


class CeramicFactory:
    """
    Full supply-chain model of AzulCer Tile Industries.

    Usage::

        env     = simpy.Environment()
        factory = CeramicFactory(env, scenario="baseline", seed=42)
        factory.register_processes()
        env.run(until=SIM_DURATION)
        kpis = factory.metrics.compute_kpis(SIM_DAYS)
    """

    def __init__(
        self,
        env: simpy.Environment,
        scenario: str = "baseline",
        seed: int = 42,
    ) -> None:
        self.env      = env
        self.scenario = scenario
        self.scen     = SCENARIOS[scenario]

        random.seed(seed)

        # ── Raw-material inventory (tonnes) ───────────────────────────────────
        self.raw_mat: Dict[str, simpy.Container] = {}
        for mat, cfg in SUPPLIERS.items():
            init = INITIAL_INVENTORY[mat] * self.scen["safety_stock_factor"]
            init = min(init, cfg["max_stock_t"])
            self.raw_mat[mat] = simpy.Container(
                env, capacity=cfg["max_stock_t"], init=init
            )

        # ── Inter-stage buffers ───────────────────────────────────────────────
        self.powder_buf    = simpy.Container(env, capacity=8_000, init=250)
        # Stores carry ProductionBatch objects so product type travels with the tile
        self.unglazed_store  = simpy.Store(env)
        self.ready_to_fire   = simpy.Store(env)
        self.fired_store     = simpy.Store(env)

        # ── Finished-goods warehouse (m²) ─────────────────────────────────────
        self.fg: Dict[str, simpy.Container] = {
            prod: simpy.Container(
                env,
                capacity=FG_MAX_M2[prod],
                init=FG_INITIAL_M2[prod],
            )
            for prod in PRODUCTS
        }

        # ── Machine resources ─────────────────────────────────────────────────
        self.machines: Dict[str, simpy.Resource] = {}
        for key, cfg in MACHINES.items():
            count = cfg["count"]
            if key == "kiln":
                count += self.scen["extra_kilns"]
            self.machines[key] = simpy.Resource(env, capacity=count)

        # ── Order queue (shared by multiple fulfilment workers) ───────────────
        self.order_queue = simpy.Store(env)

        # ── Metrics ───────────────────────────────────────────────────────────
        self.metrics = MetricsCollector(env)

        # ── Internal state ────────────────────────────────────────────────────
        self._pending_replen: Dict[str, int] = {m: 0 for m in SUPPLIERS}
        self._machine_busy_hr: Dict[str, float] = {k: 0.0 for k in MACHINES}
        self._daily_prod: Dict[str, float] = {p: 0.0 for p in PRODUCTS}

    # =========================================================================
    # Helpers
    # =========================================================================

    def _proc_time(self, machine_key: str) -> Tuple[float, bool]:
        """
        Sample processing time for one batch on *machine_key*.

        Returns ``(duration_hours, had_breakdown)``.  If a breakdown occurs,
        ``duration_hours`` already includes the repair time so the caller
        just yields a single timeout.
        """
        cfg     = MACHINES[machine_key]
        rel     = self.scen["machine_reliability_factor"]
        base_t  = max(0.05, random.normalvariate(cfg["proc_mean_hr"], cfg["proc_std_hr"]))
        eff_mtbf = cfg["mtbf_hr"] * rel

        # Probability of at least one failure in *base_t* hours of operation
        p_fail  = 1.0 - math.exp(-base_t / eff_mtbf)
        if random.random() < p_fail:
            repair_t = random.expovariate(1.0 / cfg["mttr_hr"])
            event = BreakdownEvent(
                machine_id      = machine_key,
                machine_name    = cfg["name"],
                occurred_at     = self.env.now + base_t,
                repair_duration = repair_t,
                repair_cost_eur = FINANCIAL["breakdown_repair_cost_eur"],
            )
            self.metrics.breakdowns.append(event)
            return base_t + repair_t, True
        return base_t, False

    def _choose_product(self) -> str:
        """
        Weighted product selection for a new press batch.

        Biases toward products whose finished-goods level is below target
        so the factory naturally replenishes low-stock SKUs.
        """
        scores = {}
        for prod, cfg in PRODUCTS.items():
            level  = self.fg[prod].level
            target = FG_INITIAL_M2[prod] * 2.0
            deficit_bonus = max(0.0, (target - level) / target) * 0.25
            scores[prod]  = cfg["demand_share"] + deficit_bonus

        total = sum(scores.values())
        r, cum = random.random() * total, 0.0
        for prod, s in scores.items():
            cum += s
            if r <= cum:
                return prod
        return list(PRODUCTS.keys())[0]

    # =========================================================================
    # Supply-chain processes
    # =========================================================================

    def supply_monitor(self):
        """
        Inventory review every 4 hours.
        Triggers replenishment orders when stock falls below the reorder point.
        A maximum of 2 in-flight orders per material prevents over-ordering.
        """
        while True:
            yield self.env.timeout(4)

            for mat, cfg in SUPPLIERS.items():
                # ── Scenario: kaolin supply disruption ────────────────────────
                disruption = self.scen["kaolin_disruption"]
                if disruption and mat == "kaolin":
                    d_start, d_end = disruption
                    if d_start <= self.env.now <= d_end:
                        self.metrics.disruption_hours += 4
                        continue   # No kaolin orders during the strike

                reorder_pt = cfg["reorder_point_t"] * self.scen["safety_stock_factor"]
                if (
                    self.raw_mat[mat].level < reorder_pt
                    and self._pending_replen[mat] < 2
                ):
                    self._pending_replen[mat] += 1
                    self.env.process(self._supplier_delivery(mat))

    def _supplier_delivery(self, material: str):
        """
        Simulate one supplier delivery:
          1. Compute lead time (Normal, truncated at 4 h minimum).
          2. Apply reliability — unreliable suppliers add random delays.
          3. Arrive at factory gate and top up the raw-material container.
        """
        cfg        = SUPPLIERS[material]
        ordered_at = self.env.now
        rel_factor = self.scen["supplier_reliability_factor"]

        lead_t  = max(4.0, random.normalvariate(
            cfg["lead_time_mean_hr"], cfg["lead_time_std_hr"]
        ))
        eff_rel = cfg["reliability"] * rel_factor
        on_time = random.random() < eff_rel
        if not on_time:
            lead_t *= random.uniform(1.25, 2.50)   # Late delivery penalty

        yield self.env.timeout(lead_t)

        space   = self.raw_mat[material].capacity - self.raw_mat[material].level
        qty     = min(cfg["delivery_qty_t"], space)
        if qty > 0:
            yield self.raw_mat[material].put(qty)

        self.metrics.deliveries.append(SupplierDelivery(
            supplier_name   = cfg["name"],
            material        = material,
            quantity_tonnes = qty,
            unit_cost_eur_t = cfg["unit_cost_eur_t"],
            ordered_at      = ordered_at,
            delivered_at    = self.env.now,
            on_time         = on_time,
        ))
        self._pending_replen[material] -= 1

    # =========================================================================
    # Production stages
    # =========================================================================

    def body_preparation(self):
        """
        Stage 1 — Body preparation (mixing + ball-milling + spray drying).

        Consumes four raw materials and produces press powder (m² equivalent).
        One SimPy process instance per body-prep line.
        """
        BATCH = BATCH_SIZE_M2

        # Tonnes of each mineral consumed per batch
        mat_per_batch = {
            mat: BATCH * AVG_BODY_KG_M2 * frac / 1000   # kg → t
            for mat, frac in BODY_COMPOSITION.items()
        }

        while True:
            # ── Wait until all raw materials are available ──────────────────
            while not all(
                self.raw_mat[m].level >= qty
                for m, qty in mat_per_batch.items()
            ):
                self.metrics.record_stall("body_prep")
                yield self.env.timeout(1.0)   # poll every hour

            # ── Consume raw materials ────────────────────────────────────────
            # (Safe: we checked all levels; no yield between checks and gets,
            #  so no other body-prep process can interleave and steal stock.)
            for m, qty in mat_per_batch.items():
                yield self.raw_mat[m].get(qty)

            # ── Process on a body-prep line ──────────────────────────────────
            with self.machines["body_prep"].request() as req:
                yield req
                t, _ = self._proc_time("body_prep")
                yield self.env.timeout(t)
                self._machine_busy_hr["body_prep"] += t

            yield self.powder_buf.put(BATCH)
            self.metrics.record_stage("body_prep", BATCH)

    def forming_and_drying(self):
        """
        Stage 2 — Pressing & drying.

        Gets powder from the buffer, assigns a product type, produces a
        ProductionBatch object that carries the product identity downstream.
        One process per hydraulic press.
        """
        BATCH = BATCH_SIZE_M2
        while True:
            yield self.powder_buf.get(BATCH)
            product = self._choose_product()

            with self.machines["forming"].request() as req:
                yield req
                t, _ = self._proc_time("forming")
                yield self.env.timeout(t)
                self._machine_busy_hr["forming"] += t

            batch = ProductionBatch(
                product      = product,
                quantity_m2  = BATCH,
                created_at   = self.env.now,
                forming_done = self.env.now,
            )
            yield self.unglazed_store.put(batch)
            self.metrics.record_stage("forming", BATCH)

    def surface_treatment(self):
        """
        Stage 3 — Glaze application.

        Glazed products (FLOOR-6060, WALL-3045) go through the glaze line.
        RUSTIC-4545 bypasses it entirely — the loop is still needed so the
        batch is forwarded to ready_to_fire.
        One process per glaze line.
        """
        while True:
            batch = yield self.unglazed_store.get()
            cfg   = PRODUCTS[batch.product]

            if cfg["needs_glaze"]:
                glaze_qty = batch.quantity_m2 * cfg["glaze_kg_per_m2"] / 1000  # t

                # ── Wait for glaze material ──────────────────────────────────
                while self.raw_mat["glaze"].level < glaze_qty:
                    self.metrics.record_stall("glazing")
                    yield self.env.timeout(1.0)

                yield self.raw_mat["glaze"].get(glaze_qty)

                with self.machines["glazing"].request() as req:
                    yield req
                    t, _ = self._proc_time("glazing")
                    yield self.env.timeout(t)
                    self._machine_busy_hr["glazing"] += t

            batch.glazing_done = self.env.now
            yield self.ready_to_fire.put(batch)
            self.metrics.record_stage("glazing", batch.quantity_m2)

    def kiln_firing(self):
        """
        Stage 4 — Roller hearth kiln firing.  ★ The production bottleneck.

        One process per kiln.  Breakdowns here have the biggest impact on
        throughput because this stage has the lowest theoretical capacity.
        """
        while True:
            batch = yield self.ready_to_fire.get()

            with self.machines["kiln"].request() as req:
                yield req
                t, _ = self._proc_time("kiln")
                yield self.env.timeout(t)
                self._machine_busy_hr["kiln"] += t

            batch.firing_done = self.env.now
            yield self.fired_store.put(batch)
            self.metrics.record_stage("kiln", batch.quantity_m2)

    def finishing(self):
        """
        Stage 5 — Optical sorting, grading, and palletised packaging.

        Applies the quality split (Grade A / Grade B / Reject) and moves
        saleable tiles into the finished-goods warehouse.
        One process per sorting & packaging line.
        """
        while True:
            batch = yield self.fired_store.get()

            with self.machines["finishing"].request() as req:
                yield req
                t, _ = self._proc_time("finishing")
                yield self.env.timeout(t)
                self._machine_busy_hr["finishing"] += t

            q              = QUALITY
            batch.grade_a_m2 = batch.quantity_m2 * q["grade_a_rate"]
            batch.grade_b_m2 = batch.quantity_m2 * q["grade_b_rate"]
            batch.reject_m2  = batch.quantity_m2 * q["reject_rate"]
            batch.finished_at = self.env.now

            # Add saleable tiles to finished-goods warehouse (capped at capacity)
            fg_store = self.fg[batch.product]
            space    = fg_store.capacity - fg_store.level
            put_qty  = min(batch.saleable_m2, space)
            if put_qty > 0:
                yield fg_store.put(put_qty)

            self.metrics.completed_batches.append(batch)
            self.metrics.record_stage("finishing", batch.quantity_m2)
            self._daily_prod[batch.product] = (
                self._daily_prod.get(batch.product, 0.0) + put_qty
            )

    # =========================================================================
    # Demand & order fulfilment
    # =========================================================================

    def demand_generator(self):
        """
        Generates customer orders via a Poisson arrival process.

        Inter-arrival times are Exponential(λ) where λ = orders/hour.
        Order sizes are drawn from a truncated Normal distribution.
        """
        counter = 0
        while True:
            df        = self.scen["demand_factor"]
            rate_hr   = DEMAND["mean_orders_per_day"] * df / HOURS_PER_DAY
            yield self.env.timeout(random.expovariate(rate_hr))

            counter += 1
            is_express = random.random() < DEMAND["express_fraction"]
            product    = random.choices(
                list(PRODUCTS.keys()),
                weights=[PRODUCTS[p]["demand_share"] for p in PRODUCTS],
            )[0]
            qty = max(
                DEMAND["min_order_m2"],
                random.normalvariate(DEMAND["mean_order_m2"], DEMAND["std_order_m2"]),
            )
            lead_days  = (DEMAND["express_lead_time_days"] if is_express
                          else DEMAND["std_lead_time_days"])
            base_price = PRODUCTS[product]["price_eur_m2"]
            unit_price = base_price * (DEMAND["express_premium"] if is_express else 1.0)

            order = CustomerOrder(
                order_id    = f"ORD-{counter:04d}",
                customer    = random.choice(CUSTOMERS),
                product     = product,
                quantity_m2 = round(qty),
                is_express  = is_express,
                created_at  = self.env.now,
                due_at      = self.env.now + lead_days * HOURS_PER_DAY,
                unit_price  = unit_price,
            )
            self.metrics.orders.append(order)
            yield self.order_queue.put(order)

    def order_fulfilment(self):
        """
        Picks orders from the shared queue and ships from finished-goods stock.

        Full fulfilment: ship everything immediately.
        Partial fulfilment: ship what is available, record a partial.
        Zero stock: record a stockout.
        """
        while True:
            order = yield self.order_queue.get()
            fg    = self.fg[order.product]
            avail = fg.level

            if avail >= order.quantity_m2:
                yield fg.get(order.quantity_m2)
                order.fulfilled_qty = order.quantity_m2
            elif avail > 0:
                yield fg.get(avail)
                order.fulfilled_qty = avail
                self.metrics.partial_fulfils += 1
            else:
                # Complete stockout — lost sale
                self.metrics.stockout_events.append({
                    "time":        self.env.now,
                    "product":     order.product,
                    "quantity_m2": order.quantity_m2,
                })

            order.fulfilled_at = self.env.now

    # =========================================================================
    # Monitoring
    # =========================================================================

    def daily_recorder(self):
        """
        Snapshots key system state once per simulated day for trend charts.
        """
        while True:
            yield self.env.timeout(HOURS_PER_DAY)
            day = int(self.env.now / HOURS_PER_DAY)

            self.metrics.daily_snapshots.append({
                "day":           day,
                "raw_mat":       {m: self.raw_mat[m].level for m in SUPPLIERS},
                "powder":        self.powder_buf.level,
                "fg":            {p: self.fg[p].level for p in PRODUCTS},
                "produced_m2":   dict(self._daily_prod),
                "wip":           (len(self.unglazed_store.items)
                                  + len(self.ready_to_fire.items)
                                  + len(self.fired_store.items)),
                "utilization":   self._current_utilization(),
            })
            self._daily_prod = {p: 0.0 for p in PRODUCTS}

    def _current_utilization(self) -> Dict[str, float]:
        """Cumulative utilisation fraction for each machine group."""
        util = {}
        for key, res in self.machines.items():
            denom = res.capacity * self.env.now
            util[key] = (
                min(1.0, self._machine_busy_hr[key] / denom) if denom > 0 else 0.0
            )
        return util

    # =========================================================================
    # Bootstrap
    # =========================================================================

    def register_processes(self) -> None:
        """
        Register every SimPy process.  Call this before ``env.run()``.
        """
        env = self.env

        # Supply chain
        env.process(self.supply_monitor())
        # Kick-start initial deliveries for all materials
        for mat in SUPPLIERS:
            env.process(self._supplier_delivery(mat))

        # Production pipeline — N workers per stage ≈ N machines
        for _ in range(MACHINES["body_prep"]["count"]):
            env.process(self.body_preparation())
        for _ in range(MACHINES["forming"]["count"]):
            env.process(self.forming_and_drying())
        for _ in range(MACHINES["glazing"]["count"]):
            env.process(self.surface_treatment())

        kiln_count = MACHINES["kiln"]["count"] + self.scen["extra_kilns"]
        for _ in range(kiln_count):
            env.process(self.kiln_firing())

        for _ in range(MACHINES["finishing"]["count"]):
            env.process(self.finishing())

        # Demand & fulfilment
        env.process(self.demand_generator())
        for _ in range(4):   # 4 fulfilment workers → no bottleneck here
            env.process(self.order_fulfilment())

        # Daily KPI snapshot
        env.process(self.daily_recorder())
