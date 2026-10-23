"""TekunoAI Event Management - MVP prototype (stdlib only)."""
from .manager import EventManager
from .models import Attendee, Event, Expense, Task, Vendor
from .planner import suggest_plan

__all__ = [
    "EventManager",
    "Event",
    "Attendee",
    "Vendor",
    "Task",
    "Expense",
    "suggest_plan",
]

__version__ = "0.1.0"
