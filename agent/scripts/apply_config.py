"""Apply secrets and settings to Hermes. Idempotent.

Usage (from the host):  make configure
  = docker exec -i -u hermes hermes python3 /opt/hja/scripts/apply_config.py < secrets.env

1. Reads KEY=VALUE lines from stdin and upserts them into Hermes' .env
   (existing keys are updated in place, new ones appended, empty values skipped).
2. Applies the settings this project relies on via `hermes config set`.
3. Disables the terminal and code-execution toolsets on every surface the agent uses.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

HOME = os.environ.get("HERMES_HOME", "/opt/data")
ENV_PATH = os.path.join(HOME, ".env")
KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")

# (key, value, force): force writes keys the CLI does not list in its defaults
# but the gateway reads (display.tool_progress).
SETTINGS = [
    ("display.tool_progress", "off", True),
    ("display.show_reasoning", "false", False),
    ("display.show_commentary", "false", False),
    ("agent.gateway_notify_interval", "0", False),
    ("cron.wrap_response", "false", False),
    ("cron.catch_up_missed", "true", False),
]
SEARCH = ("web.search_backend", "brave-free", "BRAVE_SEARCH_API_KEY")
EXTRACT = ("web.extract_backend", "tavily", "TAVILY_API_KEY")
DISABLED_TOOLSETS = ["terminal", "code_execution"]
PLATFORMS = ["cli", "telegram", "cron"]


def parse(lines: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        value = value.strip('"').strip("'")
        if KEY_RE.match(key) and value:
            values[key] = value
    return values


def upsert_env(path: str, updates: dict[str, str]) -> tuple[list[str], list[str]]:
    env_file = Path(path)
    existing = env_file.read_text(encoding="utf-8").splitlines() if env_file.exists() else []
    pending = dict(updates)
    changed, added, out = [], [], []
    for line in existing:
        key = line.split("=", 1)[0].strip() if "=" in line and not line.lstrip().startswith("#") else None
        if key in pending:
            new_line = f"{key}={pending.pop(key)}"
            if new_line != line:
                changed.append(key)
            out.append(new_line)
        else:
            out.append(line)
    for key, value in pending.items():
        out.append(f"{key}={value}")
        added.append(key)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write("\n".join(out) + "\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return changed, added


def hermes(*args: str) -> bool:
    result = subprocess.run(["hermes", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        print(f"  ! hermes {' '.join(args)}: {detail[-1] if detail else 'failed'}")
        return False
    return True


def main() -> int:
    secrets = parse(sys.stdin.readlines())
    changed, added = upsert_env(ENV_PATH, secrets)
    print(f".env: {len(added)} added, {len(changed)} updated, {len(secrets) - len(added) - len(changed)} unchanged")
    for key in added + changed:
        print(f"  {key}")

    current = parse(Path(ENV_PATH).read_text(encoding="utf-8").splitlines())
    settings = list(SETTINGS)
    for key, value, required_secret in (SEARCH, EXTRACT):
        if required_secret in current:
            settings.append((key, value, False))
        else:
            print(f"  - skipping {key}: {required_secret} not set")

    print("settings:")
    for key, value, force in settings:
        ok = hermes("config", "set", key, value, *(["--force"] if force else []))
        print(f"  {'✓' if ok else '✗'} {key} = {value}")

    print("tools disabled:")
    for platform in PLATFORMS:
        ok = hermes("tools", "disable", *DISABLED_TOOLSETS, "--platform", platform)
        print(f"  {'✓' if ok else '✗'} {', '.join(DISABLED_TOOLSETS)} on {platform}")

    print("Restart to apply: make restart")
    return 0


if __name__ == "__main__":
    sys.exit(main())
