#!/usr/bin/env python3
"""Build data/events.json for the COP31 platform.

Pulls and merges four public sources into one searchable event list:

  u  UNFCCC official meetings calendar (the feed behind unfccc.int/cop31/meetings-at-a-glance)
     plus the Antalya Leaders' Summit schedule from unfccc.int/cop31/high-level
  w  WhatTheCOP programme (whatthecop.com/programme): pavilion sessions
  a  Action Agenda Axis 1 timeline (momomtaz.github.io/axis1-timeline)

Usage:
  python3 scripts/build_data.py            # fetch live and write data/events.json
  python3 scripts/build_data.py --cache DIR  # also save/reuse raw downloads in DIR

Privacy: organiser e-mail addresses and phone numbers present in the source
feeds are dropped. Only organisation names are kept.
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "events.json")
UA = "Mozilla/5.0 (compatible; COP31-consolidation/1.0; +https://github.com/kd-ops/cop31)"

URLS = {
    "unfccc_feed": "https://unfcccstagresprd01.blob.core.windows.net/$web/meetings_102_full.json",
    "wtc_programme": "https://whatthecop.com/programme",
    "axis": "https://momomtaz.github.io/axis1-timeline/",
}

# ----------------------------------------------------------------- fetching

def fetch(key, cache):
    path = os.path.join(cache, key) if cache else None
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    req = urllib.request.Request(URLS[key], headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read().decode("utf-8", errors="replace")
    if path:
        os.makedirs(cache, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
    return body


def clean(s):
    if not s:
        return ""
    s = html.unescape(re.sub(r"<[^>]+>", " ", str(s)))
    return re.sub(r"\s+", " ", s).strip()


def slug_label(slug):
    special = {
        "ai-data": "AI & data", "cities-local": "Cities & local action",
        "youth-education": "Youth & education", "agriculture-food": "Agriculture & food",
        "forests-land": "Forests & land", "grids-storage": "Grids & storage",
        "fossil-phaseout": "Fossil fuel phase-out", "indigenous-communities": "Indigenous communities",
        "culture-heritage": "Culture & heritage", "food-loss-waste": "Food loss & waste",
        "composting-organics": "Composting & organics", "landfill-incineration": "Landfill & incineration",
        "taff": "Transition away from fossil fuels",
    }
    if slug in special:
        return special[slug]
    return slug.replace("-", " ").capitalize()

# ----------------------------------------------------------------- UNFCCC

UNFCCC_KIND = {
    "Side Events": "Side event", "Press/Media": "Press conference",
    "Negotiating Groups": "Negotiations", "BOR Negotiating groups": "Negotiations",
    "UNFCCC Events": "UNFCCC event", "UNFCCC Meeting": "UNFCCC event",
    "Global Climate Action event": "Global Climate Action", "Observers": "Observer meeting",
    "Observer Event": "Observer meeting", "Mandated event": "Mandated event",
    "UNFCCC Pavilions": "UNFCCC pavilion", "COP Presidency event": "Presidency event",
}


def unfccc(raw):
    d = json.loads(raw)
    out = []
    for m in d["meetings"]:
        if m.get("deleted"):
            continue
        start, end = m.get("start") or "", m.get("end") or ""
        orgs = []
        for o in m.get("organizers") or []:
            name = (o.get("organization") or "").strip()
            if name and name not in orgs:
                orgs.append(name)  # e-mail / phone deliberately not kept
        kind = UNFCCC_KIND.get(m.get("type"), m.get("type") or "UNFCCC")
        topics = [kind]
        if m.get("thematic_category"):
            topics.append(m["thematic_category"])
        room = ", ".join(x for x in [m.get("room_name"), m.get("room_tags")] if x)
        links = {"src": "https://unfccc.int/cop31/meetings-at-a-glance"}
        if m.get("webcast") and m.get("webcast_link"):
            links["watch"] = m["webcast_link"]
        if m.get("document_url"):
            links["doc"] = m["document_url"]
        out.append({
            "id": f"u{m['id']}", "s": ["u"], "t": clean(m.get("title")),
            "d": start[:10] or None, "st": start[11:16], "en": end[11:16],
            "v": room, "z": "Blue Zone", "k": kind,
            "o": "; ".join(orgs), "sp": clean(m.get("speakers")),
            "x": clean(m.get("description") or (m.get("body") if len(m.get("body") or "") > 12 else "")),
            "tp": topics, "l": links,
            "f": ["closed"] if m.get("closed") else [],
        })
    return out, d.get("last_updated")


HL = "https://unfccc.int/cop31/high-level#schedule-of-events"
LEADERS = [
    ("2026-11-11", "08:30", "11:00", "Arrival of Heads of State or Government", "Blue Zone"),
    ("2026-11-11", "12:15", "13:30", "Opening session of the Antalya Leaders' Summit", "Blue Zone"),
    ("2026-11-11", "14:00", "14:30", "Ceremonial opening of the first part of the High-Level Segment for Heads of State and Government", "Plenary Anadolu"),
    ("2026-11-11", "14:30", "18:30", "High-Level Segment: delivery of national statements by Heads of State and Government", "Plenary Anadolu"),
    ("2026-11-11", "15:00", "16:30", "Presidential High-Level Dialogue: Clean Energy Transition and Electrification, \u201c35 by 35: Powering the Future\u201d", "Blue Zone"),
    ("2026-11-11", "15:00", "17:00", "Summit High-Level Party Event: Leaders' Summit Event on Forests", "Blue Zone"),
    ("2026-11-11", "16:00", "17:30", "Leaders' Roundtable: Zero Waste, Circularity and Methane", "Blue Zone"),
    ("2026-11-11", "17:00", "18:30", "Presidential High-Level Dialogue: Seizing the Green Industrial Opportunity: Investment, Jobs and Growth for Every Economy", "Blue Zone"),
    ("2026-11-11", "17:00", "18:30", "UN Secretary-General High-Level Event: Early Warnings for All, Delivering on Our Promise to Protect Everyone", "Blue Zone"),
    ("2026-11-12", "09:00", "10:00", "Summit High-Level Party Event: COP31 Leaders-Level Non-CO\u2082 Greenhouse Gases Summit", "Blue Zone"),
    ("2026-11-12", "10:00", "11:30", "UN Secretary-General High-Level Event: Global Grids Accelerator, Power for Future: Grids for Energy Security and Prosperity", "Blue Zone"),
    ("2026-11-12", "10:00", "16:00", "High-Level Segment (continued): national statements by Heads of State and Government", "Plenary Anadolu"),
    ("2026-11-12", "10:45", "12:30", "Summit High-Level Party Event: Advancing the Mountain Agenda: Glaciers, Cryosphere and Resilience", "Blue Zone"),
    ("2026-11-12", "12:00", "13:30", "Presidential High-Level Roundtable: The Second Decade of the Paris Agreement: Accelerating Implementation and Access to Finance", "Blue Zone"),
    ("2026-11-12", "13:30", "17:00", "Presidential High-Level Dialogue: Urban Resilience, Adaptation and Climate Action", "Blue Zone"),
    ("2026-11-12", "14:30", "16:00", "Leaders' Roundtable: Clean Cooking in Africa", "Blue Zone"),
    ("2026-11-12", "15:30", "17:00", "High-Level Dialogue: African Leadership on Climate Action: Resilience, Adaptation and Sustainable Development", "Blue Zone"),
    ("2026-11-12", "15:30", "17:00", "Summit High-Level Party Event: Pacific Resilience Facility Showcase, \u201cUSD 1.5 billion for a 1.5C World\u201d", "Blue Zone"),
    ("2026-11-12", "17:00", "17:00", "End of the Antalya Leaders' Summit", "Blue Zone"),
    ("2026-11-17", "", "", "Resumed High-Level Segment: national statements (Parties whose leaders did not speak on 11\u201312 Nov)", "Plenary"),
    ("2026-11-18", "", "", "Resumed High-Level Segment: national statements (continued)", "Plenary"),
]


def leaders():
    out = []
    for i, (d, st, en, t, v) in enumerate(LEADERS):
        out.append({
            "id": f"uls{i}", "s": ["u"], "t": t, "d": d, "st": st, "en": en, "v": v,
            "z": "Blue Zone", "k": "Leaders' Summit", "o": "COP31 Presidency / UNFCCC",
            "sp": "", "x": "Antalya Leaders' Summit, under the theme \u201cTowards a Sustainable, Resilient and Equitable Future\u201d. Timings are subject to minor changes.",
            "tp": ["Leaders' Summit", "High-level"], "l": {"src": HL}, "f": ["leaders"],
        })
    return out

# ----------------------------------------------------------------- WhatTheCOP

def wtc(raw):
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', raw, re.S)
    full = "".join(json.loads('"' + c + '"') for c in chunks)
    dec = json.JSONDecoder()
    seen = {}
    for m in re.finditer(r'\{"id":"[0-9a-f-]{36}","title"', full):
        try:
            o, _ = dec.raw_decode(full, m.start())
        except ValueError:
            continue
        if "day" in o and "pavilion" in o:
            seen[o["id"]] = o
    out = []
    zone_map = {"blue": "Blue Zone", "green": "Green Zone"}
    access_map = {"blue_zone": "Blue Zone", "green_zone": "Green Zone", "offsite": "Off-site", "online": "Online"}
    for o in seen.values():
        pav = o.get("pavilion") or {}
        zone = access_map.get(o.get("access")) or zone_map.get(pav.get("zone"), "")
        links = {"src": f"https://whatthecop.com/sessions/{o['id']}"}
        if o.get("source"):
            links["org"] = o["source"]
        if o.get("registration"):
            links["reg"] = o["registration"]
        if o.get("watchUrl") or o.get("livestream"):
            links["watch"] = o.get("watchUrl") or o.get("livestream")
        if o.get("recording"):
            links["rec"] = o["recording"]
        flags = []
        if o.get("status") == "cancelled":
            flags.append("cancelled")
        if links.get("watch"):
            flags.append("live")
        out.append({
            "id": f"w{o['id'][:8]}", "s": ["w"], "t": clean(o.get("title")),
            "d": o.get("day"), "st": o.get("start") or "", "en": o.get("end") or "",
            "v": pav.get("name") or "", "z": zone, "k": "Pavilion session",
            "o": "; ".join(o.get("organisers") or []), "sp": "; ".join(o.get("speakers") or []),
            "x": "", "tp": [slug_label(t) for t in (o.get("topics") or [])],
            "l": links, "f": flags,
        })
    return out

# ----------------------------------------------------------------- Axis 1

def axis(raw):
    m = re.search(r'<script[^>]*id="data"[^>]*>(.*?)</script>', raw, re.S)
    data = json.loads(m.group(1))
    upd = re.search(r"Updated\s+(\d{1,2} \w{3} 20\d\d)", re.sub(r"<[^>]+>", " ", raw))
    out = []
    for e in data:
        time = e.get("time") or ""
        parts = re.split(r"[\u2013-]", time)
        st = parts[0].strip() if parts and re.match(r"\d\d:\d\d", parts[0].strip()) else ""
        en = parts[1].strip() if len(parts) > 1 and re.match(r"\d\d:\d\d", parts[1].strip()) else ""
        tags = []
        for t in e.get("tags") or []:
            if t == "all":
                tags.append("All Axis 1 sectors")
            elif t.startswith("gi-"):
                tags.append("Green industry: " + slug_label(t[3:]).lower())
            else:
                tags.append(slug_label(t))
        tags += [p for p in (e.get("pas") or [])]
        flags = []
        if e.get("status") == "Unconfirmed":
            flags.append("unconfirmed")
        elif e.get("status") == "Under review":
            flags.append("review")
        lvl = e.get("level")
        if lvl and lvl != "Standard":
            flags.append({"Heads of State / Leaders": "leaders", "Ministerial": "ministerial", "High-level": "highlevel"}.get(lvl, "highlevel"))
        links = {"src": "https://momomtaz.github.io/axis1-timeline/"}
        if e.get("srcurl"):
            links["org"] = e["srcurl"]
        space = e.get("space") or ""
        zone = {"Action Agenda": "Blue Zone", "COP31 Presidency": "Blue Zone", "Blue Zone": "Blue Zone",
                "Green Zone": "Green Zone", "Off-site": "Off-site"}.get(space, "")
        out.append({
            "id": f"a{e['id']}", "s": ["a"], "t": clean(e.get("title")),
            "d": e.get("date"), "st": st, "en": en, "v": e.get("loc") or "", "z": zone,
            "k": "Action Agenda (Axis 1)" + (f" \u00b7 {space}" if space in ("Action Agenda", "COP31 Presidency") else ""),
            "o": e.get("org") or "", "sp": "", "x": clean(e.get("desc")),
            "tp": tags, "l": links, "f": flags,
        })
    return out, (upd.group(1) if upd else None)

# ----------------------------------------------------------------- merge

def norm(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())[:60]


def merge(events):
    """Fold events that appear in more than one source into a single record."""
    index, out = {}, []
    for ev in events:
        keys = {norm(ev["t"])}
        if ": " in ev["t"]:
            keys.add(norm(ev["t"].split(": ", 1)[1]))
        keys = {(ev["d"], ev["st"], k) for k in keys if len(k) > 12}
        hit = next((index[k] for k in keys if k in index), None)
        if hit is not None and not set(ev["s"]) & set(hit["s"]):
            hit["s"] += ev["s"]
            for k in ("v", "o", "sp", "x", "z"):
                if not hit[k] and ev[k]:
                    hit[k] = ev[k]
            hit["tp"] += [t for t in ev["tp"] if t not in hit["tp"]]
            for lk, lv in ev["l"].items():
                hit["l"].setdefault(lk if lk != "src" else "src_" + ev["s"][0], lv)
            hit["f"] += [f for f in ev["f"] if f not in hit["f"]]
            hit.setdefault("ids", [hit["id"]]).append(ev["id"])
            continue
        out.append(ev)
        for k in keys:
            index.setdefault(k, ev)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", help="directory to save/reuse raw downloads")
    args = ap.parse_args()

    u, u_upd = unfccc(fetch("unfccc_feed", args.cache))
    u += leaders()
    w = wtc(fetch("wtc_programme", args.cache))
    a, a_upd = axis(fetch("axis", args.cache))
    print(f"UNFCCC {len(u)}  WhatTheCOP {len(w)}  Axis1 {len(a)}", file=sys.stderr)
    if min(len(u), len(w), len(a)) < 20:
        sys.exit("A source returned almost nothing; refusing to overwrite data/events.json")

    events = merge(u + w + a)
    events.sort(key=lambda e: (e["d"] or "9999", e["st"] or "99", e["t"]))
    for e in events:  # drop empty fields to keep the file small
        for k in [k for k, v in e.items() if v in ("", [], {}, None) and k not in ("d", "s", "t")]:
            del e[k]

    payload = {
        "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sources": {
            "u": {"name": "UNFCCC official", "url": "https://unfccc.int/cop31", "count": len(u), "updated": u_upd},
            "w": {"name": "WhatTheCOP", "url": "https://whatthecop.com/", "count": len(w)},
            "a": {"name": "Axis 1 Action Agenda", "url": "https://momomtaz.github.io/axis1-timeline/", "count": len(a), "updated": a_upd},
        },
        "events": events,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    merged = len(u) + len(w) + len(a) - len(events)
    print(f"wrote {len(events)} events ({merged} cross-source duplicates merged) -> {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
