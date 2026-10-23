"""Tests for TekunoAI Event Management prototype (stdlib unittest only)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tekunoai_events import EventManager
from tekunoai_events.planner import suggest_plan


def make_manager():
    manager = EventManager()
    manager.create_event(
        name="Test Launch",
        event_type="corporate",
        event_date="2026-11-15",
        start_time="10:00",
        location="San Diego, CA",
        expected_guests=80,
        budget_total=10000,
    )
    return manager


class TestEventCreation(unittest.TestCase):
    def test_create_event_stores_fields(self):
        manager = make_manager()
        self.assertEqual(manager.event.name, "Test Launch")
        self.assertEqual(manager.event.expected_guests, 80)
        self.assertEqual(manager.event.budget_total, 10000)

    def test_create_event_requires_name(self):
        manager = EventManager()
        with self.assertRaises(ValueError):
            manager.create_event(name="")

    def test_operations_require_event(self):
        manager = EventManager()
        with self.assertRaises(RuntimeError):
            manager.add_attendee("No Event Yet")


class TestAttendeesVendorsTasks(unittest.TestCase):
    def test_attendee_summary_counts(self):
        manager = make_manager()
        manager.add_attendee("A", rsvp_status="confirmed", is_vip=True)
        manager.add_attendee("B", rsvp_status="confirmed")
        manager.add_attendee("C", rsvp_status="invited")
        manager.add_attendee("D", rsvp_status="declined")
        summary = manager.attendee_summary()
        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["confirmed"], 2)
        self.assertEqual(summary["invited"], 1)
        self.assertEqual(summary["declined"], 1)
        self.assertEqual(summary["vip"], 1)

    def test_invalid_rsvp_rejected(self):
        manager = make_manager()
        with self.assertRaises(ValueError):
            manager.add_attendee("Bad", rsvp_status="maybe")

    def test_vendor_and_task_added(self):
        manager = make_manager()
        vendor = manager.add_vendor("Catering Co", category="catering",
                                    cost=2000, status="booked")
        task = manager.add_task("Book venue", owner="Raghav", priority="high")
        self.assertEqual(vendor.cost, 2000)
        self.assertEqual(task.status, "todo")
        self.assertEqual(len(manager.vendors), 1)
        self.assertEqual(len(manager.tasks), 1)


class TestBudget(unittest.TestCase):
    def test_budget_summary_math(self):
        manager = make_manager()
        manager.add_vendor("Venue", category="venue", cost=3000, status="booked")
        manager.add_vendor("Catering", category="catering", cost=2000,
                           status="confirmed")
        manager.record_expense("Signage", amount=500, category="signage")
        summary = manager.budget_summary()
        self.assertEqual(summary["vendor_committed"], 5000)
        self.assertEqual(summary["expenses_total"], 500)
        self.assertEqual(summary["total_spend"], 5500)
        self.assertEqual(summary["remaining"], 4500)
        self.assertEqual(summary["utilisation_percent"], 55.0)
        self.assertFalse(summary["over_budget"])
        self.assertEqual(summary["by_category"]["venue"], 3000)

    def test_over_budget_detected_and_cancelled_vendor_excluded(self):
        manager = make_manager()
        manager.add_vendor("Huge Venue", category="venue", cost=11000,
                           status="booked")
        manager.add_vendor("Cancelled DJ", category="entertainment",
                           cost=5000, status="cancelled")
        summary = manager.budget_summary()
        self.assertEqual(summary["vendor_committed"], 11000)
        self.assertTrue(summary["over_budget"])
        self.assertEqual(summary["remaining"], -1000)


class TestSchedule(unittest.TestCase):
    def test_schedule_starts_at_event_time_and_is_contiguous(self):
        manager = make_manager()
        schedule = manager.generate_schedule()
        self.assertTrue(len(schedule) >= 4)
        self.assertEqual(schedule[0]["start"], "10:00")
        for prev, nxt in zip(schedule, schedule[1:]):
            self.assertEqual(prev["end"], nxt["start"])
        for block in schedule:
            self.assertGreater(block["duration_minutes"], 0)


class TestPlanner(unittest.TestCase):
    def test_planner_capacity_has_headroom(self):
        plan = suggest_plan("wedding", guest_count=100)
        self.assertEqual(plan["venue_capacity_recommended"], 110)
        self.assertIn("catering", plan["vendor_checklist"])
        self.assertTrue(plan["starter_tasks"])
        self.assertTrue(plan["timeline"])
        total_pct = sum(plan["budget_allocation_percent"].values())
        self.assertEqual(total_pct, 100)

    def test_planner_budget_amounts_sum_to_budget(self):
        plan = suggest_plan("corporate", guest_count=50, budget_total=10000)
        amounts = plan["budget_allocation_amounts"]
        self.assertIsNotNone(amounts)
        self.assertAlmostEqual(sum(amounts.values()), 10000, places=2)

    def test_planner_scales_staffing_with_guests(self):
        small = suggest_plan("birthday", guest_count=20)
        large = suggest_plan("birthday", guest_count=400)
        self.assertGreater(large["staffing"]["support_staff"],
                           small["staffing"]["support_staff"])

    def test_planner_unknown_type_falls_back(self):
        plan = suggest_plan("underwater-basket-weaving", guest_count=10)
        self.assertTrue(plan["vendor_checklist"])

    def test_planner_rejects_zero_guests(self):
        with self.assertRaises(ValueError):
            suggest_plan("corporate", guest_count=0)


class TestExport(unittest.TestCase):
    def test_export_plan_is_complete_and_serialisable(self):
        import json
        manager = make_manager()
        manager.add_attendee("A", rsvp_status="confirmed")
        manager.add_vendor("Venue", category="venue", cost=1000, status="booked")
        manager.add_task("Setup")
        plan = manager.export_plan()
        self.assertEqual(plan["event"]["name"], "Test Launch")
        self.assertEqual(len(plan["attendees"]), 1)
        self.assertEqual(len(plan["vendors"]), 1)
        self.assertIn("budget", plan)
        self.assertIn("schedule", plan)
        json.dumps(plan)  # must not raise


if __name__ == "__main__":
    unittest.main()
