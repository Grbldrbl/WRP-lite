from flask import Flask, Response
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/<path:url>')
def proxy(url):
    # Prepend "https://" if no scheme is provided
    if not url.startswith("http"):
        url = "https://" + url
    try:
        # Fetch the live page with a User-Agent header
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})

        # Parse and simplify HTML
        soup = BeautifulSoup(resp.content, "html.parser")
        for tag in soup(["script", "style", "noscript", "img"]):
            tag.decompose()  # Remove these tags for retro/browser compatibility

        # Serve the simplified HTML
        return Response(
            str(soup),
            content_type=resp.headers.get("Content-Type", "text/html")
        )
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        # Show the full Python error report on failure
        return f"<h1>Proxy Error</h1><pre>{tb}</pre>", 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
