"""Data-model classes shared across the simulation."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import uuid


def _short_id() -> str:
    return uuid.uuid4().hex[:8].upper()


@dataclass
class ProductionBatch:
    """Tracks a single 250 m² tile batch from raw material through to packaging."""

    batch_id:     str   = field(default_factory=_short_id)
    product:      str   = ""
    quantity_m2:  float = 0.0
    created_at:   float = 0.0          # simulation time (hours)

    # Stage-completion timestamps (set as batch moves through pipeline)
    forming_done:  Optional[float] = None
    glazing_done:  Optional[float] = None
    firing_done:   Optional[float] = None
    finished_at:   Optional[float] = None

    # Quality outcomes (set in the finishing stage)
    grade_a_m2:  float = 0.0
    grade_b_m2:  float = 0.0
    reject_m2:   float = 0.0

    @property
    def cycle_time_hr(self) -> Optional[float]:
        """End-to-end production time from batch creation to packaging."""
        if self.finished_at is not None:
            return self.finished_at - self.created_at
        return None

    @property
    def saleable_m2(self) -> float:
        return self.grade_a_m2 + self.grade_b_m2


@dataclass
class CustomerOrder:
    """A purchase order from a customer."""

    order_id:     str   = field(default_factory=lambda: f"ORD-{_short_id()}")
    customer:     str   = ""
    product:      str   = ""
    quantity_m2:  float = 0.0
    is_express:   bool  = False
    created_at:   float = 0.0
    due_at:       float = 0.0
    unit_price:   float = 0.0          # €/m²

    # Filled in during / after fulfilment
    fulfilled_qty: float          = 0.0
    fulfilled_at:  Optional[float] = None

    @property
    def is_complete(self) -> bool:
        return self.fulfilled_qty >= self.quantity_m2 * 0.999

    @property
    def is_overdue(self) -> bool:
        return self.fulfilled_at is not None and self.fulfilled_at > self.due_at

    @property
    def revenue_eur(self) -> float:
        return self.fulfilled_qty * self.unit_price

    @property
    def fill_fraction(self) -> float:
        return min(1.0, self.fulfilled_qty / self.quantity_m2) if self.quantity_m2 > 0 else 0.0


@dataclass
class SupplierDelivery:
    """A raw-material delivery that arrived at the factory gate."""

    delivery_id:      str   = field(default_factory=lambda: f"DEL-{_short_id()}")
    supplier_name:    str   = ""
    material:         str   = ""
    quantity_tonnes:  float = 0.0
    unit_cost_eur_t:  float = 0.0
    ordered_at:       float = 0.0
    delivered_at:     float = 0.0
    on_time:          bool  = True

    @property
    def total_cost_eur(self) -> float:
        return self.quantity_tonnes * self.unit_cost_eur_t

    @property
    def lead_time_hr(self) -> float:
        return self.delivered_at - self.ordered_at


@dataclass
class BreakdownEvent:
    """A machine failure and subsequent repair."""

    machine_id:      str   = ""
    machine_name:    str   = ""
    occurred_at:     float = 0.0    # simulation time when failure occurred
    repair_duration: float = 0.0    # hours until back online
    repair_cost_eur: float = 2_500.0

    @property
    def resolved_at(self) -> float:
        return self.occurred_at + self.repair_duration
