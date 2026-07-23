# DocForge — batch document generator

Turn a spreadsheet into hundreds of finished, personalized documents in seconds.
Contracts, offer letters, invoices, proposals, mail-merge letters — anything that's
"same template, different data." Pure Python standard library: no installs, no API
keys, no data ever leaves your machine.

> This is both a **portfolio proof** for the service and a **reusable deliverable** —
> it can be adapted to almost any client's document-automation job in minutes.

## Quick start
```bash
python docforge.py --data samples/leads.csv --template samples/offer_letter.html \
    --outdir output --name-by "{property_id}_{last_name}_offer"
```
Then open any file in `output/` in a browser and print-to-PDF to finalize.

## Try it without writing files
```bash
python docforge.py --data samples/leads.csv --template samples/offer_letter.html --dry-run
```

## Template syntax
| Syntax | Does |
|--------|------|
| `{{ field }}` | insert a column value |
| `{{ price \| money }}` | `250000` → `$250,000.00` |
| `{{ date \| date }}` | normalizes common date formats to `Month DD, YYYY` |
| `{{ name \| upper/lower/title }}` | change case |
| `{[ if repairs ]} ... {[ endif ]}` | show a block only when a field has a value |

## Make it yours
1. Replace `samples/leads.csv` with your data (any columns).
2. Write any template file (`.html`, `.txt`, `.md`) using the syntax above.
3. Run it. Done.

## Why clients pay for this
A person doing 200 personalized letters by hand at 4 min each = 13+ hours.
This does it in seconds, error-free, every time. That gap is the value.
