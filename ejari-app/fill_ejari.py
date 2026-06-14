"""
fill_ejari.py — Ejari Unified Tenancy Contract PDF filler
All coordinates pixel-verified at 1000px render height against official DLD template.
"""

from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter
import io

PAGE_W, PAGE_H = 596, 842

# ── Verified reportlab y (from bottom) for each field's dotted baseline ──
F = {
    'date':            725.8,
    'ownerName':       667.7,
    'lessorName':      645.0,
    'lessorEID':       621.4,   # corrected: y=262 → rl_y=621.4
    'licenseNo':       591.1,
    'licensingAuth':   591.1,
    'lessorEmail':     574.2,
    'lessorPhone':     553.2,
    'tenantName':      497.6,
    'tenantEID':       474.0,   # corrected: y=437 → rl_y=474.0
    'tenantEmail':     426.9,
    'tenantPhone':     405.0,
    # property
    'plotNo':          325.0,
    'makaniNo':        323.3,
    'buildingName':    302.3,
    'propertyNo':      300.6,   # corrected: y=643 → rl_y=300.6
    'propertyType':    277.9,
    'propertyArea':    277.0,   # corrected: y=670 → rl_y=277.0 (best of 668-672)
    'location':        256.8,
    'dewaPremises':    255.1,   # corrected: y=697 → rl_y=255.1
    # contract
    'contractFrom':    187.8,
    'contractTo':      187.8,
    'contractValue':   196.2,
    'annualRent':      186.9,
    'securityDeposit': 174.3,
    'modeOfPayment':   152.4,
}

# ── Entry field x-start positions (verified) ──
# EID fields: label ends at pdf_x~105, entry starts at 110, Arabic label starts at ~494
# Property right column: label ends ~348, Arabic starts ~534 (PropertyNo), ~492 (Area), ~379 (DEWA)
X = {
    'lessorEID_start':    110,   # after 'Lessor's Emirates ID' label
    'lessorEID_mid':      298,   # midpoint for 2nd EID (110+494)/2 + gap
    'lessorEID_end':      490,   # before Arabic label
    'tenantEID_start':    110,
    'tenantEID_mid':      298,
    'tenantEID_end':      490,
    'propertyNo_x':       350,   # after 'Property No.' label end (~348)
    'propertyArea_x':     350,   # after 'Property Area' label
    'dewaPremises_x':     350,   # after 'Premises No. (DEWA)' label - Arabic starts at 379 so tight
    'ownerName_x':        110,   # after 'Owner's Name' label
    'ownerName2_x':       300,   # 2nd owner name in same row
}

# ── Radio circle centers (pdf_x, rl_y) — pixel verified ──
# Circles at y≈582-593px → center y≈587px → rl_y = 842 - 587/1.187 = 842 - 494.5 = 347.5
USAGE = {
    'residential': (180.5 / (707/596), 347.5),   # px center 180.5 → pdf_x 152.2
    'commercial':  (307.0 / (707/596), 347.5),   # px center 307 → pdf_x 258.8
    'industrial':  (441.0 / (707/596), 347.5),   # px center 441 → pdf_x 371.8
}
# Recalculate cleanly:
_sx = 707 / 596
USAGE = {
    'industrial':  (180.5 / _sx, 347.5),   # leftmost circle
    'commercial':  (307.0 / _sx, 347.5),   # middle circle
    'residential': (441.0 / _sx, 347.5),   # rightmost circle
}


def _draw(c, text, x, rl_y, maxw=None, fs=8):
    text = str(text or '').strip()
    if not text:
        return
    c.setFont("Helvetica", fs)
    if maxw:
        while len(text) > 1 and c.stringWidth(text, "Helvetica", fs) > maxw:
            text = text[:-1]
    c.drawString(x, rl_y, text)


def fill_ejari_pdf(data: dict, template_path: str) -> bytes:
    """
    Fill the Ejari Unified Tenancy Contract.

    data['landlords'] = list of {name, lessorName, emiratesId, email, phone, licenseNo, licensingAuth}
    data['tenants']   = list of {name, emiratesId, email, phone}
    All other keys: date, propertyUsage, location, buildingName, propertyNo, propertyType,
                    propertyArea, plotNo, makaniNo, dewaPremises,
                    contractFrom, contractTo, contractValue, annualRent,
                    securityDeposit, modeOfPayment
    """
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(PAGE_W, PAGE_H))
    c.setFillColorRGB(0, 0, 0)

    def d(val, x, key, maxw=None, fs=8):
        _draw(c, val, x, F[key], maxw, fs)

    # ── Date ──────────────────────────────────────────────────────────
    d(data.get('date', ''), 30, 'date')

    # ── Landlords ─────────────────────────────────────────────────────
    landlords = data.get('landlords') or [{}]
    ll = landlords[0]
    owner1 = ll.get('name', '')

    # Owner's Name row: if 2+ landlords, show both names separated
    if len(landlords) >= 2:
        owner2 = landlords[1].get('name', '')
        _draw(c, owner1, X['ownerName_x'], F['ownerName'],  maxw=175, fs=8)
        _draw(c, owner2, X['ownerName2_x'], F['ownerName'], maxw=175, fs=8)
        # Lessor name row: same treatment
        _draw(c, owner1, X['ownerName_x'], F['lessorName'],  maxw=175, fs=8)
        _draw(c, owner2, X['ownerName2_x'], F['lessorName'], maxw=175, fs=8)
    else:
        d(owner1, X['ownerName_x'], 'ownerName',  maxw=360)
        d(ll.get('lessorName', owner1), X['ownerName_x'], 'lessorName', maxw=360)

    # EID row: primary EID left, 2nd EID right (if present)
    eid1 = ll.get('emiratesId', '')
    if eid1:
        _draw(c, eid1, X['lessorEID_start'], F['lessorEID'], maxw=175, fs=8)
    if len(landlords) >= 2:
        eid2 = landlords[1].get('emiratesId', '')
        if eid2:
            _draw(c, eid2, X['lessorEID_mid'], F['lessorEID'], maxw=175, fs=8)

    d(ll.get('licenseNo', ''),    90, 'licenseNo',    maxw=155)
    d(ll.get('licensingAuth', ''), 376, 'licensingAuth', maxw=84)
    d(ll.get('email', ''),         90, 'lessorEmail',  maxw=370)
    d(ll.get('phone', ''),         90, 'lessorPhone',  maxw=370)

    # 3rd+ landlords: small annotation line below phone
    if len(landlords) > 2:
        c.setFont("Helvetica-Bold", 6.5)
        c.setFillColorRGB(0.1, 0.2, 0.6)
        base_y = F['lessorPhone'] - 11
        for i, extra in enumerate(landlords[2:], 3):
            note = (f"+ Landlord {i}: {extra.get('name','')}  "
                    f"ID: {extra.get('emiratesId','')}  {extra.get('phone','')}")
            c.drawString(90, base_y - (i - 3) * 9, note)
        c.setFillColorRGB(0, 0, 0)

    # ── Tenants ────────────────────────────────────────────────────────
    tenants = data.get('tenants') or [{}]
    tt = tenants[0]
    d(tt.get('name', ''), 90, 'tenantName', maxw=370)

    # Tenant EID: primary left, 2nd right
    teid1 = tt.get('emiratesId', '')
    if teid1:
        _draw(c, teid1, X['tenantEID_start'], F['tenantEID'], maxw=175, fs=8)
    if len(tenants) >= 2:
        teid2 = tenants[1].get('emiratesId', '')
        if teid2:
            _draw(c, teid2, X['tenantEID_mid'], F['tenantEID'], maxw=175, fs=8)

    d(tt.get('email', ''), 90, 'tenantEmail', maxw=370)
    d(tt.get('phone', ''), 90, 'tenantPhone', maxw=370)

    # 2nd+ tenant names annotation below phone (names + IDs for extra tenants)
    if len(tenants) > 1:
        c.setFont("Helvetica-Bold", 6.5)
        c.setFillColorRGB(0.1, 0.2, 0.6)
        base_y = F['tenantPhone'] - 11
        for i, extra in enumerate(tenants[1:], 2):
            note = (f"+ Tenant {i}: {extra.get('name','')}  "
                    f"ID: {extra.get('emiratesId','')}  {extra.get('phone','')}")
            c.drawString(90, base_y - (i - 2) * 9, note)
        c.setFillColorRGB(0, 0, 0)

    # ── Property Usage — X inside the correct circle ───────────────────
    usage = str(data.get('propertyUsage', 'residential')).lower()
    if usage in USAGE:
        ux, uy = USAGE[usage]
        c.setFont("Helvetica-Bold", 7)
        c.setFillColorRGB(0, 0, 0)
        # Draw X centered on circle
        c.drawCentredString(ux, uy - 2.5, 'X')

    # ── Property fields ────────────────────────────────────────────────
    d(data.get('plotNo', ''),         65, 'plotNo',       maxw=155)
    d(data.get('makaniNo', ''),       347, 'makaniNo',     maxw=113)
    d(data.get('buildingName', ''),    90, 'buildingName', maxw=155)
    # Property No: starts after label (label ends ~348pt)
    _draw(c, data.get('propertyNo', ''), X['propertyNo_x'], F['propertyNo'], maxw=155, fs=8)
    d(data.get('propertyType', ''),    90, 'propertyType', maxw=155)
    # Property Area: after label
    _draw(c, data.get('propertyArea', ''), X['propertyArea_x'], F['propertyArea'], maxw=125, fs=8)
    d(data.get('location', ''),        90, 'location',     maxw=155)
    # DEWA Premises: tight — Arabic starts at pdf_x~379
    _draw(c, data.get('dewaPremises', ''), X['dewaPremises_x'], F['dewaPremises'], maxw=110, fs=8)

    # ── Contract ───────────────────────────────────────────────────────
    d(data.get('contractFrom', ''),      147, 'contractFrom',    maxw=58)
    d(data.get('contractTo', ''),        217, 'contractTo',      maxw=78)
    d(data.get('contractValue', ''),     347, 'contractValue',   maxw=113)
    d(data.get('annualRent', ''),         90, 'annualRent',      maxw=155)
    d(data.get('securityDeposit', ''),   347, 'securityDeposit', maxw=113)
    d(data.get('modeOfPayment', ''),      90, 'modeOfPayment',   maxw=370)

    # ── Additional terms on page 3 — pixel-verified y positions ──────
    TERM_YS = [526.2, 494.3, 462.3, 430.3, 398.3]

    c.save()
    packet.seek(0)

    # Build a separate overlay for page 3 if there are additional terms
    page3_packet = None
    terms = data.get('additionalTerms') or []
    terms = [t for t in terms if t and str(t).strip()]
    if terms:
        page3_packet = io.BytesIO()
        c3 = canvas.Canvas(page3_packet, pagesize=(PAGE_W, PAGE_H))
        c3.setFillColorRGB(0, 0, 0)
        for i, term in enumerate(terms[:5]):
            t = str(term).strip()
            c3.setFont("Helvetica", 7.5)
            # Truncate to fit 490pt width
            while len(t) > 1 and c3.stringWidth(t, "Helvetica", 7.5) > 490:
                t = t[:-1]
            c3.drawString(58, TERM_YS[i], t)
        c3.save()
        page3_packet.seek(0)

    template = PdfReader(template_path)
    overlay  = PdfReader(packet)
    writer   = PdfWriter()
    for i, page in enumerate(template.pages):
        if i == 0:
            page.merge_page(overlay.pages[0])
        elif i == 2 and page3_packet:
            p3_overlay = PdfReader(page3_packet)
            page.merge_page(p3_overlay.pages[0])
        writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()
