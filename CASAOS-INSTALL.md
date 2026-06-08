# Installing What's 4 Dinner on CasaOS (as a dashboard app)

This gets you a clickable tile in the CasaOS dashboard with an icon and a
"Open Web UI" button. CasaOS installs by pulling an image rather than building
one, so the trick is to **build the image once on the server**, then point
CasaOS at that local image.

## 1. Copy the project to the server (from your PC, in PowerShell)

```powershell
scp -r "C:\Users\Matt\Desktop\Dev\whats4dinner" <user>@<server-ip>:~/whats4dinner
```

## 2. Build the image on the server (over SSH)

```bash
ssh <user>@<server-ip>
cd ~/whats4dinner
docker build -t whats4dinner:latest .
```

When it finishes, confirm it's there:

```bash
docker images | grep whats4dinner
```

## 3. Add it to the CasaOS dashboard

1. Open the CasaOS web dashboard.
2. Click the **+** (top of the apps area) → **Install a customized app**.
3. Click the **import** icon (top-right of the dialog) and **paste the entire
   contents of `casaos-app.yml`** from this project.
4. Review the settings — the WebUI port is `8137`, timezone is
   `America/Los_Angeles`, and data is stored at
   `/DATA/AppData/whats4dinner/data`.
5. Click **Install**.

CasaOS uses the local `whats4dinner:latest` image (the `pull_policy: never` line
stops it from trying to download from the internet), starts the container, and
adds the tile. Click the tile's **Open Web UI** to launch it.

> Don't also run `docker compose up` for this app — let CasaOS manage the
> container so it doesn't fight over the port.

## Updating later

When you change the code, rebuild and let CasaOS recreate the container:

```bash
cd ~/whats4dinner
git pull            # or scp the new files over again
docker build -t whats4dinner:latest .
```

Then in CasaOS, open the app's **settings → recreate** (or remove and
re-import). Your dinners and history are safe in `/DATA/AppData/whats4dinner/data`.

## Changing the port

If `8137` clashes with something, edit `casaos-app.yml` before importing and
change `published: "8137"` and the `port_map: "8137"` line to a free port.
```
