"""Download the season files of tennis-data.co.uk (ATP from 2000, WTA from 2007).

Run:
    python -m tennis_networks.download              # seasons up to 2025
    python -m tennis_networks.download --last 2026

Files go to data/raw/tennisdata/atp/<year>.xls[x] and data/raw/tennisdata/wta/<year>.xls[x];
data/raw/tennisdata/manifest.csv records URL, date, size and SHA-256 of every file.
Links are read from alldata.php because the site serves them under a changing path.
"""

import argparse
import csv
import datetime as dt
import hashlib
import re
import time
import urllib.request
from pathlib import Path

from tennis_networks.config import ROOT
from tennis_networks.tennisdata import TENNISDATA

BASE = "https://www.tennis-data.co.uk/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
LINK = re.compile(r'href="([^"]*/(\d{4})(w?)/\d{4}\.xlsx?)"', re.IGNORECASE)
EXCEL_MAGIC = (b"\xd0\xcf\x11\xe0", b"PK\x03\x04")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--last", type=int, default=2025, help="last season to download")
    args = parser.parse_args()

    page = fetch(BASE + "alldata.php").decode("latin-1")
    links = sorted({(m.group(1), int(m.group(2)), m.group(3).lower()) for m in LINK.finditer(page)})
    rows = []
    for href, year, w in links:
        if year > args.last:
            continue
        tour = "wta" if w else "atp"
        target = TENNISDATA / tour / f"{year}{Path(href).suffix.lower()}"
        target.parent.mkdir(parents=True, exist_ok=True)
        data = fetch(BASE + href)
        if data[:4] not in EXCEL_MAGIC:
            raise ValueError(f"{href}: the response is not an Excel file")
        target.write_bytes(data)
        rows.append(
            {
                "tour": tour,
                "year": year,
                "file": target.relative_to(ROOT).as_posix(),
                "url": BASE + href,
                "downloaded": dt.date.today().isoformat(),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
        print(f"{tour} {year}: {len(data)} bytes")
        time.sleep(0.5)

    with open(TENNISDATA / "manifest.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} files in {TENNISDATA}")


if __name__ == "__main__":
    main()
