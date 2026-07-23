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

    # 4. the config that makes this client unique
    cfg = {
        "clientId": args.slug, "business": args.business, "trade": args.trade,
        "themeColor": args.theme, "shopZip": args.shop, "taxRate": args.tax,
        "depositPct": args.deposit,
        "contact": {"name": args.name, "phone": args.phone, "email": args.email},
    }
    if args.pricebook:
        cfg["pricebook"] = json.loads(Path(args.pricebook).read_text(encoding="utf-8"))
    (dest / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    print(f"Created client app: {dest}")
    print(f"  Local files : {[p.name for p in dest.iterdir()]}")
    print(f"  Live link   : <your-pages>/clients/{args.slug}/  (or drag this folder to app.netlify.com/drop)")


if __name__ == "__main__":
    main()
