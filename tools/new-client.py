#!/usr/bin/env python3
"""
new-client.py — stamp out a unique, self-contained CRM copy for one client.

Each client gets their OWN folder under docs/clients/<slug>/ containing a copy of
the app engine plus a config.json that holds their branding, trade, and prices.
Editing one client's config.json changes only THAT client's app. Improving the
master engine and re-running this updates only the clients you choose to re-stamp.

Create a client:
    python tools/new-client.py --slug summit-comfort-hvac --business "Summit Comfort HVAC" \
        --trade hvac --theme "#d35400" --shop "Ocala, FL" --tax 7 --deposit 50 \
        --logo ~/clients/summit/logo.png \
        --biz-phone "(352) 555-0199" --biz-email office@summitcomfort.com \
        --name "You @ Vivid Static Lab" --phone "(352) 555-0100" --email you@example.com

Each client folder ends up self-contained: their app, their config, their logo, their
service worker, their handoff page, and `how-to.html` with their own link and support
address already filled in — nothing left to edit by hand before you hand it over.

Push an engine improvement out to clients (their config.json is left alone):
    python tools/new-client.py --update-engine --slug summit-comfort-hvac
    python tools/new-client.py --update-engine --all

Then host docs/clients/<slug>/ (Netlify Drop is easiest = its own URL = fully isolated),
or it's already live at <your-pages>/clients/<slug>/ .

Whose contact is whose: --biz-phone / --biz-email are the CLIENT's own details and
print on their estimates and invoices. --name / --phone / --email are OUR support
contact, shown on the app's Help screen and handoff page.
"""
import argparse, json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CLIENTS = DOCS / "clients"
ICONS = ("icon-192.png", "icon-512.png", "apple-touch-icon.png", "favicon-64.png")

# Bump this cache name whenever the engine changes, or already-installed apps
# keep serving the old crm.html from their offline cache.
CLIENT_SW = """/* Offline cache for this client's app only. */
const CACHE='client-cache-v2';
const ASSETS=['./','./crm.html','./config.json','./manifest-crm.json','./client-handoff.html','./how-to.html',
  './icons/icon-192.png','./icons/icon-512.png','./icons/apple-touch-icon.png'__EXTRA_ASSETS__];
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


def default_url(slug):
    return f"https://superwrldcoin.github.io/ai-automation-service/clients/{slug}/"


def client_guide(client_url, support_email):
    """The plain-English guide with this client's own link and support address filled in,
    so there is nothing left to edit by hand at handover time."""
    guide = (DOCS / "how-to.html").read_text(encoding="utf-8")
    guide = guide.replace("[YOUR TOOL LINK GOES HERE]", client_url)
    guide = guide.replace("hello@vividstatic.com", support_email)
    # inside a client's own folder, "All tools" just bounces back to their app
    return guide.replace(
        '<a href="crm.html">← Open your Business Hub</a> &middot; <a href="index.html">All tools</a>',
        '<a href="crm.html">← Open your Business Hub</a>')


def stamp_files(dest, slug, business, theme, trade, support_email, client_url, logo=None):
    """Write everything DERIVED from a client's config: engine, icons, manifest,
    service worker, redirect, handoff package and their filled-in guide.

    It deliberately never writes config.json, so it is safe to re-run against a
    live client to push an engine improvement without touching their settings."""
    (dest / "icons").mkdir(parents=True, exist_ok=True)

    shutil.copy(DOCS / "crm.html", dest / "crm.html")
    for ic in ICONS:
        src = DOCS / "icons" / ic
        if src.exists():
            shutil.copy(src, dest / "icons" / ic)

    (dest / "manifest-crm.json").write_text(json.dumps({
        "name": f"{business} — Hub", "short_name": "Hub",
        "start_url": "./crm.html", "scope": "./", "display": "standalone",
        "orientation": "portrait", "background_color": "#12212e", "theme_color": theme,
        "icons": [
            {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }, indent=2), encoding="utf-8")

    # keep the logo available offline too — it prints on every estimate
    extra = ",'./%s'" % logo if logo else ""
    (dest / "sw.js").write_text(CLIENT_SW.replace("__EXTRA_ASSETS__", extra), encoding="utf-8")
    (dest / "index.html").write_text(REDIRECT, encoding="utf-8")
    (dest / "how-to.html").write_text(client_guide(client_url, support_email), encoding="utf-8")
    (dest / "client-handoff.html").write_text(HANDOFF_HTML.format(
        business=business, theme=theme, client_url=client_url, support_email=support_email,
    ), encoding="utf-8")
    (dest / "README.md").write_text(HANDOFF_README.format(
        business=business, trade=trade, client_url=client_url,
        support_email=support_email, slug=slug,
    ), encoding="utf-8")


def update_engine(slugs):
    """Re-stamp existing clients with the current master engine, keeping their config.json."""
    if not slugs:
        sys.exit("No client folders under docs/clients/ — create one first.")
    for slug in slugs:
        dest = CLIENTS / slug
        cfgfile = dest / "config.json"
        if not cfgfile.exists():
            print(f"  skipped {slug} — no config.json, so it isn't a client folder")
            continue
        cfg = json.loads(cfgfile.read_text(encoding="utf-8"))
        handoff = cfg.get("handoff") or {}
        contact = cfg.get("contact") or {}
        stamp_files(
            dest, slug,
            cfg.get("business", "Business"),
            cfg.get("themeColor", "#1a6feb"),
            cfg.get("trade", "hvac"),
            handoff.get("supportEmail") or contact.get("email") or "hello@vividstatic.com",
            handoff.get("url") or default_url(slug),
            cfg.get("logo") or None,
        )
        print(f"  updated {slug} — engine, guide + handoff refreshed, config.json untouched")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", help="folder name, e.g. summit-comfort-hvac")
    ap.add_argument("--business")
    ap.add_argument("--trade", default="hvac", choices=["hvac", "plumbing", "electrical", "roofing"])
    ap.add_argument("--theme", default="#1a6feb", help="accent color hex")
    ap.add_argument("--shop", default="", help="shop ZIP or city (trip-fee origin)")
    ap.add_argument("--tax", type=float, default=7)
    ap.add_argument("--deposit", type=float, default=50)
    ap.add_argument("--biz-phone", default="", help="the CLIENT's own phone — prints on their quotes")
    ap.add_argument("--biz-email", default="", help="the CLIENT's own email — prints on their quotes")
    ap.add_argument("--logo", default="", help="path to the client's logo image — shows in their app and on their quotes")
    ap.add_argument("--name", default="Vivid Static Lab", help="support contact name (ours)")
    ap.add_argument("--phone", default="", help="support phone (ours)")
    ap.add_argument("--email", default="hello@vividstatic.com", help="support email (ours)")
    ap.add_argument("--client-url", default="", help="public URL for the client's app, defaults to the GitHub Pages pattern")
    ap.add_argument("--pricebook", default="", help="optional path to a JSON pricebook override")
    ap.add_argument("--update-engine", action="store_true",
                    help="re-stamp existing client(s) with the current engine, keeping their config.json")
    ap.add_argument("--all", action="store_true", help="with --update-engine: every client folder")
    args = ap.parse_args()

    if args.update_engine:
        if args.all:
            slugs = sorted(p.name for p in CLIENTS.iterdir() if p.is_dir()) if CLIENTS.exists() else []
        elif args.slug:
            slugs = [args.slug]
        else:
            sys.exit("--update-engine needs either --slug <name> or --all")
        print("Pushing the current engine to client app(s):")
        update_engine(slugs)
        print("Re-upload any folder hosted outside GitHub Pages (e.g. a Netlify drop).")
        return

    if not args.slug or not args.business:
        sys.exit("Creating a client needs --slug and --business "
                 "(or use --update-engine to refresh existing ones).")

    dest = CLIENTS / args.slug
    client_url = args.client_url or default_url(args.slug)

    # the client's logo lands beside their app as logo.<ext>, so it works offline
    logo_name = None
    if args.logo:
        src = Path(args.logo)
        if not src.exists():
            sys.exit(f"--logo: no such file: {src}")
        logo_name = "logo" + src.suffix.lower()
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest / logo_name)

    stamp_files(dest, args.slug, args.business, args.theme, args.trade, args.email, client_url, logo_name)

    # the config that makes this client unique
    cfg = {
        "clientId": args.slug, "business": args.business, "trade": args.trade,
        "themeColor": args.theme, "shopZip": args.shop, "taxRate": args.tax,
        "depositPct": args.deposit,
        "businessPhone": args.biz_phone, "businessEmail": args.biz_email,
        "contact": {"name": args.name, "phone": args.phone, "email": args.email},
        "handoff": {"url": client_url, "supportEmail": args.email}
    }
    if logo_name:
        cfg["logo"] = logo_name
    if args.pricebook:
        cfg["pricebook"] = json.loads(Path(args.pricebook).read_text(encoding="utf-8"))
    (dest / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    print(f"Created client app: {dest}")
    print(f"  Local files : {sorted(p.name for p in dest.iterdir())}")
    print(f"  Live link   : {client_url}")
    print(f"  Handoff page: {dest / 'client-handoff.html'}")
    print(f"  Their guide : {dest / 'how-to.html'}  (link + support email already filled in)")
    if not logo_name:
        print("  No logo     : pass --logo path/to/their-logo.png to brand the app and their quotes")


if __name__ == "__main__":
    main()
