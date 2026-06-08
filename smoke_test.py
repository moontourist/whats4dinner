"""Quick end-to-end check of the API using FastAPI's TestClient."""
import os, tempfile
os.environ["DATA_DIR"] = tempfile.mkdtemp()
os.environ["TZ"] = "America/New_York"

from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as c:  # 'with' triggers lifespan -> init_db + scheduler
    assert c.get("/api/config").json()["timezone"] == "America/New_York"

    # No dinners yet -> roll should 400
    assert c.post("/api/roll").status_code == 400

    # Add a few
    for n in ["Tacos", "Pasta", "Stir Fry", "Pizza"]:
        r = c.post("/api/dinners", json={"name": n})
        assert r.status_code == 201, r.text
    assert len(c.get("/api/dinners").json()) == 4

    # Rename + pause one
    d = c.get("/api/dinners").json()[0]
    assert c.patch(f"/api/dinners/{d['id']}", json={"active": False}).status_code == 200

    # Roll picks an active dinner and records today
    pick = c.post("/api/roll").json()
    assert pick["name"] in ["Tacos", "Pasta", "Stir Fry", "Pizza"]
    today = c.get("/api/today").json()
    assert today["selection"]["name"] == pick["name"]
    assert today["selection"]["manual"] == 1

    # "No instant repeat": with last pick known, rolling 20x never repeats
    #   immediately when >1 active option exists.
    prev = pick["name"]
    repeats = 0
    for _ in range(20):
        nxt = c.post("/api/roll").json()["name"]
        if nxt == prev:
            repeats += 1
        prev = nxt
    assert repeats == 0, f"got {repeats} back-to-back repeats"

    # History reflects rolls (one row per day, so just 1 here)
    hist = c.get("/api/history").json()
    assert len(hist) == 1 and hist[0]["manual"] == 1

    # Delete a dinner
    assert c.delete(f"/api/dinners/{d['id']}").status_code == 204
    assert len(c.get("/api/dinners").json()) == 3

    # Index page serves HTML
    assert "<title>What's 4 Dinner?" in c.get("/").text

print("ALL CHECKS PASSED ✅")
