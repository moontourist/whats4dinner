"""The core dinner-picking logic, shared by the scheduler and the API."""

import os
import random
from datetime import datetime
from zoneinfo import ZoneInfo

from . import database as db

TZ = os.environ.get("TZ", "UTC")


def today_str() -> str:
    """Today's date in the configured timezone (YYYY-MM-DD)."""
    return datetime.now(ZoneInfo(TZ)).strftime("%Y-%m-%d")


def choose_dinner(active_dinners: list, avoid_name: str | None):
    """Pick one dinner at random, avoiding `avoid_name` when there's a choice."""
    if not active_dinners:
        return None
    pool = active_dinners
    if avoid_name and len(active_dinners) > 1:
        filtered = [d for d in active_dinners if d["name"] != avoid_name]
        if filtered:
            pool = filtered
    return random.choice(pool)


def pick_for_today(manual: bool = False, force: bool = False):
    """Select a dinner for today and persist it.

    Returns the selection dict, or None if there are no active dinners.
    If a pick already exists for today and `force` is False, it is returned
    unchanged (so the scheduler never clobbers a manual override).
    """
    day = today_str()
    existing = db.get_selection(day)
    if existing and not force:
        return existing

    active = [d for d in db.list_dinners() if d["active"]]
    avoid = db.last_pick_name()
    chosen = choose_dinner(active, avoid)
    if chosen is None:
        return None
    return db.set_selection(day, chosen, manual=manual)
