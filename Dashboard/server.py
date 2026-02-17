#!/usr/bin/env python3
"""
Simple HTTP server for the Grasshopper Dashboard
Run this script to serve the dashboard locally
"""

import http.server
import socketserver
import os
import sys

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow cross-origin requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def guess_type(self, path):
        # Ensure .wasm files are served with correct MIME type
        mimetype, encoding = super().guess_type(path)
        if path.endswith('.wasm'):
            return 'application/wasm', encoding
        return mimetype, encoding

    def log_message(self, format, *args):
        # Custom log format
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format % args))

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print("Grasshopper Dashboard Server")
        print(f"Serving on http://localhost:{PORT}")
        print(f"Directory: {os.getcwd()}")
        print(f"\nMake sure Rhino.Compute is running on http://localhost:8081")
        print(f"\nPress Ctrl+C to stop the server\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped.")
