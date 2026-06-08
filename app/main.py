"""What's 4 Dinner — FastAPI app, scheduler, and JSON API."""

import os
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import database as db
from . import picker

TZ = os.environ.get("TZ", "UTC")
PICK_HOUR = int(os.environ.get("PICK_HOUR", "14"))      # 2 PM by default
PICK_MINUTE = int(os.environ.get("PICK_MINUTE", "0"))

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
scheduler = BackgroundScheduler(timezone=ZoneInfo(TZ))


def scheduled_pick():
    """Job run every day at the configured time."""
    picker.pick_for_today(manual=False, force=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    scheduler.add_job(
        scheduled_pick,
        trigger=CronTrigger(hour=PICK_HOUR, minute=PICK_MINUTE, timezone=ZoneInfo(TZ)),
        id="daily_dinner_pick",
        replace_existing=True,
    )
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(title="What's 4 Dinner", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class DinnerIn(BaseModel):
    name: str


class DinnerPatch(BaseModel):
    name: str | None = None
    active: bool | None = None


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.get("/api/config")
def get_config():
    return {
        "timezone": TZ,
        "pick_hour": PICK_HOUR,
        "pick_minute": PICK_MINUTE,
        "today": picker.today_str(),
    }


@app.get("/api/dinners")
def api_list_dinners():
    return db.list_dinners()


@app.post("/api/dinners", status_code=201)
def api_add_dinner(payload: DinnerIn):
    try:
        return db.add_dinner(payload.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/api/dinners/{dinner_id}")
def api_update_dinner(dinner_id: int, payload: DinnerPatch):
    if db.get_dinner(dinner_id) is None:
        raise HTTPException(status_code=404, detail="Dinner not found")
    try:
        return db.update_dinner(dinner_id, name=payload.name, active=payload.active)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/dinners/{dinner_id}", status_code=204)
def api_delete_dinner(dinner_id: int):
    db.delete_dinner(dinner_id)


@app.get("/api/today")
def api_today():
    day = picker.today_str()
    selection = db.get_selection(day)
    return {"date": day, "selection": selection}


@app.post("/api/roll")
def api_roll():
    """Manually (re)roll today's dinner, overriding any existing pick."""
    selection = picker.pick_for_today(manual=True, force=True)
    if selection is None:
        raise HTTPException(
            status_code=400,
            detail="No active dinners to choose from. Add some first!",
        )
    return selection


@app.get("/api/history")
def api_history(limit: int = 30):
    return db.history(limit=limit)


# ---------------------------------------------------------------------------
# Static front-end
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/", StaticFiles(directory=STATIC_DIR), name="static")
