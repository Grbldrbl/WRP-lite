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
            # The browser is making a relative path request (rare in proxy mode)
            self.send_error(400, "Bad request")
            return
        else:
            target_url = "http://" + url
        try:
            # Set a real User-Agent!
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            }
            resp = requests.get(target_url, headers=headers, timeout=10)
            ctype = resp.headers.get('Content-Type', '').lower()
            content = resp.content
            if "text/html" in ctype:
                soup = BeautifulSoup(content, "html.parser")
                for tag in soup(["script", "style", "noscript", "img"]):
                    tag.decompose()
                content = str(soup).encode('utf-8')
            self.send_response(resp.status_code)
            self.send_header('Content-Type', ctype or 'text/html')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(502, f"Proxy error: {e}")

def run_proxy():
    with socketserver.ThreadingTCPServer(("", PORT), LiteProxy) as httpd:
        print(f"[*] Serving 'lite' HTTP proxy on port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_proxy()
