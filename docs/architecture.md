# Architecture - TekunoAI AI Powered Event Management

Status: MVP prototype in active development.

## Overview

The prototype is deliberately small and dependency-free. The core is a
Python package, `tekunoai_events`, that models an event and everything
attached to it. A demo script exercises the whole flow. There is no
database, web server, or external API in this version; those are roadmap
items layered on top of the same core.

## Components

### `tekunoai_events/models.py`

Plain data models using `dataclasses`:

- `Event` - name, event_type, date, start_time, location, expected_guests,
  budget_total, description.
- `Attendee` - name, email, rsvp_status (`invited`, `confirmed`,
  `declined`, `waitlisted`), dietary_notes, is_vip.
- `Vendor` - name, category, cost, contact_email, phone, status
  (`prospect`, `booked`, `confirmed`, `paid`, `cancelled`), notes.
- `Task` - title, owner, priority (`low`, `medium`, `high`), status
  (`todo`, `in_progress`, `done`), due_date.
- `Expense` - label, category, amount, vendor_name (optional). Used for
  spend that is recorded in addition to committed vendor costs.

Each model validates its enum-like fields and exposes `to_dict()`.

### `tekunoai_events/manager.py`

`EventManager` owns one current event plus its attendees, vendors, tasks,
and expenses, and provides:

- `create_event(...)` - create / replace the current event.
- `add_attendee(...)`, `add_vendor(...)`, `add_task(...)`,
  `record_expense(...)`.
- `attendee_summary()` - total, confirmed, invited, declined, VIP counts.
- `budget_summary()` - budget_total, vendor_committed, expenses_total,
  total_spend, remaining, utilisation_percent, over_budget flag, and a
  per-category breakdown.
- `generate_schedule()` - a timed timeline for the event day. Schedule
  templates differ by event type (corporate, wedding, birthday,
  conference, generic) and are anchored to the event start time.
- `export_plan()` - the whole event as a JSON-serialisable dictionary:
  event, attendees, vendors, tasks, schedule, and budget summary.

All state is in memory. Persistence is a roadmap item.

### `tekunoai_events/planner.py`

` suggest_plan(event_type, guest_count, budget_total=None) ` is the AI
planner prototype. It is deterministic and rule-based (no external calls):

Inputs: event type, expected guest count, optional budget.

Outputs (dictionary):

- `venue_capacity_recommended` - guest count plus headroom.
- `staffing` - suggested host / coordinator / support counts scaled to
  guest count.
- `vendor_checklist` - categories to book for that event type.
- `timeline` - suggested programme blocks with durations.
- `starter_tasks` - first tasks an organiser should create.
- `budget_allocation` - percentage split (venue, catering, AV, decor,
  entertainment, contingency, other) and, if a budget was given, amounts.
- `catering_note` - a per-guest planning hint.
- `risks_and_tips` - practical reminders for that event type / size.

Design note: the function signature is the contract a future LLM-backed
planner will keep. The core manager does not depend on how a plan was
produced, so the rule-based planner can be swapped for a model-backed one
without changing `EventManager`.

## Data Flow

1. Organiser calls `suggest_plan()` to get a draft.
2. Organiser creates the event with `EventManager.create_event()`,
   optionally using values from the draft.
3. Attendees, vendors, tasks, and expenses are added as planning proceeds.
4. `generate_schedule()` produces the day-of timeline.
5. `budget_summary()` is checked at any point to keep spend in bounds.
6. `export_plan()` produces a shareable snapshot (used by `demo.py`).

## Testing

`tests/test_event_management.py` uses `unittest` from the standard library
and covers event creation, attendee / vendor / task handling, schedule
generation, budget math including over-budget detection, planner output
for different sizes, and full plan export.

Run:

```bash
python3 -m unittest discover -s tests -v
```

## Future Architecture (Roadmap)

- Persistence layer (SQLite first, then Postgres) behind `EventManager`.
- FastAPI service exposing the manager and planner as REST endpoints.
- Web frontend consuming that API.
- LLM planner implementation behind the existing `suggest_plan` contract.
- Agent layer: vendor, attendee, and logistics agents that can follow up,
  negotiate, and flag conflicts, coordinated by the manager.
