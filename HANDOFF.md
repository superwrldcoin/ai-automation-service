# Project Handoff / Context Brief — Vivid Static Lab

> Paste this file (or share the repo) into a new Claude chat to continue planning without
> re-explaining everything. It captures the strategy, decisions, architecture, current
> state, and open next steps as of **2026-07-27**.

---

## 1. What this is
**Vivid Static Lab** sells a **done-for-you automation service** to small businesses. The
flagship product is a **"Business Hub" CRM** built as a single offline web app that each
client owns outright — no subscription, data stays on their device.

- **Live site (sales + demo):** https://superwrldcoin.github.io/ai-automation-service/
- **Repo:** https://github.com/superwrldcoin/ai-automation-service
- **Brand name:** Vivid Static Lab · **Contact email:** hello@vividstatic.com
- Keep GitHub links OFF client-facing pages (share repo separately on request only).

## 2. The thesis
The scarce resource is converting AI leverage into something people pay for. We build
revenue-capable assets at near-zero marginal cost and sell the **outcome**, not software.
Rules: legal + honest only; no fantasy autonomy (the human — the operator — collects money
and does outreach; the build side is automated).

## 3. Niche decision (committed): Home Services / Skilled Trades
Beachhead: **HVAC + plumbing + electrical**. Why: most AI-proof sector (91/100 resistance),
recession-proof ($543B–$842B US market), ~500k open jobs / time-starved operators, low
software adoption (barriers = "cost & complexity"), and a hard ROI hook — contractors lose
up to **$62k/yr to admin** and **~20% of revenue** to un-followed-up verbal quotes.

## 4. Differentiation thesis (vs Docupilot/Housecall Pro/ServiceTitan/Jobber)
We don't out-feature funded SaaS. We win on the **model**: done-for-you (not DIY),
**own-it-once** (no subscription/metering), data stays private/local, built to their exact
workflow, and a human (us) who knows their setup. Positioning: *"Own your automation. Don't
rent it."* No-brainer offer = free working sample on their real data + a guarantee.

## 5. Architecture — how each client stays unique
- **One master engine** (`docs/crm.html`) + a per-client **`config.json`** (business name,
  trade, theme color, pricebook, shop location, tax, deposit, support contact).
- Data uses storage key `crm_<clientId>` → never collides. Data is per-device localStorage.
- **Generator:** `python tools/new-client.py --slug ... --business ... --trade ...` stamps a
  self-contained copy into `docs/clients/<slug>/` (engine + config + own manifest + own sw).
- Editing a client's config changes only that client. Improving the master → re-stamp to push.
- **Hosting options:** folder on one free site (data still isolated) · free Netlify subdomain ·
  custom domain (upsell). Live sample: `/clients/summit-comfort-hvac/` (orange theme).
- **Offline + installable:** PWA manifests + `sw.js` service worker; installs as a phone icon.

## 6. Everything a client receives (deliverables)
**The branded Business Hub CRM** with: Home dashboard (KPIs, today's follow-ups, upcoming
jobs), Customers (records + history), Quotes & Jobs pipeline (lead→quoted→won→lost),
New-quote builder (pricebook line items + live address geocode → auto trip fee + Estimate/
Invoice PDF), Follow-ups (at-risk revenue, due/overdue, won/lost/snooze), Schedule, Settings
(editable pricebook), Help (with support email), and JSON backup/restore.
**Plus onboarding:** home-screen app icon, offline use, the plain-English client guide
(`docs/how-to.html`), a walkthrough video (operator records), and day-2/day-7 check-ins.

## 7. Repo map
- `docs/` = the live site (GitHub Pages). Key files: `index.html` (storefront),
  `crm.html` (CRM engine), `demo.html` (standalone quote builder + smart file analyzer),
  `tracker.html`, `why-us.html` (positioning + ROI calc), `how-to.html` (client guide),
  `sw.js`, `manifest*.json`, `icons/`, `clients/<slug>/` (per-client copies).
- `tools/new-client.py` = client generator.
- `outreach/` = `gig-copy.md`, `cold-outreach.md`, `demo-script.md`, `delivery-playbook.md`.
- `OPERATION.md` = the operating plan.

## 8. Current state (2026-07-27)
Product + delivery system are built, live, and audited (all pages 200, links resolve, JS
validated, PWA/offline working). Grade: A–. **Not yet distributed to real clients.**

## 9. Open items / next steps
1. **Distribution (the real bottleneck):** find + contact the first ~20 HVAC/plumbing shops,
   offer the free sample. This is the operator's job — see `outreach/`.
2. Optionally merge the **smart file analyzer** (paste text / upload CSV·PDF → auto-quote)
   from `demo.html` into the CRM's new-quote builder.
3. Paid upgrades to build when a client says yes: **AI document reading** (Claude API — needs
   a small backend + key = first thing worth spending money on), **property-data enrichment**
   (ATTOM/Estated), **custom domain** setup.
4. Optional: pre-loaded sample workspace for demos; a "What's included" one-pager PDF.

## 10. Notes for a planning chat
- Don't rebuild what exists — read the repo first.
- The operator is technical, time-rich, cash-poor; optimize for zero-cost, high-leverage moves.
- Verify any file/flag still exists before recommending it (this brief may age).
