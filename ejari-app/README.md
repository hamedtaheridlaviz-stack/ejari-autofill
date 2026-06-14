# Ejari Contract Auto-Fill

Generate filled Ejari Unified Tenancy Contract PDFs from a mobile-friendly web form.
Includes **Emirates ID scanning** — take a photo and fields auto-populate via Claude Vision.

## Features

- ✅ Fill all Ejari contract fields (Owner, Tenant, Property, Contract)
- 📷 Scan Emirates ID with camera → auto-fills name + ID number
- 📱 Mobile-first responsive design, works on phone
- ⬇️ Instant PDF download, ready to print and sign
- 🇦🇪 Bilingual UI (English + Arabic labels)

## Quick Start (Local)

```bash
# Install dependencies
pip install pypdf reportlab

# Add your API key (for ID scanning)
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=sk-ant-...

# Run
python server.py
# Open http://localhost:3000
```

## Deploy to Vercel (Node.js version)

If you prefer Vercel, install Node dependencies and deploy:

```bash
npm install
vercel

# Add ANTHROPIC_API_KEY in Vercel dashboard → Settings → Environment Variables
```

## Project Structure

```
ejari-app/
├── public/
│   └── index.html        # Mobile-first form UI
├── api/
│   ├── generate.js       # PDF fill (Vercel/Node)
│   └── scan-id.js        # Emirates ID OCR (Vercel/Node)
├── server.py             # Local dev server (pure Python)
├── fill_ejari.py         # PDF fill logic (Python)
├── ejari_template.pdf    # Official Ejari PDF template
├── requirements.txt      # Python dependencies
├── vercel.json           # Vercel config
└── .env.example
```

## Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Required for ID scan. Get from console.anthropic.com |
| `PORT` | Server port (default: 3000) |

## Emirates ID Scanning

The scan feature uses Claude Vision API to read ID cards:
- **Front side**: extracts name, Emirates ID number, nationality, DOB
- Scanned values auto-fill the relevant form section with a blue highlight
- Works with camera capture or uploaded photos
