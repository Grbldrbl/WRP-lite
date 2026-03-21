import requests
from flask import Flask, Response, redirect, request, send_file
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, unquote
import os

app = Flask(__name__)

SIMPLE_CSS = """
body { background: #fff; color: #222; font-family: sans-serif; margin: 10px; }
a { color: #0044cc; }
img { max-width: 100vw; height: auto; }
pre, code { background: #eee; padding: 2px 4px; }
"""

def simplify_html(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "iframe", "noscript", "link", "object", "embed"]):
        tag.decompose()
    for tag in soup(True):
        tag.attrs = {k: v for k, v in tag.attrs.items() if k in ['href', 'src', 'alt']}
    head = soup.head or soup.new_tag("head")
    style = soup.new_tag("style", type="text/css")
    style.string = SIMPLE_CSS
    head.append(style)
    if not soup.head:
        soup.html.insert(0, head)
    # Proxy all <a href> and <img src>
    for tag in soup.find_all('a', href=True):
        href = urljoin(base_url, tag['href'])
        if href.startswith('http'):
            tag['href'] = '/' + href
    for tag in soup.find_all('img', src=True):
        src = urljoin(base_url, tag['src'])
        if src.startswith('http'):
            tag['src'] = '/' + src
    return str(soup)

@app.route('/', methods=['GET'])
def root():
    url = request.args.get('url', '')
    if url:
        if not url.startswith('http'):
            url = 'http://' + url
        return redirect('/' + url)
    # Serve the static index.html page
    return send_file(os.path.join(os.path.dirname(__file__), 'index.html'))

@app.route('/<path:target_url>')
def proxy(target_url):
    real_url = unquote(target_url)
    if not (real_url.startswith('http://') or real_url.startswith('https://')):
        real_url = 'http://' + real_url
    parsed = urlparse(real_url)
    if parsed.hostname in ['localhost', '127.0.0.1', '::1']:
        return "Blocked"
    try:
        r = requests.get(real_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        ct = r.headers.get('content-type','')
        if 'text/html' in ct:
            html = simplify_html(r.text, r.url)
            return Response(html, content_type='text/html')
        elif ct.startswith('image/'):
            return Response(r.content, content_type=ct)
        else:
            return Response(r.content, content_type=ct)
    except Exception as e:
        return f"<b>Error:</b> {e}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
