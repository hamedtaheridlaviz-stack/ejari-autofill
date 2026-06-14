"""server.py — Ejari Contract Generator · pure Python, no dependencies beyond stdlib"""

import os, json, base64, urllib.request, urllib.error, io
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from fill_ejari import fill_ejari_pdf

BASE   = Path(__file__).parent
TPL    = str(BASE / 'ejari_template.pdf')
PUB    = BASE / 'public'
KEY    = os.environ.get('ANTHROPIC_API_KEY', '')

class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *a): print(f"  {fmt % a}")

    def body(self):
        return self.rfile.read(int(self.headers.get('Content-Length', 0)))

    def json_out(self, status, data):
        b = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(b))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        p = self.path.split('?')[0]
        if p == '/': p = '/index.html'
        fp = PUB / p.lstrip('/')
        if fp.exists() and fp.is_file():
            data = fp.read_bytes()
            ct = {'html':'text/html','css':'text/css','js':'application/javascript',
                  'png':'image/png','ico':'image/x-icon'}.get(fp.suffix.lstrip('.'), 'application/octet-stream')
            self.send_response(200)
            self.send_header('Content-Type', ct)
            self.send_header('Content-Length', len(data))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.json_out(404, {'error': 'Not found'})

    def do_POST(self):
        p = self.path.split('?')[0]
        if p == '/api/generate':    self._generate()
        elif p == '/api/scan-id':   self._scan_id()
        else:                        self.json_out(404, {'error': 'Not found'})

    def _generate(self):
        try:
            data = json.loads(self.body())
            pdf  = fill_ejari_pdf(data, TPL)
            tenant = (data.get('tenants') or [{}])[0].get('name', 'contract').replace(' ','_')
            fname  = f'ejari_{tenant}.pdf'
            self.send_response(200)
            self.send_header('Content-Type', 'application/pdf')
            self.send_header('Content-Disposition', f'attachment; filename="{fname}"')
            self.send_header('Content-Length', len(pdf))
            self.end_headers()
            self.wfile.write(pdf)
        except Exception as e:
            print(f'  ERROR generate: {e}')
            self.json_out(500, {'error': str(e)})

    def _scan_id(self):
        if not KEY:
            return self.json_out(503, {'error': 'ANTHROPIC_API_KEY not set. See .env.example.'})
        try:
            payload  = json.loads(self.body())
            b64      = payload.get('imageBase64')
            mime     = payload.get('mimeType', 'image/jpeg')
            side     = payload.get('side', 'front')
            doc_type = payload.get('docType', 'eid')

            if not b64:
                return self.json_out(400, {'error': 'No image'})

            if doc_type == 'deed':
                prompt = (
                    'This is a Dubai Land Department (DLD) title deed or property document. '
                    'Extract all visible property details: owner full name, unit/apartment number, '
                    'building name, location/area (e.g. Dubai Marina), plot number, '
                    'property type (apartment/villa/office), total area in square meters, '
                    'DEWA premises number, Makani number if visible. '
                    'Return ONLY valid JSON with keys: ownerName, unitNo, buildingName, '
                    'location, plotNo, propertyType, area, dewaNo, makaniNo. '
                    'Use null for any field not visible in the document.'
                )
            elif doc_type == 'passport':
                prompt = (
                    'This is a passport document. Extract: full name in English, passport number, '
                    'nationality, date of birth (DD/MM/YYYY), gender, expiry date. '
                    'Return ONLY valid JSON with keys: fullName, passportNo, nationality, '
                    'dateOfBirth, gender, expiryDate. Use null for unclear fields.'
                )
            elif side == 'back':
                prompt = (
                    'UAE Emirates ID back side. Extract: address, employer, occupation, expiry date. '
                    'Return ONLY JSON: {address, employer, occupation, expiryDate}. null for missing.'
                )
            else:
                prompt = (
                    'UAE Emirates ID front side. Extract: full name in English, '
                    'Emirates ID number (format 784-XXXX-XXXXXXX-X), nationality, '
                    'date of birth DD/MM/YYYY, gender, expiry date. '
                    'Return ONLY valid JSON: {fullName, emiratesId, nationality, '
                    'dateOfBirth, gender, expiryDate}. null for unclear fields.'
                )

            req_data = json.dumps({
                'model': 'claude-sonnet-4-6',
                'max_tokens': 500,
                'messages': [{'role': 'user', 'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': mime, 'data': b64}},
                    {'type': 'text',  'text': prompt}
                ]}]
            }).encode()

            req = urllib.request.Request(
                'https://api.anthropic.com/v1/messages',
                data=req_data,
                headers={'Content-Type': 'application/json',
                         'x-api-key': KEY,
                         'anthropic-version': '2023-06-01'},
                method='POST'
            )
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())

            text  = (result.get('content') or [{}])[0].get('text', '')
            clean = text.replace('```json','').replace('```','').strip()
            self.json_out(200, json.loads(clean))

        except urllib.error.HTTPError as e:
            print(f'  Anthropic error: {e.code} {e.read().decode()}')
            self.json_out(502, {'error': f'AI API error {e.code}'})
        except Exception as e:
            print(f'  ERROR scan: {e}')
            self.json_out(500, {'error': str(e)})


if __name__ == '__main__':
    env = BASE / '.env'
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())
        KEY = os.environ.get('ANTHROPIC_API_KEY', '')

    port = int(os.environ.get('PORT', 3000))
    srv  = HTTPServer(('0.0.0.0', port), H)
    print(f'\n🏛️  Ejari Contract Generator  →  http://localhost:{port}')
    print(f'   ID scan: {"✅ enabled" if KEY else "⚠️  disabled (add ANTHROPIC_API_KEY to .env)"}')
    print('   Ctrl+C to stop\n')
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')
