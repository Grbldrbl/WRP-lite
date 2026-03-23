import socketserver
import http.server
import requests
from bs4 import BeautifulSoup

PORT = 8080

class LiteProxy(http.server.BaseHTTPRequestHandler):
    def do_CONNECT(self):
        self.send_error(501, "HTTPS not supported in this lite proxy.")
        
    def do_GET(self):
        url = self.path
        if url.startswith("http://"):
            target_url = url
        elif url.startswith("/http://"):
            target_url = url[1:]
        elif url.startswith("/"):
            self.send_error(400, "Bad request (path should be absolute URL, e.g. http://notyoutube.net/)")
            return
        else:
            target_url = "http://" + url

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/122.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "identity",  # Retro/DSi can't do gzip
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "",  # Some old sites expect empty referer
                "Host": target_url.split("/")[2]  # Extract notyoutube.net from "http://notyoutube.net/..."
            }
            # Remove port from host if present
            if ":" in headers["Host"]:
                headers["Host"] = headers["Host"].split(":")[0]
            resp = requests.get(target_url, headers=headers, timeout=20, allow_redirects=True)
            ctype = resp.headers.get('Content-Type', '').lower()
            content = resp.content
            if "text/html" in ctype:
                soup = BeautifulSoup(content, "html.parser")
                for tag in soup(["script", "style", "noscript", "img"]):
                    tag.decompose()
                content = str(soup).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', ctype or 'text/html')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            # Print any server response if present
            self.send_response(503)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<h1>Proxy error: {e}</h1>".encode('utf-8'))

def run_proxy():
    with socketserver.ThreadingTCPServer(("", PORT), LiteProxy) as httpd:
        print(f"[*] Serving 'lite' HTTP proxy on port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_proxy()
