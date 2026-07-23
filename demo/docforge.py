#!/usr/bin/env python3
"""
DocForge - batch document generator for small-business operators.

Turn a spreadsheet (CSV) of records + one template into hundreds of
finished, personalized documents: contracts, offer letters, invoices,
proposals, mail-merge letters, listing sheets, you name it.

Pure standard library. No installs, no API keys, no data leaves the machine.

Usage:
    python docforge.py --data samples/leads.csv --template samples/offer_letter.html --outdir output
    python docforge.py --data samples/leads.csv --template samples/offer_letter.html --outdir output --name-by "{property_id}_{last_name}"
    python docforge.py --data samples/leads.csv --template samples/offer_letter.html --dry-run

Template syntax:
    {{ field }}                         -> value from the CSV row
    {{ price | money }}                 -> 250000 becomes $250,000.00
    {{ close_date | date }}             -> normalizes common date formats
    {{ name | upper }} / | lower / | title
    {[ if repairs ]} ... {[ endif ]}    -> block shown only if 'repairs' has a value
"""

import argparse
import csv
import datetime as dt
import re
import sys
from pathlib import Path

FIELD_RE = re.compile(r"\{\{\s*([\w]+)\s*(?:\|\s*([\w]+)\s*)?\}\}")
IF_RE = re.compile(r"\{\[\s*if\s+([\w]+)\s*\]\}(.*?)\{\[\s*endif\s*\]\}", re.DOTALL)


def money(value):
    try:
        return "${:,.2f}".format(float(str(value).replace(",", "").replace("$", "")))
    except (ValueError, TypeError):
        return value


def normalize_date(value):
    value = str(value).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%B %d, %Y", "%m/%d/%y"):
        try:
            return dt.datetime.strptime(value, fmt).strftime("%B %d, %Y")
        except ValueError:
            continue
    return value  # leave untouched if we can't parse it


FILTERS = {
    "money": money,
    "date": normalize_date,
    "upper": lambda v: str(v).upper(),
    "lower": lambda v: str(v).lower(),
    "title": lambda v: str(v).title(),
}


def render(template, row):
    """Render one template against one row of data."""
    # 1. resolve conditional blocks first
    def if_sub(m):
        field, block = m.group(1), m.group(2)
        return block if str(row.get(field, "")).strip() else ""
    text = IF_RE.sub(if_sub, template)

    # 2. resolve fields + filters
    missing = set()

    def field_sub(m):
        field, filt = m.group(1), m.group(2)
        if field not in row:
            missing.add(field)
            return m.group(0)
        val = row[field]
        if filt and filt in FILTERS:
            val = FILTERS[filt](val)
        return str(val)

    return FIELD_RE.sub(field_sub, text), missing


def safe_name(pattern, row, index, ext):
    try:
        name = pattern.format(**row)
    except (KeyError, IndexError):
        name = f"document_{index:03d}"
    name = re.sub(r"[^\w\-.]+", "_", name).strip("_") or f"document_{index:03d}"
    return f"{name}{ext}"


def main():
    ap = argparse.ArgumentParser(description="Batch document generator.")
    ap.add_argument("--data", required=True, help="Path to CSV data file")
    ap.add_argument("--template", required=True, help="Path to template file")
    ap.add_argument("--outdir", default="output", help="Output directory")
    ap.add_argument("--name-by", default="document_{__index__}",
                    help="Filename pattern using CSV columns, e.g. '{property_id}_{last_name}'")
    ap.add_argument("--dry-run", action="store_true", help="Validate without writing files")
    args = ap.parse_args()

    data_path = Path(args.data)
    tpl_path = Path(args.template)
    if not data_path.exists():
        sys.exit(f"ERROR: data file not found: {data_path}")
    if not tpl_path.exists():
        sys.exit(f"ERROR: template file not found: {tpl_path}")

    template = tpl_path.read_text(encoding="utf-8")
    ext = tpl_path.suffix or ".txt"

    with data_path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        sys.exit("ERROR: no rows found in data file.")

    outdir = Path(args.outdir)
    if not args.dry_run:
        outdir.mkdir(parents=True, exist_ok=True)

    all_missing = set()
    written = 0
    for i, row in enumerate(rows, 1):
        row["__index__"] = f"{i:03d}"
        rendered, missing = render(template, row)
        all_missing |= missing
        fname = safe_name(args.name_by, row, i, ext)
        if args.dry_run:
            print(f"  [dry-run] would write {fname}")
        else:
            (outdir / fname).write_text(rendered, encoding="utf-8")
            written += 1

    print("-" * 52)
    print(f"Records processed : {len(rows)}")
    print(f"Documents written : {written if not args.dry_run else 0}"
          f"{'  (dry-run)' if args.dry_run else ''}")
    if all_missing:
        print(f"WARNING: template referenced fields not in CSV: "
              f"{', '.join(sorted(all_missing))}")
    if not args.dry_run:
        print(f"Output folder     : {outdir.resolve()}")
        print("Tip: open any .html file in a browser and print-to-PDF to finalize.")


if __name__ == "__main__":
    main()
