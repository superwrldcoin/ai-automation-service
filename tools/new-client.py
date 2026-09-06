#!/usr/bin/env python3
"""
new-client.py — stamp out a unique, self-contained CRM copy for one client.

Each client gets their OWN folder under docs/clients/<slug>/ containing a copy of
the app engine plus a config.json that holds their branding, trade, and prices.
Editing one client's config.json changes only THAT client's app. Improving the
master engine and re-running this updates only the clients you choose to re-stamp.

Usage:
    python tools/new-client.py --slug summit-comfort-hvac --business "Summit Comfort HVAC" \
        --trade hvac --theme "#d35400" --shop "Ocala, FL" --tax 7 --deposit 50 \
        --name "You @ Vivid Static Lab" --phone "(352) 555-0100" --email you@example.com

Then host docs/clients/<slug>/ (Netlify Drop is easiest = its own URL = fully isolated),
or it's already live at <your-pages>/clients/<slug>/ .
"""
import argparse, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

CLIENT_SW = """/* Offline cache for this client's app only. */
const CACHE='client-cache-v1';
const ASSETS=['./','./crm.html','./config.json','./manifest-crm.json',
  './icons/icon-192.png','./icons/icon-512.png','./icons/apple-touch-icon.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>Promise.all(ASSETS.map(u=>c.add(u).catch(()=>null)))).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==CACHE).map(x=>caches.delete(x)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{const r=e.request; if(r.method!=='GET'||new URL(r.url).origin!==self.location.origin)return;
  e.respondWith(caches.match(r).then(h=>h||fetch(r).then(res=>{const c=res.clone();caches.open(CACHE).then(x=>x.put(r,c)).catch(()=>{});return res;}).catch(()=>caches.match(r).then(h=>h||caches.match('./')))));});
"""

REDIRECT = ('<!DOCTYPE html><html><head><meta charset="utf-8">'
            '<meta http-equiv="refresh" content="0; url=crm.html">'
            '<link rel="canonical" href="crm.html"></head>'
            '<body>Opening your app… <a href="crm.html">tap here</a> if it doesn\'t.</body></html>')

HANDOFF_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{business} | Client handoff</title>
  <style>
    :root {{ --ink:#12212e; --accent:{theme}; --bg:#f7f9fc; --line:#e6ebf1; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; background:var(--bg); color:var(--ink); line-height:1.6; }}
    .wrap {{ max-width:760px; margin:0 auto; padding:36px 22px 60px; }}
    .card {{ background:#fff; border:1px solid var(--line); border-radius:16px; padding:24px; box-shadow:0 8px 24px rgba(18,33,46,.04); }}
    h1 {{ margin:0 0 8px; font-size:32px; }}
    .sub {{ color:#5a6b7b; margin:0 0 24px; }}
    .cta {{ display:inline-block; background:var(--accent); color:#fff; text-decoration:none; font-weight:700; padding:12px 22px; border-radius:10px; margin-bottom:20px; }}
    .meta {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin:18px 0 8px; }}
    .meta div {{ border:1px solid var(--line); border-radius:10px; padding:10px 12px; background:#f9fbff; }}
    .label {{ display:block; text-transform:uppercase; letter-spacing:.08em; font-size:11px; color:#5a6b7b; margin-bottom:4px; }}
    .list {{ margin:0; padding-left:18px; }}
    .footer {{ margin-top:18px; color:#5a6b7b; font-size:13px; }}
    @media (max-width: 640px) {{ .meta {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>{business}</h1>
      <p class="sub">Client handoff and access guide</p>
      <a class="cta" href="crm.html">Open the Business Hub</a>
      <div class="meta">
        <div><span class="label">App URL</span><strong>{client_url}</strong></div>
        <div><span class="label">Support contact</span><strong>{support_email}</strong></div>
      </div>
      <h2>What this includes</h2>
      <ul class="list">
        <li>Customer records and contact history</li>
        <li>Quote, invoice, and job pipeline</li>
        <li>Follow-up tracker for overdue and due work</li>
        <li>Editable pricebook and local settings</li>
        <li>Offline-friendly installation on the device</li>
      </ul>
      <h2>How to use</h2>
      <ol class="list">
        <li>Open the app from the link above.</li>
        <li>Use the dashboard to add customers and quote work.</li>
        <li>Generate and save a quote as PDF when ready.</li>
        <li>Use the Follow-ups view to revisit due and overdue jobs.</li>
      </ol>
      <h2>Support</h2>
      <p>Questions, updates, or help with your setup can be sent to <strong>{support_email}</strong>.</p>
      <div class="footer">Built by <strong>Vivid Static Lab</strong> · Private, local, and owner-operated.</div>
    </div>
  </div>
</body>
</html>
'''

HANDOFF_README = '''# {business}

## Client handoff

This folder contains the branded Business Hub for {business}. It is a private, local-first workflow manager built for {trade} operations.

## Access
- App URL: {client_url}
- Support: {support_email}
- Local app folder: {slug}/

## Included
- Customer list and contact records
- Quote + invoice workflow
- Follow-ups for due and overdue jobs
- Editable pricebook and settings
- Offline-capable app experience

## Notes
- Data stays local to the device and browser unless a separate backend is added later.
- For support, contact {support_email}.
- This is a handoff package for production deployment, not a full multi-user SaaS backend.
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True, help="folder name, e.g. summit-comfort-hvac")
    ap.add_argument("--business", required=True)
    ap.add_argument("--trade", default="hvac", choices=["hvac", "plumbing", "electrical", "roofing"])
    ap.add_argument("--theme", default="#1a6feb", help="accent color hex")
    ap.add_argument("--shop", default="", help="shop ZIP or city (trip-fee origin)")
    ap.add_argument("--tax", type=float, default=7)
    ap.add_argument("--deposit", type=float, default=50)
    ap.add_argument("--name", default="Vivid Static Lab", help="support contact name")
    ap.add_argument("--phone", default="")
    ap.add_argument("--email", default="hello@vividstatic.com")
    ap.add_argument("--client-url", default="", help="public URL for the client's app, defaults to the GitHub Pages pattern")
    ap.add_argument("--pricebook", default="", help="optional path to a JSON pricebook override")
    args = ap.parse_args()

    dest = DOCS / "clients" / args.slug
    (dest / "icons").mkdir(parents=True, exist_ok=True)

    # 1. copy the engine
    shutil.copy(DOCS / "crm.html", dest / "crm.html")
    for ic in ("icon-192.png", "icon-512.png", "apple-touch-icon.png", "favicon-64.png"):
        src = DOCS / "icons" / ic
        if src.exists():
            shutil.copy(src, dest / "icons" / ic)

    # 2. client manifest
    (dest / "manifest-crm.json").write_text(json.dumps({
        "name": f"{args.business} — Hub", "short_name": "Hub",
        "start_url": "./crm.html", "scope": "./", "display": "standalone",
        "orientation": "portrait", "background_color": "#12212e", "theme_color": args.theme,
        "icons": [
            {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }, indent=2), encoding="utf-8")

    # 3. client service worker + redirect
    (dest / "sw.js").write_text(CLIENT_SW, encoding="utf-8")
    (dest / "index.html").write_text(REDIRECT, encoding="utf-8")

    # 4. client handoff files
    client_url = args.client_url or f"https://superwrldcoin.github.io/ai-automation-service/clients/{args.slug}/"
    handoff_html = HANDOFF_HTML.format(
        business=args.business,
        theme=args.theme,
        client_url=client_url,
        support_email=args.email,
    )
    (dest / "client-handoff.html").write_text(handoff_html, encoding="utf-8")
    (dest / "README.md").write_text(HANDOFF_README.format(
        business=args.business,
        trade=args.trade,
        client_url=client_url,
        support_email=args.email,
        slug=args.slug,
    ), encoding="utf-8")

    # 5. the config that makes this client unique
    cfg = {
        "clientId": args.slug, "business": args.business, "trade": args.trade,
        "themeColor": args.theme, "shopZip": args.shop, "taxRate": args.tax,
        "depositPct": args.deposit,
        "contact": {"name": args.name, "phone": args.phone, "email": args.email},
        "handoff": {"url": client_url, "supportEmail": args.email}
    }
    if args.pricebook:
        cfg["pricebook"] = json.loads(Path(args.pricebook).read_text(encoding="utf-8"))
    (dest / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    print(f"Created client app: {dest}")
    print(f"  Local files : {[p.name for p in dest.iterdir()]}")
    print(f"  Live link   : {client_url}")
    print(f"  Handoff page: {dest / 'client-handoff.html'}")


if __name__ == "__main__":
    main()
