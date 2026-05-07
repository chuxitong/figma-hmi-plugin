"""
Temporary HTTP server to serve mockup PNGs for Figma plugin import.
Run this, then load the import plugin in Figma.
Stop with Ctrl+C when done.
"""
import http.server
import os

PORT = 8888
DIR = os.path.join(os.path.dirname(__file__), "png")

class CORSHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET")
        super().end_headers()

print(f"Serving mockup PNGs from: {DIR}")
print(f"URL: http://localhost:{PORT}/")
print("Keep this running while importing into Figma. Press Ctrl+C to stop.")
http.server.HTTPServer(("0.0.0.0", PORT), CORSHandler).serve_forever()
