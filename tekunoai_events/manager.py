"""EventManager: core in-memory manager for TekunoAI Event Management."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from .models import Attendee, Event, Expense, Task, Vendor
from .planner import suggest_plan


def _parse_hhmm(value: str) -> datetime:
    return datetime.strptime(value, "%H:%M")


class EventManager:
    """Owns one current event and its attendees, vendors, tasks, expenses."""

    def __init__(self):
        self.event: Optional[Event] = None
        self.attendees: list[Attendee] = []
        self.vendors: list[Vendor] = []
        self.tasks: list[Task] = []
        self.expenses: list[Expense] = []

    # -- event -----------------------------------------------------------
    def create_event(self, name: str, event_type: str = "generic",
                     event_date: str = "", start_time: str = "10:00",
                     location: str = "", expected_guests: int = 0,
                     budget_total: float = 0.0,
                     description: str = "") -> Event:
        self.event = Event(
            name=name, event_type=event_type, event_date=event_date,
            start_time=start_time, location=location,
            expected_guests=expected_guests, budget_total=budget_total,
            description=description,
        )
        return self.event

    def _require_event(self) -> Event:
        if self.event is None:
            raise RuntimeError("no event created yet; call create_event() first")
        return self.event

    # -- attendees / vendors / tasks / expenses --------------------------
    def add_attendee(self, name: str, email: str = "",
                     rsvp_status: str = "invited", dietary_notes: str = "",
                     is_vip: bool = False) -> Attendee:
        self._require_event()
        attendee = Attendee(name=name, email=email, rsvp_status=rsvp_status,
                            dietary_notes=dietary_notes, is_vip=is_vip)
        self.attendees.append(attendee)
        return attendee

    def add_vendor(self, name: str, category: str = "other", cost: float = 0.0,
                   contact_email: str = "", phone: str = "",
                   status: str = "prospect", notes: str = "") -> Vendor:
        self._require_event()
        vendor = Vendor(name=name, category=category, cost=cost,
                        contact_email=contact_email, phone=phone,
                        status=status, notes=notes)
        self.vendors.append(vendor)
        return vendor

    def add_task(self, title: str, owner: str = "", priority: str = "medium",
                 status: str = "todo", due_date: str = "") -> Task:
        self._require_event()
        task = Task(title=title, owner=owner, priority=priority,
                    status=status, due_date=due_date)
        self.tasks.append(task)
        return task

    def record_expense(self, label: str, amount: float, category: str = "other",
                       vendor_name: str = "") -> Expense:
        self._require_event()
        expense = Expense(label=label, amount=amount, category=category,
                          vendor_name=vendor_name)
        self.expenses.append(expense)
        return expense

    # -- summaries ---------------------------------------------------------
    def attendee_summary(self) -> dict:
        counts = {"total": len(self.attendees), "confirmed": 0, "invited": 0,
                  "declined": 0, "waitlisted": 0, "vip": 0}
        for a in self.attendees:
            counts[a.rsvp_status] = counts.get(a.rsvp_status, 0) + 1
            if a.is_vip:
                counts["vip"] += 1
        return counts

    def budget_summary(self) -> dict:
        event = self._require_event()
        # Cancelled vendors are not committed spend.
        vendor_committed = round(
            sum(v.cost for v in self.vendors if v.status != "cancelled"), 2)
        expenses_total = round(sum(e.amount for e in self.expenses), 2)
        total_spend = round(vendor_committed + expenses_total, 2)
        remaining = round(event.budget_total - total_spend, 2)
        utilisation = (
            round(total_spend / event.budget_total * 100, 2)
            if event.budget_total > 0 else 0.0
        )
        by_category: dict[str, float] = {}
        for v in self.vendors:
            if v.status == "cancelled":
                continue
            by_category[v.category] = round(
                by_category.get(v.category, 0.0) + v.cost, 2)
        for e in self.expenses:
            by_category[e.category] = round(
                by_category.get(e.category, 0.0) + e.amount, 2)
        return {
            "budget_total": event.budget_total,
            "vendor_committed": vendor_committed,
            "expenses_total": expenses_total,
            "total_spend": total_spend,
            "remaining": remaining,
            "utilisation_percent": utilisation,
            "over_budget": total_spend > event.budget_total > 0,
            "by_category": by_category,
        }

    # -- schedule ----------------------------------------------------------
    def generate_schedule(self) -> list[dict]:
        """Auto-generate a timed timeline for the event day.

        Blocks and durations come from the planner template for the event
        type, anchored to the event start_time.
        """
        event = self._require_event()
        guest_count = max(1, event.expected_guests or len(self.attendees) or 1)
        plan = suggest_plan(event.event_type, guest_count)
        try:
            cursor = _parse_hhmm(event.start_time)
        except ValueError:
            cursor = _parse_hhmm("10:00")
        schedule = []
        for block in plan["timeline"]:
            start = cursor
            end = start + timedelta(minutes=block["duration_minutes"])
            schedule.append({
                "block": block["block"],
                "start": start.strftime("%H:%M"),
                "end": end.strftime("%H:%M"),
                "duration_minutes": block["duration_minutes"],
            })
            cursor = end
        return schedule

    # -- export ------------------------------------------------------------
    def export_plan(self) -> dict:
        event = self._require_event()
        return {
            "event": event.to_dict(),
            "attendees": [a.to_dict() for a in self.attendees],
            "attendee_summary": self.attendee_summary(),
            "vendors": [v.to_dict() for v in self.vendors],
            "tasks": [t.to_dict() for t in self.tasks],
            "expenses": [e.to_dict() for e in self.expenses],
            "schedule": self.generate_schedule(),
            "budget": self.budget_summary(),
        }
