# Design principles

Rules these templates follow. Each is checkable in the workflow JSON.

1. **A human approves anything outward-facing.** The content publisher waits for an explicit Telegram approval for the text and, separately, for the image. Nothing is posted without it.
2. **Low confidence is a branch, not a guess.** The call analyzer routes results below its confidence threshold to a manual-review path instead of writing uncertain data to the CRM.
3. **One trigger, one clear entry.** Each workflow starts from a webhook, a schedule or a sheet change. Multi-stage jobs are split into separate workflows (lead intake vs. daily follow-up) so each can be tested alone.
4. **Config at the top, logic below.** Values a user must change (sheet names, URLs, thresholds) live in a config or Set node, not scattered through expressions.
5. **No secrets in the file.** Credentials are referenced by placeholder id only. CI fails on anything else.
6. **Data stays in tools the user already owns.** Google Sheets as the database where a database would be overkill.
7. **Test with realistic input first.** Run once manually with sample data before activating a trigger.
