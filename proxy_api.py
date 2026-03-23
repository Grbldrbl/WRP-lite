import http.server

PORT = 8080
HandlerClass = http.server.SimpleHTTPRequestHandler

# The right class for proxy mode is named 'http.server.ThreadingHTTPServer' (Python 3.7+) and '--bind'/'--proxy' flags.
# But for a real proxy you'll want a library like PySocks, or you can use 3rd party like 'python3 -m http.server --bind 0.0.0.0 --cgi --directory . --proxy' (Python 3.11+)
# For DSi, here's the easiest library-based proxy:

try:
    from http.server import ThreadingHTTPServer
except ImportError:
    from socketserver import ThreadingTCPServer as ThreadingHTTPServer

class Proxy(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        import urllib.request
        url = self.path
        if url.startswith('http://') or url.startswith('https://'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with urllib.request.urlopen(url) as f:
                self.copyfile(f, self.wfile)
        else:
            self.send_error(400, "Bad request")

httpd = ThreadingHTTPServer(('0.0.0.0', PORT), Proxy)
print(f"Serving HTTP proxy on port {PORT}")
httpd.serve_forever()
