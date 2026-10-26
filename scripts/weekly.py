#!/usr/bin/env python3
"""Otsikoihin perustuva viikkokatsaus. Ei väitä ehdotuksia päätöksiksi."""
import datetime as dt
import html
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo

today=dt.datetime.now(ZoneInfo("Europe/Helsinki")).date()
data=json.loads(Path("data.json").read_text(encoding="utf-8"))
if data.get("status")!="ok":
    raise SystemExit("Lähteen haku ei onnistunut: vanhaa koostetta ei korvata.")
cutoff=today-dt.timedelta(days=7)
exclude=("kokouksen laillisuus","pöytäkirjan tarkastaj","esityslistan hyväksyminen",
         "ilmoitusasia","viranhaltijapäätökset","muut asiat","ajankohtaiset asiat",
         "tehtäväalueiden ajankohtaiset")
keywords=("talous","vero","koulu","kaava","rakennus","hyvinvointi",
          "työllisyys","liikenne","investointi","maapoliittinen","palvelu")
articles=[]
seen=set()
for row in data.get("items",[]):
    title=html.unescape(row.get("title","")).strip()
    match=re.match(r"^(.*?)\s+(\d{1,2}\.\d{1,2}\.\d{4})\s*/\s*(.+)$",title)
    if not match: continue
    body, date_text, subject=match.groups()
    try: day=dt.datetime.strptime(date_text,"%d.%m.%Y").date()
    except ValueError: continue
    if day<cutoff or day>today+dt.timedelta(days=7):continue
    if any(e in subject.lower() for e in exclude):continue
    key=subject.casefold()
    if key in seen:continue
    seen.add(key)
    status="Tulossa käsittelyyn" if day>today else "Kokousasia (päätöstä ei vahvistettu)"
    articles.append({"title":subject,"body":body,"meeting_date":day.isoformat(),
                     "status":status,"url":row["url"],
                     "_score":sum(3 for k in keywords if k in subject.lower())+(2 if day>=today else 0)})
articles.sort(key=lambda x:(-x["_score"],x["meeting_date"],x["title"]))
for item in articles:item.pop("_score")
out={"week":today.isocalendar().week,"year":today.year,"published":today.isoformat(),
     "notice":"Kooste perustuu julkisiin kokousasioiden otsikoihin. Se ei ole päätöspöytäkirjojen eikä asiakirjasisältöjen tekoälytiivistelmä.",
     "items":articles[:10]}
Path("weekly.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(f"Viikkokatsaus: {len(out['items'])} asiaa")
