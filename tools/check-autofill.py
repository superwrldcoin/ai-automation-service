#!/usr/bin/env python3
"""
check-autofill.py — tests for the CRM's quote auto-fill matcher.

    python tools/check-autofill.py

The matcher lives in `docs/crm.html` (the auto-fill block near the quote builder).
The site is plain static HTML with no test runner and no Node dependency, so the
matcher's logic is mirrored here in Python and run against realistic job
descriptions. This is how the price-read-as-quantity and dropped-ZIP bugs were
caught, so it earns its keep.

A mirror can drift from the original, so the second half of this script reads the
regexes and lookup tables straight back out of `docs/crm.html` and asserts they
are character-for-character what was tested. If you change the matcher in the
HTML, run this: it fails loudly on drift rather than quietly testing stale rules.

Exit code 0 = cases pass and the HTML matches. Anything else = look at the output.
"""
import io
import re
import sys
from pathlib import Path

CRM = Path(__file__).resolve().parents[1] / "docs" / "crm.html"

# --------------------------------------------------------------------------
# Mirror of the matcher in docs/crm.html
# --------------------------------------------------------------------------
SYN = {
 'AC tune-up & maintenance':['tune-up','tune up','tuneup','maintenance','not cooling','service the ac'],
 'Refrigerant recharge (per lb)':['refrigerant','freon','recharge','low coolant','low on coolant'],
 'New 3-ton AC system installed':['new system','new ac','replace ac','install ac','new unit','replace the unit','system replacement'],
 'Smart thermostat install':['thermostat','nest','ecobee'],
 'Capacitor replacement':['capacitor'],'Duct cleaning':['duct'],'Blower motor replacement':['blower'],
 'Condenser fan motor':['condenser','fan motor'],'Diagnostic / service call':['diagnostic','service call','not working','inspect'],
 '40-gal water heater install':['water heater'],'Tankless water heater install':['tankless'],
 'Main drain cleaning':['drain','clog','clogged','snake the'],'Toilet replacement':['toilet'],
 'Faucet replacement':['faucet'],'Sump pump replacement':['sump'],'Leak detection':['leak'],
 'Repipe (per fixture)':['repipe','re-pipe'],'Service call / diagnostic':['service call','diagnostic','inspect'],
 '200A panel upgrade':['panel','breaker box','service upgrade'],'EV charger install':['ev charger','ev charging','tesla charger','car charger'],
 'Ceiling fan install':['ceiling fan'],'Recessed lighting (per fixture)':['recessed','can light','lighting'],
 'Whole-home surge protector':['surge'],'Generator transfer switch':['generator','transfer switch'],
 'Outlet / switch replacement':['outlet','receptacle','gfci','light switch'],
 'Full reroof (avg home)':['reroof','new roof','replace roof','roof replacement'],
 'Shingle replacement (per square)':['shingle'],'Minor roof repair':['roof repair','repair roof','roof leak'],
 'Gutter replacement (per ft)':['gutter'],'Skylight install':['skylight'],
 'Attic ventilation':['attic','ventilation','soffit vent'],'Roof inspection':['roof inspection','inspect roof'],
 'Flashing repair':['flashing'],
}
CONFLICT = [('Tankless water heater install', '40-gal water heater install')]
STOPW = ['install','installed','installation','replace','replacement','replaced','service','call',
         'home','with','per','whole','system','unit','your']
NUMWORD = {'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,
           'ten':10,'eleven':11,'twelve':12,'fifteen':15,'twenty':20}

# the exact regex sources that must also appear in docs/crm.html
P_LB      = r"\b(\d{1,4}(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty)\s*(?:lbs?\b|pounds?\b)"
P_FT      = r"\b(\d{1,5}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty)\s*(?:ft\b|feet\b|foot\b|lf\b|linear\b)"
P_SQUARE  = r"\b(\d{1,4}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty)\s*squares?\b"
P_FIXTURE = r"\b(\d{1,3}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty)\s*(?:fixtures?|outlets?|receptacles?|cans?|lights?)\b"
P_QTY_BEFORE = r"(?:^|[^\d.$])(\d{1,3})\s*(?:x\s*)?[a-z]{0,12}\s*$"
P_NUMWORD_BEFORE = r"([a-z]+)\s+$"
P_ADDR = (r"\d{1,6}\s+[\w.'-]+(?:\s+[\w.'-]+){0,4}\s+"
          r"(?:st|street|ave|avenue|rd|road|dr|drive|blvd|boulevard|ln|lane|ct|court|way|pl|place|"
          r"ter|terrace|cir|circle|pkwy|parkway|hwy|highway|trl|trail)\b\.?"
          r"(?:\s*(?:apt|unit|ste|#)\s*[\w-]+)?"
          r"(?:,\s*[A-Za-z][A-Za-z .'-]{0,24}[A-Za-z])?(?:,?\s*[A-Z]{2}\b)?(?:,?\s*\d{5}(?:-\d{4})?)?")
P_PHONE = r"(?:\+?1[\s.-]?)?\(?\b\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"
P_EMAIL = r"[\w.+-]+@[\w-]+\.[\w.]{2,}"
P_PRICED = r"^[-*•\d.)\s]*([A-Za-z][^$]{2,70}?)\s*[:\-–—]?\s*\$\s?([\d,]+(?:\.\d{1,2})?)$"
P_NAME_LABEL = r"(?:[Cc]ustomer|[Cc]lient|[Cc]ontact|[Nn]ame)\s*[:\-]\s*([A-Z][\w'’-]+(?:\s+[A-Z][\w'’-]+){0,2})"

UNITRE = {'lb': re.compile(P_LB), 'ft': re.compile(P_FT),
          'square': re.compile(P_SQUARE), 'fixture': re.compile(P_FIXTURE)}
ADDR_RE = re.compile(P_ADDR, re.I)
PHONE_RE = re.compile(P_PHONE)
EMAIL_RE = re.compile(P_EMAIL)

# the four stock pricebooks, plus a stand-in for services a client adds themselves
BOOKS = {
 'hvac': [('Diagnostic / service call',89),('AC tune-up & maintenance',129),('Refrigerant recharge (per lb)',95),
          ('Capacitor replacement',189),('Condenser fan motor',475),('Blower motor replacement',650),
          ('Smart thermostat install',325),('Duct cleaning',450),('New 3-ton AC system installed',6800)],
 'plumbing': [('Service call / diagnostic',79),('Main drain cleaning',250),('Leak detection',225),
              ('Faucet replacement',185),('Toilet replacement',375),('Sump pump replacement',650),
              ('40-gal water heater install',1850),('Tankless water heater install',3900),('Repipe (per fixture)',450)],
 'electrical': [('Service call / diagnostic',95),('Outlet / switch replacement',145),('Ceiling fan install',185),
                ('Recessed lighting (per fixture)',125),('Whole-home surge protector',325),('EV charger install',1250),
                ('Generator transfer switch',950),('200A panel upgrade',2400)],
 'roofing': [('Roof inspection',150),('Flashing repair',325),('Minor roof repair',450),('Attic ventilation',550),
             ('Skylight install',850),('Gutter replacement (per ft)',12),('Shingle replacement (per square)',375),
             ('Full reroof (avg home)',9500)],
 'client-added': [('Crawlspace dehumidifier setup', 900), ('Attic insulation top-up', 1200)],
}


def item_words(name):
    if name in SYN:
        return SYN[name]
    stripped = re.sub(r'\([^)]*\)', ' ', name.lower())
    return [w for w in re.split(r'[^a-z0-9]+', stripped) if len(w) > 3 and w not in STOPW]


def qty_for(low, word, name):
    idx = low.find(word)
    if idx < 0:
        return 1
    m_per = re.search(r'\(per\s+([a-z]+)', name.lower())
    per = m_per.group(1) if m_per else None
    if per and per in UNITRE:
        m = UNITRE[per].search(low[max(0, idx - 45): idx + len(word) + 45])
        if m:
            tok = m.group(1)
            n = NUMWORD.get(tok, 0) or (round(float(tok)) if re.match(r'^[\d.]+$', tok) else 0)
            if 0 < n < 10000:
                return n
    before = low[max(0, idx - 16): idx]
    d = re.search(P_QTY_BEFORE, before)
    if d:
        n = int(d.group(1))
        if 0 < n < 100:
            return n
    w = re.search(P_NUMWORD_BEFORE, before)
    if w and w.group(1) in NUMWORD:
        return NUMWORD[w.group(1)]
    return 1


def match_pricebook(text, items):
    low = ' ' + re.sub(r'\s+', ' ', str(text).lower()) + ' '
    hits = []
    for i, (name, price) in enumerate(items):
        word = next((k for k in item_words(name) if k and low.find(k) >= 0), None)
        if word:
            hits.append({'i': i, 'name': name, 'qty': qty_for(low, word, name), 'price': price})
    for win, lose in CONFLICT:
        if any(h['name'] == win for h in hits):
            hits = [h for h in hits if h['name'] != lose]
    return hits


def extract_priced_lines(text, taken):
    out, seen = [], set()
    for raw in re.split(r'[\n\r;•]+', str(text)):
        line = re.sub(r'\s+', ' ', raw).strip()
        if len(line) < 4 or len(line) > 140:
            continue
        m = re.match(P_PRICED, line)
        if not m:
            continue
        name = re.sub(r'[\s.:\-–—]+$', '', m.group(1)).strip()
        price = float(m.group(2).replace(',', ''))
        if not name or not price > 0:
            continue
        key = name.lower()
        if key in seen or key in taken:
            continue
        seen.add(key)
        out.append({'name': name, 'price': price, 'qty': 1})
    return out[:12]


def extract_contact(text, customers=()):
    out = {}
    flat = re.sub(r'\s+', ' ', str(text)).strip()
    low = flat.lower()
    known = next((c for c in customers if c.get('name') and len(c['name'].strip()) > 2
                  and low.find(c['name'].strip().lower()) >= 0), None)
    if known:
        out['customerId'] = known['id']
        out['name'] = known['name']
    if 'name' not in out:
        pats = [P_NAME_LABEL,
                r"\b([A-Z][a-z'’-]+\s+[A-Z][a-z'’-]+)\s+(?:at|lives|needs|wants|called|asked)\b",
                r"^([A-Z][a-z'’-]+\s+[A-Z][a-z'’-]+)\b"]
        for p in pats:
            m = re.search(p, flat)
            if m:
                out['name'] = m.group(1).strip()
                break
    a = ADDR_RE.search(flat)
    if a:
        out['addr'] = re.sub(r'\s+,', ',', a.group(0)).strip()
    p = PHONE_RE.search(flat)
    if p:
        out['phone'] = p.group(0).strip()
    e = EMAIL_RE.search(flat)
    if e:
        out['email'] = e.group(0).strip()
    return out


# --------------------------------------------------------------------------
# Cases. Each one is something an operator would plausibly paste in.
# --------------------------------------------------------------------------
CASES = [
 dict(label='a texted job description', trade='hvac',
      text="Dana Whitmore at 1012 NE 1st Ave, Gainesville FL 32601 - needs an AC tune-up, "
           "2 smart thermostats and duct cleaning. Call (352) 555-0142.",
      want_items={'AC tune-up & maintenance':1,'Smart thermostat install':2,'Duct cleaning':1},
      want=dict(name='Dana Whitmore', phone='(352) 555-0142',
                addr='1012 NE 1st Ave, Gainesville FL 32601')),
 dict(label='number words, units, capitalised label', trade='hvac',
      text="Customer: Ray Holt. Add four lbs of refrigerant, replace the capacitor, "
           "and the blower motor is shot. 88 SW 3rd Street, Ocala FL",
      want_items={'Refrigerant recharge (per lb)':4,'Capacitor replacement':1,'Blower motor replacement':1},
      want=dict(name='Ray Holt', addr='88 SW 3rd Street, Ocala FL')),
 dict(label='roofing squares and linear feet', trade='roofing',
      text="18 squares of shingle replacement plus 120 ft of gutter and a roof inspection.",
      want_items={'Shingle replacement (per square)':18,'Gutter replacement (per ft)':120,'Roof inspection':1},
      want=dict()),
 dict(label='counted fixtures', trade='electrical',
      text="Needs 6 outlets swapped, 3 ceiling fans, and a 200A panel upgrade. jane.doe@mail.com",
      want_items={'Outlet / switch replacement':6,'Ceiling fan install':3,'200A panel upgrade':1},
      want=dict(email='jane.doe@mail.com')),
 dict(label='tankless wins over the 40-gal', trade='plumbing',
      text="Replace the old tankless water heater; also a leaking faucet.",
      want_items={'Tankless water heater install':1,'Faucet replacement':1,'Leak detection':1},
      want=dict()),
 dict(label='inspection report: a price is not a quantity', trade='hvac',
      text="Findings:\n- Replace flue pipe - $240\n- Seal return plenum - $180.50\n"
           "- Duct cleaning recommended\nTotal noted below",
      want_items={'Duct cleaning':1},
      want_priced=['Replace flue pipe','Seal return plenum']),
 dict(label='a known customer beats the name regex', trade='hvac',
      text="Follow up with Marcus Bell about the condenser fan motor.",
      customers=[{'id':'c1','name':'Marcus Bell'}],
      want_items={'Condenser fan motor':1},
      want=dict(name='Marcus Bell', customerId='c1')),
 dict(label='a ZIP is not a quantity', trade='hvac',
      text="Job at 40 Oak Lane, Newberry FL 32669 thermostat install",
      want_items={'Smart thermostat install':1},
      want=dict(addr='40 Oak Lane, Newberry FL 32669')),
 dict(label="client-added services match on their own words", trade='client-added',
      text="Wants the crawlspace dehumidifier sorted and attic insulation topped up.",
      want_items={'Crawlspace dehumidifier setup':1,'Attic insulation top-up':1},
      want=dict()),
 dict(label='apartment address, 2x shorthand', trade='hvac',
      text="Priya Raman needs 2x smart thermostats at 12 Main St Apt 4B, Tampa FL 33601",
      want_items={'Smart thermostat install':2},
      want=dict(name='Priya Raman', addr='12 Main St Apt 4B, Tampa FL 33601')),
 dict(label='nothing to match, nothing invented', trade='hvac',
      text="Left a voicemail, will call back tomorrow.",
      want_items={}, want=dict()),
]


def run_cases():
    fails = 0
    for c in CASES:
        hits = match_pricebook(c['text'], BOOKS[c['trade']])
        got = {h['name']: h['qty'] for h in hits}
        contact = extract_contact(c['text'], c.get('customers', []))
        priced = extract_priced_lines(c['text'], [h['name'].lower() for h in hits])
        problems = []
        if got != c['want_items']:
            problems.append('items: got %r want %r' % (got, c['want_items']))
        for k, v in c.get('want', {}).items():
            if contact.get(k) != v:
                problems.append('%s: got %r want %r' % (k, contact.get(k), v))
        if 'want_priced' in c:
            names = [p['name'] for p in priced]
            if names != c['want_priced']:
                problems.append('priced: got %r want %r' % (names, c['want_priced']))
        fails += 1 if problems else 0
        print('  %s  %s' % ('pass' if not problems else 'FAIL', c['label']))
        for p in problems:
            print('        >>', p)
    print('  %d case(s), %d failing' % (len(CASES), fails))
    return fails


# --------------------------------------------------------------------------
# Drift guard: the same rules must be in docs/crm.html
# --------------------------------------------------------------------------
def check_html():
    if not CRM.exists():
        print('  cannot find %s' % CRM)
        return 1
    html = io.open(CRM, encoding='utf-8').read()

    def line_from(anchor):
        i = html.index(anchor)
        return html[i:html.index('\n', i)]

    def between(line, start, end):
        return line[line.index(start) + len(start): line.rindex(end)]

    checks = []
    for key, want in (('lb', P_LB), ('ft', P_FT), ('square', P_SQUARE), ('fixture', P_FIXTURE)):
        line = line_from('  %s:/' % key)
        checks.append((key + ' unit', between(line, '/', '/'), want))
    checks.append(('ADDR_RE', between(line_from('const ADDR_RE='), '/', '/i'), P_ADDR))
    checks.append(('PHONE_RE', between(line_from('const PHONE_RE='), '/', '/'), P_PHONE))
    checks.append(('EMAIL_RE', between(line_from('const EMAIL_RE='), '/', '/'), P_EMAIL))
    checks.append(('qty-before', between(line_from('  const d=before.match('), '(/', '/)'), P_QTY_BEFORE))
    checks.append(('numword-before', between(line_from('  const w=before.match('), '(/', '/)'), P_NUMWORD_BEFORE))
    checks.append(('priced-line', between(line_from('    const m=line.match('), '(/', '/)'), P_PRICED))
    checks.append(('name-label', between(line_from('    const pats=['), '[/', '/,'), P_NAME_LABEL))

    numword_line = line_from('const NUMWORD=')
    html_numword = {k.strip(): int(v) for k, v in
                    (p.split(':') for p in between(numword_line, '{', '}').split(','))}
    checks.append(('NUMWORD', html_numword, NUMWORD))
    checks.append(('STOPW', re.findall(r"'([^']*)'", line_from('const STOPW=')), STOPW))

    html_syn = {}
    blk = html[html.index('const SYN={'): html.index('/* when both match')]
    for m in re.finditer(r"'([^']+)':\[([^\]]*)\]", blk):
        html_syn[m.group(1)] = re.findall(r"'([^']*)'", m.group(2))
    checks.append(('SYN table', html_syn, SYN))

    bad = 0
    for name, got, want in checks:
        if got == want:
            print('  ok    %s' % name)
        else:
            bad += 1
            print('  DRIFT %s' % name)
            print('        html: %r' % (got,))
            print('        here: %r' % (want,))

    # every stock service needs synonyms, or it silently stops matching
    stock = {n for t in ('hvac', 'plumbing', 'electrical', 'roofing') for n, _ in BOOKS[t]}
    gaps = sorted(n for n in stock if n not in SYN)
    if gaps:
        bad += 1
        print('  GAP   stock services with no synonyms: %s' % gaps)
    else:
        print('  ok    synonym coverage (%d stock services)' % len(stock))
    return bad


if __name__ == '__main__':
    print('Auto-fill cases:')
    failed = run_cases()
    print('\nAgainst docs/crm.html:')
    drift = check_html()
    print()
    if failed or drift:
        print('FAILED — %d case(s) wrong, %d drift/gap issue(s)' % (failed, drift))
        sys.exit(1)
    print('All good.')
