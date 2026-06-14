/**
 * generate.js — Vercel serverless function
 * Fills page 1 of the Ejari Unified Tenancy Contract (official DLD PDF).
 * Pages 2 & 3 (terms, additional conditions, logos) are preserved exactly from the template.
 * Uses pdf-lib. Coordinates pixel-verified against the official template at 1000px height.
 */
import { PDFDocument, rgb, StandardFonts } from 'pdf-lib';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PAGE_H = 842;

// Reportlab y = PAGE_H - pdf_top. These match fill_ejari.py exactly.
const F = {
  date:            725.8,
  ownerName:       667.7,
  lessorName:      645.0,
  lessorEID:       621.4,
  licenseNo:       591.1,
  licensingAuth:   591.1,
  lessorEmail:     574.2,
  lessorPhone:     553.2,
  tenantName:      497.6,
  tenantEID:       474.0,
  tenantEmail:     426.9,
  tenantPhone:     405.0,
  plotNo:          325.0,
  makaniNo:        323.3,
  buildingName:    302.3,
  propertyNo:      300.6,
  propertyType:    277.9,
  propertyArea:    277.0,
  location:        256.8,
  dewaPremises:    255.1,
  contractFrom:    187.8,
  contractTo:      187.8,
  contractValue:   196.2,
  annualRent:      186.9,
  securityDeposit: 174.3,
  modeOfPayment:   152.4,
};

// X positions matching fill_ejari.py
const X = {
  lessorEID_start:  110,
  lessorEID_mid:    298,
  tenantEID_start:  110,
  tenantEID_mid:    298,
  ownerName_x:      110,
  ownerName2_x:     300,
  propertyNo_x:     350,
  propertyArea_x:   350,
  dewaPremises_x:   350,
};

// Radio circle centers (x, pdf_y_from_bottom) - pixel verified
const USAGE = {
  industrial:  [152.2, 347.5],
  commercial:  [258.8, 347.5],
  residential: [371.8, 347.5],
};

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  try {
    const data = req.body;

    // Load template from project root (all 3 pages with logos intact)
    const templatePath = path.join(process.cwd(), 'ejari_template.pdf');
    const templateBytes = fs.readFileSync(templatePath);
    const pdfDoc = await PDFDocument.load(templateBytes);

    const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
    const fontBold = await pdfDoc.embedFont(StandardFonts.HelveticaBold);
    const pages = pdfDoc.getPages();
    const page = pages[0]; // Only fill page 1; pages 2 & 3 stay untouched

    // Helper: draw text clipped to maxWidth
    function drawText(text, x, rlY, { maxw = 380, size = 8, bold = false } = {}) {
      if (!text) return;
      let t = String(text).trim();
      const f = bold ? fontBold : font;
      while (t.length > 1 && f.widthOfTextAtSize(t, size) > maxw) {
        t = t.slice(0, -1);
      }
      page.drawText(t, { x, y: rlY, size, font: f, color: rgb(0, 0, 0) });
    }

    function d(key, x, val, opts = {}) {
      if (F[key] === undefined) return;
      drawText(val, x, F[key], opts);
    }

    // ── Date ──────────────────────────────────────────────────────────
    d('date', 30, data.date);

    // ── Landlords ─────────────────────────────────────────────────────
    const landlords = (data.landlords && data.landlords.length) ? data.landlords : [{}];
    const ll = landlords[0];
    const owner1 = ll.name || '';

    if (landlords.length >= 2) {
      const owner2 = landlords[1].name || '';
      drawText(owner1, X.ownerName_x,  F.ownerName,  { maxw: 175 });
      drawText(owner2, X.ownerName2_x, F.ownerName,  { maxw: 175 });
      drawText(owner1, X.ownerName_x,  F.lessorName, { maxw: 175 });
      drawText(owner2, X.ownerName2_x, F.lessorName, { maxw: 175 });
    } else {
      d('ownerName',  X.ownerName_x, owner1,                    { maxw: 360 });
      d('lessorName', X.ownerName_x, ll.lessorName || owner1,   { maxw: 360 });
    }

    // EID row — primary left, 2nd right
    if (ll.emiratesId) drawText(ll.emiratesId, X.lessorEID_start, F.lessorEID, { maxw: 175 });
    if (landlords.length >= 2 && landlords[1].emiratesId) {
      drawText(landlords[1].emiratesId, X.lessorEID_mid, F.lessorEID, { maxw: 175 });
    }

    d('licenseNo',     90, ll.licenseNo    || '', { maxw: 155 });
    d('licensingAuth', 376, ll.licensingAuth || '', { maxw: 84 });
    d('lessorEmail',   90, ll.email        || '', { maxw: 370 });
    d('lessorPhone',   90, ll.phone        || '', { maxw: 370 });

    // Extra landlords annotation
    if (landlords.length > 2) {
      let noteY = F.lessorPhone - 11;
      for (let i = 2; i < landlords.length; i++) {
        const ex = landlords[i];
        const note = `+ Landlord ${i+1}: ${ex.name||''}  ID: ${ex.emiratesId||''}  ${ex.phone||''}`;
        page.drawText(note, { x: 90, y: noteY - (i-2)*9, size: 6.5, font, color: rgb(0.1, 0.2, 0.6) });
      }
    }

    // ── Tenants ────────────────────────────────────────────────────────
    const tenants = (data.tenants && data.tenants.length) ? data.tenants : [{}];
    const tt = tenants[0];

    d('tenantName', 90, tt.name || '', { maxw: 370 });
    if (tt.emiratesId) drawText(tt.emiratesId, X.tenantEID_start, F.tenantEID, { maxw: 175 });
    if (tenants.length >= 2 && tenants[1].emiratesId) {
      drawText(tenants[1].emiratesId, X.tenantEID_mid, F.tenantEID, { maxw: 175 });
    }
    d('tenantEmail', 90, tt.email || '', { maxw: 370 });
    d('tenantPhone', 90, tt.phone || '', { maxw: 370 });

    // Extra tenants annotation
    if (tenants.length > 1) {
      let noteY = F.tenantPhone - 11;
      for (let i = 1; i < tenants.length; i++) {
        const ex = tenants[i];
        const note = `+ Tenant ${i+1}: ${ex.name||''}  ID: ${ex.emiratesId||''}  ${ex.phone||''}`;
        page.drawText(note, { x: 90, y: noteY - (i-1)*9, size: 6.5, font, color: rgb(0.1, 0.2, 0.6) });
      }
    }

    // ── Property Usage X inside circle ────────────────────────────────
    const usage = (data.propertyUsage || 'residential').toLowerCase();
    if (USAGE[usage]) {
      const [ux, uy] = USAGE[usage];
      page.drawText('X', { x: ux - 3, y: uy - 3, size: 7, font: fontBold, color: rgb(0, 0, 0) });
    }

    // ── Property fields ───────────────────────────────────────────────
    d('plotNo',      65,  data.plotNo      || '', { maxw: 155 });
    d('makaniNo',    347, data.makaniNo    || '', { maxw: 113 });
    d('buildingName', 90, data.buildingName|| '', { maxw: 155 });
    drawText(data.propertyNo   || '', X.propertyNo_x,   F.propertyNo,   { maxw: 155 });
    d('propertyType', 90, data.propertyType|| '', { maxw: 155 });
    drawText(data.propertyArea || '', X.propertyArea_x, F.propertyArea, { maxw: 125 });
    d('location',     90, data.location   || '', { maxw: 155 });
    drawText(data.dewaPremises || '', X.dewaPremises_x, F.dewaPremises, { maxw: 110 });

    // ── Contract fields ───────────────────────────────────────────────
    d('contractFrom',    147, data.contractFrom    || '', { maxw: 58 });
    d('contractTo',      217, data.contractTo      || '', { maxw: 78 });
    d('contractValue',   347, data.contractValue   || '', { maxw: 113 });
    d('annualRent',       90, data.annualRent      || '', { maxw: 155 });
    d('securityDeposit', 347, data.securityDeposit || '', { maxw: 113 });
    d('modeOfPayment',    90, data.modeOfPayment   || '', { maxw: 370 });

    // ── Additional terms on page 3 — pixel-verified y positions ──────
    const TERM_YS = [526.2, 494.3, 462.3, 430.3, 398.3];
    if (data.additionalTerms && Array.isArray(data.additionalTerms)) {
      const page3 = pages[2];
      data.additionalTerms.slice(0, 5).forEach((term, i) => {
        if (!term || !term.trim()) return;
        page3.drawText(term.trim(), {
          x: 58, y: TERM_YS[i], size: 7.5, font,
          color: rgb(0, 0, 0), maxWidth: 490,
        });
      });
    }

    // ── Additional terms on page 3 (lines 1-5 are fillable) ──────────
    // Page 3 has 5 dotted lines for additional terms starting at ~pdf_y=530, spacing ~22
    if (data.additionalTerms && Array.isArray(data.additionalTerms)) {
      const page3 = pages[2];
      const termStartY = 530;
      const termSpacing = 22;
      data.additionalTerms.slice(0, 5).forEach((term, i) => {
        if (!term) return;
        page3.drawText(String(term), {
          x: 45,
          y: termStartY - i * termSpacing,
          size: 7.5,
          font,
          color: rgb(0, 0, 0),
          maxWidth: 490,
        });
      });
    }

    const pdfBytes = await pdfDoc.save();

    const tenantName = (tt.name || 'contract').replace(/\s+/g, '_');
    const dateStr = (data.date || 'undated').replace(/\//g, '-');

    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="ejari_${tenantName}_${dateStr}.pdf"`);
    res.setHeader('Content-Length', pdfBytes.length);
    res.status(200).send(Buffer.from(pdfBytes));

  } catch (err) {
    console.error('Generate error:', err);
    res.status(500).json({ error: err.message, stack: err.stack?.slice(0, 500) });
  }
}
