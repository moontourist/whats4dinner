<div align="center">

```
__        ___  _   ____
\ \      / / || | |  _ \
 \ \ /\ / /| || |_| | | |
  \ V  V / |__   _| |_| |
   \_/\_/     |_| |____/
```

`· what's 4 dinner? ·`

a tiny self-hosted dinner chooser for your casaos (or any docker) server.
feed it a list of dinners; every day at **14:00** it picks one at random and
serves it as the day's dinner.

</div>

---

## `[ the gist ]`

```
 ════════════════════════════════════════════════
 ┌─[ tonight's dinner ]──────────────────────────┐
 │              >> TACOS <<                       │
 │           auto-picked at 2:00 pm               │
 │              [ roll the dice ]                 │
 └────────────────────────────────────────────────┘
 ┌─[ dinner options ]────────────────────────────┐
 │  > add a dinner...                    [ add ]  │
 │  [x] tacos                            [del]    │
 │  [ ] meatloaf                         [del]    │
 └────────────────────────────────────────────────┘
        -=[ est. 2026 ]=-  ·  best viewed in any terminal
```

- **automatic daily pick** at a configurable time (default `14:00`, your timezone)
- **manage dinners** — add, rename (click the name), pause `[x]`/`[ ]`, or delete
- **roll the dice** to manually re-pick at any time
- **no instant repeats** — won't choose the same dinner two picks in a row
- **history log** of recent picks
- **persistent storage** via sqlite on a mounted volume
- single small container · vanilla web ui · no build step

---

## `[ requirements ]`

- a server running **docker** (casaos already includes it)
- a free port for the web ui — this guide uses **`8137`**

---

## `[ install — casaos dashboard tile ]`  *(recommended)*

casaos installs apps by **pulling an image**, so the trick is to build the
image once on the server, then point casaos at that local image.

**1 · clone the repo onto the server** *(over ssh)*

```bash
cd ~
git clone https://github.com/moontourist/whats4dinner.git
cd whats4dinner
```

**2 · build the image**

```bash
docker build -t whats4dinner:latest .
```

confirm it exists:

```bash
docker images | grep whats4dinner
```

**3 · set your timezone** — open `casaos-app.yml` and make sure `TZ` matches
your locale (this decides when `14:00` actually fires):

```yaml
environment:
  TZ: America/Los_Angeles    # <- your timezone
  PICK_HOUR: "14"            # 24h clock — 14 = 2 pm
  PICK_MINUTE: "0"
```

**4 · add the tile in casaos**

1. open the casaos dashboard → **`+`** → **install a customized app**
2. click the **import** icon (top-right) and paste the full contents of
   **`casaos-app.yml`**
3. click **install**

casaos uses your local `whats4dinner:latest` image (the `pull_policy: never`
line stops it trying to download from the internet), starts the container, and
drops a tile on your dashboard. click **open web ui** to launch it on `:8137`.

> don't also run `docker compose up` for this app — let casaos own the
> container so they don't fight over the port.

---

## `[ install — plain docker compose ]`  *(no dashboard tile)*

prefer the command line, or not on casaos? use the included compose file.

```bash
git clone https://github.com/moontourist/whats4dinner.git
cd whats4dinner
# edit docker-compose.yml -> set TZ to your timezone, then:
docker compose up -d --build
```

then open **`http://<server-ip>:8137`** and start adding dinners.

---

## `[ configuration ]`

all settings are environment variables:

| variable      | default | description                                  |
| ------------- | ------- | -------------------------------------------- |
| `TZ`          | `UTC`   | timezone used to decide when the pick fires  |
| `PICK_HOUR`   | `14`    | hour of day (24h) for the automatic pick     |
| `PICK_MINUTE` | `0`     | minute of the hour for the automatic pick    |
| `DATA_DIR`    | `/data` | where the sqlite database is stored          |

**changing the port:** edit the published port (`8137`) in `casaos-app.yml`
(`published:` **and** `port_map:`) or in `docker-compose.yml` (`"8137:8080"`).
the app always listens on `8080` *inside* the container — only change the
left/host side.

---

## `[ how the daily pick works ]`

- a background scheduler runs once a day at `PICK_HOUR:PICK_MINUTE` in `TZ`
- it chooses a random **active** dinner and records it for that date
- the automatic job won't overwrite a pick you made manually that same day
- **roll the dice** always overrides today's pick
- if the server is off at pick time, no pick is recorded for the missed slot,
  but you can still roll manually whenever you like

---

## `[ updating ]`

```bash
cd ~/whats4dinner
git pull
docker build -t whats4dinner:latest .
```

then recreate the app in casaos (app settings → recreate), or
`docker compose up -d --build` for the compose setup. your dinners and history
are safe in the data volume (`/DATA/AppData/whats4dinner/data` on casaos).

---

## `[ local development ]`

```bash
pip install -r requirements.txt
DATA_DIR=./data TZ=America/Los_Angeles uvicorn app.main:app --reload --port 8137
```

then open `http://localhost:8137`. `smoke_test.py` runs a quick end-to-end
check of the api:

```bash
python smoke_test.py
```

---

## `[ project layout ]`

```
app/
  main.py        fastapi app · scheduler · json api
  database.py    sqlite storage helpers
  picker.py      random dinner-picking logic
  static/        web ui (index.html · style.css · app.js)
Dockerfile
docker-compose.yml     plain compose deploy
casaos-app.yml         casaos custom-install file (dashboard tile)
CASAOS-INSTALL.md      step-by-step casaos walkthrough
```

---

## `[ api ]`

| method | path                 | description                        |
| ------ | -------------------- | ---------------------------------- |
| GET    | `/api/config`        | timezone + schedule info           |
| GET    | `/api/dinners`       | list all dinners                   |
| POST   | `/api/dinners`       | add a dinner `{ "name": "tacos" }` |
| PATCH  | `/api/dinners/{id}`  | rename / toggle active             |
| DELETE | `/api/dinners/{id}`  | delete a dinner                    |
| GET    | `/api/today`         | today's selection                  |
| POST   | `/api/roll`          | re-roll today's pick               |
| GET    | `/api/history`       | recent picks                       |

---

<div align="center">

`-=[ est. 2026 ]=-  ·  served fresh daily @ 14:00  ·  best viewed in any terminal`

</div>
