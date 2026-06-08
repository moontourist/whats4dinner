# 🍽️ What's 4 Dinner?

A tiny self-hosted dinner chooser for your CasaOS (or any Docker) server.
You supply a list of possible dinners; every day at **2 PM** the app picks one
at random and shows it as the day's dinner. Includes a clean web UI for
managing your list and browsing past picks.

## Features

- 🎲 **Automatic daily pick** at a configurable time (default 2 PM, your timezone)
- 📝 **Manage dinners** — add, rename (click the name), pause/enable, or delete
- 🔁 **Roll again** button to manually re-pick at any time
- 🧠 **No instant repeats** — avoids choosing the same dinner two picks in a row
- 📜 **History** of recent picks
- 💾 **Persistent storage** via SQLite on a mounted volume

## Quick start (Docker Compose)

1. Edit `docker-compose.yml` and set `TZ` to your timezone
   (e.g. `America/New_York`, `Europe/London`). This controls when 2 PM is.
2. Build and run:

   ```bash
   docker compose up -d --build
   ```

3. Open <http://your-server-ip:8137> and start adding dinners.

## Adding to CasaOS

CasaOS can import a Compose file directly:

1. In CasaOS, go to **App Store → Custom Install** (the `+` / `Install a customized app`).
2. Either paste the contents of `docker-compose.yml`, or build the image first
   (`docker compose build`) and point CasaOS at the `whats4dinner` image.
3. Make sure the **TZ** environment variable matches your locale and that the
   `/data` volume is mapped to persistent storage.
4. Set the WebUI port to `8137` so CasaOS shows a clickable launch button.

## Configuration

All settings are environment variables:

| Variable      | Default | Description                                  |
| ------------- | ------- | -------------------------------------------- |
| `TZ`          | `UTC`   | Timezone used to decide when the pick fires  |
| `PICK_HOUR`   | `14`    | Hour of day (24h) for the automatic pick     |
| `PICK_MINUTE` | `0`     | Minute of the hour for the automatic pick    |
| `DATA_DIR`    | `/data` | Where the SQLite database is stored          |

## How the daily pick works

- A background scheduler runs once a day at `PICK_HOUR:PICK_MINUTE` in `TZ`.
- It chooses a random **active** dinner and records it for that date.
- The automatic job won't overwrite a pick you made manually that same day.
- The **Roll again** button always overrides today's pick.
- If the server is off at 2 PM, no pick is recorded for the missed time, but
  you can still roll manually whenever you like.

## Local development

```bash
pip install -r requirements.txt
DATA_DIR=./data TZ=America/New_York uvicorn app.main:app --reload --port 8080
```

## Project layout

```
app/
  main.py        FastAPI app, scheduler, JSON API
  database.py    SQLite storage helpers
  picker.py      Random dinner-picking logic
  static/        Web UI (index.html, style.css, app.js)
Dockerfile
docker-compose.yml
```

## API

| Method | Path                 | Description                       |
| ------ | -------------------- | --------------------------------- |
| GET    | `/api/config`        | Timezone + schedule info          |
| GET    | `/api/dinners`       | List all dinners                  |
| POST   | `/api/dinners`       | Add a dinner `{ "name": "Tacos" }`|
| PATCH  | `/api/dinners/{id}`  | Rename / toggle active            |
| DELETE | `/api/dinners/{id}`  | Delete a dinner                   |
| GET    | `/api/today`         | Today's selection                 |
| POST   | `/api/roll`          | Re-roll today's pick              |
| GET    | `/api/history`       | Recent picks                      |
```
