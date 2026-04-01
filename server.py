"""
Juggernaut Method — Local Dev Server

Serves static files AND provides a JSON file-save API:
  GET  /api/data  → returns juggernaut-data.json (or {} if missing)
  POST /api/data  → writes request body to juggernaut-data.json

This keeps your training data as a plain file on disk,
independent of browser localStorage.
"""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'juggernaut-data.json')

class JuggernautHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    self.wfile.write(f.read().encode())
            else:
                self.wfile.write(b'{}')
            return
        return super().do_GET()

    def do_POST(self):
        if self.path == '/api/data':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                # Validate it's real JSON before writing
                data = json.loads(body)
                # Atomic write: write to temp file, then rename
                tmp_file = DATA_FILE + '.tmp'
                with open(tmp_file, 'w') as f:
                    json.dump(data, f, indent=2)
                os.replace(tmp_file, DATA_FILE)  # atomic on POSIX
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"ok": true}')
            except json.JSONDecodeError as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        # Quieter logging — only show errors and API calls
        if '/api/' in (args[0] if args else ''):
            super().log_message(format, *args)

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = HTTPServer(('127.0.0.1', port), JuggernautHandler)
    print(f'Juggernaut server running on http://localhost:{port}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down.')
        server.shutdown()
