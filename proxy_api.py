from flask import Flask, request, Response
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/', defaults={'url': ''})
@app.route('/<path:url>')
def proxy(url):
    full_url = request.args.get("u") or ("http://" + url if url else None)
    if not full_url or full_url == "http://":
        return '''
            <h2>No host supplied</h2>
            <p>To use this web proxy, add a URL:<br>
            <code>http://[your-ip]:8080/http://example.com</code> or 
            <code>http://[your-ip]:8080/?u=http://example.com</code>
            </p>
        ''', 400
    try:
        resp = requests.get(full_url, timeout=10)
        soup = BeautifulSoup(resp.content, "html.parser")

        # Remove scripts, images, and style for compatibility
        for tag in soup(["script", "style", "noscript", "img"]):
            tag.decompose()
        for tag in soup(["link"]):
            if tag.get("rel") == ["stylesheet"]:
                tag.decompose()

        # You could also strip out big tables, divs, or other "heavy" tags here
        # for tag in soup(["table", "iframe", "object", "embed"]): tag.decompose()

        return Response(str(soup), content_type=resp.headers.get("Content-Type", "text/html"))
    except Exception as e:
        return f"<h1>Proxy Error</h1><p>{e}</p>", 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
