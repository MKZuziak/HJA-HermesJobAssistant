# Operations

| Task | Command |
|---|---|
| Status and health | `make ps` |
| Logs | `make logs` (Ctrl-C stops following; Hermes keeps running) |
| Jobs and recent runs | `make status` |
| Run the scout now | `make run`, or the trigger button in the dashboard |
| Market brief now | `make brief` |
| Three-month plan now | `make strategy` |
| Dashboard | http://localhost:9119, user `admin`, password `DASH_PASS` in `.env` |
| Shell in the container | `make shell` |
| Stop / start | `make down` / `make up` |
| Start on boot | `sudo systemctl enable docker` (the container has `restart: unless-stopped`) |
| Update Hermes and Claude Code | `make update` |
| Back up | `make backup` (the archive contains secrets; store it safely) |

A restart cancels a scheduled run in progress (it shows up as `KeyboardInterrupt`). Runs missed while the container was down are caught up once when it returns.

## Reproducible builds

`HERMES_TAG` in `.env` selects the upstream image. Once a version works for you, pin it:

```sh
docker run --rm nousresearch/hermes-agent:stable --version
# put that version in .env:  HERMES_TAG=X.Y.Z
make build && make up
```

## Moving to a cloud server

1. Create a small x86 server: 2 vCPU, 4 GB RAM, about 40 GB of disk.
2. Lock it down: SSH keys only, a firewall allowing only SSH, automatic security updates.
3. Install Docker Engine and the Compose plugin.
4. Clone the repo, then copy your data from the old machine:
   ```sh
   rsync -a ~/.hermes ~/scout <server>:~/
   scp .env secrets.env <server>:~/hja/
   ```
   On the server, set `HERMES_UID`/`HERMES_GID` in `.env` to the server user's `id -u`/`id -g`, and run `sudo chown -R $(id -u):$(id -g) ~/.hermes ~/scout`.
5. **Stop Hermes on the old machine first** (`make down`). Two instances would compete for the same Telegram bot.
6. On the server: `make build && make up`.
7. Dashboard through an SSH tunnel: `ssh -L 9119:127.0.0.1:9119 <server>`, then http://localhost:9119.

## Migrating an older install (container user 10000)

Earlier versions ran Hermes as UID 10000. Now it runs as you, so take the files over once:

```sh
make down
sudo chown -R $(id -u):$(id -g) ~/.hermes ~/scout/out
make init     # adds HERMES_UID/HERMES_GID if .env is new; otherwise add them to .env by hand
make up
```

If you created `scout-profile` or `scout-tracker` by chatting with the bot, remove those copies so the `hja/` versions are the only ones:

```sh
find ~/.hermes/skills -mindepth 1 -maxdepth 2 -type d -name 'scout-*' -not -path '*/hja/*'   # review
find ~/.hermes/skills -mindepth 1 -maxdepth 2 -type d -name 'scout-*' -not -path '*/hja/*' -exec rm -r {} +
make bootstrap
```
