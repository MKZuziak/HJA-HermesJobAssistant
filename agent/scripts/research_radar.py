"""Collect new papers and new citations of the user's work for the research radar.

Installed into Hermes' scripts folder by install.sh and attached to the `radar` job
(cron --script): its output is injected into the agent's prompt, and the agent
judges relevance. Standard library only.

Sources
- arXiv API (export.arxiv.org): keyword queries, newest first, one request per
  ~3 s as the arXiv API terms ask. Thank you to arXiv for use of its open access
  interoperability.
- OpenAlex API: works that cite the user's papers. Needs a free key
  (OPENALEX_API_KEY in Hermes' .env) and the user's OpenAlex author ID.

Config: /opt/data/materials/radar.json (see templates/materials/radar.json).
State:  /opt/data/scout/radar/state.json (ids already reported).
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOME = Path(os.environ.get("HERMES_HOME", "/opt/data"))
CONFIG_PATH = HOME / "materials" / "radar.json"
STATE_PATH = HOME / "scout" / "radar" / "state.json"
ENV_PATH = HOME / ".env"

ARXIV_URL = "https://export.arxiv.org/api/query"
ARXIV_DELAY_S = 3.5
OPENALEX_URL = "https://api.openalex.org"
USER_AGENT = "hermes-job-assistant-radar/1.0"
ATOM = {"a": "http://www.w3.org/2005/Atom"}
MAX_SEEN = 5000
SUMMARY_CHARS = 500

DEFAULTS = {
    "lookback_days": 3,
    "arxiv_queries": [],
    "arxiv_categories": [],
    "max_per_query": 25,
    "openalex_author_id": "",
}


# --- helpers -----------------------------------------------------------------

def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def load_json(path: Path, default: dict) -> dict:
    try:
        return {**default, **json.loads(path.read_text(encoding="utf-8"))}
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(default)


def http_get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    # Only fixed https endpoints (arXiv, OpenAlex) are ever requested.
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def clean(text: str) -> str:
    return " ".join((text or "").split())


# --- arXiv ---------------------------------------------------------------------

def arxiv_query_url(query: str, categories: list[str], max_results: int) -> str:
    search = f"({query})"
    if categories:
        search += " AND (" + " OR ".join(f"cat:{c}" for c in categories) + ")"
    params = {
        "search_query": search,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": str(max_results),
    }
    return ARXIV_URL + "?" + urllib.parse.urlencode(params)


def parse_arxiv(xml_bytes: bytes, since: datetime) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    papers = []
    for entry in root.findall("a:entry", ATOM):
        published = entry.findtext("a:published", "", ATOM)
        try:
            when = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except ValueError:
            continue
        if when < since:
            continue
        raw_id = entry.findtext("a:id", "", ATOM)
        arxiv_id = raw_id.rsplit("/abs/", 1)[-1].split("v")[0] if "/abs/" in raw_id else raw_id
        authors = [clean(a.findtext("a:name", "", ATOM)) for a in entry.findall("a:author", ATOM)]
        papers.append({
            "id": f"arxiv:{arxiv_id}",
            "title": clean(entry.findtext("a:title", "", ATOM)),
            "authors": authors,
            "date": when.date().isoformat(),
            "link": f"https://arxiv.org/abs/{arxiv_id}",
            "summary": clean(entry.findtext("a:summary", "", ATOM))[:SUMMARY_CHARS],
        })
    return papers


# --- OpenAlex ------------------------------------------------------------------

def openalex_url(path: str, params: dict[str, str], key: str) -> str:
    return f"{OPENALEX_URL}/{path}?" + urllib.parse.urlencode({**params, "api_key": key})


def short_openalex_id(value: str) -> str:
    return value.rstrip("/").rsplit("/", 1)[-1]


def parse_citing(data: dict) -> list[dict]:
    works = []
    for work in data.get("results", []):
        authorships = work.get("authorships") or []
        authors = [clean((a.get("author") or {}).get("display_name", "")) for a in authorships]
        institutions = sorted({
            clean(inst.get("display_name", ""))
            for a in authorships for inst in (a.get("institutions") or []) if inst.get("display_name")
        })
        source = ((work.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
        works.append({
            "id": f"openalex:{short_openalex_id(work.get('id', ''))}",
            "title": clean(work.get("title") or work.get("display_name") or ""),
            "authors": authors,
            "institutions": institutions[:6],
            "venue": clean(source),
            "date": work.get("publication_date") or "",
            "link": work.get("doi") or work.get("id", ""),
        })
    return works


# --- output --------------------------------------------------------------------

def fmt_authors(authors: list[str], limit: int = 6) -> str:
    shown = ", ".join(authors[:limit])
    return shown + (f" +{len(authors) - limit}" if len(authors) > limit else "")


def render(citing: list[dict], papers: list[dict], notes: list[str]) -> str:
    out: list[str] = []
    if citing:
        out.append("=== CITING YOUR WORK")
        for w in citing:
            inst = f" | {'; '.join(w['institutions'])}" if w["institutions"] else ""
            venue = f" | {w['venue']}" if w["venue"] else ""
            out.append(f"- {w['date']} | {w['title']} | {fmt_authors(w['authors'])}{inst}{venue} | {w['link']}")
    if papers:
        out.append("=== NEW PAPERS")
        for p in papers:
            out.append(f"- {p['date']} | {p['title']} | {fmt_authors(p['authors'])} | {p['link']}")
            out.append(f"  {p['summary']}")
    if notes:
        out.append("=== NOTES")
        out.extend(f"- {n}" for n in notes)
    if not citing and not papers:
        out.insert(0, "NO_NEW_PAPERS")
    return "\n".join(out)


# --- main ----------------------------------------------------------------------

def collect_arxiv(cfg: dict, since: datetime, seen: set[str], notes: list[str]) -> list[dict]:
    found: dict[str, dict] = {}
    for i, query in enumerate(cfg["arxiv_queries"]):
        if i:
            time.sleep(ARXIV_DELAY_S)
        url = arxiv_query_url(query, cfg["arxiv_categories"], int(cfg["max_per_query"]))
        try:
            for paper in parse_arxiv(http_get(url), since):
                if paper["id"] not in seen:
                    found.setdefault(paper["id"], paper)
        except urllib.error.HTTPError as err:
            notes.append(f"arXiv query skipped ({err.code}): {query}")
            if err.code == 429:
                break  # rate-limited: stop for today rather than hammer the API
        except (urllib.error.URLError, ET.ParseError, TimeoutError) as err:
            notes.append(f"arXiv query failed ({type(err).__name__}): {query}")
    return sorted(found.values(), key=lambda p: p["date"], reverse=True)


def collect_citing(cfg: dict, key: str, since: datetime, seen: set[str], notes: list[str]) -> list[dict]:
    author = cfg.get("openalex_author_id", "").strip()
    if not author:
        notes.append("Citation tracking off: set openalex_author_id in radar.json.")
        return []
    if not key:
        notes.append("Citation tracking off: OPENALEX_API_KEY is not set.")
        return []
    try:
        mine = json.loads(http_get(openalex_url("works", {
            "filter": f"author.id:{short_openalex_id(author)}",
            "select": "id", "per_page": "100"}, key)))
        ids = [short_openalex_id(w["id"]) for w in mine.get("results", [])]
        if not ids:
            notes.append("OpenAlex lists no works for this author ID.")
            return []
        citing: list[dict] = []
        for start in range(0, len(ids), 50):  # OR-filter in chunks
            chunk = "|".join(ids[start:start + 50])
            data = json.loads(http_get(openalex_url("works", {
                "filter": f"cites:{chunk},from_publication_date:{since.date().isoformat()}",
                "select": "id,doi,title,display_name,publication_date,authorships,primary_location",
                "sort": "publication_date:desc", "per_page": "50"}, key)))
            citing.extend(w for w in parse_citing(data) if w["id"] not in seen)
        return citing
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, TimeoutError) as err:
        notes.append(f"OpenAlex lookup failed ({type(err).__name__}).")
        return []


def main() -> int:
    cfg = load_json(CONFIG_PATH, DEFAULTS)
    if not cfg["arxiv_queries"] and not cfg.get("openalex_author_id"):
        print(f"NO_RADAR_CONFIG: create {CONFIG_PATH} (template: templates/materials/radar.json)")
        return 0
    state = load_json(STATE_PATH, {"seen": []})
    seen = set(state["seen"])
    env = load_env(ENV_PATH)
    now = datetime.now(timezone.utc)
    notes: list[str] = []

    papers = collect_arxiv(cfg, now - timedelta(days=int(cfg["lookback_days"])), seen, notes)
    # Citations appear in OpenAlex with a lag; look back further and rely on `seen`.
    citing = collect_citing(cfg, env.get("OPENALEX_API_KEY", ""), now - timedelta(days=60), seen, notes)

    print(render(citing, papers, notes))

    new_ids = [x["id"] for x in citing + papers]
    state["seen"] = (state["seen"] + new_ids)[-MAX_SEEN:]
    state["last_run"] = now.isoformat(timespec="seconds")
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
