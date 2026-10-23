#!/usr/bin/env python3
"""End-to-end demo for TekunoAI AI Powered Event Management.

Run:  python3 demo.py
No external dependencies - Python standard library only.
"""
import json

from tekunoai_events import EventManager
from tekunoai_events.planner import suggest_plan


def main():
    print("=" * 64)
    print("TekunoAI - AI Powered Event Management (MVP prototype)")
    print("=" * 64)

    # 1. Ask the AI planner for a suggested plan.
    print("\n[1] AI planner suggestion for a corporate event, 80 guests")
    plan = suggest_plan("corporate", guest_count=80, budget_total=12000)
    print(f"    Venue capacity recommended: {plan['venue_capacity_recommended']}")
    print(f"    Staffing: {plan['staffing']}")
    print(f"    Vendor checklist: {', '.join(plan['vendor_checklist'])}")
    print(f"    Budget allocation (%): {plan['budget_allocation_percent']}")
    print(f"    Starter tasks: {', '.join(plan['starter_tasks'])}")

    # 2. Create the event.
    print("\n[2] Creating event...")
    manager = EventManager()
    event = manager.create_event(
        name="TekunoAI Product Launch",
        event_type="corporate",
        event_date="2026-11-15",
        start_time="10:00",
        location="San Diego, CA",
        expected_guests=80,
        budget_total=12000,
        description="Launch event for a new TekunoAI product.",
    )
    print(f"    Created: {event.name} on {event.event_date} at {event.location}")

    # 3. Add attendees.
    print("\n[3] Adding attendees...")
    manager.add_attendee("Priya Example", email="priya@example.com",
                         rsvp_status="confirmed", is_vip=True)
    manager.add_attendee("Alex Example", email="alex@example.com",
                         rsvp_status="confirmed", dietary_notes="vegetarian")
    manager.add_attendee("Sam Example", email="sam@example.com",
                         rsvp_status="invited")
    manager.add_attendee("Jordan Example", email="jordan@example.com",
                         rsvp_status="declined")
    print(f"    Attendee summary: {manager.attendee_summary()}")

    # 4. Add vendors and record an extra expense.
    print("\n[4] Adding vendors...")
    manager.add_vendor("Harbor View Venue", category="venue", cost=3000,
                       status="booked", contact_email="events@venue.example.com")
    manager.add_vendor("City Catering Co", category="catering", cost=3600,
                       status="confirmed")
    manager.add_vendor("Bright AV Rentals", category="av", cost=1500,
                       status="booked")
    manager.add_vendor("Lens Photography", category="photography", cost=900,
                       status="prospect")
    manager.record_expense("Printed signage", amount=250, category="signage")
    print("    Vendors: Harbor View Venue, City Catering Co, "
          "Bright AV Rentals, Lens Photography")

    # 5. Add tasks from the planner's starter list.
    print("\n[5] Adding tasks...")
    for title in plan["starter_tasks"]:
        manager.add_task(title, owner="Raghav Shah", priority="high")
    manager.add_task("Send reminder to invited guests", owner="Events team",
                     priority="medium")

    # 6. Generate the schedule.
    print("\n[6] Auto-generated schedule:")
    for block in manager.generate_schedule():
        print(f"    {block['start']}-{block['end']}  {block['block']}")

    # 7. Budget vs spend.
    print("\n[7] Budget summary:")
    budget = manager.budget_summary()
    for key, value in budget.items():
        print(f"    {key}: {value}")

    # 8. Export the full plan.
    print("\n[8] Full event plan (JSON):")
    print(json.dumps(manager.export_plan(), indent=2))

    print("\nDemo completed successfully.")


if __name__ == "__main__":
    main()
