#!/usr/bin/env python3
"""Hakee julkisen Dynasty-RSS:n. Ei tuota arvauksia eikä käytä tekoälyä."""
import datetime as dt
import json
import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

URL = "https://lempaala10.oncloudos.com/cgi/DREQUEST.PHP?page=rss/meetingitems&show=100"
OUTPUT = Path("data.json")
now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
previous = {"items": []}
if OUTPUT.exists():
    try:
        previous = json.loads(OUTPUT.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        pass

def clean(s):
    return " ".join((s or "").split())[:240]

try:
    req = urllib.request.Request(URL, headers={"User-Agent": "LempaalanPaatokset/1.0 (public RSS reader)", "Accept": "application/rss+xml, application/xml, text/xml"})
    with urllib.request.urlopen(req, timeout=25) as response:
        content = response.read(2_000_000)
    root = ET.fromstring(content)
    channel = root.find("channel")
    if channel is None:
        raise ValueError("RSS-kanavaa ei löydy")
    entries = []
    for item in channel.findall("item"):
        title = clean(item.findtext("title"))
        url = (item.findtext("link") or "").strip()
        date = clean(item.findtext("pubDate"))
        parsed = urllib.parse.urlsplit(url)
        if not title or parsed.scheme != "https" or parsed.hostname != "lempaala10.oncloudos.com":
            continue
        entries.append({"title": title, "url": url, "published": date})
    if not entries:
        raise ValueError("Syöte ei sisältänyt kelvollisia asioita")
    data = {"status": "ok", "checked_at": now, "items": entries[:50]}
except Exception as e:
    # Säilytä aiemmin varmennetut linkit mutta näytä vanhentunut tila.
    print(f"Lähteen haku epäonnistui: {e}")
    data = {"status": "unavailable", "checked_at": now, "items": previous.get("items", [])[:50]}
OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Tila: {data['status']}, linkkejä: {len(data['items'])}")
