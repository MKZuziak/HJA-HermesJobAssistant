# Daily use

## In Telegram

| You send | What happens |
|---|---|
| *(nothing)* | Every 12 h: new matches, highest score first, top matches (85+) under "Top matches — apply?". Silent if nothing new scores 60+. |
| a job link, optionally with "track this" or "draft" | Opened, verified, scored and added to the tracker; drafts written if it scores 60+ or you say "draft". |
| `apply <slug>` | Status "planned"; drafts checked; deadline reminders start (14, 7, 3 and 1 days before). |
| `skip <slug>` | Status "dropped"; never suggested again. |
| `applied to X` · `interview at Y` · `rejected from Z` · `offer from W` | Status and date updated. |
| `status` | Open applications by deadline, plus counts per status. |

## Files

| File | Contents |
|---|---|
| `~/scout/out/applications.md` | The tracker: one row per opportunity, with status history in the notes. |
| `~/scout/out/drafts/<slug>/cover_letter.md` | Draft cover letter. Edit it before use. |
| `~/scout/out/drafts/<slug>/checklist.md` | Required documents and submission steps. |
| `~/scout/out/seen.md` | Everything already assessed, so nothing is reported twice. |

## Teaching it

The model doesn't change. Hermes improves by writing things down, and scheduled runs start fresh, so **feedback only sticks once it is in a skill**:

1. Tell the bot what to change, e.g. *"Cover letters: under 350 words, open with the overlap with the PI's recent papers, never list my publications."*
2. Add: *"Update the scout-profile skill with this."*
3. Check the file: `~/.hermes/skills/hja/scout-profile/SKILL.md`.

Changes to `criteria.md` work the same way: edit the file, then run `make profile` to rebuild the skill.

## Customising

| Change | How |
|---|---|
| Criteria, CV, writing samples | Edit `~/scout/materials/`, then `make profile`. |
| Sites and queries | Edit `~/scout/materials/sources.md`. Picked up on the next run. |
| What each run does | Edit `agent/prompts/scout.md` or `deadlines.md`, then `make jobs`. |
| Tracker behaviour | Edit `agent/skills/scout-tracker/SKILL.md`, then `make install`. |
| Standing rules | Edit `agent/SOUL.md`, then `make install && make restart`. |
| Schedule | Change `every 12h` / `every 24h` in `agent/scripts/jobs.sh`, then `make jobs`. |
