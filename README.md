# COP31 Antalya Programme

One searchable calendar for everything happening at COP31 (Antalya, Türkiye, 9–20 November 2026). It combines:

| Source | What it adds |
| --- | --- |
| [UNFCCC COP31](https://unfccc.int/cop31) | The official meetings calendar (negotiations, side events, press conferences, mandated and Global Climate Action events), the Antalya Leaders' Summit schedule, key facts and official links |
| [WhatTheCOP](https://whatthecop.com/) | The pavilion programme (4,000+ sessions with speakers, registration and livestream links), the daily themes and the eight negotiation questions |
| [Axis 1 Action Agenda timeline](https://momomtaz.github.io/axis1-timeline/) | Action Agenda events on electrification, efficiency, fuels, transport, maritime, green industry and transition away from fossil fuels |

When the same event appears in more than one source it is shown once, tagged with each source.

## What you can do

- **Calendar**: a November month grid with event counts per day, and an hour-by-hour agenda for the selected day, headed by the Presidency's theme for that day.
- **Keyword search**: searches titles, organisations, speakers, pavilions, rooms, topics and descriptions. Use quotes for phrases (`"loss and damage"`) and a minus sign to exclude (`finance -press`). The calendar updates to show which days have matches.
- **Filters**: source, zone, event type, topic, livestreamed only, hide unconfirmed or cancelled.
- **Event details**: links back to the source, registration, livestream, organiser page, and one-click *Add to Google Calendar* / *Add to Outlook*.
- **My shortlist**: star events to keep them in a personal list (stored in your browser only).
- **Key info**: about COP31, key dates, daily themes, what is being negotiated, and useful official links.
- Shareable links: `#day-2026-11-12`, `#list`, `#info`, or a single event.

## Files

```
index.html                 the whole app (no build step)
data/events.json           merged events, generated
data/overview.json         curated briefing content (edit by hand)
scripts/build_data.py      fetches the sources and rebuilds data/events.json
.github/workflows/         refreshes data every 3 hours and deploys to GitHub Pages
```

## Run locally

```bash
python3 scripts/build_data.py     # refresh the data (optional)
python3 -m http.server 8000       # then open http://localhost:8000
```

## Publish on GitHub Pages

1. Merge this branch into `main`.
2. In the repository, go to **Settings → Pages** and set **Source** to **GitHub Actions**.
3. The workflow then refreshes the data every three hours and redeploys. You can also run it by hand from the **Actions** tab.

## Notes

- All times are Antalya local time (UTC+3).
- Programmes change constantly during a COP; always confirm with the source before attending.
- Organiser e-mail addresses and phone numbers in the UNFCCC feed are deliberately not republished.
- This is an unofficial aggregation. All content belongs to the respective sources.
