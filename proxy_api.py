import requests
from flask import Flask, request, redirect, Response, url_for
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, quote, unquote

app = Flask(__name__)

SIMPLE_CSS = """
body { background: #fff; color: #222; font-family: sans-serif; margin: 10px; line-height: 1.4; }
a { color: #0044cc; }
img { max-width: 100vw; height: auto; }
pre, code { background: #eee; padding: 2px 4px; }
"""

def simplify_html(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    # Remove scripts, styles, iframes, embeds (etc.)
    for tag in soup(["script", "style", "iframe", "noscript", "link", "object", "embed"]):
        tag.decompose()
    # Remove inline style/class
    for tag in soup(True):
        tag.attrs = {k:v for k,v in tag.attrs.items() if k in ['href', 'src', 'alt']}
    # Add simple CSS
    head = soup.head or soup.new_tag("head")
    style = soup.new_tag("style", type="text/css")
    style.string = SIMPLE_CSS
    head.append(style)
    if not soup.head:
        soup.html.insert(0, head)
    # Rewrite all <a href...> and <img src...> to use our proxy
    for tag in soup.find_all(['a', 'img'], href=True) + soup.find_all(['img'], src=True):
        if tag.name == 'a' and 'href' in tag.attrs:
            href = urljoin(base_url, tag['href'])
            tag['href'] = url_for('proxy', url=quote(href))
        elif tag.name == 'img' and 'src' in tag.attrs:
            src = urljoin(base_url, tag['src'])
            tag['src'] = url_for('proxy', url=quote(src))
    return str(soup)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        url = request.form.get('url', '')
        if not url.startswith('http'):
            url = 'http://' + url
        return redirect(url_for('proxy', url=quote(url)))
    return '''
    <html>
      <head>
        <title>Simple Proxy</title>
        <style>
            body { font-family:sans-serif; margin:1em; background:#fafaff; }
            input[type=text] { width:320px; font-size:1em; }
            button, input[type=submit] { font-size:1em; }
        </style>
      </head>
      <body>
        <h2>Simple Web Proxy</h2>
        <form method="post">
            <input name="url" type="text" placeholder="https://example.com" required>
            <input type="submit" value="Go">
        </form>
        <p>Enter a URL above. Click links to stay proxied.<br>CSS/images are simplified for DSi browsers.</p>
      </body>
    </html>
    '''

@app.route('/proxy')
def proxy():
    url = request.args.get('url')
    if not url: return redirect(url_for('home'))
    url = unquote(url)
    # block access to localhost and local IPs to prevent SSRF
    parsed = urlparse(url)
    if parsed.hostname in ['localhost', '127.0.0.1', '::1']:
        return "Localhost blocked."
    try:
        resp = requests.get(url, timeout=10, headers={'User-Agent':'Mozilla/5.0'})
        ct = resp.headers.get('content-type','')
        if 'text/html' in ct:
            base_url = resp.url
            html = simplify_html(resp.text, base_url)
            return Response(html, content_type='text/html')
        elif ct.startswith('image/'):
            return Response(resp.content, content_type=ct)
        else:
            # basic passthrough for other content
            return Response(resp.content, content_type=ct)
    except Exception as e:
        return f"<b>Error:</b> {e}"

# Optional: Make /proxy/anything as easy as /proxy?url=
@app.route('/proxy/<path:url_part>')
def proxy_path(url_part):
    raw_url = unquote(url_part)
    if not (raw_url.startswith('http://') or raw_url.startswith('https://')):
        raw_url = 'http://' + raw_url
    return proxy_with_arg(raw_url)

def proxy_with_arg(url):
    # block SSRF as before, could unify
    parsed = urlparse(url)
    if parsed.hostname in ['localhost', '127.0.0.1', '::1']:
        return "Localhost blocked."
    try:
        resp = requests.get(url, timeout=10, headers={'User-Agent':'Mozilla/5.0'})
        ct = resp.headers.get('content-type','')
        if 'text/html' in ct:
            base_url = resp.url
            html = simplify_html(resp.text, base_url)
            return Response(html, content_type='text/html')
        elif ct.startswith('image/'):
            return Response(resp.content, content_type=ct)
        else:
            return Response(resp.content, content_type=ct)
    except Exception as e:
        return f"<b>Error:</b> {e}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
