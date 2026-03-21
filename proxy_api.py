import requests
from flask import Flask, request, Response
from bs4 import BeautifulSoup

app = Flask(__name__)

SIMPLE_CSS = """
body {
    background: #fff; color: #222; font-family: sans-serif; margin: 10px; line-height: 1.4;
}
a { color: #0044cc; }
img { max-width: 100vw; height: auto; }
pre, code { background: #eee; padding: 2px 4px; }
"""

def simplify_html(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "iframe", "noscript", "link", "object", "embed"]):
        tag.decompose()
    for tag in soup(True):
        tag.attrs = {k: v for k, v in tag.attrs.items() if k in ["href", "src", "alt"]}
    head = soup.head or soup.new_tag("head")
    style = soup.new_tag("style", type="text/css")
    style.string = SIMPLE_CSS
    head.append(style)
    if not soup.head:
        soup.html.insert(0, head)
    return str(soup)

@app.route("/api/proxy")
def proxy_endpoint():
    url = request.args.get("url")
    if not url:
        return Response("Missing url parameter", status=400)
    if not url.startswith("http"):
        url = "http://" + url
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        html = simplify_html(resp.text)
        # Optionally rewrite links as in the previous example
        return Response(html, content_type="text/html")
    except Exception as e:
        return Response(f"Error: {str(e)}", status=400)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)