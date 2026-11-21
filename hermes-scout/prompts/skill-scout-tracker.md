Create a skill called scout-tracker with exactly these rules:

Purpose: track my job and grant search in /opt/data/scout/applications.md.

When I send a link (with or without a comment):
1. Open the page and confirm title, institution, location, deadline, eligibility and how to apply. Mark anything you cannot confirm as "unconfirmed".
2. Score it with the scout-profile rubric.
3. Add one row to the tracker table: today's date, role, institution, location, deadline, score, status "found", one-line fit reason, link.
4. If the score is 60 or higher, or I say "draft", write cover_letter.md and checklist.md to /opt/data/scout/drafts/<short-slug>/ and set status to "drafting".
5. Reply with the row and the draft folder.

When I reply "apply <role or slug>": set that row to "planned", make sure drafts exist, and confirm the deadline.
When I reply "skip <role or slug>": set it to "dropped".

When I report progress ("applied to X", "interview at Y", "rejected from Z", "offer from W"): update that row's status and add the date in notes.
Statuses: found, drafting, planned, applied, interview, rejected, offer, dropped.

When I ask "status" or "summary": list open items by deadline, then counts per status.

Never delete rows. Never submit applications or send emails.
