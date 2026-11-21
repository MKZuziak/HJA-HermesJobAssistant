Use the scout-tracker skill. Read /opt/data/scout/applications.md.

For every row with status "planned" or "drafting", compute the days left until the deadline.
Remind me when a threshold (14, 7, 3 or 1 days) has been crossed since the last reminder recorded in that row's notes, or when the deadline is overdue.
For each reminder give: role, institution, deadline, days left, draft folder, and what is still missing from its checklist.md.
After reminding, add "reminded <YYYY-MM-DD>" to that row's notes. Do not change any status.

If nothing qualifies, reply only with [SILENT].
