"""Data models for TekunoAI Event Management (stdlib only)."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


RSVP_STATUSES = {"invited", "confirmed", "declined", "waitlisted"}
VENDOR_STATUSES = {"prospect", "booked", "confirmed", "paid", "cancelled"}
TASK_STATUSES = {"todo", "in_progress", "done"}
TASK_PRIORITIES = {"low", "medium", "high"}


@dataclass
class Event:
    name: str
    event_type: str = "generic"
    event_date: str = ""  # ISO date, e.g. "2026-11-15"
    start_time: str = "10:00"  # 24h "HH:MM"
    location: str = ""
    expected_guests: int = 0
    budget_total: float = 0.0
    description: str = ""

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("event name is required")
        if self.expected_guests < 0:
            raise ValueError("expected_guests cannot be negative")
        if self.budget_total < 0:
            raise ValueError("budget_total cannot be negative")

    def to_dict(self):
        return asdict(self)


@dataclass
class Attendee:
    name: str
    email: str = ""
    rsvp_status: str = "invited"
    dietary_notes: str = ""
    is_vip: bool = False

    def __post_init__(self):
        if self.rsvp_status not in RSVP_STATUSES:
            raise ValueError(f"invalid rsvp_status: {self.rsvp_status}")

    def to_dict(self):
        return asdict(self)


@dataclass
class Vendor:
    name: str
    category: str = "other"
    cost: float = 0.0
    contact_email: str = ""
    phone: str = ""
    status: str = "prospect"
    notes: str = ""

    def __post_init__(self):
        if self.status not in VENDOR_STATUSES:
            raise ValueError(f"invalid vendor status: {self.status}")
        if self.cost < 0:
            raise ValueError("vendor cost cannot be negative")

    def to_dict(self):
        return asdict(self)


@dataclass
class Task:
    title: str
    owner: str = ""
    priority: str = "medium"
    status: str = "todo"
    due_date: str = ""

    def __post_init__(self):
        if self.priority not in TASK_PRIORITIES:
            raise ValueError(f"invalid priority: {self.priority}")
        if self.status not in TASK_STATUSES:
            raise ValueError(f"invalid task status: {self.status}")

    def to_dict(self):
        return asdict(self)


@dataclass
class Expense:
    label: str
    amount: float
    category: str = "other"
    vendor_name: str = ""

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("expense amount cannot be negative")

    def to_dict(self):
        return asdict(self)
