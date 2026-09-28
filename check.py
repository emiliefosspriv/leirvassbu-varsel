"""Sjekker om påskebooking på Leirvassbu er åpen og sender varsel til ntfy.

Kjøres av GitHub Actions hvert 5. minutt. Varsler ved hver kjøring så lenge
bookingen er åpen – deaktiver workflowen når du har booket.
"""
import json
import os
import sys
import urllib.error
import urllib.request

CABIN_ID = 101059
FROM, TO = "2027-03-25", "2027-03-28"
ADULTS = 5
API = f"https://hyttebestilling.dnt.no/api/booking/available-price?cabinId={CABIN_ID}&fromDate={FROM}&toDate={TO}"
BOOK_URL = f"https://hyttebestilling.dnt.no/hytte/{CABIN_ID}?fromDate={FROM}&toDate={TO}&adults={ADULTS}&numberOfGuests={ADULTS}"
NTFY_TOPIC = os.environ["NTFY_TOPIC"]


def ntfy(title, message):
    req = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}", data=message.encode(),
        headers={"Title": title, "Click": BOOK_URL, "Priority": "urgent", "Tags": "mountain"},
    )
    urllib.request.urlopen(req, timeout=30)


def main():
    if os.environ.get("TEST") == "true":
        ntfy("Leirvassbu-varsel: test", "GitHub-varsler virker. Trykk for å åpne bestillingen.")
        return

    req = urllib.request.Request(API, headers={"User-Agent": "Mozilla/5.0 leirvassbu-watch"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode()
    except urllib.error.HTTPError as e:
        body = e.read().decode()

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print("Ukjent svar:", body[:200])
        return

    err = (data.get("error") or {}).get("faultstring", "")
    if "stengt" in err.lower():
        print("Stengt:", err)
    elif "data" in data:
        print("ÅPEN!")
        ntfy("Leirvassbu påske: booking er åpen!", "25.–28. mars, 5 voksne. Trykk for å bestille nå.")
    else:
        print("Endret svar:", err or body[:200])
        ntfy("Leirvassbu: bookingstatus endret", f"{err or 'Nytt svar fra DNT'}. Sjekk nå.")


if __name__ == "__main__":
    sys.exit(main())
